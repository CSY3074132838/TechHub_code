"""
数据中心 API - 数据大屏统计

【第三次迭代陈思言负责】
(1) 数据中心查看权限控制：总经理、副总经理、数据分析员可直接查看，其他人需申请权限
(2) 数据中心显示全公司数据：所有有权限用户看到的都是公司全部数据，而非个人数据 √
(3) 审计日志详情页面优化：补充丰富内容，更直观展示详细信息 √
(4) 审计日志四个看板改为可交互按钮，增强交互性 √
(5) 个人中心与用户管理同步，支持显示多个身份
(6) 实现中英文网页语言切换
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import func
from app import db
from app.models import User, Project, Task, Approval, Activity, Client, Contract, Ticket
from app.services import AuditService, PermissionService

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/overview', methods=['GET'])
@jwt_required()
def get_overview():
    """获取工作台概览数据"""
    current_user_id = get_jwt_identity()
    
    # 我的待办任务
    my_pending_tasks = Task.query.filter_by(
        assignee_id=current_user_id
    ).filter(Task.status != 'done').count()
    
    # 我的项目数
    my_projects = Project.query.filter(
        (Project.leader_id == current_user_id) |
        (Project.members.any(id=current_user_id))
    ).count()
    
    # 待处理审批
    my_pending_approvals = Approval.query.filter_by(
        applicant_id=current_user_id,
        status='pending'
    ).count()
    
    # 今日完成任务
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_completed = Task.query.filter(
        Task.assignee_id == current_user_id,
        Task.status == 'done',
        Task.completed_at >= today
    ).count()
    
    return jsonify({
        'my_pending_tasks': my_pending_tasks,
        'my_projects': my_projects,
        'my_pending_approvals': my_pending_approvals,
        'today_completed': today_completed
    }), 200


@dashboard_bp.route('/finance-overview', methods=['GET'])
@jwt_required()
def get_finance_overview():
    """【第二次迭代】财务概览看板"""
    current_user_id = get_jwt_identity()
    
    # 权限控制：仅管理员/财务可查看全部
    if not PermissionService.check_permission(current_user_id, 'all'):
        return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    from app.models import Expense, PaymentRecord
    from datetime import date
    
    today = datetime.now().date()
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)
    
    # 本月报销统计
    month_expenses = Expense.query.filter(
        db.extract('year', Expense.created_at) == today.year,
        db.extract('month', Expense.created_at) == today.month
    )
    pending_expenses = month_expenses.filter_by(status='pending').count()
    month_expense_amount = db.session.query(db.func.sum(Expense.amount)).filter(
        db.extract('year', Expense.created_at) == today.year,
        db.extract('month', Expense.created_at) == today.month,
        Expense.status.in_(['approved', 'reimbursed'])
    ).scalar() or 0
    
    # 本月收支
    month_income = db.session.query(db.func.sum(PaymentRecord.amount)).filter(
        PaymentRecord.payment_type == 'income',
        PaymentRecord.status == 'completed',
        db.extract('year', PaymentRecord.payment_date) == today.year,
        db.extract('month', PaymentRecord.payment_date) == today.month
    ).scalar() or 0
    
    month_payment_expense = db.session.query(db.func.sum(PaymentRecord.amount)).filter(
        PaymentRecord.payment_type == 'expense',
        PaymentRecord.status == 'completed',
        db.extract('year', PaymentRecord.payment_date) == today.year,
        db.extract('month', PaymentRecord.payment_date) == today.month
    ).scalar() or 0
    
    # 应收（合同总金额 - 已收款）
    total_contract_amount = db.session.query(db.func.sum(Contract.amount)).scalar() or 0
    total_received = db.session.query(db.func.sum(PaymentRecord.amount)).filter(
        PaymentRecord.payment_type == 'income',
        PaymentRecord.status == 'completed'
    ).scalar() or 0
    
    # 近6个月财务趋势
    from datetime import timedelta
    trend = []
    for i in range(5, -1, -1):
        d = datetime.now().replace(day=1) - timedelta(days=i*30)
        ty, tm = d.year, d.month
        inc = db.session.query(db.func.sum(PaymentRecord.amount)).filter(
            PaymentRecord.payment_type == 'income',
            PaymentRecord.status == 'completed',
            db.extract('year', PaymentRecord.payment_date) == ty,
            db.extract('month', PaymentRecord.payment_date) == tm
        ).scalar() or 0
        exp = db.session.query(db.func.sum(PaymentRecord.amount)).filter(
            PaymentRecord.payment_type == 'expense',
            PaymentRecord.status == 'completed',
            db.extract('year', PaymentRecord.payment_date) == ty,
            db.extract('month', PaymentRecord.payment_date) == tm
        ).scalar() or 0
        reimb = db.session.query(db.func.sum(Expense.amount)).filter(
            Expense.status.in_(['approved', 'reimbursed']),
            db.extract('year', Expense.created_at) == ty,
            db.extract('month', Expense.created_at) == tm
        ).scalar() or 0
        trend.append({
            'month': f'{ty}-{tm:02d}',
            'income': round(float(inc), 2),
            'expense': round(float(exp), 2),
            'reimbursement': round(float(reimb), 2)
        })
    
    # 报销类别分布
    category_dist = db.session.query(
        Expense.category,
        db.func.count(Expense.id),
        db.func.sum(Expense.amount)
    ).filter(
        db.extract('year', Expense.created_at) == today.year,
        db.extract('month', Expense.created_at) == today.month
    ).group_by(Expense.category).all()
    
    # 待审批报销 Top5
    pending_expense_list = Expense.query.filter_by(status='pending').order_by(
        Expense.created_at.desc()
    ).limit(5).all()
    
    return jsonify({
        'overview': {
            'month_income': round(float(month_income), 2),
            'month_expense': round(float(month_payment_expense), 2),
            'month_reimbursement': round(float(month_expense_amount), 2),
            'pending_expenses': pending_expenses,
            'total_contract_amount': round(float(total_contract_amount), 2),
            'total_received': round(float(total_received), 2),
            'receivable': round(float(total_contract_amount) - float(total_received), 2)
        },
        'trend': trend,
        'category_distribution': [
            {'category': c[0], 'count': c[1], 'amount': round(float(c[2] or 0), 2)}
            for c in category_dist
        ],
        'pending_expense_list': [e.to_dict() for e in pending_expense_list]
    }), 200

@dashboard_bp.route('/todos', methods=['GET'])
@jwt_required()
def get_todos():
    """获取工作台待办任务列表，按优先级排序"""
    current_user_id = get_jwt_identity()
    status = request.args.get('status')
    
    # 查询当前用户的未完成任务
    query = Task.query.filter(
        Task.assignee_id == current_user_id,
        Task.status != 'done'
    )
    
    if status:
        query = query.filter(Task.status == status)
    
    # 按优先级排序：urgent > high > medium > low
    priority_order = db.case(
        (Task.priority == 'urgent', 1),
        (Task.priority == 'high', 2),
        (Task.priority == 'medium', 3),
        (Task.priority == 'low', 4),
        else_=5
    )
    
    tasks = query.order_by(priority_order, Task.created_at.desc()).all()
    
    return jsonify({
        'tasks': [task.to_dict() for task in tasks],
        'total': len(tasks)
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
        (Project.leader_id == current_user_id) |
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
    """获取数据中心统计 - 所有有权限的用户都看到全部数据"""
    current_user_id = get_jwt_identity()
    
    # 【第三次迭代陈思言负责】(2) 数据中心显示全公司数据
    # 所有能访问数据中心的用户（总经理、副总经理、数据分析员等）都看到全部数据
    # 不再按 DataScope 区分，统一显示公司全部数据
    
    # 系统整体统计（全部数据）
    total_users = User.query.filter_by(is_active=True).count()
    total_projects = Project.query.filter_by(status='active').count()
    total_tasks = Task.query.count()
    completed_tasks = Task.query.filter_by(status='done').count()
    
    task_completion_rate = round(completed_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0
    
    # 3. 任务状态分布（全部数据）
    task_status_dist = db.session.query(
        Task.status,
        func.count(Task.id)
    ).group_by(Task.status).all()
    
    # 4. 近7天任务趋势（全部数据）
    dates = []
    created_trend = []
    completed_trend = []
    
    for i in range(6, -1, -1):
        date = datetime.now().date() - timedelta(days=i)
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
        Task.status == 'done'
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
            {'status': s, 'count': c} for s, c in task_status_dist
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
        Task.status != 'done'
    ).count()
    completed_tasks = Task.query.filter_by(
        assignee_id=user_id,
        status='done'
    ).count()
    
    # 近7天趋势
    dates = []
    completed_trend = []
    
    for i in range(6, -1, -1):
        date = datetime.now().date() - timedelta(days=i)
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
    
    # 检查权限
    if not PermissionService.check_permission(current_user_id, 'team_manage') and \
       not PermissionService.check_permission(current_user_id, 'all'):
        return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    # 本月统计
    today = datetime.now()
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # 所有用户的绩效
    user_stats = []
    for u in User.query.filter_by(is_active=True).all():
        # 本月完成任务
        month_completed = Task.query.filter(
            Task.assignee_id == u.id,
            Task.status == 'done',
            Task.completed_at >= month_start
        ).count()
        
        # 总任务
        total_assigned = Task.query.filter_by(assignee_id=u.id).count()
        total_completed = Task.query.filter_by(
            assignee_id=u.id,
            status='done'
        ).count()
        
        # 逾期任务
        overdue = Task.query.filter(
            Task.assignee_id == u.id,
            Task.status != 'done',
            Task.due_date < datetime.now()
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



@dashboard_bp.route('/crm-overview', methods=['GET'])
@jwt_required()
def get_crm_overview():
    """获取CRM概览数据"""
    current_user_id = get_jwt_identity()
    
    # 数据中心：所有有权限的用户都看到全部数据
    client_query = Client.query
    contract_query = Contract.query
    ticket_query = Ticket.query
    
    total_clients = client_query.count()
    active_clients = client_query.filter_by(status='active').count()
    potential_clients = client_query.filter_by(status='potential').count()
    
    total_contracts = contract_query.count()
    active_contracts = contract_query.filter_by(status='active').count()
    total_amount = db.session.query(func.sum(Contract.amount)).filter(
        Contract.id.in_([c.id for c in contract_query.all()])
    ).scalar() or 0
    
    total_tickets = ticket_query.count()
    open_tickets = ticket_query.filter_by(status='open').count()
    resolved_tickets = ticket_query.filter_by(status='resolved').count()
    
    # 近30天新增客户趋势
    dates = []
    client_trend = []
    ticket_trend = []
    
    for i in range(29, -1, -1):
        date = datetime.now().date() - timedelta(days=i)
        dates.append(date.strftime('%m-%d'))
        
        day_start = datetime.combine(date, datetime.min.time())
        day_end = datetime.combine(date, datetime.max.time())
        
        client_count = client_query.filter(
            Client.created_at >= day_start,
            Client.created_at <= day_end
        ).count()
        client_trend.append(client_count)
        
        ticket_count = ticket_query.filter(
            Ticket.created_at >= day_start,
            Ticket.created_at <= day_end
        ).count()
        ticket_trend.append(ticket_count)
    
    return jsonify({
        'overview': {
            'total_clients': total_clients,
            'active_clients': active_clients,
            'potential_clients': potential_clients,
            'total_contracts': total_contracts,
            'active_contracts': active_contracts,
            'total_amount': float(total_amount),
            'total_tickets': total_tickets,
            'open_tickets': open_tickets,
            'resolved_tickets': resolved_tickets
        },
        'trend': {
            'dates': dates,
            'clients': client_trend,
            'tickets': ticket_trend
        }
    }), 200


@dashboard_bp.route('/crm-ranking', methods=['GET'])
@jwt_required()
def get_crm_ranking():
    """获取客户金额排行和工单处理排行"""
    current_user_id = get_jwt_identity()
    
    # 数据中心：所有有权限的用户都看到全部合同数据
    contract_query = Contract.query
    
    # 客户金额排行 Top 10
    client_amounts = db.session.query(
        Client,
        func.sum(Contract.amount).label('total_amount'),
        func.count(Contract.id).label('contract_count')
    ).join(Contract, Contract.client_id == Client.id).filter(
        Contract.id.in_([c.id for c in contract_query.all()])
    ).group_by(Client.id).order_by(func.sum(Contract.amount).desc()).limit(10).all()
    
    # 客户经理业绩排行
    manager_stats = db.session.query(
        User,
        func.sum(Contract.amount).label('total_amount'),
        func.count(Contract.id).label('contract_count')
    ).join(Client, Client.manager_id == User.id).join(
        Contract, Contract.client_id == Client.id
    ).filter(
        Contract.id.in_([c.id for c in contract_query.all()])
    ).group_by(User.id).order_by(func.sum(Contract.amount).desc()).limit(10).all()
    
    return jsonify({
        'client_ranking': [
            {
                'client': c.to_dict(),
                'total_amount': float(a) if a else 0,
                'contract_count': cc
            } for c, a, cc in client_amounts
        ],
        'manager_ranking': [
            {
                'user': u.to_dict(),
                'total_amount': float(a) if a else 0,
                'contract_count': cc
            } for u, a, cc in manager_stats
        ]
    }), 200
