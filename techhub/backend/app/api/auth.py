"""
认证相关 API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from app import db
from app.models import User, Role
from app.services import AuditService, CacheService
from datetime import datetime

# 登录安全策略常量
MAX_LOGIN_ATTEMPTS = 5      # 最大尝试次数
LOGIN_LOCKOUT_MINUTES = 15  # 锁定时长（分钟）


def _get_login_fail_key(username):
    """获取登录失败计数缓存Key"""
    return f"login_fail:{username}"


def _is_account_locked(username):
    """检查账号是否因登录失败过多被锁定"""
    fail_count = CacheService.get(_get_login_fail_key(username))
    if fail_count and int(fail_count) >= MAX_LOGIN_ATTEMPTS:
        return True
    return False


def _record_login_failure(username):
    """记录一次登录失败"""
    key = _get_login_fail_key(username)
    fail_count = CacheService.get(key)
    if fail_count is None:
        fail_count = 0
    fail_count = int(fail_count) + 1
    CacheService.set(key, fail_count, ttl=LOGIN_LOCKOUT_MINUTES * 60)
    return fail_count


def _clear_login_failures(username):
    """登录成功后清除失败计数"""
    CacheService.delete(_get_login_fail_key(username))

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    
    # 验证必填字段
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'message': '请提供用户名、邮箱和密码', 'error': 'missing_fields'}), 400
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': '用户名已存在', 'error': 'username_exists'}), 409
    
    # 检查邮箱是否已存在
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': '邮箱已存在', 'error': 'email_exists'}), 409
    
    # 创建新用户
    user = User(
        username=data['username'],
        email=data['email'],
        real_name=data.get('real_name', ''),
        phone=data.get('phone', ''),
        department=data.get('department', ''),
        position=data.get('position', '')
    )
    user.set_password(data['password'])
    
    # 分配默认角色
    default_role = Role.query.filter_by(name='member').first()
    if default_role:
        user.roles.append(default_role)
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'message': '注册成功',
        'user': user.to_dict()
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': '请提供用户名和密码', 'error': 'missing_credentials'}), 400
    
    username_input = data.get('username')
    
    # 检查账号是否被锁定
    if _is_account_locked(username_input):
        AuditService.log(
            action=AuditService.LOGIN_FAILED,
            username=username_input,
            detail={'reason': 'account_locked', 'ip': request.remote_addr},
            status='failure'
        )
        return jsonify({
            'message': f'登录失败次数过多，账号已锁定 {LOGIN_LOCKOUT_MINUTES} 分钟',
            'error': 'account_locked',
            'lockout_minutes': LOGIN_LOCKOUT_MINUTES
        }), 403
    
    # 查找用户（支持用户名或邮箱登录）
    user = User.query.filter(
        (User.username == username_input) | (User.email == username_input)
    ).first()
    
    if not user or not user.check_password(data['password']):
        fail_count = _record_login_failure(username_input)
        remaining = max(0, MAX_LOGIN_ATTEMPTS - fail_count)
        
        AuditService.log(
            action=AuditService.LOGIN_FAILED,
            username=username_input,
            detail={'reason': 'invalid_credentials', 'ip': request.remote_addr, 'fail_count': fail_count},
            status='failure'
        )
        
        if remaining == 0:
            return jsonify({
                'message': f'登录失败次数过多，账号已锁定 {LOGIN_LOCKOUT_MINUTES} 分钟',
                'error': 'account_locked',
                'lockout_minutes': LOGIN_LOCKOUT_MINUTES
            }), 403
        
        return jsonify({
            'message': f'用户名或密码错误，还剩 {remaining} 次机会',
            'error': 'invalid_credentials',
            'remaining_attempts': remaining
        }), 401
    
    if not user.is_active:
        AuditService.log(
            action=AuditService.LOGIN_FAILED,
            user_id=user.id,
            username=user.username,
            detail={'reason': 'account_disabled'},
            status='failure'
        )
        return jsonify({'message': '账号已被禁用', 'error': 'account_disabled'}), 403
    
    # 更新最后登录时间
    user.last_login = datetime.now()
    db.session.commit()
    
    # 登录成功，清除失败计数
    _clear_login_failures(username_input)
    
    # 记录登录成功审计日志
    AuditService.log(
        action=AuditService.LOGIN,
        user_id=user.id,
        username=user.username,
        detail={'ip': request.remote_addr},
        status='success'
    )
    
    # 创建 JWT Token（携带权限版本号，用于即时生效校验）
    access_token = create_access_token(
        identity=user.id,
        additional_claims={
            'username': user.username,
            'roles': [role.name for role in user.roles],
            'permission_version': user.permission_version
        }
    )
    refresh_token = create_refresh_token(
        identity=user.id,
        additional_claims={
            'permission_version': user.permission_version
        }
    )
    
    return jsonify({
        'message': '登录成功',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict(include_email=True)
    }), 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """刷新访问令牌"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.is_active:
        return jsonify({'message': '用户不存在或已被禁用', 'error': 'invalid_user'}), 401
    
    access_token = create_access_token(
        identity=user.id,
        additional_claims={
            'username': user.username,
            'roles': [role.name for role in user.roles],
            'permission_version': user.permission_version
        }
    )
    
    # 记录Token刷新审计日志
    AuditService.log(
        action=AuditService.TOKEN_REFRESH,
        user_id=user.id,
        username=user.username,
        status='success'
    )
    
    return jsonify({
        'access_token': access_token
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """用户登出"""
    jti = get_jwt()['jti']
    exp = get_jwt()['exp']
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # 计算token剩余有效期用于缓存TTL
    import time
    expires_in = int(exp - time.time()) if exp else 86400
    CacheService.revoke_token(jti, expires_in=expires_in)
    
    # 记录登出审计日志
    AuditService.log(
        action=AuditService.LOGOUT,
        user_id=current_user_id,
        username=user.username if user else 'unknown',
        status='success'
    )
    
    return jsonify({'message': '登出成功'}), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """获取当前用户信息"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': '用户不存在', 'error': 'user_not_found'}), 404
    
    return jsonify({
        'user': user.to_dict(include_email=True)
    }), 200

@auth_bp.route('/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    """修改密码"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': '用户不存在', 'error': 'user_not_found'}), 404
    
    data = request.get_json()
    
    if not data or not data.get('old_password') or not data.get('new_password'):
        return jsonify({'message': '请提供旧密码和新密码', 'error': 'missing_fields'}), 400
    
    if not user.check_password(data['old_password']):
        return jsonify({'message': '旧密码错误', 'error': 'wrong_password'}), 400
    
    user.set_password(data['new_password'])
    db.session.commit()
    
    # 记录密码修改审计日志
    AuditService.log(
        action=AuditService.PASSWORD_CHANGE,
        user_id=current_user_id,
        username=user.username,
        status='success'
    )
    
    return jsonify({'message': '密码修改成功'}), 200

# JWT Token 黑名单检查
@auth_bp.route('/check-token', methods=['GET'])
@jwt_required()
def check_token():
    """检查 Token 是否有效"""
    return jsonify({'valid': True}), 200
