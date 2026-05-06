"""
【第二次迭代】部门管理 API - 组织架构管理
作者: 于然
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Department, User
from app.decorators import require_permission
from app.services import AuditService

departments_bp = Blueprint('departments', __name__)


@departments_bp.route('/', methods=['GET'])
@jwt_required()
def get_departments():
    """【第二次迭代】获取部门列表（树形结构）"""
    # 获取所有顶级部门（无父部门）
    root_depts = Department.query.filter_by(parent_id=None).order_by(Department.sort_order).all()
    return jsonify({
        'departments': [dept.to_dict(include_children=True) for dept in root_depts]
    }), 200


@departments_bp.route('/flat', methods=['GET'])
@jwt_required()
def get_departments_flat():
    """【第二次迭代】获取扁平化部门列表（用于下拉选择）"""
    departments = Department.query.order_by(Department.sort_order).all()
    return jsonify({
        'departments': [dept.to_dict() for dept in departments]
    }), 200


@departments_bp.route('/', methods=['POST'])
@require_permission('user_manage')
def create_department():
    """【第二次迭代】创建部门（仅管理员）"""
    data = request.get_json()
    if not data or not data.get('name') or not data.get('code'):
        return jsonify({'message': '部门名称和编码不能为空', 'error': 'missing_fields'}), 400
    
    # 检查编码是否已存在
    if Department.query.filter_by(code=data['code']).first():
        return jsonify({'message': '部门编码已存在', 'error': 'code_exists'}), 409
    
    dept = Department(
        name=data['name'],
        code=data['code'],
        description=data.get('description', ''),
        parent_id=data.get('parent_id'),
        manager_id=data.get('manager_id'),
        sort_order=data.get('sort_order', 0)
    )
    db.session.add(dept)
    db.session.commit()
    
    AuditService.log_from_current_user(
        action=AuditService.USER_UPDATE,  # 复用或新增常量
        resource_type='department',
        resource_id=dept.id,
        detail={'name': dept.name, 'code': dept.code},
        status='success'
    )
    
    return jsonify({
        'message': '部门创建成功',
        'department': dept.to_dict(include_children=True)
    }), 201


@departments_bp.route('/<int:dept_id>', methods=['PUT'])
@require_permission('user_manage')
def update_department(dept_id):
    """【第二次迭代】更新部门信息（仅管理员）"""
    dept = Department.query.get_or_404(dept_id)
    data = request.get_json()
    
    before = dept.to_dict()
    
    if 'name' in data:
        dept.name = data['name']
    if 'code' in data:
        # 检查新编码是否冲突
        existing = Department.query.filter_by(code=data['code']).first()
        if existing and existing.id != dept_id:
            return jsonify({'message': '部门编码已存在', 'error': 'code_exists'}), 409
        dept.code = data['code']
    if 'description' in data:
        dept.description = data['description']
    if 'parent_id' in data:
        # 防止循环引用
        if data['parent_id'] == dept_id:
            return jsonify({'message': '不能将自己设为父部门', 'error': 'circular_reference'}), 400
        dept.parent_id = data['parent_id']
    if 'manager_id' in data:
        dept.manager_id = data['manager_id']
    if 'sort_order' in data:
        dept.sort_order = data['sort_order']
    
    db.session.commit()
    
    AuditService.log_from_current_user(
        action=AuditService.USER_UPDATE,
        resource_type='department',
        resource_id=dept_id,
        detail={'before': before, 'after': dept.to_dict()},
        status='success'
    )
    
    return jsonify({
        'message': '部门更新成功',
        'department': dept.to_dict(include_children=True)
    }), 200


@departments_bp.route('/<int:dept_id>', methods=['DELETE'])
@require_permission('user_manage')
def delete_department(dept_id):
    """【第二次迭代】删除部门（仅管理员，需先清空成员和子部门）"""
    dept = Department.query.get_or_404(dept_id)
    
    # 检查是否有子部门
    if dept.children:
        return jsonify({
            'message': '该部门下还有子部门，无法删除',
            'error': 'has_children'
        }), 409
    
    # 检查是否有成员
    if dept.members:
        return jsonify({
            'message': '该部门下还有成员，请先将成员移至其他部门',
            'error': 'has_members',
            'member_count': len(dept.members)
        }), 409
    
    dept_data = dept.to_dict()
    db.session.delete(dept)
    db.session.commit()
    
    AuditService.log_from_current_user(
        action=AuditService.USER_UPDATE,
        resource_type='department',
        resource_id=dept_id,
        detail={'deleted_department': dept_data},
        status='success'
    )
    
    return jsonify({'message': '部门已删除'}), 200


@departments_bp.route('/<int:dept_id>/members', methods=['GET'])
@jwt_required()
def get_department_members(dept_id):
    """【第二次迭代】获取部门成员列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    include_sub_depts = request.args.get('include_sub', 'false').lower() == 'true'
    
    dept = Department.query.get_or_404(dept_id)
    
    if include_sub_depts:
        # 递归获取所有子部门ID
        def get_all_children_ids(department):
            ids = [department.id]
            for child in department.children:
                ids.extend(get_all_children_ids(child))
            return ids
        
        dept_ids = get_all_children_ids(dept)
        query = User.query.filter(User.department_id.in_(dept_ids))
    else:
        query = User.query.filter_by(department_id=dept_id)
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'members': [user.to_dict(include_email=True) for user in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'department': dept.to_dict()
    }), 200


@departments_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_department_stats():
    """【第二次迭代】获取部门统计概览"""
    total_depts = Department.query.count()
    total_members = User.query.filter(User.department_id.isnot(None)).count()
    
    # 按部门统计人数
    dept_stats = db.session.query(
        Department.id,
        Department.name,
        db.func.count(User.id)
    ).outerjoin(User, User.department_id == Department.id) \
     .group_by(Department.id).all()
    
    return jsonify({
        'total_departments': total_depts,
        'total_members_with_dept': total_members,
        'by_department': [
            {'id': d[0], 'name': d[1], 'count': d[2]} for d in dept_stats
        ]
    }), 200
