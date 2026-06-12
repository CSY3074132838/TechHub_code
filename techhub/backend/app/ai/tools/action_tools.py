"""
操作工具 - 用于 AI 助手执行实际操作

【第三次迭代程思同负责】
(2) AI 帮助员工新建任务等加快工作效率：
    - create_task: 创建新任务（指定标题、项目、执行人、截止日期）
    - generate_weekly_report: 生成个人工作周报
    - get_smart_reminders: 获取智能提醒（即将到期任务、待审批事项等）
    - get_work_overview: 获取工作总览（今日/本周/本月统计）
"""
from datetime import datetime, timedelta
from app.ai.tools import register_tool, get_current_user
from app.models import Task, Project, Client, Approval, ApprovalNode, Activity, ActivityType
from app import db


@register_tool(
    name="create_task",
    description="创建新任务，需要指定标题、所属项目，可选分配执行人和截止日期",
    parameters={
        "title": {
            "type": "string",
            "description": "任务标题",
            "required": True
        },
        "project_id": {
            "type": "integer",
            "description": "所属项目ID",
            "required": True
        },
        "description": {
            "type": "string",
            "description": "任务描述",
            "required": False
        },
        "assignee_id": {
            "type": "integer",
            "description": "执行人ID",
            "required": False
        },
        "priority": {
            "type": "string",
            "enum": ["low", "medium", "high", "urgent"],
            "description": "优先级，默认medium",
            "required": False
        },
        "due_date": {
            "type": "string",
            "description": "截止日期，格式YYYY-MM-DD",
            "required": False
        }
    }
)
def create_task(user_id=None, title=None, project_id=None, description="", 
                assignee_id=None, priority="medium", due_date=None):
    """创建新任务"""
    user = get_current_user(user_id)
    if not user:
        return {"error": "用户未登录"}
    
    # 验证项目存在
    project = Project.query.get(project_id)
    if not project:
        return {"error": f"项目ID {project_id} 不存在"}
    
    # 验证执行人
    if assignee_id:
        from app.models import User
        assignee = User.query.get(assignee_id)
        if not assignee:
            return {"error": f"执行人ID {assignee_id} 不存在"}
    
    # 解析截止日期
    due_datetime = None
    if due_date:
        try:
            due_datetime = datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            return {"error": "截止日期格式错误，请使用 YYYY-MM-DD 格式"}
    
    try:
        task = Task(
            title=title,
            description=description,
            project_id=project_id,
            assignee_id=assignee_id,
            creator_id=user.id,
            priority=priority,
            due_date=due_datetime,
            status="todo"
        )
        db.session.add(task)
        db.session.commit()
        
        # 记录活动
        activity = Activity(
            activity_type="task_created",
            title=f"创建了任务: {title}",
            user_id=user.id,
            task_id=task.id,
            project_id=project_id
        )
        db.session.add(activity)
        db.session.commit()
        
        return {
            "success": True,
            "message": f"任务「{title}」创建成功",
            "task": {
                "id": task.id,
                "title": task.title,
                "project": project.name,
                "priority": task.priority,
                "status": task.status,
                "due_date": task.due_date.isoformat() if task.due_date else None
            }
        }
    except Exception as e:
        db.session.rollback()
        return {"error": f"创建任务失败: {str(e)}"}


