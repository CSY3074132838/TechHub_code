"""
任务管理 API

【第三次迭代程思同/郝益墨负责】
(8) 任务提交审批权限放开：全部项目成员都可提交任务审批（原仅项目负责人）
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models import Task, Project, User, Comment, Activity
from app.services import AuditService, PermissionService, NotificationService

def parse_task_status(value):
    """规范化任务状态字符串"""
    valid = {'todo', 'in_progress', 'review', 'done'}
    return value if value in valid else 'todo'

def parse_task_priority(value):
    """规范化任务优先级字符串"""
    valid = {'low', 'medium', 'high', 'urgent'}
    return value if value in valid else 'medium'

def parse_datetime(dt_str):
    """解析日期时间字符串为 datetime 对象"""
    if not dt_str:
        return None
    if isinstance(dt_str, str):
        # 优先尝试 ISO 8601 格式（带毫秒和时区，如 2026-04-25T10:00:00.000Z）
        for fmt in ('%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%S.%f%z', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
            try:
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                continue
        # 兜底：使用 fromisoformat（支持 +00:00 时区格式）
        try:
            s = dt_str
            if s.endswith('Z'):
                s = s[:-1] + '+00:00'
            return datetime.fromisoformat(s)
        except ValueError:
            pass
    return dt_str

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/', methods=['GET'])
@jwt_required()
def get_tasks():
    """获取任务列表 - 带 DataScope 数据范围控制"""
    current_user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    project_id = request.args.get('project_id', type=int)
    status = request.args.get('status')
    priority = request.args.get('priority')
    assignee_id = request.args.get('assignee_id', type=int)
    search = request.args.get('search')
    
    query = Task.query
    
    # 筛选条件
    if project_id:
        query = query.filter_by(project_id=project_id)
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if assignee_id:
        query = query.filter_by(assignee_id=assignee_id)
    if search:
        query = query.filter(Task.title.contains(search))
    
    # DataScope 数据范围过滤
    scope = PermissionService.get_user_data_scope(current_user_id)
    if scope.value != 'all':
        # 非管理员只能看与自己相关的任务
        query = query.filter(
            (Task.assignee_id == current_user_id) |
            (Task.creator_id == current_user_id) |
            Task.project_id.in_(
                db.session.query(Project.id).filter(
                    (Project.leader_id == current_user_id) |
                    (Project.members.any(id=current_user_id))
                )
            )
        )
    
    pagination = query.order_by(Task.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    tasks = pagination.items
    
    return jsonify({
        'tasks': [task.to_dict() for task in tasks],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    }), 200

@tasks_bp.route('/', methods=['POST'])
@jwt_required()
def create_task():
    """创建新任务"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('title'):
        return jsonify({'message': '任务标题不能为空', 'error': 'missing_title'}), 400
    
    if not data.get('project_id'):
        return jsonify({'message': '请指定所属项目', 'error': 'missing_project_id'}), 400
    
    # 检查项目是否存在
    project = Project.query.get(data['project_id'])
    if not project:
        return jsonify({'message': '项目不存在', 'error': 'project_not_found'}), 404
    
    # 检查用户是否有权限在此项目创建任务
    if project.leader_id != current_user_id and current_user_id not in [m.id for m in project.members]:
        if not PermissionService.check_permission(current_user_id, 'task_manage'):
            return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    task = Task(
        title=data['title'],
        description=data.get('description', ''),
        project_id=data['project_id'],
        assignee_id=data.get('assignee_id'),
        creator_id=current_user_id,
        priority=parse_task_priority(data.get('priority', 'medium')),
        due_date=parse_datetime(data.get('due_date')),
        order=data.get('order', 0)
    )
    
    db.session.add(task)
    db.session.commit()
    
    # 记录活动
    activity = Activity(
        activity_type='task_created',
        title=f'创建了任务 "{task.title}"',
        user_id=current_user_id,
        task_id=task.id,
        project_id=task.project_id
    )
    db.session.add(activity)
    db.session.commit()
    
    # 记录审计日志
    AuditService.log_from_current_user(
        action=AuditService.TASK_CREATE,
        resource_type='task',
        resource_id=task.id,
        detail={'title': task.title, 'project_id': task.project_id},
        status='success'
    )
    
    # 【自动化】任务指派通知
    if task.assignee_id:
        NotificationService.notify_task_assigned(task, task.assignee_id)
    
    return jsonify({
        'message': '任务创建成功',
        'task': task.to_dict()
    }), 201

