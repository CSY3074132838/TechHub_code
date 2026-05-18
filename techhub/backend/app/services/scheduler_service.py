"""
【自动化迭代】定时任务调度服务 - 统一管理所有自动化定时任务
使用 APScheduler BackgroundScheduler 实现后台定时执行
"""
from datetime import datetime, timedelta, date
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# SocketIO 实例（由 app/__init__.py 注入）
socketio = None
scheduler = None


def init_scheduler(app, socketio_instance=None):
    """
    初始化定时任务调度器
    在 create_app() 中调用
    """
    global scheduler, socketio
    socketio = socketio_instance

    if scheduler is not None and scheduler.running:
        return scheduler

    scheduler = BackgroundScheduler()

    # 注册所有定时任务
    _register_jobs(app)

    scheduler.start()
    print("[SchedulerService] 定时任务调度器已启动")
    return scheduler


def _register_jobs(app):
    """注册所有定时任务"""

    # 1. 任务截止提醒 - 每天 09:00
    scheduler.add_job(
        func=_job_with_app_context,
        args=[app, _check_task_deadlines],
        trigger=CronTrigger(hour=9, minute=0),
        id='check_task_deadlines',
        name='任务截止提醒检查',
        replace_existing=True
    )

    # 2. 个人日报生成 - 每天 18:00
    scheduler.add_job(
        func=_job_with_app_context,
        args=[app, _generate_daily_reports],
        trigger=CronTrigger(hour=18, minute=0),
        id='generate_daily_reports',
        name='个人日报生成',
        replace_existing=True
    )

    # 3. 考勤异常检测 - 每天 21:00
    scheduler.add_job(
        func=_job_with_app_context,
        args=[app, _check_attendance_abnormal],
        trigger=CronTrigger(hour=21, minute=0),
        id='check_attendance_abnormal',
        name='考勤异常检测',
        replace_existing=True
    )

    # 4. 费用报销月度报表 - 每月1号 09:00
    scheduler.add_job(
        func=_job_with_app_context,
        args=[app, _generate_expense_report],
        trigger=CronTrigger(day=1, hour=9, minute=0),
        id='generate_expense_report',
        name='费用报销月度报表',
        replace_existing=True
    )

    # 5. 项目进度检查 - 每天 10:00
    scheduler.add_job(
        func=_job_with_app_context,
        args=[app, _check_project_progress],
        trigger=CronTrigger(hour=10, minute=0),
        id='check_project_progress',
        name='项目进度检查',
        replace_existing=True
    )

    # 【已移除】项目截止日期预警改为用户行为触发（查看项目详情时）
    # 原定时任务逻辑已迁移至 app/api/projects.py 的 _check_deadline_warning_on_view


def _job_with_app_context(app, job_func):
    """
    在 Flask app context 下执行任务的包装器
    解决多线程环境下 SQLAlchemy session 问题
    """
    with app.app_context():
        try:
            job_func()
        except Exception as e:
            print(f"[SchedulerService] 定时任务执行失败 {job_func.__name__}: {e}")


# ==================== 定时任务实现 ====================

def _check_task_deadlines():
    """任务截止提醒 - 每天 09:00 执行"""
    from app.models import Task
    from app.services.notification_service import NotificationService

    now = datetime.now()
    tomorrow = now + timedelta(days=1)

    # 查找 due_date 在接下来 24 小时内且未完成的任务
    tasks = Task.query.filter(
        Task.due_date != None,
        Task.due_date <= tomorrow,
        Task.due_date >= now,
        Task.status != 'done'
    ).all()

    for task in tasks:
        # 去重检查
        reminder_key = f'task_deadline_{task.id}_{now.strftime("%Y-%m-%d")}'
        if NotificationService.is_reminder_sent(reminder_key):
            continue

        # 计算还有多久截止
        hours_left = (task.due_date - now).total_seconds() / 3600
        if hours_left <= 0:
            days_before = 0  # 今天截止
        else:
            days_before = 1  # 明天截止

        NotificationService.notify_task_deadline(task, days_before)
        NotificationService.mark_reminder_sent(reminder_key)

    print(f"[SchedulerService] 任务截止提醒检查完成，共提醒 {len(tasks)} 个任务")


