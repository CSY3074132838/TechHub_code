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
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

# 用于存储已注销的token（生产环境应使用Redis）
revoked_tokens = set()

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
    
    # 查找用户（支持用户名或邮箱登录）
    user = User.query.filter(
        (User.username == data['username']) | (User.email == data['username'])
    ).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'message': '用户名或密码错误', 'error': 'invalid_credentials'}), 401
    
    if not user.is_active:
        return jsonify({'message': '账号已被禁用', 'error': 'account_disabled'}), 403
    
    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # 创建 JWT Token
    access_token = create_access_token(
        identity=user.id,
        additional_claims={
            'username': user.username,
            'roles': [role.name for role in user.roles]
        }
    )
    refresh_token = create_refresh_token(identity=user.id)
    
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
            'roles': [role.name for role in user.roles]
        }
    )
    
    return jsonify({
        'access_token': access_token
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """用户登出"""
    jti = get_jwt()['jti']
    revoked_tokens.add(jti)
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
    
    return jsonify({'message': '密码修改成功'}), 200

# JWT Token 黑名单检查
@auth_bp.route('/check-token', methods=['GET'])
@jwt_required()
def check_token():
    """检查 Token 是否有效"""
    return jsonify({'valid': True}), 200
