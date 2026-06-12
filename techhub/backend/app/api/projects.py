"""
项目管理 API

【第三次迭代程思同负责】
(1) 增加AI小助手功能，接入DeepSeek大模型，支持AI创建任务、大数据分析
(2) AI帮助员工进行大数据筛选，判断最优客户，分析各种大数据
(4) 增加项目搜索功能：支持按项目名字、项目成员、关联客户、项目负责人搜索 √
(5) 修复项目删除：改为软删除（status='deleted'），删除后不再显示在列表中 √
(6) 修复项目负责人权限同步：编辑项目时更新leader_id，同时确保新负责人加入成员列表 √
(7) 编辑项目功能增加项目负责人下拉框，可选择员工作为负责人 √
(8) 项目任务提交审批权限：全部项目成员都可提交审批（原仅负责人） √
(9) 新增项目增加项目负责人下拉框，可选择员工作为负责人 √
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
    
    # 【第三次迭代程思同负责】(4) 项目搜索功能
    # 支持按项目名称、成员名、关联客户名、项目负责人名搜索
    
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
            (Project.leader_id.in_(member_ids)) |
            (Project.members.any(User.id.in_(member_ids)))
        )
    else:
        # 普通成员：只看自己参与的项目
        query = Project.query.filter(
            (Project.leader_id == current_user_id) |
            (Project.members.any(id=current_user_id))
        )
    
    # 默认过滤掉已删除的项目
    query = query.filter(Project.status != 'deleted')
    
    if status:
        query = query.filter_by(status=status)
    
    if search:
        # 【第三次迭代程思同负责】(4) 多维度搜索：项目名称/成员/客户/负责人
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
    
    # 【第三次迭代程思同负责】(6) 项目负责人选择：前端传入leader_id则使用，否则默认创建者
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
    
    # 【第三次迭代程思同负责】(6) 项目负责人自动加入成员列表，确保权限同步
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
    current_user_id = get_jwt_identity()
    project = Project.query.get_or_404(project_id)
    
    # 【自动化】项目截止日期预警检查（用户行为触发）
    _check_deadline_warning_on_view(project, current_user_id)
    
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
    
    # 【第三次迭代程思同负责】(6) 编辑项目时支持修改项目负责人
    # 更新字段：包括leader_id，修改后新负责人自动获得权限
    allowed_fields = ['name', 'description', 'color', 'status', 'client_id', 'leader_id']
    for field in allowed_fields:
        if field in data:
            setattr(project, field, data[field])
    
    # 日期字段需要解析
    if 'start_date' in data:
        project.start_date = parse_date(data['start_date'])
    if 'end_date' in data:
        project.end_date = parse_date(data['end_date'])
    
    # 【第三次迭代程思同负责】(6) 更新成员列表，确保新负责人被包含在成员中
    if 'member_ids' in data:
        members = User.query.filter(User.id.in_(data['member_ids'])).all()
        project.members = members
        # 确保项目负责人始终在成员列表中
        leader = User.query.get(project.leader_id)
        if leader and leader not in project.members:
            project.members.append(leader)
    
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
    
    # 【第三次迭代程思同负责】(5) 项目软删除：将状态设为deleted，不再显示在列表中
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
    
    # 检查权限：只有项目负责人或管理员可添加成员
    if project.leader_id != current_user_id:
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
    
    # 检查权限：只有项目负责人或管理员可移除成员
    if project.leader_id != current_user_id:
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


def _check_deadline_warning_on_view(project, user_id):
    """
    【自动化】用户查看项目详情时，检查是否需要触发截止日期预警
    触发条件：
    1. 项目有 end_date 且状态为 active
    2. 今天是 end_date 的前一天 或 end_date 当天
    3. 项目完成度 < 75%
    4. 该用户今天首次查看该项目
    5. 该用户是项目成员
    """
    try:
        from datetime import date, timedelta
        from app.services.notification_service import NotificationService
        
        if not project.end_date or project.status != 'active':
            return
        
        today = date.today()
        deadline = project.end_date
        
        # 检查是否在预警窗口内（截止日前一天或当天）
        warning_start = deadline - timedelta(days=1)
        if today < warning_start or today > deadline:
            return
        
        # 检查完成度
        stats = project.get_task_stats()
        if stats.get('progress', 0) >= 75:
            return
        
        # 检查该用户今天是否已触发过
        reminder_key = f'project_deadline_view_{project.id}_{user_id}_{today.strftime("%Y-%m-%d")}'
        if NotificationService.is_reminder_sent(reminder_key):
            return
        
        # 检查该用户是否是项目成员
        member_ids = {m.id for m in project.members}
        if project.leader_id:
            member_ids.add(project.leader_id)
        if user_id not in member_ids:
            return
        
        # 发送预警通知给该用户
        days_left = (deadline - today).days
        if days_left == 0:
            title = f'【截止日期预警】{project.name}'
            content = (f'项目「{project.name}」今日截止！当前完成度 {stats["progress"]}%，'
                       f'未达到75%的目标要求。请尽快处理剩余任务，确保项目按时交付。')
        else:
            title = f'【即将截止】{project.name}'
            content = (f'项目「{project.name}」明日截止！当前完成度 {stats["progress"]}%，'
                       f'未达到75%的目标要求。请尽快处理剩余任务，确保项目按时交付。')
        
        NotificationService.create_notification(
            user_id=user_id,
            title=title,
            content=content,
            notification_type='system',
            related_type='project',
            related_id=project.id
        )
        NotificationService.mark_reminder_sent(reminder_key)
    except Exception as e:
        # 预警失败不影响主查询
        print(f"[Project Deadline Warning] 检查失败: {e}")
