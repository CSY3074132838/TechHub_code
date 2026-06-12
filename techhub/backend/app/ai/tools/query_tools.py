"""
数据查询工具 - 用于 AI 助手查询系统数据

【第三次迭代程思同负责】
(3) AI 数据查询：帮助员工查看人力无法快速总结的各种数据
    - query_my_tasks: 查询当前用户的任务列表
    - query_projects: 查询项目列表
    - query_clients: 查询客户列表
    - query_client_detail: 查询客户详情
    - query_approvals: 查询审批列表
    - query_tickets: 查询工单列表
    - query_dashboard_stats: 查询工作台统计
    - search_users: 搜索用户
"""
from datetime import datetime, timedelta
from app.ai.tools import register_tool, get_current_user
from app.models import (
    Task, Project, Client, Contract, Ticket, Approval, User,
    TaskStatus, TaskPriority, ClientStatus, ContractStatus, TicketStatus, ApprovalStatus
)
from app import db


@register_tool(
    name="query_my_tasks",
    description="查询当前用户的任务列表，支持按状态、优先级、时间范围筛选",
    parameters={
        "status": {
            "type": "string",
            "enum": ["todo", "in_progress", "review", "done", "all"],
            "description": "任务状态筛选，默认all显示全部",
            "required": False
        },
        "priority": {
            "type": "string",
            "enum": ["low", "medium", "high", "urgent", "all"],
            "description": "优先级筛选，默认all显示全部",
            "required": False
        },
        "time_range": {
            "type": "string",
            "enum": ["today", "week", "month", "overdue", "all"],
            "description": "时间范围：today今天截止/week本周截止/month本月截止/overdue已逾期/all全部",
            "required": False
        },
        "limit": {
            "type": "integer",
            "description": "返回数量限制，默认20",
            "required": False
        }
    }
)
def query_my_tasks(user_id=None, status="all", priority="all", time_range="all", limit=20):
    """查询当前用户的任务"""
    user = get_current_user(user_id)
    if not user:
        return {"error": "用户未登录"}
    
    query = Task.query.filter_by(assignee_id=user.id)
    
    # 状态筛选
    if status and status != "all":
        query = query.filter_by(status=status)
    
    # 优先级筛选
    if priority and priority != "all":
        query = query.filter_by(priority=priority)
    
    # 时间范围筛选
    now = datetime.now()
    if time_range == "today":
        today_end = now.replace(hour=23, minute=59, second=59)
        query = query.filter(Task.due_date <= today_end)
    elif time_range == "week":
        week_end = now + timedelta(days=7)
        query = query.filter(Task.due_date <= week_end)
    elif time_range == "month":
        month_end = now + timedelta(days=30)
        query = query.filter(Task.due_date <= month_end)
    elif time_range == "overdue":
        query = query.filter(Task.due_date < now, Task.status != "done")
    
    tasks = query.order_by(Task.due_date.asc()).limit(limit).all()
    
    return {
        "total": query.count(),
        "returned": len(tasks),
        "tasks": [{
            "id": t.id,
            "title": t.title,
            "status": t.status,
            "priority": t.priority,
            "project": t.project.name if t.project else None,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None
        } for t in tasks]
    }


@register_tool(
    name="query_projects",
    description="查询项目列表，支持按状态、负责人筛选",
    parameters={
        "status": {
            "type": "string",
            "enum": ["active", "archived", "all"],
            "description": "项目状态筛选",
            "required": False
        },
        "my_projects_only": {
            "type": "boolean",
            "description": "是否只查看我参与的项目",
            "required": False
        },
        "limit": {
            "type": "integer",
            "description": "返回数量限制，默认20",
            "required": False
        }
    }
)
def query_projects(user_id=None, status="active", my_projects_only=False, limit=20):
    """查询项目列表"""
    user = get_current_user(user_id)
    if not user:
        return {"error": "用户未登录"}
    
    query = Project.query
    
    if status and status != "all":
        query = query.filter_by(status=status)
    
    if my_projects_only:
        # 我创建的项目 或 我是负责人的项目 或 我是成员的项目
        query = query.filter(
            db.or_(
                Project.creator_id == user.id,
                Project.leader_id == user.id,
                Project.members.any(id=user.id)
            )
        )
    
    projects = query.order_by(Project.created_at.desc()).limit(limit).all()
    
    return {
        "total": query.count(),
        "returned": len(projects),
        "projects": [{
            "id": p.id,
            "name": p.name,
            "status": p.status,
            "leader": p.leader.real_name if p.leader else None,
            "client": p.client.name if p.client else None,
            "stats": p.get_task_stats(),
            "start_date": p.start_date.isoformat() if p.start_date else None,
            "end_date": p.end_date.isoformat() if p.end_date else None
        } for p in projects]
    }


