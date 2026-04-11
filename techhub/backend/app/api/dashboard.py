"""
数据中心 API - 数据大屏统计
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import func
from app import db
from app.models import User, Project, Task, Approval, Activity, TaskStatus

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/overview', methods=['GET'])
@jwt_required()
def get_overview():
    """获取工作台概览数据"""
    current_user_id = get_jwt_identity()
    
    # 我的待办任务
    my_pending_tasks = Task.query.filter_by(
        assignee_id=current_user_id
    ).filter(Task.status != TaskStatus.DONE).count()
    
    # 我的项目数
    my_projects = Project.query.filter(
        (Project.creator_id == current_user_id) |
        (Project.members.any(id=current_user_id))
    ).count()
    
    # 待处理审批
    my_pending_approvals = Approval.query.filter_by(
        applicant_id=current_user_id,
        status='pending'
    ).count()
    
    # 今日完成任务
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_completed = Task.query.filter(
        Task.assignee_id == current_user_id,
        Task.status == TaskStatus.DONE,
        Task.completed_at >= today
    ).count()
    
    return jsonify({
        'my_pending_tasks': my_pending_tasks,
        'my_projects': my_projects,
        'my_pending_approvals': my_pending_approvals,
        'today_completed': today_completed
    }), 200

@dashboard_bp.route('/activities', methods=['GET'])
@jwt_required()
def get_activities():
    """获取团队动态"""
    current_user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # 获取用户参与的项目
    user_projects = Project.query.filter(
        (Project.creator_id == current_user_id) |
        (Project.members.any(id=current_user_id))
    ).all()
    
    project_ids = [p.id for p in user_projects]
    
    # 获取相关活动
    query = Activity.query.filter(
        (Activity.project_id.in_(project_ids)) |
        (Activity.user_id == current_user_id)
    )
    
    pagination = query.order_by(Activity.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    activities = pagination.items
    
    return jsonify({
        'activities': [activity.to_dict() for activity in activities],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

@dashboard_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    """获取数据中心统计"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # 检查权限（只有管理员可以查看全部统计）
    if not user.has_permission('dashboard_view') and not user.has_permission('all'):
        # 只能看自己的数据
        return get_personal_statistics(current_user_id)
    
    # 系统整体统计
    
    # 1. 用户统计
    total_users = User.query.filter_by(is_active=True).count()
    
    # 2. 项目统计
    total_projects = Project.query.filter_by(status='active').count()
    total_tasks = Task.query.count()
    completed_tasks = Task.query.filter_by(status=TaskStatus.DONE).count()
    task_completion_rate = round(completed_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0
    
    # 3. 任务状态分布
    task_status_dist = db.session.query(
        Task.status,
        func.count(Task.id)
    ).group_by(Task.status).all()
    
    # 4. 近7天任务趋势
    dates = []
    created_trend = []
    completed_trend = []
    
    for i in range(6, -1, -1):
        date = datetime.utcnow().date() - timedelta(days=i)
        dates.append(date.strftime('%m-%d'))
        
        day_start = datetime.combine(date, datetime.min.time())
        day_end = datetime.combine(date, datetime.max.time())
        
        created = Task.query.filter(
            Task.created_at >= day_start,
            Task.created_at <= day_end
        ).count()
        
        completed = Task.query.filter(
            Task.completed_at >= day_start,
            Task.completed_at <= day_end
        ).count()
        
        created_trend.append(created)
        completed_trend.append(completed)
    
    # 5. 部门任务分布
    dept_task_dist = db.session.query(
        User.department,
        func.count(Task.id)
    ).join(Task, Task.assignee_id == User.id).group_by(User.department).all()
    
    # 6. 团队绩效 TOP5
    top_performers = db.session.query(
        User,
        func.count(Task.id).label('completed_count')
    ).join(Task, Task.assignee_id == User.id).filter(
        Task.status == TaskStatus.DONE
    ).group_by(User.id).order_by(func.count(Task.id).desc()).limit(5).all()
    
    # 7. 项目进度排行
    project_progress = []
    for project in Project.query.filter_by(status='active').all():
        stats = project.get_task_stats()
        project_progress.append({
            'id': project.id,
            'name': project.name,
            'progress': stats['progress'],
            'total': stats['total'],
            'done': stats['done']
        })
    project_progress.sort(key=lambda x: x['progress'], reverse=True)
    
    return jsonify({
        'overview': {
            'total_users': total_users,
            'total_projects': total_projects,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'task_completion_rate': task_completion_rate
        },
        'task_status_distribution': [
            {'status': s.value, 'count': c} for s, c in task_status_dist
        ],
        'task_trend': {
            'dates': dates,
            'created': created_trend,
            'completed': completed_trend
        },
        'department_distribution': [
            {'department': d, 'count': c} for d, c in dept_task_dist if d
        ],
        'top_performers': [
            {
                'user': u.to_dict(),
                'completed_count': c
            } for u, c in top_performers
        ],
        'project_progress': project_progress[:10]
    }), 200

def get_personal_statistics(user_id):
    """获取个人统计"""
    # 个人任务统计
    total_tasks = Task.query.filter_by(assignee_id=user_id).count()
    pending_tasks = Task.query.filter(
        Task.assignee_id == user_id,
        Task.status != TaskStatus.DONE
    ).count()
    completed_tasks = Task.query.filter_by(
        assignee_id=user_id,
        status=TaskStatus.DONE
    ).count()
    
    # 近7天趋势
    dates = []
    completed_trend = []
    
    for i in range(6, -1, -1):
        date = datetime.utcnow().date() - timedelta(days=i)
        dates.append(date.strftime('%m-%d'))
        
        day_start = datetime.combine(date, datetime.min.time())
        day_end = datetime.combine(date, datetime.max.time())
        
        completed = Task.query.filter(
            Task.assignee_id == user_id,
            Task.completed_at >= day_start,
            Task.completed_at <= day_end
        ).count()
        
        completed_trend.append(completed)
    
    return jsonify({
        'overview': {
            'total_tasks': total_tasks,
            'pending_tasks': pending_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': round(completed_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0
        },
        'task_trend': {
            'dates': dates,
            'completed': completed_trend
        }
    }), 200

@dashboard_bp.route('/performance', methods=['GET'])
@jwt_required()
def get_performance():
    """获取团队绩效数据"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # 检查权限
    if not user.has_permission('team_manage') and not user.has_permission('all'):
        return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    # 本月统计
    today = datetime.utcnow()
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # 所有用户的绩效
    user_stats = []
    for u in User.query.filter_by(is_active=True).all():
        # 本月完成任务
        month_completed = Task.query.filter(
            Task.assignee_id == u.id,
            Task.status == TaskStatus.DONE,
            Task.completed_at >= month_start
        ).count()
        
        # 总任务
        total_assigned = Task.query.filter_by(assignee_id=u.id).count()
        total_completed = Task.query.filter_by(
            assignee_id=u.id,
            status=TaskStatus.DONE
        ).count()
        
        # 逾期任务
        overdue = Task.query.filter(
            Task.assignee_id == u.id,
            Task.status != TaskStatus.DONE,
            Task.due_date < datetime.utcnow()
        ).count()
        
        user_stats.append({
            'user': u.to_dict(),
            'month_completed': month_completed,
            'total_assigned': total_assigned,
            'total_completed': total_completed,
            'completion_rate': round(total_completed / total_assigned * 100, 1) if total_assigned > 0 else 0,
            'overdue': overdue
        })
    
    # 按本月完成数排序
    user_stats.sort(key=lambda x: x['month_completed'], reverse=True)
    
    return jsonify({
        'performance': user_stats
    }), 200
