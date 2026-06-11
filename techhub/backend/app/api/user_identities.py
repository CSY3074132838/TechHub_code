"""
用户身份管理 API
一个用户可在多个部门拥有不同身份（部门+职位+角色）
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, UserIdentity, Department, Role
from app.decorators import require_permission
from app.services import AuditService

user_identities_bp = Blueprint('user_identities', __name__)


@user_identities_bp.route('/users/<int:user_id>/identities', methods=['GET'])
@jwt_required()
def get_user_identities(user_id):
    """获取用户的所有身份"""
    user = User.query.get_or_404(user_id)
    identities = UserIdentity.query.filter_by(user_id=user_id).order_by(
        UserIdentity.is_primary.desc(),
        UserIdentity.created_at.asc()
    ).all()
    return jsonify({
        'identities': [identity.to_dict() for identity in identities]
    }), 200


@user_identities_bp.route('/users/<int:user_id>/identities', methods=['POST'])
@jwt_required()
@require_permission('user_manage')
def create_user_identity(user_id):
    """为用户添加新身份"""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if not data.get('department_id'):
        return jsonify({'message': '请选择部门', 'error': 'missing_department'}), 400
    
    department = Department.query.get(data['department_id'])
    if not department:
        return jsonify({'message': '部门不存在', 'error': 'department_not_found'}), 404
    
    # 创建身份
    identity = UserIdentity(
        user_id=user_id,
        department_id=data['department_id'],
        position=data.get('position', ''),
        is_primary=data.get('is_primary', False)
    )
    
    # 如果设为唯一身份，自动设为主身份
    existing_count = UserIdentity.query.filter_by(user_id=user_id).count()
    if existing_count == 0 or data.get('is_primary'):
        # 取消其他主身份
        if data.get('is_primary'):
            UserIdentity.query.filter_by(user_id=user_id, is_primary=True).update({'is_primary': False})
        identity.is_primary = True
    
    # 分配角色
    if 'role_ids' in data:
        roles = Role.query.filter(Role.id.in_(data['role_ids'])).all()
        identity.roles = roles
    
    db.session.add(identity)
    db.session.commit()
    
    # 同步更新用户主部门/职位（保持兼容性）
    _sync_user_primary_identity(user)
    
    AuditService.log_from_current_user(
        action=AuditService.USER_UPDATE,
        resource_type='user_identity',
        resource_id=identity.id,
        detail={'user_id': user_id, 'department_id': data['department_id'], 'action': 'create_identity'},
        status='success'
    )
    
    return jsonify({
        'message': '身份添加成功',
        'identity': identity.to_dict()
    }), 201


@user_identities_bp.route('/users/<int:user_id>/identities/<int:identity_id>', methods=['PUT'])
@jwt_required()
@require_permission('user_manage')
def update_user_identity(user_id, identity_id):
    """更新用户身份"""
    identity = UserIdentity.query.filter_by(id=identity_id, user_id=user_id).first_or_404()
    data = request.get_json()
    
    if 'department_id' in data:
        department = Department.query.get(data['department_id'])
        if not department:
            return jsonify({'message': '部门不存在', 'error': 'department_not_found'}), 404
        identity.department_id = data['department_id']
    
    if 'position' in data:
        identity.position = data['position']
    
    if 'is_primary' in data and data['is_primary']:
        # 取消其他主身份
        UserIdentity.query.filter_by(user_id=user_id, is_primary=True).update({'is_primary': False})
        identity.is_primary = True
    
    if 'role_ids' in data:
        roles = Role.query.filter(Role.id.in_(data['role_ids'])).all()
        identity.roles = roles
    
    db.session.commit()
    
    # 同步更新用户主部门/职位
    user = User.query.get(user_id)
    _sync_user_primary_identity(user)
    
    AuditService.log_from_current_user(
        action=AuditService.USER_UPDATE,
        resource_type='user_identity',
        resource_id=identity_id,
        detail={'user_id': user_id, 'action': 'update_identity'},
        status='success'
    )
    
    return jsonify({
        'message': '身份更新成功',
        'identity': identity.to_dict()
    }), 200


@user_identities_bp.route('/users/<int:user_id>/identities/<int:identity_id>', methods=['DELETE'])
@jwt_required()
@require_permission('user_manage')
def delete_user_identity(user_id, identity_id):
    """删除用户身份"""
    identity = UserIdentity.query.filter_by(id=identity_id, user_id=user_id).first_or_404()
    was_primary = identity.is_primary
    
    db.session.delete(identity)
    db.session.commit()
    
    # 如果删除的是主身份，需要重新指定主身份
    user = User.query.get(user_id)
    if was_primary:
        remaining = UserIdentity.query.filter_by(user_id=user_id).order_by(UserIdentity.created_at.asc()).first()
        if remaining:
            remaining.is_primary = True
            db.session.commit()
    
    # 同步更新用户主部门/职位
    _sync_user_primary_identity(user)
    
    AuditService.log_from_current_user(
        action=AuditService.USER_UPDATE,
        resource_type='user_identity',
        resource_id=identity_id,
        detail={'user_id': user_id, 'action': 'delete_identity'},
        status='success'
    )
    
    return jsonify({'message': '身份已删除'}), 200


@user_identities_bp.route('/users/<int:user_id>/identities/<int:identity_id>/set-primary', methods=['POST'])
@jwt_required()
@require_permission('user_manage')
def set_primary_identity(user_id, identity_id):
    """设为主身份"""
    identity = UserIdentity.query.filter_by(id=identity_id, user_id=user_id).first_or_404()
    
    # 取消其他主身份
    UserIdentity.query.filter_by(user_id=user_id, is_primary=True).update({'is_primary': False})
    identity.is_primary = True
    db.session.commit()
    
    # 同步更新用户主部门/职位
    user = User.query.get(user_id)
    _sync_user_primary_identity(user)
    
    return jsonify({
        'message': '已设为主身份',
        'identity': identity.to_dict()
    }), 200


# ================================================
# 【第三次迭代于然负责】(6) 用户管理与组织架构同步
# 当用户管理页面编辑某员工部门后，同步更新 users 表
# 使组织架构部门正确显示该员工
# ================================================
def _sync_user_primary_identity(user):
    """同步用户主身份到 users 表（保持向后兼容）
    【第三次迭代于然负责】(6) 实现用户管理与组织架构的同步"""
    primary = UserIdentity.query.filter_by(user_id=user.id, is_primary=True).first()
    if primary:
        user.department_id = primary.department_id
        user.department = primary.department.name if primary.department else None
        user.position = primary.position
    else:
        # 没有身份时清空
        remaining = UserIdentity.query.filter_by(user_id=user.id).order_by(UserIdentity.created_at.asc()).first()
        if remaining:
            remaining.is_primary = True
            user.department_id = remaining.department_id
            user.department = remaining.department.name if remaining.department else None
            user.position = remaining.position
        else:
            user.department_id = None
            user.department = None
            user.position = None
    db.session.commit()