@register_tool(
    name="generate_weekly_report",
    description="生成个人工作周报，汇总本周的任务完成情况、项目进展等",
    parameters={
        "week_offset": {
            "type": "integer",
            "description": "周偏移，0=本周，-1=上周，默认0",
            "required": False
        }
    }
)
def generate_weekly_report(user_id=None, week_offset=0):
    """生成个人工作周报"""
    user = get_current_user(user_id)
    if not user:
        return {"error": "用户未登录"}
    
    now = datetime.now()
    # 计算目标周的起止时间
    target_week_start = now - timedelta(days=now.weekday() + week_offset * 7)
    target_week_start = target_week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    target_week_end = target_week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
    
    # 本周完成的任务
    completed_tasks = Task.query.filter(
        Task.assignee_id == user.id,
        Task.status == "done",
        Task.completed_at >= target_week_start,
        Task.completed_at <= target_week_end
    ).all()
    
    # 本周新增的任务
    new_tasks = Task.query.filter(
        Task.assignee_id == user.id,
        Task.created_at >= target_week_start,
        Task.created_at <= target_week_end
    ).all()
    
    # 进行中的任务
    in_progress_tasks = Task.query.filter(
        Task.assignee_id == user.id,
        Task.status == "in_progress"
    ).all()
    
    # 逾期的任务
    overdue_tasks = Task.query.filter(
        Task.assignee_id == user.id,
        Task.due_date < now,
        Task.status != "done"
    ).all()
    
    # 本周参与的项目活动
    activities = Activity.query.filter(
        Activity.user_id == user.id,
        Activity.created_at >= target_week_start,
        Activity.created_at <= target_week_end
    ).order_by(Activity.created_at.desc()).all()
    
    # 统计项目分布
    project_stats = {}
    for task in completed_tasks:
        p_name = task.project.name if task.project else "未分配项目"
        if p_name not in project_stats:
            project_stats[p_name] = {"completed": 0, "new": 0}
        project_stats[p_name]["completed"] += 1
    
    for task in new_tasks:
        p_name = task.project.name if task.project else "未分配项目"
        if p_name not in project_stats:
            project_stats[p_name] = {"completed": 0, "new": 0}
        project_stats[p_name]["new"] += 1
    
    week_label = "本周" if week_offset == 0 else ("上周" if week_offset == -1 else f"{abs(week_offset)}周前")
    
    return {
        "week_label": week_label,
        "week_range": {
            "start": target_week_start.strftime("%Y-%m-%d"),
            "end": target_week_end.strftime("%Y-%m-%d")
        },
        "summary": {
            "completed_count": len(completed_tasks),
            "new_count": len(new_tasks),
            "in_progress_count": len(in_progress_tasks),
            "overdue_count": len(overdue_tasks)
        },
        "completed_tasks": [{
            "id": t.id,
            "title": t.title,
            "project": t.project.name if t.project else None,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None
        } for t in completed_tasks],
        "new_tasks": [{
            "id": t.id,
            "title": t.title,
            "project": t.project.name if t.project else None,
            "priority": t.priority
        } for t in new_tasks],
        "in_progress_tasks": [{
            "id": t.id,
            "title": t.title,
            "project": t.project.name if t.project else None,
            "due_date": t.due_date.isoformat() if t.due_date else None
        } for t in in_progress_tasks],
        "overdue_tasks": [{
            "id": t.id,
            "title": t.title,
            "project": t.project.name if t.project else None,
            "days_overdue": (now.date() - t.due_date.date()).days if t.due_date else 0
        } for t in overdue_tasks],
        "project_stats": project_stats,
        "activities": [{
            "type": a.activity_type,
            "title": a.title,
            "created_at": a.created_at.isoformat() if a.created_at else None
        } for a in activities[:10]]
    }


