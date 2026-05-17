"""
项目管理 API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models import Project, User, Task, Activity, Client
from app.decorators import require_permission, data_scope_required
from app.services import AuditService, PermissionService

def parse_date(date_str):
    """解析日期字符串为 date 对象"""
    if not date_str:
        return None
    if isinstance(date_str, str):
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return None
    return date_str

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/', methods=['GET'])
@jwt_required()
def get_projects():
    """获取项目列表 - 带 DataScope 数据范围控制"""
    current_user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')
    search = request.args.get('search')
    
    # 根据数据范围构建基础查询
    scope = PermissionService.get_user_data_scope(current_user_id)
    user = User.query.get(current_user_id)
    
    if scope.value == 'all':
        query = Project.query
    elif scope.value in ('dept', 'dept_and_below'):
        # 部门负责人：看本部门成员参与的项目
        dept_members = User.query.filter_by(department=user.department).all()
        member_ids = [m.id for m in dept_members]
        query = Project.query.filter(
            (Project.creator_id.in_(member_ids)) |
            (Project.members.any(User.id.in_(member_ids)))
        )
    else:
        # 普通成员：只看自己参与的项目
        query = Project.query.filter(
            (Project.creator_id == current_user_id) |
            (Project.members.any(id=current_user_id))
        )
    
    # 默认过滤掉已删除的项目
    query = query.filter(Project.status != 'deleted')
    
    if status:
        query = query.filter_by(status=status)
    
    if search:
        # 支持按项目名称、成员名、客户名、负责人名搜索
        search_filter = db.or_(
            Project.name.contains(search),
            Project.members.any(User.real_name.contains(search)),
            Project.client.has(Client.name.contains(search)),
            Project.leader.has(User.real_name.contains(search))
        )
        query = query.filter(search_filter)
    
    pagination = query.order_by(Project.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    projects = pagination.items
    
    return jsonify({
        'projects': [project.to_dict() for project in projects],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    }), 200

@projects_bp.route('/', methods=['POST'])
@jwt_required()
def create_project():
    """创建新项目"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'message': '项目名称不能为空', 'error': 'missing_name'}), 400
    
    # 确定项目负责人：如果前端传了leader_id就用，否则用创建者
    leader_id = data.get('leader_id', current_user_id)
    
    project = Project(
        name=data['name'],
        description=data.get('description', ''),
        color=data.get('color', '#1890ff'),
        start_date=parse_date(data.get('start_date')),
        end_date=parse_date(data.get('end_date')),
        creator_id=current_user_id,
        client_id=data.get('client_id'),
        leader_id=leader_id
    )
    
    # 添加成员
    if 'member_ids' in data:
        members = User.query.filter(User.id.in_(data['member_ids'])).all()
        project.members.extend(members)
    
    # 创建者自动成为成员
    creator = User.query.get(current_user_id)
    if creator not in project.members:
        project.members.append(creator)
    
    # 项目负责人如果不是创建者，也自动加入成员
    leader = User.query.get(leader_id)
    if leader and leader not in project.members:
        project.members.append(leader)
    
    db.session.add(project)
    db.session.commit()
    
    # 记录活动
    activity = Activity(
        activity_type='project_created',
        title=f'创建了新项目 "{project.name}"',
        user_id=current_user_id,
        project_id=project.id
    )
    db.session.add(activity)
    db.session.commit()
    
    # 记录审计日志
    AuditService.log_from_current_user(
        action=AuditService.PROJECT_CREATE,
        resource_type='project',
        resource_id=project.id,
        detail={'name': project.name},
        status='success'
    )
    
    return jsonify({
        'message': '项目创建成功',
        'project': project.to_dict()
    }), 201

@projects_bp.route('/<int:project_id>', methods=['GET'])
@jwt_required()
def get_project(project_id):
    """获取项目详情"""
    project = Project.query.get_or_404(project_id)
    return jsonify({'project': project.to_dict(include_tasks=True)}), 200

@projects_bp.route('/<int:project_id>', methods=['PUT'])
@jwt_required()
def update_project(project_id):
    """更新项目信息"""
    current_user_id = get_jwt_identity()
    project = Project.query.get_or_404(project_id)
    
    # 检查权限（只有项目负责人可直接修改，其他需要 project_manage 权限）
    if project.leader_id != current_user_id:
        if not PermissionService.check_permission(current_user_id, 'project_manage'):
            AuditService.log_from_current_user(
                action=AuditService.PERMISSION_DENIED,
                resource_type='project',
                resource_id=project_id,
                detail={'action': 'update_project'},
                status='failure'
            )
            return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    data = request.get_json()
    before_data = {'name': project.name, 'status': project.status, 'description': project.description}
    
    # 更新字段
    allowed_fields = ['name', 'description', 'color', 'status', 'client_id', 'leader_id']
    for field in allowed_fields:
        if field in data:
            setattr(project, field, data[field])
    
    # 日期字段需要解析
    if 'start_date' in data:
        project.start_date = parse_date(data['start_date'])
    if 'end_date' in data:
        project.end_date = parse_date(data['end_date'])
    
    # 更新成员
    if 'member_ids' in data:
        members = User.query.filter(User.id.in_(data['member_ids'])).all()
        project.members = members
    
    db.session.commit()
    
    AuditService.log_from_current_user(
        action=AuditService.PROJECT_UPDATE,
        resource_type='project',
        resource_id=project_id,
        detail={'before': before_data, 'after': {'name': project.name, 'status': project.status}},
        status='success'
    )
    
    return jsonify({
        'message': '项目更新成功',
        'project': project.to_dict()
    }), 200