@register_tool(
    name="query_clients",
    description="查询客户列表，支持按状态、级别、负责人筛选",
    parameters={
        "status": {
            "type": "string",
            "enum": ["potential", "active", "inactive", "lost", "all"],
            "description": "客户状态筛选",
            "required": False
        },
        "level": {
            "type": "string",
            "enum": ["s", "a", "b", "c", "all"],
            "description": "客户级别筛选",
            "required": False
        },
        "my_clients_only": {
            "type": "boolean",
            "description": "是否只查看我负责的客户",
            "required": False
        },
        "limit": {
            "type": "integer",
            "description": "返回数量限制，默认20",
            "required": False
        }
    }
)
def query_clients(user_id=None, status="all", level="all", my_clients_only=False, limit=20):
    """查询客户列表"""
    user = get_current_user(user_id)
    if not user:
        return {"error": "用户未登录"}
    
    query = Client.query
    
    if status and status != "all":
        query = query.filter_by(status=status)
    
    if level and level != "all":
        query = query.filter_by(level=level)
    
    if my_clients_only:
        query = query.filter_by(manager_id=user.id)
    
    clients = query.order_by(Client.created_at.desc()).limit(limit).all()
    
    return {
        "total": query.count(),
        "returned": len(clients),
        "clients": [{
            "id": c.id,
            "name": c.name,
            "industry": c.industry,
            "status": c.status,
            "level": c.level,
            "manager": c.manager.real_name if c.manager else None,
            "contact_name": c.contact_name,
            "contract_count": c.contracts.count(),
            "ticket_count": c.tickets.count()
        } for c in clients]
    }


@register_tool(
    name="query_client_detail",
    description="查询单个客户的详细信息，包括合同、工单、项目",
    parameters={
        "client_id": {
            "type": "integer",
            "description": "客户ID",
            "required": True
        }
    }
)
def query_client_detail(user_id=None, client_id=None):
    """查询客户详情"""
    user = get_current_user(user_id)
    if not user:
        return {"error": "用户未登录"}
    
    client = Client.query.get(client_id)
    if not client:
        return {"error": f"客户ID {client_id} 不存在"}
    
    # 获取合同信息
    contracts = [{
        "id": c.id,
        "contract_no": c.contract_no,
        "name": c.name,
        "amount": float(c.amount) if c.amount else 0,
        "status": c.status,
        "sign_date": c.sign_date.isoformat() if c.sign_date else None
    } for c in client.contracts.order_by(Contract.sign_date.desc()).all()]
    
    # 获取工单信息
    tickets = [{
        "id": t.id,
        "ticket_no": t.ticket_no,
        "title": t.title,
        "status": t.status,
        "priority": t.priority,
        "created_at": t.created_at.isoformat() if t.created_at else None
    } for t in client.tickets.order_by(Ticket.created_at.desc()).limit(10).all()]
    
    # 计算总合同金额
    total_contract_amount = sum(float(c.amount) for c in client.contracts.all() if c.amount)
    
    return {
        "id": client.id,
        "name": client.name,
        "industry": client.industry,
        "status": client.status,
        "level": client.level,
        "contact_name": client.contact_name,
        "contact_phone": client.contact_phone,
        "contact_email": client.contact_email,
        "address": client.address,
        "remark": client.remark,
        "manager": client.manager.real_name if client.manager else None,
        "total_contract_amount": total_contract_amount,
        "contract_count": len(contracts),
        "ticket_count": client.tickets.count(),
        "project_count": len(client.projects) if client.projects else 0,
        "contracts": contracts,
        "tickets": tickets,
        "created_at": client.created_at.isoformat() if client.created_at else None
    }


@register_tool(
    name="query_approvals",
    description="查询审批列表，支持按状态、类型筛选",
    parameters={
        "status": {
            "type": "string",
            "enum": ["pending", "approved", "rejected", "all"],
            "description": "审批状态筛选",
            "required": False
        },
        "approval_type": {
            "type": "string",
            "enum": ["leave", "expense", "purchase", "overtime", "permission", "other", "all"],
            "description": "审批类型筛选",
            "required": False
        },
        "my_approvals_only": {
            "type": "boolean",
            "description": "是否只查看我提交的审批",
            "required": False
        },
        "pending_for_me": {
            "type": "boolean",
            "description": "是否查看待我审批的",
            "required": False
        },
        "limit": {
            "type": "integer",
            "description": "返回数量限制，默认20",
            "required": False
        }
    }
)
def query_approvals(user_id=None, status="pending", approval_type="all", 
                    my_approvals_only=False, pending_for_me=False, limit=20):
    """查询审批列表"""
    user = get_current_user(user_id)
    if not user:
        return {"error": "用户未登录"}
    
    query = Approval.query
    
    if status and status != "all":
        query = query.filter_by(status=status)
    
    if approval_type and approval_type != "all":
        query = query.filter_by(approval_type=approval_type)
    
    if my_approvals_only:
        query = query.filter_by(applicant_id=user.id)
    
    if pending_for_me:
        # 查找当前处理节点是该用户的审批
        from app.models import ApprovalNode
        query = query.join(ApprovalNode).filter(
            ApprovalNode.handler_id == user.id,
            ApprovalNode.status == "pending"
        )
    
    approvals = query.order_by(Approval.created_at.desc()).limit(limit).all()
    
    return {
        "total": query.count(),
        "returned": len(approvals),
        "approvals": [{
            "id": a.id,
            "title": a.title,
            "type": a.approval_type,
            "status": a.status,
            "amount": float(a.amount) if a.amount else None,
            "applicant": a.applicant.real_name if a.applicant else None,
            "is_urgent": a.is_urgent,
            "created_at": a.created_at.isoformat() if a.created_at else None
        } for a in approvals]
    }