@register_tool(
    name="get_smart_reminders",
    description="获取智能提醒，包括即将到期的任务、待审批事项、逾期工单等",
    parameters={}
)
def get_smart_reminders(user_id=None):
    """获取智能提醒"""
    user = get_current_user(user_id)
    if not user:
        return {"error": "用户未登录"}
    
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    three_days_later = now + timedelta(days=3)
    
    reminders = []
    
    # 1. 今日到期的任务
    today_tasks = Task.query.filter(
        Task.assignee_id == user.id,
        Task.due_date <= tomorrow,
        Task.due_date >= now,
        Task.status != "done"
    ).all()
    
    for t in today_tasks:
        reminders.append({
            "type": "task_due_today",
            "priority": "high",
            "title": f"任务今日到期: {t.title}",
            "detail": f"所属项目: {t.project.name if t.project else '无'}",
            "related_id": t.id,
            "related_type": "task"
        })
    
    # 2. 3天内到期的任务
    upcoming_tasks = Task.query.filter(
        Task.assignee_id == user.id,
        Task.due_date > tomorrow,
        Task.due_date <= three_days_later,
        Task.status != "done"
    ).all()
    
    for t in upcoming_tasks:
        reminders.append({
            "type": "task_due_soon",
            "priority": "medium",
            "title": f"任务即将到期: {t.title}",
            "detail": f"截止日期: {t.due_date.strftime('%m-%d') if t.due_date else '未设置'}",
            "related_id": t.id,
            "related_type": "task"
        })
    
    # 3. 已逾期的任务
    overdue_tasks = Task.query.filter(
        Task.assignee_id == user.id,
        Task.due_date < now,
        Task.status != "done"
    ).all()
    
    for t in overdue_tasks:
        days = (now.date() - t.due_date.date()).days if t.due_date else 0
        reminders.append({
            "type": "task_overdue",
            "priority": "urgent",
            "title": f"任务已逾期{days}天: {t.title}",
            "detail": f"所属项目: {t.project.name if t.project else '无'}",
            "related_id": t.id,
            "related_type": "task"
        })
    
    # 4. 待我审批的
    pending_approvals = Approval.query.join(ApprovalNode).filter(
        ApprovalNode.handler_id == user.id,
        ApprovalNode.status == "pending"
    ).all()
    
    for a in pending_approvals:
        reminders.append({
            "type": "approval_pending",
            "priority": "high",
            "title": f"待审批: {a.title}",
            "detail": f"申请人: {a.applicant.real_name if a.applicant else '未知'}",
            "related_id": a.id,
            "related_type": "approval"
        })
    
    # 5. 我提交的待审批
    my_pending = Approval.query.filter_by(applicant_id=user.id, status="pending").all()
    if my_pending:
        reminders.append({
            "type": "my_approval_pending",
            "priority": "low",
            "title": f"您有 {len(my_pending)} 个审批正在等待处理",
            "detail": "",
            "related_id": None,
            "related_type": "approval"
        })
    
    # 6. 指派给我的未处理工单
    my_tickets = Ticket.query.filter(
        Ticket.assignee_id == user.id,
        Ticket.status.in_(["open", "in_progress"])
    ).all()
    
    for t in my_tickets:
        reminders.append({
            "type": "ticket_open",
            "priority": "medium",
            "title": f"待处理工单: {t.title}",
            "detail": f"客户: {t.client.name if t.client else '未知'}",
            "related_id": t.id,
            "related_type": "ticket"
        })
    
    # 按优先级排序
    priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
    reminders.sort(key=lambda x: priority_order.get(x["priority"], 99))
    
    return {
        "total": len(reminders),
        "urgent_count": len([r for r in reminders if r["priority"] == "urgent"]),
        "high_count": len([r for r in reminders if r["priority"] == "high"]),
        "medium_count": len([r for r in reminders if r["priority"] == "medium"]),
        "low_count": len([r for r in reminders if r["priority"] == "low"]),
        "reminders": reminders
    }


@register_tool(
    name="get_work_overview",
    description="获取工作总览，包括今日/本周/本月的工作统计和待办事项",
    parameters={}
)
def get_work_overview(user_id=None):
    """获取工作总览"""
    user = get_current_user(user_id)
    if not user:
        return {"error": "用户未登录"}
    
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)
    
    # 今日统计
    today_completed = Task.query.filter(
        Task.assignee_id == user.id,
        Task.status == "done",
        Task.completed_at >= today_start
    ).count()
    
    # 本周统计
    week_completed = Task.query.filter(
        Task.assignee_id == user.id,
        Task.status == "done",
        Task.completed_at >= week_start
    ).count()
    
    week_new = Task.query.filter(
        Task.assignee_id == user.id,
        Task.created_at >= week_start
    ).count()
    
    # 本月统计
    month_completed = Task.query.filter(
        Task.assignee_id == user.id,
        Task.status == "done",
        Task.completed_at >= month_start
    ).count()
    
    # 当前待办
    pending_tasks = Task.query.filter(
        Task.assignee_id == user.id,
        Task.status.in_(["todo", "in_progress"])
    ).count()
    
    # 逾期
    overdue = Task.query.filter(
        Task.assignee_id == user.id,
        Task.due_date < now,
        Task.status != "done"
    ).count()
    
    # 高优先级待办
    high_priority = Task.query.filter(
        Task.assignee_id == user.id,
        Task.status != "done",
        Task.priority.in_(["high", "urgent"])
    ).count()
    
    return {
        "today": {
            "completed": today_completed,
            "pending": pending_tasks
        },
        "this_week": {
            "completed": week_completed,
            "new": week_new
        },
        "this_month": {
            "completed": month_completed
        },
        "current_status": {
            "pending_tasks": pending_tasks,
            "overdue_tasks": overdue,
            "high_priority_tasks": high_priority
        },
        "workload_assessment": "繁重" if pending_tasks > 20 else ("饱和" if pending_tasks > 10 else ("适中" if pending_tasks > 5 else "轻松"))
    }