@projects_bp.route('/<int:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    """删除项目"""
    current_user_id = get_jwt_identity()
    project = Project.query.get_or_404(project_id)
    
    # 检查权限：只有项目负责人或管理员可删除
    if project.leader_id != current_user_id:
        if not PermissionService.check_permission(current_user_id, 'project_manage'):
            return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    project.status = 'deleted'
    db.session.commit()
    
    AuditService.log_from_current_user(
        action=AuditService.PROJECT_DELETE,
        resource_type='project',
        resource_id=project_id,
        detail={'name': project.name, 'soft_delete': True},
        status='success'
    )
    
    return jsonify({'message': '项目已删除'}), 200

@projects_bp.route('/<int:project_id>/tasks', methods=['GET'])
@jwt_required()
def get_project_tasks(project_id):
    """获取项目的所有任务（看板数据）"""
    project = Project.query.get_or_404(project_id)
    
    # 按状态分组返回任务
    tasks_by_status = {
        'todo': [],
        'in_progress': [],
        'review': [],
        'done': []
    }
    
    for task in project.tasks:
        status_key = task.status if task.status else 'todo'
        if status_key in tasks_by_status:
            tasks_by_status[status_key].append(task.to_dict())
    
    # 对每个状态的任务按order排序
    for status in tasks_by_status:
        tasks_by_status[status].sort(key=lambda x: x.get('order', 0))
    
    return jsonify({
        'project': project.to_dict(),
        'board': tasks_by_status
    }), 200

@projects_bp.route('/<int:project_id>/stats', methods=['GET'])
@jwt_required()
def get_project_stats(project_id):
    """获取项目统计信息"""
    project = Project.query.get_or_404(project_id)
    
    # 任务统计
    total_tasks = project.tasks.count()
    status_counts = db.session.query(
        Task.status,
        db.func.count(Task.id)
    ).filter_by(project_id=project_id).group_by(Task.status).all()
    
    # 成员贡献统计
    member_stats = []
    for member in project.members:
        assigned = Task.query.filter_by(project_id=project_id, assignee_id=member.id).count()
        completed = Task.query.filter_by(
            project_id=project_id, 
            assignee_id=member.id,
            status='done'
        ).count()
        member_stats.append({
            'user': member.to_dict(),
            'assigned': assigned,
            'completed': completed
        })
    
    return jsonify({
        'total_tasks': total_tasks,
        'status_distribution': {s: c for s, c in status_counts},
        'member_contributions': member_stats
    }), 200

@projects_bp.route('/<int:project_id>/members', methods=['POST'])
@jwt_required()
def add_project_member(project_id):
    """添加项目成员"""
    current_user_id = get_jwt_identity()
    project = Project.query.get_or_404(project_id)
    
    # 检查权限
    if project.creator_id != current_user_id:
        if not PermissionService.check_permission(current_user_id, 'project_manage'):
            return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'message': '请指定用户', 'error': 'missing_user_id'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': '用户不存在', 'error': 'user_not_found'}), 404
    
    if user in project.members:
        return jsonify({'message': '用户已是项目成员', 'error': 'already_member'}), 409
    
    project.members.append(user)
    db.session.commit()
    
    return jsonify({
        'message': '成员添加成功',
        'members': [m.to_dict() for m in project.members]
    }), 200

@projects_bp.route('/<int:project_id>/members/<int:user_id>', methods=['DELETE'])
@jwt_required()
def remove_project_member(project_id, user_id):
    """移除项目成员"""
    current_user_id = get_jwt_identity()
    project = Project.query.get_or_404(project_id)
    
    # 检查权限
    if project.creator_id != current_user_id:
        if not PermissionService.check_permission(current_user_id, 'project_manage'):
            return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    user = User.query.get(user_id)
    if user and user in project.members:
        project.members.remove(user)
        db.session.commit()
    
    return jsonify({'message': '成员已移除'}), 200


@projects_bp.route('/<int:project_id>/activities', methods=['GET'])
@jwt_required()
def get_project_activities(project_id):
    """获取项目最近动态"""
    project = Project.query.get_or_404(project_id)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Activity.query.filter_by(project_id=project_id).order_by(Activity.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'activities': [activity.to_dict() for activity in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page
    }), 200