@register_tool(
    name="query_tickets",
    description="查询工单列表",
    parameters={
        "status": {
            "type": "string",
            "enum": ["open", "in_progress", "waiting", "resolved", "closed", "all"],
            "description": "工单状态筛选",
            "required": False
        },
        "my_tickets_only": {
            "type": "boolean",
            "description": "是否只查看指派给我的工单",
            "required": False
        },
        "limit": {
            "type": "integer",
            "description": "返回数量限制，默认20",
            "required": False
        }
    }
)
def query_tickets(user_id=None, status="all", my_tickets_only=False, limit=20):
    """查询工单列表"""
    user = get_current_user(user_id)
    if not user:
        return {"error": "用户未登录"}
    
    query = Ticket.query
    
    if status and status != "all":
        query = query.filter_by(status=status)
    
    if my_tickets_only:
        query = query.filter_by(assignee_id=user.id)
    
    tickets = query.order_by(Ticket.created_at.desc()).limit(limit).all()
    
    return {
        "total": query.count(),
        "returned": len(tickets),
        "tickets": [{
            "id": t.id,
            "ticket_no": t.ticket_no,
            "title": t.title,
            "status": t.status,
            "priority": t.priority,
            "client": t.client.name if t.client else None,
            "assignee": t.assignee.real_name if t.assignee else None,
            "created_at": t.created_at.isoformat() if t.created_at else None
        } for t in tickets]
    }


@register_tool(
    name="query_dashboard_stats",
    description="查询当前用户的工作台统计数据",
    parameters={}
)
def query_dashboard_stats(user_id=None):
    """查询工作台统计"""
    user = get_current_user(user_id)
    if not user:
        return {"error": "用户未登录"}
    
    now = datetime.now()
    today_end = now.replace(hour=23, minute=59, second=59)
    week_end = now + timedelta(days=7)
    
    # 任务统计
    total_tasks = Task.query.filter_by(assignee_id=user.id).count()
    pending_tasks = Task.query.filter_by(assignee_id=user.id, status="todo").count()
    in_progress_tasks = Task.query.filter_by(assignee_id=user.id, status="in_progress").count()
    overdue_tasks = Task.query.filter(
        Task.assignee_id == user.id,
        Task.due_date < now,
        Task.status != "done"
    ).count()
    
    # 今日到期
    due_today = Task.query.filter(
        Task.assignee_id == user.id,
        Task.due_date <= today_end,
        Task.status != "done"
    ).count()
    
    # 本周到期
    due_this_week = Task.query.filter(
        Task.assignee_id == user.id,
        Task.due_date <= week_end,
        Task.due_date > today_end,
        Task.status != "done"
    ).count()
    
    # 审批统计
    my_pending_approvals = Approval.query.filter_by(applicant_id=user.id, status="pending").count()
    
    # 客户统计（我负责的）
    my_clients = Client.query.filter_by(manager_id=user.id).count()
    
    # 工单统计
    my_tickets = Ticket.query.filter_by(assignee_id=user.id).filter(
        Ticket.status.in_(["open", "in_progress", "waiting"])
    ).count()
    
    return {
        "tasks": {
            "total": total_tasks,
            "pending": pending_tasks,
            "in_progress": in_progress_tasks,
            "overdue": overdue_tasks,
            "due_today": due_today,
            "due_this_week": due_this_week
        },
        "approvals": {
            "my_pending": my_pending_approvals
        },
        "clients": {
            "my_total": my_clients
        },
        "tickets": {
            "my_open": my_tickets
        }
    }


@register_tool(
    name="search_users",
    description="搜索用户，按姓名或用户名",
    parameters={
        "keyword": {
            "type": "string",
            "description": "搜索关键词（姓名或用户名）",
            "required": True
        },
        "limit": {
            "type": "integer",
            "description": "返回数量限制，默认10",
            "required": False
        }
    }
)
def search_users(user_id=None, keyword="", limit=10):
    """搜索用户"""
    user = get_current_user(user_id)
    if not user:
        return {"error": "用户未登录"}
    
    query = User.query.filter(
        db.or_(
            User.real_name.contains(keyword),
            User.username.contains(keyword)
        ),
        User.is_active == True
    )
    
    users = query.limit(limit).all()
    
    return {
        "total": query.count(),
        "users": [{
            "id": u.id,
            "username": u.username,
            "real_name": u.real_name,
            "department": u.department,
            "position": u.position
        } for u in users]
    }