@tasks_bp.route('/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    """获取任务详情"""
    task = Task.query.get_or_404(task_id)
    return jsonify({'task': task.to_dict(include_comments=True)}), 200

@tasks_bp.route('/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    """更新任务"""
    current_user_id = get_jwt_identity()
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    
    # 检查权限：任务负责人/创建者/项目负责人/管理员可修改
    if task.assignee_id != current_user_id and task.creator_id != current_user_id:
        project = Project.query.get(task.project_id)
        if project.leader_id != current_user_id:
            if not PermissionService.check_permission(current_user_id, 'task_manage'):
                AuditService.log_from_current_user(
                    action=AuditService.PERMISSION_DENIED,
                    resource_type='task',
                    resource_id=task_id,
                    detail={'action': 'update_task'},
                    status='failure'
                )
                return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    # 记录状态变更
    old_status = task.status
    old_data = task.to_dict()
    
    # 更新字段
    if 'status' in data:
        task.status = parse_task_status(data['status'])
    if 'priority' in data:
        task.priority = parse_task_priority(data['priority'])
    allowed_fields = ['title', 'description', 'assignee_id', 'order']
    for field in allowed_fields:
        if field in data:
            setattr(task, field, data[field])
    
    if 'due_date' in data:
        task.due_date = parse_datetime(data['due_date'])
    
    # 如果状态变为完成，记录完成时间
    if data.get('status') == 'done' and old_status != 'done':
        task.completed_at = datetime.now()
        activity_type = 'task_completed'
        activity_title = f'完成了任务 "{task.title}"'
    else:
        activity_type = 'task_updated'
        activity_title = f'更新了任务 "{task.title}"'
    
    db.session.commit()
    
    # 记录活动
    activity = Activity(
        activity_type=activity_type,
        title=activity_title,
        user_id=current_user_id,
        task_id=task.id,
        project_id=task.project_id,
        metadata={'old_status': old_status if old_status else None}
    )
    db.session.add(activity)
    db.session.commit()
    
    # 记录审计日志
    AuditService.log_from_current_user(
        action=AuditService.TASK_UPDATE,
        resource_type='task',
        resource_id=task_id,
        detail={'old_status': old_status if old_status else None},
        status='success'
    )
    
    # 【自动化】任务完成通知创建者
    if data.get('status') == 'done' and old_status != 'done':
        current_user = User.query.get(current_user_id)
        NotificationService.notify_task_completed(task, current_user)
    
    # 【自动化】任务指派变更通知
    if 'assignee_id' in data and data['assignee_id'] and data['assignee_id'] != old_data.get('assignee', {}).get('id'):
        NotificationService.notify_task_assigned(task, data['assignee_id'])
    
    # 【自动化】项目进度检查（状态变更时）
    if 'status' in data and old_status != data['status']:
        _check_project_progress_on_task_change(task.project)
    
    return jsonify({
        'message': '任务更新成功',
        'task': task.to_dict()
    }), 200

@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    """删除任务"""
    current_user_id = get_jwt_identity()
    task = Task.query.get_or_404(task_id)
    
    # 检查权限：项目负责人或管理员可删除
    project = Project.query.get(task.project_id)
    if project.leader_id != current_user_id:
        if not PermissionService.check_permission(current_user_id, 'task_manage'):
                return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    db.session.delete(task)
    db.session.commit()
    
    AuditService.log_from_current_user(
        action=AuditService.TASK_DELETE,
        resource_type='task',
        resource_id=task_id,
        detail={'title': task.title},
        status='success'
    )
    
    return jsonify({'message': '任务已删除'}), 200

@tasks_bp.route('/<int:task_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(task_id):
    """添加任务评论"""
    current_user_id = get_jwt_identity()
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    
    if not data or not data.get('content'):
        return jsonify({'message': '评论内容不能为空', 'error': 'missing_content'}), 400
    
    comment = Comment(
        content=data['content'],
        task_id=task_id,
        author_id=current_user_id
    )
    
    db.session.add(comment)
    
    # 记录活动
    activity = Activity(
        activity_type='comment_added',
        title=f'评论了任务 "{task.title}"',
        user_id=current_user_id,
        task_id=task.id,
        project_id=task.project_id
    )
    db.session.add(activity)
    db.session.commit()
    
    # 【自动化】评论通知任务相关人员
    NotificationService.notify_comment_added(comment, task)
    
    return jsonify({
        'message': '评论添加成功',
        'comment': comment.to_dict()
    }), 201

@tasks_bp.route('/<int:task_id>/comments', methods=['GET'])
@jwt_required()
def get_comments(task_id):
    """获取任务评论列表"""
    task = Task.query.get_or_404(task_id)
    comments = Comment.query.filter_by(task_id=task_id).order_by(Comment.created_at.desc()).all()
    
    return jsonify({
        'comments': [comment.to_dict() for comment in comments]
    }), 200

@tasks_bp.route('/board/update', methods=['PUT'])
@jwt_required()
def update_board():
    """批量更新看板任务状态（拖拽排序）"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('updates'):
        return jsonify({'message': '请提供更新数据', 'error': 'missing_updates'}), 400
    
    updates = data['updates']
    
    # 记录状态变更的任务用于后续通知
    status_changed_tasks = []
    
    for update in updates:
        task_id = update.get('task_id')
        new_status = update.get('status')
        new_order = update.get('order')
        
        task = Task.query.get(task_id)
        if task:
            # 检查权限
            if task.assignee_id != current_user_id and task.creator_id != current_user_id:
                project = Project.query.get(task.project_id)
                if project.leader_id != current_user_id:
                    if not PermissionService.check_permission(current_user_id, 'task_manage'):
                        continue  # 跳过无权限的任务
            
            if new_status and task.status != new_status:
                status_changed_tasks.append((task, task.status, new_status))
                task.status = parse_task_status(new_status)
            if new_order is not None:
                task.order = new_order
    
    db.session.commit()
    
    # 【自动化】看板状态变更通知
    for task, old_status, new_status in status_changed_tasks:
        if new_status == 'done' and old_status != 'done':
            current_user = User.query.get(current_user_id)
            NotificationService.notify_task_completed(task, current_user)
        _check_project_progress_on_task_change(task.project)
    
    return jsonify({'message': '看板更新成功'}), 200

@tasks_bp.route('/my-tasks', methods=['GET'])
@jwt_required()
def get_my_tasks():
    """获取当前用户的任务"""
    current_user_id = get_jwt_identity()
    status = request.args.get('status')
    
    query = Task.query.filter_by(assignee_id=current_user_id)
    
    if status:
        query = query.filter(Task.status == status)
    
    tasks = query.order_by(Task.created_at.desc()).all()
    
    return jsonify({
        'tasks': [task.to_dict() for task in tasks]
    }), 200


@tasks_bp.route('/<int:task_id>/review', methods=['POST'])
@jwt_required()
def review_task(task_id):
    """审核任务 - 通过或驳回
    只有项目负责人可以审核
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()
    action = data.get('action')  # 'approve' 或 'reject'
    
    if action not in ('approve', 'reject'):
        return jsonify({'message': '操作类型错误', 'error': 'invalid_action'}), 400
    
    task = Task.query.get_or_404(task_id)
    project = Project.query.get(task.project_id)
    
    if not project:
        return jsonify({'message': '项目不存在', 'error': 'project_not_found'}), 404
    
    # 检查权限：项目负责人或管理员可以审核
    if project.leader_id != current_user_id:
        if not PermissionService.check_permission(current_user_id, 'task_manage'):
            return jsonify({'message': '只有项目负责人可以审核任务', 'error': 'forbidden'}), 403
    
    # 只有审核中的任务可以被审核
    if task.status != 'review':
        return jsonify({'message': '只有审核中的任务可以进行审核操作', 'error': 'not_in_review'}), 400
    
    if action == 'approve':
        task.status = 'done'
        task.completed_at = datetime.now()
        message = f'任务 "{task.title}" 审核通过'
        activity_type = 'task_completed'
    else:
        task.status = 'in_progress'
        message = f'任务 "{task.title}" 被驳回，返回进行中'
        activity_type = 'task_updated'
    
    db.session.commit()
    
    # 记录活动
    activity = Activity(
        activity_type=activity_type,
        title=message,
        user_id=current_user_id,
        task_id=task.id,
        project_id=task.project_id,
        meta_data={'action': action, 'reviewer_id': current_user_id}
    )
    db.session.add(activity)
    db.session.commit()
    
    # 【自动化】任务审核结果通知
    if task.assignee_id and task.assignee_id != current_user_id:
        action_text = '通过' if action == 'approve' else '驳回'
        current_user = User.query.get(current_user_id)
        reviewer_name = current_user.real_name or current_user.username
        NotificationService.create_notification(
            user_id=task.assignee_id,
            title=f'【任务审核{action_text}】{task.title}',
            content=f'您提交的任务「{task.title}」已被 {reviewer_name} 审核{action_text}。',
            notification_type='task',
            related_type='task',
            related_id=task.id
        )
    
    # 【自动化】项目进度检查
    _check_project_progress_on_task_change(project)
    
    return jsonify({
        'message': message,
        'task': task.to_dict()
    }), 200


@tasks_bp.route('/<int:task_id>/submit-review', methods=['POST'])
@jwt_required()
def submit_task_for_review(task_id):
    """提交任务进行审核 - 项目成员均可提交"""
    current_user_id = get_jwt_identity()
    task = Task.query.get_or_404(task_id)
    project = Project.query.get(task.project_id)
    
    if not project:
        return jsonify({'message': '项目不存在', 'error': 'project_not_found'}), 404
    
    # 检查权限：项目成员均可提交审核
    member_ids = [m.id for m in project.members]
    if current_user_id not in member_ids and project.leader_id != current_user_id:
        if not PermissionService.check_permission(current_user_id, 'task_manage'):
            return jsonify({'message': '只有项目成员可以提交审核', 'error': 'forbidden'}), 403
    
    if task.status != 'in_progress':
        return jsonify({'message': '只有进行中的任务可以提交审核', 'error': 'not_in_progress'}), 400
    
    task.status = 'review'
    db.session.commit()
    
    # 记录活动
    activity = Activity(
        activity_type='task_updated',
        title=f'提交了任务 "{task.title}" 进行审核',
        user_id=current_user_id,
        task_id=task.id,
        project_id=task.project_id,
        meta_data={'action': 'submit_review'}
    )
    db.session.add(activity)
    db.session.commit()
    
    # 【自动化】提交审核通知项目负责人
    if project.leader_id and project.leader_id != current_user_id:
        current_user = User.query.get(current_user_id)
        submitter_name = current_user.real_name or current_user.username
        NotificationService.create_notification(
            user_id=project.leader_id,
            title=f'【待审核】{task.title}',
            content=f'{submitter_name} 提交了任务「{task.title}」等待审核，请尽快处理。',
            notification_type='task',
            related_type='task',
            related_id=task.id
        )
    
    return jsonify({
        'message': '任务已提交审核',
        'task': task.to_dict()
    }), 200


def _check_project_progress_on_task_change(project):
    """
    【自动化】任务状态变更时检查项目进度
    如果进度落后预期超过20%，发送预警通知
    """
    from datetime import date
    from app.services.notification_service import NotificationService

    if not project or not project.start_date or not project.end_date:
        return

    today = date.today()
    total_days = (project.end_date - project.start_date).days
    if total_days <= 0:
        return

    elapsed_days = (today - project.start_date).days
    if elapsed_days < 0:
        return

    stats = project.get_task_stats()
    actual_progress = stats.get('progress', 0)
    expected_progress = round((elapsed_days / total_days) * 100, 1)

    # 预警条件：落后超过 20%
    if expected_progress - actual_progress > 20:
        # 去重：同一天同一项目只发一次
        reminder_key = f'project_warning_{project.id}_{today.strftime("%Y-%m-%d")}'
        if not NotificationService.is_reminder_sent(reminder_key):
            NotificationService.notify_project_progress_warning(
                project, expected_progress, actual_progress
            )
            NotificationService.mark_reminder_sent(reminder_key)
