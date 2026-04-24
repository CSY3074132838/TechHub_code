"""
任务管理 API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models import Task, Project, User, Comment, Activity, ActivityType, TaskStatus, TaskPriority

def parse_task_status(value):
    """将字符串转换为 TaskStatus 枚举"""
    if value is None or isinstance(value, TaskStatus):
        return value
    mapping = {
        'todo': TaskStatus.TODO,
        'in_progress': TaskStatus.IN_PROGRESS,
        'review': TaskStatus.REVIEW,
        'done': TaskStatus.DONE
    }
    return mapping.get(value)

def parse_task_priority(value):
    """将字符串转换为 TaskPriority 枚举"""
    if value is None or isinstance(value, TaskPriority):
        return value
    mapping = {
        'low': TaskPriority.LOW,
        'medium': TaskPriority.MEDIUM,
        'high': TaskPriority.HIGH,
        'urgent': TaskPriority.URGENT
    }
    return mapping.get(value)

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
    """获取任务列表"""
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
    
    # 用户只能看到与自己相关的任务
    query = query.filter(
        (Task.assignee_id == current_user_id) |
        (Task.creator_id == current_user_id) |
        Task.project_id.in_(
            db.session.query(Project.id).filter(
                (Project.creator_id == current_user_id) |
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
    user = User.query.get(current_user_id)
    if project.creator_id != current_user_id and current_user_id not in [m.id for m in project.members]:
        if not user.has_permission('all'):
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
        activity_type=ActivityType.TASK_CREATED,
        title=f'创建了任务 "{task.title}"',
        user_id=current_user_id,
        task_id=task.id,
        project_id=task.project_id
    )
    db.session.add(activity)
    db.session.commit()
    
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
    
    # 检查权限
    user = User.query.get(current_user_id)
    if task.assignee_id != current_user_id and task.creator_id != current_user_id:
        project = Project.query.get(task.project_id)
        if project.creator_id != current_user_id and not user.has_permission('all'):
            return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    # 记录状态变更
    old_status = task.status
    
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
    if data.get('status') == 'done' and old_status != TaskStatus.DONE:
        task.completed_at = datetime.utcnow()
        activity_type = ActivityType.TASK_COMPLETED
        activity_title = f'完成了任务 "{task.title}"'
    else:
        activity_type = ActivityType.TASK_UPDATED
        activity_title = f'更新了任务 "{task.title}"'
    
    db.session.commit()
    
    # 记录活动
    activity = Activity(
        activity_type=activity_type,
        title=activity_title,
        user_id=current_user_id,
        task_id=task.id,
        project_id=task.project_id,
        metadata={'old_status': old_status.value if old_status else None}
    )
    db.session.add(activity)
    db.session.commit()
    
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
    
    # 检查权限
    user = User.query.get(current_user_id)
    if task.creator_id != current_user_id:
        project = Project.query.get(task.project_id)
        if project.creator_id != current_user_id and not user.has_permission('all'):
            return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    db.session.delete(task)
    db.session.commit()
    
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
        activity_type=ActivityType.COMMENT_ADDED,
        title=f'评论了任务 "{task.title}"',
        user_id=current_user_id,
        task_id=task.id,
        project_id=task.project_id
    )
    db.session.add(activity)
    db.session.commit()
    
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
    
    for update in updates:
        task_id = update.get('task_id')
        new_status = update.get('status')
        new_order = update.get('order')
        
        task = Task.query.get(task_id)
        if task:
            # 检查权限
            user = User.query.get(current_user_id)
            if task.assignee_id != current_user_id and task.creator_id != current_user_id:
                project = Project.query.get(task.project_id)
                if project.creator_id != current_user_id and not user.has_permission('all'):
                    continue  # 跳过无权限的任务
            
            if new_status:
                task.status = parse_task_status(new_status)
            if new_order is not None:
                task.order = new_order
    
    db.session.commit()
    
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
