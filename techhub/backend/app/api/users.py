"""
用户管理 API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Role
from app.decorators import require_permission
from app.services import AuditService, RoleService
from sqlalchemy import extract

users_bp = Blueprint('users', __name__)

# 系统预定义权限点列表
SYSTEM_PERMISSIONS = [
    {'code': 'all', 'label': '全部权限', 'category': '系统'},
    {'code': 'dashboard_view', 'label': '仪表盘查看', 'category': '数据'},
    {'code': 'team_manage', 'label': '团队管理', 'category': '管理'},
    {'code': 'approval_process', 'label': '审批处理', 'category': '审批'},
    {'code': 'approval_urgent', 'label': '紧急审批', 'category': '审批'},
    {'code': 'project_manage', 'label': '项目管理', 'category': '项目'},
    {'code': 'task_manage', 'label': '任务管理', 'category': '任务'},
    {'code': 'task_assign', 'label': '任务分配', 'category': '任务'},
    {'code': 'team_view', 'label': '团队查看', 'category': '数据'},
    {'code': 'task_view', 'label': '任务查看', 'category': '任务'},
    {'code': 'task_execute', 'label': '任务执行', 'category': '任务'},
    {'code': 'approval_submit', 'label': '审批提交', 'category': '审批'},
    {'code': 'user_manage', 'label': '用户管理', 'category': '管理'},
    {'code': 'role_manage', 'label': '角色管理', 'category': '管理'},
    {'code': 'audit_view', 'label': '审计日志查看', 'category': '系统'},
    {'code': 'data_export', 'label': '数据导出', 'category': '数据'},
]

@users_bp.route('/', methods=['GET'])
@jwt_required()
def get_users():
    """获取用户列表 - 【第二次迭代】增强搜索与筛选"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    department = request.args.get('department')
    department_id = request.args.get('department_id', type=int)
    search = request.args.get('search')
    employee_status = request.args.get('employee_status')  # 【第二次迭代】按员工状态筛选
    role_id = request.args.get('role_id', type=int)         # 【第二次迭代】按角色筛选
    is_active = request.args.get('is_active', type=lambda x: x.lower() == 'true')
    entry_month = request.args.get('entry_month')  # 格式: 2025-05，【第二次迭代】按入职月份筛选
    
    query = User.query
    
    # 【第二次迭代】按入职月份筛选（统计卡片点击穿透）
    if entry_month:
        try:
            year, month = map(int, entry_month.split('-'))
            query = query.filter(
                extract('year', User.entry_date) == year,
                extract('month', User.entry_date) == month
            )
        except ValueError:
            pass
    
    if department:
        query = query.filter_by(department=department)
    
    # 【第二次迭代】按部门ID筛选
    if department_id:
        query = query.filter_by(department_id=department_id)
    
    # 【第二次迭代】按员工状态筛选
    if employee_status:
        query = query.filter_by(employee_status=employee_status)
    
    # 【第二次迭代】按角色筛选
    if role_id:
        query = query.filter(User.roles.any(Role.id == role_id))
    
    # 【第二次迭代】按账号状态筛选
    if is_active is not None:
        query = query.filter_by(is_active=is_active)
    
    if search:
        # 【第二次迭代】增强搜索：支持用户名、姓名、邮箱、手机号、工号
        query = query.filter(
            (User.username.contains(search)) |
            (User.real_name.contains(search)) |
            (User.email.contains(search)) |
            (User.phone.contains(search)) |
            (User.employee_no.contains(search))
        )
    
    pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    users = pagination.items
    
    return jsonify({
        'users': [user.to_dict(include_email=True) for user in users],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    }), 200

@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """获取单个用户信息 - 【第二次迭代】支持返回完整档案"""
    user = User.query.get_or_404(user_id)
    include_detail = request.args.get('detail', 'false').lower() == 'true'
    return jsonify({'user': user.to_dict(include_email=True, include_detail=include_detail)}), 200

