"""
角色管理 API - 组织架构中的角色类管理
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Role, User
from app.decorators import require_permission
from app.services import AuditService

roles_bp = Blueprint('roles', __name__)


@roles_bp.route('/', methods=['GET'])
@jwt_required()
def get_roles():
    """获取所有角色列表"""
    roles = Role.query.order_by(Role.level).all()
    return jsonify({
        'roles': [{
            'id': r.id,
            'name': r.name,
            'description': r.description,
            'level': r.level,
            'permissions': r.permissions or [],
            'user_count': len(r.users),
            'created_at': r.created_at.isoformat() if r.created_at else None
        } for r in roles]
    }), 200


@roles_bp.route('/<int:role_id>', methods=['GET'])
@jwt_required()
def get_role(role_id):
    """获取角色详情"""
    role = Role.query.get_or_404(role_id)
    return jsonify({
        'id': role.id,
        'name': role.name,
        'description': role.description,
        'level': role.level,
        'permissions': role.permissions or [],
        'data_scope': role.data_scope,
        'user_count': len(role.users),
        'created_at': role.created_at.isoformat() if role.created_at else None
    }), 200


@roles_bp.route('/', methods=['POST'])
@require_permission('user_manage')
def create_role():
    """创建角色"""
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'message': '角色名称不能为空', 'error': 'missing_fields'}), 400
    
    if Role.query.filter_by(name=data['name']).first():
        return jsonify({'message': '角色名称已存在', 'error': 'name_exists'}), 409
    
    role = Role(
        name=data['name'],
        description=data.get('description', ''),
        level=data.get('level', 4),
        permissions=data.get('permissions', []),
        data_scope=data.get('data_scope', 'self')
    )
    db.session.add(role)
    db.session.commit()
    
    AuditService.log_from_current_user(
        action='ROLE_CREATE',
        resource_type='role',
        resource_id=role.id,
        detail={'name': role.name},
        status='success'
    )
    
    return jsonify({
        'message': '角色创建成功',
        'role': {'id': role.id, 'name': role.name, 'description': role.description}
    }), 201


@roles_bp.route('/<int:role_id>', methods=['PUT'])
@require_permission('user_manage')
def update_role(role_id):
    """更新角色"""
    role = Role.query.get_or_404(role_id)
    data = request.get_json()
    
    if data.get('name') and data['name'] != role.name:
        if Role.query.filter_by(name=data['name']).first():
            return jsonify({'message': '角色名称已存在', 'error': 'name_exists'}), 409
        role.name = data['name']
    
    if 'description' in data:
        role.description = data['description']
    if 'level' in data:
        role.level = data['level']
    if 'permissions' in data:
        role.permissions = data['permissions']
    if 'data_scope' in data:
        role.data_scope = data['data_scope']
    
    db.session.commit()
    
    # 级联更新用户权限版本
    for user in role.users:
        user.permission_version = (user.permission_version or 1) + 1
    db.session.commit()
    
    AuditService.log_from_current_user(
        action='ROLE_UPDATE',
        resource_type='role',
        resource_id=role_id,
        detail={'name': role.name},
        status='success'
    )
    
    return jsonify({'message': '角色更新成功'}), 200


@roles_bp.route('/<int:role_id>', methods=['DELETE'])
@require_permission('user_manage')
def delete_role(role_id):
    """删除角色"""
    role = Role.query.get_or_404(role_id)
    
    if role.users:
        return jsonify({
            'message': '该角色下还有用户，无法删除',
            'error': 'has_users'
        }), 400
    
    db.session.delete(role)
    db.session.commit()
    
    AuditService.log_from_current_user(
        action='ROLE_DELETE',
        resource_type='role',
        resource_id=role_id,
        detail={'name': role.name},
        status='success'
    )
    
    return jsonify({'message': '角色已删除'}), 200


@roles_bp.route('/<int:role_id>/members', methods=['GET'])
@jwt_required()
def get_role_members(role_id):
    """获取角色成员列表"""
    role = Role.query.get_or_404(role_id)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    users_query = User.query.filter(User.roles.any(id=role_id))
    total = users_query.count()
    users = users_query.offset((page - 1) * per_page).limit(per_page).all()
    
    return jsonify({
        'members': [u.to_dict(include_email=True) for u in users],
        'total': total,
        'page': page,
        'per_page': per_page
    }), 200


@roles_bp.route('/<int:role_id>/members', methods=['POST'])
@require_permission('user_manage')
def add_role_member(role_id):
    """添加成员到角色"""
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'message': '请提供用户ID', 'error': 'missing_fields'}), 400
    
    role = Role.query.get_or_404(role_id)
    user = User.query.get_or_404(user_id)
    
    if role in user.roles:
        return jsonify({'message': '该用户已拥有此角色', 'error': 'already_has_role'}), 400
    
    user.roles.append(role)
    user.permission_version = (user.permission_version or 1) + 1
    db.session.commit()
    
    return jsonify({
        'message': f'已将 {user.real_name or user.username} 添加到 {role.name}'
    }), 200


@roles_bp.route('/<int:role_id>/members/<int:user_id>', methods=['DELETE'])
@require_permission('user_manage')
def remove_role_member(role_id, user_id):
    """从角色中移除成员"""
    role = Role.query.get_or_404(role_id)
    user = User.query.get_or_404(user_id)
    
    if role not in user.roles:
        return jsonify({'message': '该用户没有此角色', 'error': 'not_in_role'}), 400
    
    user.roles.remove(role)
    user.permission_version = (user.permission_version or 1) + 1
    db.session.commit()
    
    return jsonify({
        'message': f'已将 {user.real_name or user.username} 从 {role.name} 移除'
    }), 200


@roles_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_role_stats():
    """获取角色统计"""
    from sqlalchemy import func
    total_roles = Role.query.count()
    total_users_with_role = User.query.filter(User.roles.any()).count()
    
    role_stats = db.session.query(
        Role.id, Role.name, func.count(User.id)
    ).outerjoin(User, Role.users).group_by(Role.id).all()
    
    return jsonify({
        'total_roles': total_roles,
        'total_users_with_role': total_users_with_role,
        'by_role': [
            {'id': r[0], 'name': r[1], 'count': r[2]} for r in role_stats
        ]
    }), 200
