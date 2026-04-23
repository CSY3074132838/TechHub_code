"""
用户管理 API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Role

users_bp = Blueprint('users', __name__)

def admin_required(fn):
    """管理员权限装饰器"""
    from functools import wraps
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user or not user.has_permission('all'):
            return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
        return fn(*args, **kwargs)
    return wrapper

@users_bp.route('/', methods=['GET'])
@jwt_required()
def get_users():
    """获取用户列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    department = request.args.get('department')
    search = request.args.get('search')
    
    query = User.query
    
    if department:
        query = query.filter_by(department=department)
    
    if search:
        query = query.filter(
            (User.username.contains(search)) |
            (User.real_name.contains(search)) |
            (User.email.contains(search))
        )
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    users = pagination.items
    
    return jsonify({
        'users': [user.to_dict() for user in users],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    }), 200

@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """获取单个用户信息"""
    user = User.query.get_or_404(user_id)
    return jsonify({'user': user.to_dict(include_email=True)}), 200

@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """更新用户信息"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # 只能修改自己的信息，或者管理员可以修改任何人
    if current_user_id != user_id and not current_user.has_permission('all'):
        return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    # 更新允许修改的字段
    allowed_fields = ['real_name', 'phone', 'department', 'position', 'avatar']
    for field in allowed_fields:
        if field in data:
            setattr(user, field, data[field])
    
    # 只有管理员可以修改角色
    if 'roles' in data and current_user.has_permission('all'):
        role_ids = data['roles']
        user.roles = Role.query.filter(Role.id.in_(role_ids)).all()
    
    # 只有管理员可以修改激活状态
    if 'is_active' in data and current_user.has_permission('all'):
        user.is_active = data['is_active']
    
    db.session.commit()
    
    return jsonify({
        'message': '用户信息更新成功',
        'user': user.to_dict(include_email=True)
    }), 200

@users_bp.route('/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """删除用户（软删除）"""
    user = User.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()
    
    return jsonify({'message': '用户已禁用'}), 200

@users_bp.route('/departments', methods=['GET'])
@jwt_required()
def get_departments():
    """获取所有部门列表"""
    departments = db.session.query(User.department).distinct().all()
    return jsonify({
        'departments': [d[0] for d in departments if d[0]]
    }), 200

@users_bp.route('/roles', methods=['GET'])
@jwt_required()
def get_roles():
    """获取所有角色列表"""
    roles = Role.query.all()
    return jsonify({
        'roles': [role.to_dict() for role in roles]
    }), 200

@users_bp.route('/roles', methods=['POST'])
@admin_required
def create_role():
    """创建新角色（仅管理员）"""
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'message': '角色名称不能为空', 'error': 'missing_name'}), 400
    
    if Role.query.filter_by(name=data['name']).first():
        return jsonify({'message': '角色名称已存在', 'error': 'name_exists'}), 409
    
    role = Role(
        name=data['name'],
        description=data.get('description', ''),
        level=data.get('level', 4),
        permissions=data.get('permissions', [])
    )
    db.session.add(role)
    db.session.commit()
    
    return jsonify({
        'message': '角色创建成功',
        'role': role.to_dict()
    }), 201

@users_bp.route('/roles/<int:role_id>', methods=['PUT'])
@admin_required
def update_role(role_id):
    """更新角色信息（仅管理员）"""
    role = Role.query.get_or_404(role_id)
    data = request.get_json()
    
    if 'name' in data:
        existing = Role.query.filter_by(name=data['name']).first()
        if existing and existing.id != role_id:
            return jsonify({'message': '角色名称已存在', 'error': 'name_exists'}), 409
        role.name = data['name']
    
    if 'description' in data:
        role.description = data['description']
    if 'level' in data:
        role.level = data['level']
    if 'permissions' in data:
        role.permissions = data['permissions']
    
    db.session.commit()
    
    return jsonify({
        'message': '角色更新成功',
        'role': role.to_dict()
    }), 200

@users_bp.route('/roles/<int:role_id>', methods=['DELETE'])
@admin_required
def delete_role(role_id):
    """删除角色（仅管理员）"""
    role = Role.query.get_or_404(role_id)
    
    # 检查是否有用户正在使用该角色
    if role.users:
        return jsonify({
            'message': '该角色下还有用户，无法删除',
            'error': 'role_in_use'
        }), 409
    
    db.session.delete(role)
    db.session.commit()
    
    return jsonify({'message': '角色已删除'}), 200

@users_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_user_stats():
    """获取用户统计数据"""
    total = User.query.count()
    active = User.query.filter_by(is_active=True).count()
    
    # 按部门统计
    dept_stats = db.session.query(
        User.department,
        db.func.count(User.id)
    ).group_by(User.department).all()
    
    return jsonify({
        'total': total,
        'active': active,
        'inactive': total - active,
        'by_department': [{'department': d[0], 'count': d[1]} for d in dept_stats if d[0]]
    }), 200