@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """更新用户信息"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # 只能修改自己的信息，或者管理员可以修改任何人
    if current_user_id != user_id and not current_user.has_permission('all'):
        AuditService.log_from_current_user(
            action=AuditService.PERMISSION_DENIED,
            resource_type='user',
            resource_id=user_id,
            detail={'action': 'update_user', 'reason': 'not_owner_or_admin'},
            status='failure'
        )
        return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    # 记录变更前数据用于审计
    before_data = {
        'real_name': user.real_name,
        'phone': user.phone,
        'department': user.department,
        'position': user.position,
        'is_active': user.is_active,
        'roles': [r.id for r in user.roles]
    }
    
    # 更新允许修改的字段
    allowed_fields = ['real_name', 'phone', 'department', 'position', 'avatar']
    for field in allowed_fields:
        if field in data:
            setattr(user, field, data[field])
    
    # 【第二次迭代】管理员可更新员工档案扩展字段
    if current_user.has_permission('all'):
        detail_fields = [
            'employee_no', 'employee_status', 'entry_date', 'probation_end_date',
            'leave_date', 'id_card', 'gender', 'birthday', 'native_place',
            'address', 'education', 'school', 'major',
            'emergency_contact', 'emergency_phone',
            'manager_id', 'department_id', 'attachments'
        ]
        for field in detail_fields:
            if field in data:
                setattr(user, field, data[field])
    
    # 只有管理员可以修改角色
    roles_changed = False
    if 'roles' in data and current_user.has_permission('all'):
        role_ids = data['roles']
        user.roles = Role.query.filter(Role.id.in_(role_ids)).all()
        user.permission_version = (user.permission_version or 1) + 1
        roles_changed = True
    
    # 只有管理员可以修改激活状态
    if 'is_active' in data and current_user.has_permission('all'):
        user.is_active = data['is_active']
    
    db.session.commit()
    
    # 记录审计日志
    after_data = {
        'real_name': user.real_name,
        'phone': user.phone,
        'department': user.department,
        'position': user.position,
        'is_active': user.is_active,
        'roles': [r.id for r in user.roles]
    }
    AuditService.log_from_current_user(
        action=AuditService.USER_UPDATE,
        resource_type='user',
        resource_id=user_id,
        detail={'before': before_data, 'after': after_data, 'roles_changed': roles_changed},
        status='success'
    )
    
    # 如果角色发生变化，提示需要重新登录
    msg = '用户信息更新成功'
    if roles_changed:
        msg += '，权限已变更，请重新登录以生效'
    
    return jsonify({
        'message': msg,
        'user': user.to_dict(include_email=True),
        'require_relogin': roles_changed
    }), 200

@users_bp.route('/<int:user_id>', methods=['DELETE'])
@require_permission('all')
def delete_user(user_id):
    """删除用户（软删除）"""
    user = User.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()
    
    AuditService.log_from_current_user(
        action=AuditService.USER_DELETE,
        resource_type='user',
        resource_id=user_id,
        detail={'username': user.username, 'soft_delete': True},
        status='success'
    )
    
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
@require_permission('all')
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
        permissions=data.get('permissions', []),
        data_scope=data.get('data_scope'),
        data_scope_custom=data.get('data_scope_custom')
    )
    db.session.add(role)
    db.session.commit()
    
    AuditService.log_from_current_user(
        action=AuditService.ROLE_CREATE,
        resource_type='role',
        resource_id=role.id,
        detail={'name': role.name, 'permissions': role.permissions, 'data_scope': str(role.data_scope) if role.data_scope else None},
        status='success'
    )
    
    return jsonify({
        'message': '角色创建成功',
        'role': role.to_dict()
    }), 201

@users_bp.route('/roles/<int:role_id>', methods=['PUT'])
@require_permission('all')
def update_role(role_id):
    """更新角色信息（仅管理员）"""
    role = Role.query.get_or_404(role_id)
    data = request.get_json()
    
    before_data = role.to_dict()
    
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
    if 'data_scope' in data:
        from app.models import DataScope
        role.data_scope = DataScope(data['data_scope']) if data['data_scope'] else DataScope.SELF
    if 'data_scope_custom' in data:
        role.data_scope_custom = data['data_scope_custom']
    
    db.session.commit()
    
    # 清除该角色下所有用户的权限缓存
    for user in role.users:
        RoleService.remove_role_from_user(user.id, role.id)
        RoleService.add_role_to_user(user.id, role.id)
    
    AuditService.log_from_current_user(
        action=AuditService.ROLE_UPDATE,
        resource_type='role',
        resource_id=role_id,
        detail={'before': before_data, 'after': role.to_dict()},
        status='success'
    )
    
    return jsonify({
        'message': '角色更新成功，已分配该角色的用户需重新登录以生效',
        'role': role.to_dict(),
        'require_relogin': True
    }), 200

@users_bp.route('/roles/<int:role_id>', methods=['DELETE'])
@require_permission('all')
def delete_role(role_id):
    """删除角色（仅管理员）"""
    role = Role.query.get_or_404(role_id)
    
    # 检查是否有用户正在使用该角色
    if role.users:
        return jsonify({
            'message': '该角色下还有用户，无法删除',
            'error': 'role_in_use'
        }), 409
    
    role_data = role.to_dict()
    db.session.delete(role)
    db.session.commit()
    
    AuditService.log_from_current_user(
        action=AuditService.ROLE_DELETE,
        resource_type='role',
        resource_id=role_id,
        detail={'deleted_role': role_data},
        status='success'
    )
    
    return jsonify({'message': '角色已删除'}), 200

@users_bp.route('/permissions', methods=['GET'])
@jwt_required()
def get_permissions():
    """获取系统所有可用权限点列表"""
    return jsonify({
        'permissions': SYSTEM_PERMISSIONS
    }), 200

@users_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_user_stats():
    """获取用户统计数据 - 【第二次迭代】增强统计维度"""
    total = User.query.count()
    active = User.query.filter_by(is_active=True).count()
    
    # 按部门统计（字符串字段，兼容旧数据）
    dept_stats = db.session.query(
        User.department,
        db.func.count(User.id)
    ).group_by(User.department).all()
    
    # 【第二次迭代】按员工状态统计
    status_stats = db.session.query(
        User.employee_status,
        db.func.count(User.id)
    ).group_by(User.employee_status).all()
    
    # 【第二次迭代】按学历统计
    edu_stats = db.session.query(
        User.education,
        db.func.count(User.id)
    ).group_by(User.education).all()
    
    # 【第二次迭代】本月入职人数
    from datetime import datetime
    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year
    new_this_month = User.query.filter(
        extract('year', User.entry_date) == current_year,
        extract('month', User.entry_date) == current_month
    ).count()
    
    return jsonify({
        'total': total,
        'active': active,
        'inactive': total - active,
        'by_department': [{'department': d[0], 'count': d[1]} for d in dept_stats if d[0]],
        # 【第二次迭代】新增统计维度
        'by_employee_status': [{'status': s[0], 'count': s[1]} for s in status_stats if s[0]],
        'by_education': [{'education': e[0], 'count': e[1]} for e in edu_stats if e[0]],
        'new_this_month': new_this_month
    }), 200


# ==================== 【第二次迭代】员工自助与体验 API ====================

@users_bp.route('/me/detail', methods=['GET'])
@jwt_required()
def get_my_detail():
    """【第二次迭代】获取当前登录用户的完整档案（员工自助）"""
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(current_user_id)
    return jsonify({'user': user.to_dict(include_email=True, include_detail=True)}), 200


@users_bp.route('/me/detail', methods=['PUT'])
@jwt_required()
def update_my_detail():
    """【第二次迭代】员工自助更新个人信息（部分字段需审批）"""
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(current_user_id)
    data = request.get_json()
    
    # 员工可自行修改的字段（无需审批）
    self_editable = ['phone', 'avatar', 'address', 'emergency_contact', 'emergency_phone']
    for field in self_editable:
        if field in data:
            setattr(user, field, data[field])
    
    db.session.commit()
    
    return jsonify({
        'message': '个人信息更新成功',
        'user': user.to_dict(include_email=True, include_detail=True)
    }), 200


@users_bp.route('/managers', methods=['GET'])
@jwt_required()
def get_managers():
    """【第二次迭代】获取可作为上级的用户列表（用于选择直属上级）"""
    # 返回所有 active 用户，供选择直属上级/部门负责人
    users = User.query.filter_by(is_active=True).order_by(User.real_name).all()
    return jsonify({
        'managers': [{'id': u.id, 'real_name': u.real_name or u.username, 'department': u.department} for u in users]
    }), 200


@users_bp.route('/export', methods=['GET'])
@require_permission('user_manage')
def export_users():
    """【第二次迭代】导出员工数据（CSV/JSON格式）"""
    import csv
    import io
    from flask import Response
    
    format_type = request.args.get('format', 'json')
    users = User.query.filter_by(is_active=True).all()
    
    if format_type == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['工号', '姓名', '用户名', '邮箱', '部门', '职位', '电话', '入职日期', '状态'])
        for user in users:
            writer.writerow([
                user.employee_no or '',
                user.real_name or '',
                user.username,
                user.email,
                user.department or '',
                user.position or '',
                user.phone or '',
                user.entry_date.isoformat() if user.entry_date else '',
                user.employee_status or ''
            ])
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=users.csv'}
        )
    
    return jsonify({
        'users': [u.to_dict(include_email=True, include_detail=True) for u in users]
    }), 200


@users_bp.route('/import', methods=['POST'])
@require_permission('user_manage')
def import_users():
    """【第二次迭代】批量导入员工数据（JSON格式）"""
    data = request.get_json()
    if not data or not isinstance(data, list):
        return jsonify({'message': '请提供用户数据列表', 'error': 'invalid_format'}), 400
    
    imported = 0
    errors = []
    
    for idx, item in enumerate(data):
        try:
            if not item.get('username') or not item.get('email'):
                errors.append({'index': idx, 'error': '缺少用户名或邮箱'})
                continue
            
            if User.query.filter_by(username=item['username']).first():
                errors.append({'index': idx, 'error': f"用户名 {item['username']} 已存在"})
                continue
            
            user = User(
                username=item['username'],
                email=item['email'],
                real_name=item.get('real_name', ''),
                phone=item.get('phone', ''),
                department=item.get('department', ''),
                position=item.get('position', ''),
                employee_no=item.get('employee_no'),
                employee_status=item.get('employee_status', 'probation'),
                entry_date=item.get('entry_date'),
                education=item.get('education', ''),
                school=item.get('school', ''),
                major=item.get('major', '')
            )
            user.set_password(item.get('password', '123456'))  # 默认密码
            
            # 分配默认角色
            default_role = Role.query.filter_by(name='member').first()
            if default_role:
                user.roles.append(default_role)
            
            db.session.add(user)
            imported += 1
        except Exception as e:
            errors.append({'index': idx, 'error': str(e)})
    
    db.session.commit()
    
    return jsonify({
        'message': f'导入完成，成功 {imported} 条，失败 {len(errors)} 条',
        'imported': imported,
        'errors': errors
    }), 200