def _generate_daily_reports():
    """个人日报生成 - 每天 18:00 执行"""
    from app.models import User, Task, Approval, WorkTimeRecord
    from app.services.notification_service import NotificationService

    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())

    # 获取所有活跃用户
    users = User.query.filter_by(is_active=True).all()

    for user in users:
        # 今日完成任务数
        completed_tasks = Task.query.filter(
            Task.assignee_id == user.id,
            Task.status == 'done',
            Task.completed_at >= today_start,
            Task.completed_at <= today_end
        ).count()

        # 今日新增任务数
        new_tasks = Task.query.filter(
            Task.assignee_id == user.id,
            Task.created_at >= today_start,
            Task.created_at <= today_end
        ).count()

        # 待处理审批数
        pending_approvals = Approval.query.filter(
            Approval.applicant_id == user.id,
            Approval.status == 'pending'
        ).count()

        # 今日工时
        work_records = WorkTimeRecord.query.filter(
            WorkTimeRecord.user_id == user.id,
            WorkTimeRecord.work_date == today
        ).all()
        work_hours = sum(float(r.hours) for r in work_records) if work_records else 0

        # 逾期任务数
        overdue_tasks = Task.query.filter(
            Task.assignee_id == user.id,
            Task.status != 'done',
            Task.due_date != None,
            Task.due_date < today_start
        ).count()

        stats = {
            'completed_tasks': completed_tasks,
            'new_tasks': new_tasks,
            'pending_approvals': pending_approvals,
            'work_hours': round(work_hours, 1) if work_hours > 0 else None,
            'overdue_tasks': overdue_tasks
        }

        # 只有有数据才推送
        if completed_tasks > 0 or new_tasks > 0 or pending_approvals > 0 or overdue_tasks > 0 or work_hours > 0:
            NotificationService.notify_daily_report(user.id, stats)

    print(f"[SchedulerService] 个人日报生成完成，共处理 {len(users)} 个用户")


def _check_attendance_abnormal():
    """考勤异常检测 - 每天 21:00 执行"""
    from app.models import User, Attendance
    from app.services.notification_service import NotificationService

    today = date.today()
    weekday = today.weekday()

    # 周末不检测
    if weekday >= 5:
        print("[SchedulerService] 今天是周末，跳过考勤检测")
        return

    # 标准工作时间
    LATE_THRESHOLD = datetime.combine(today, datetime.strptime("09:30", "%H:%M").time())
    EARLY_LEAVE_THRESHOLD = datetime.combine(today, datetime.strptime("17:30", "%H:%M").time())
    MIN_WORK_HOURS = 6

    # 获取所有活跃用户
    users = User.query.filter_by(is_active=True).all()
    abnormal_count = 0

    for user in users:
        attendance = Attendance.query.filter_by(
            user_id=user.id,
            work_date=today
        ).first()

        if not attendance:
            # 缺勤检测（简化：非周末且无记录）
            NotificationService.notify_attendance_abnormal(
                user_id=user.id,
                work_date=today,
                abnormal_type='absent',
                detail='今日无考勤记录。'
            )
            abnormal_count += 1
            continue

        # 迟到检测
        if attendance.check_in and attendance.check_in > LATE_THRESHOLD:
            attendance.status = 'late'
            late_minutes = int((attendance.check_in - LATE_THRESHOLD).total_seconds() / 60)
            NotificationService.notify_attendance_abnormal(
                user_id=user.id,
                work_date=today,
                abnormal_type='late',
                detail=f'上班打卡时间 {attendance.check_in.strftime("%H:%M")}，迟到 {late_minutes} 分钟。'
            )
            abnormal_count += 1

        # 早退检测
        elif attendance.check_out and attendance.check_out < EARLY_LEAVE_THRESHOLD:
            attendance.status = 'early'
            early_minutes = int((EARLY_LEAVE_THRESHOLD - attendance.check_out).total_seconds() / 60)
            NotificationService.notify_attendance_abnormal(
                user_id=user.id,
                work_date=today,
                abnormal_type='early',
                detail=f'下班打卡时间 {attendance.check_out.strftime("%H:%M")}，早退 {early_minutes} 分钟。'
            )
            abnormal_count += 1

        # 工时不足检测
        elif attendance.work_hours and float(attendance.work_hours) < MIN_WORK_HOURS:
            attendance.status = 'early'
            NotificationService.notify_attendance_abnormal(
                user_id=user.id,
                work_date=today,
                abnormal_type='early',
                detail=f'今日工时 {float(attendance.work_hours)} 小时，不足标准 {MIN_WORK_HOURS} 小时。'
            )
            abnormal_count += 1

    print(f"[SchedulerService] 考勤异常检测完成，共发现 {abnormal_count} 条异常")


def _generate_expense_report():
    """费用报销月度报表 - 每月1号 09:00 执行"""
    from app.models import Expense, User, Role
    from app.services.notification_service import NotificationService
    from collections import defaultdict

    # 计算上月
    today = date.today()
    if today.month == 1:
        last_month = 12
        last_month_year = today.year - 1
    else:
        last_month = today.month - 1
        last_month_year = today.year

    month_start = date(last_month_year, last_month, 1)
    if last_month == 12:
        month_end = date(last_month_year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(last_month_year, last_month + 1, 1) - timedelta(days=1)

    month_str = f'{last_month_year}年{last_month}月'

    # 查询上月已报销的记录
    expenses = Expense.query.filter(
        Expense.status == 'reimbursed',
        Expense.created_at >= datetime.combine(month_start, datetime.min.time()),
        Expense.created_at <= datetime.combine(month_end, datetime.max.time())
    ).all()

    if not expenses:
        print(f"[SchedulerService] {month_str} 无报销记录")
        return

    # 按类型汇总
    by_category = defaultdict(float)
    by_user = defaultdict(float)
    by_department = defaultdict(float)
    total_amount = 0

    for expense in expenses:
        amount = float(expense.amount)
        total_amount += amount
        by_category[expense.category] += amount
        by_user[expense.user_id] += amount
        if expense.user and expense.user.department:
            by_department[expense.user.department] += amount

    # Top 3 员工
    top_users = []
    for user_id, amount in sorted(by_user.items(), key=lambda x: x[1], reverse=True)[:3]:
        user = User.query.get(user_id)
        top_users.append({
            'name': user.real_name or user.username if user else '未知',
            'amount': amount
        })

    report_data = {
        'month': month_str,
        'total_amount': total_amount,
        'total_count': len(expenses),
        'by_category': dict(by_category),
        'by_department': dict(by_department),
        'top_users': top_users
    }

    # 推送给财务负责人
    finance_role = Role.query.filter_by(name='finance_director').first()
    if finance_role and finance_role.users:
        for user in finance_role.users:
            NotificationService.notify_expense_report(user.id, report_data)
    else:
        # 如果没有财务负责人角色，推送给 super_admin
        admin_role = Role.query.filter_by(name='super_admin').first()
        if admin_role and admin_role.users:
            for user in admin_role.users:
                NotificationService.notify_expense_report(user.id, report_data)

    print(f"[SchedulerService] {month_str} 费用报表生成完成，共 {len(expenses)} 笔，总额 ¥{total_amount:,.2f}")


def _check_project_progress():
    """项目进度检查 - 每天 10:00 执行"""
    from app.models import Project
    from app.services.notification_service import NotificationService

    today = date.today()
    projects = Project.query.filter(Project.status == 'active').all()
    warning_count = 0

    for project in projects:
        if not project.start_date or not project.end_date:
            continue

        stats = project.get_task_stats()
        actual_progress = stats.get('progress', 0)

        # 计算预期进度
        total_days = (project.end_date - project.start_date).days
        if total_days <= 0:
            continue

        elapsed_days = (today - project.start_date).days
        if elapsed_days < 0:
            continue  # 项目还没开始

        expected_progress = round((elapsed_days / total_days) * 100, 1)

        # 预警条件：落后超过 20%
        if expected_progress - actual_progress > 20:
            NotificationService.notify_project_progress_warning(
                project, expected_progress, actual_progress
            )
            warning_count += 1

    print(f"[SchedulerService] 项目进度检查完成，共 {warning_count} 个项目触发预警")


def _check_project_deadline():
    """项目截止日期预警 - 每天 00:05 执行
    检查今天截止的项目，如果完成度低于75%，通知所有成员
    """
    from app.models import Project
    from app.services.notification_service import NotificationService

    today = date.today()
    projects = Project.query.filter(
        Project.status == 'active',
        Project.end_date == today
    ).all()

    warning_count = 0
    for project in projects:
        stats = project.get_task_stats()
        actual_progress = stats.get('progress', 0)

        # 完成度低于 75% 触发预警
        if actual_progress < 75:
            # 去重：同一天同一项目只发一次
            reminder_key = f'project_deadline_{project.id}_{today.strftime("%Y-%m-%d")}'
            if not NotificationService.is_reminder_sent(reminder_key):
                NotificationService.notify_project_deadline_warning(project, actual_progress)
                NotificationService.mark_reminder_sent(reminder_key)
                warning_count += 1

    print(f"[SchedulerService] 项目截止日期检查完成，共 {warning_count} 个项目触发预警")


# ==================== 管理接口 ====================

def get_jobs():
    """获取所有定时任务列表"""
    if not scheduler:
        return []
    return [{
        'id': job.id,
        'name': job.name,
        'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None
    } for job in scheduler.get_jobs()]


def add_job(job_func, trigger, job_id, name, **kwargs):
    """动态添加定时任务"""
    if not scheduler:
        return None
    return scheduler.add_job(
        func=job_func,
        trigger=trigger,
        id=job_id,
        name=name,
        replace_existing=True,
        **kwargs
    )


def remove_job(job_id):
    """移除定时任务"""
    if not scheduler:
        return False
    try:
        scheduler.remove_job(job_id)
        return True
    except Exception:
        return False
