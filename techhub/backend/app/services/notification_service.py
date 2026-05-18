"""
【自动化迭代】通知服务 - 统一通知创建与推送
为所有自动化场景提供通知创建接口，支持 WebSocket 实时推送
"""
from datetime import datetime, timedelta, date
from app import db
from app.models import Notification, Task, Project, User, Approval, Attendance, Expense, WorkTimeRecord, Role, SystemConfig


class NotificationService:
    """通知服务 - 统一收口所有通知创建逻辑"""

    @staticmethod
    def create_notification(user_id, title, content, notification_type='system',
                           related_type=None, related_id=None):
        """
        创建通知记录（基础方法）
        失败不影响主业务
        """
        try:
            notification = Notification(
                user_id=user_id,
                title=title,
                content=content,
                notification_type=notification_type,
                related_type=related_type,
                related_id=related_id
            )
            db.session.add(notification)
            db.session.commit()

            # 尝试 WebSocket 推送
            NotificationService._emit_notification(user_id, notification.to_dict())
            return notification
        except Exception as e:
            db.session.rollback()
            print(f"[NotificationService] 创建通知失败: {e}")
            return None

    @staticmethod
    def _emit_notification(user_id, notification_dict):
        """通过 WebSocket 推送通知给指定用户"""
        try:
            from app.api.socket_events import emit_to_user
            emit_to_user(user_id, 'new_notification', {
                'user_id': user_id,
                'notification': notification_dict
            })
        except Exception as e:
            print(f"[NotificationService] WebSocket 推送失败: {e}")

    # ==================== 任务相关通知 ====================

    @staticmethod
    def notify_task_assigned(task, assignee_id):
        """任务指派通知"""
        if not assignee_id:
            return
        project_name = task.project.name if task.project else '未知项目'
        return NotificationService.create_notification(
            user_id=assignee_id,
            title=f'【任务指派】{task.title}',
            content=f'您被指派了新任务「{task.title}」，所属项目：{project_name}，'
                    f'截止日期：{task.due_date.strftime("%m月%d日") if task.due_date else "未设置"}',
            notification_type='task',
            related_type='task',
            related_id=task.id
        )

    @staticmethod
    def notify_task_deadline(task, days_before=1):
        """任务截止提醒"""
        if not task.assignee_id or task.status == 'done':
            return
        project_name = task.project.name if task.project else '未知项目'
        deadline = task.due_date.strftime("%m月%d日 %H:%M") if task.due_date else '未设置'

        if days_before == 0:
            title = f'【今日截止】{task.title}'
            content = f'任务「{task.title}」今日截止！所属项目：{project_name}，请尽快处理。'
        else:
            title = f'【即将截止】{task.title}'
            content = (f'任务「{task.title}」将在 {days_before} 天后截止（{deadline}），'
                       f'所属项目：{project_name}，当前状态：{task.status}，请合理安排时间。')

        return NotificationService.create_notification(
            user_id=task.assignee_id,
            title=title,
            content=content,
            notification_type='task',
            related_type='task',
            related_id=task.id
        )

    @staticmethod
    def notify_task_completed(task, completed_by_user):
        """任务完成通知（通知创建者）"""
        if not task.creator_id or task.creator_id == completed_by_user.id:
            return
        return NotificationService.create_notification(
            user_id=task.creator_id,
            title=f'【任务完成】{task.title}',
            content=f'您创建的任务「{task.title}」已被 {completed_by_user.real_name or completed_by_user.username} 完成。',
            notification_type='task',
            related_type='task',
            related_id=task.id
        )

    # ==================== 审批相关通知 ====================

    @staticmethod
    def notify_approval_submitted(approval):
        """审批提交后通知相关处理人"""
        # 通知第一个审批节点的处理人
        first_node = approval.nodes.order_by('order').first()
        if first_node and first_node.handler_id:
            return NotificationService.create_notification(
                user_id=first_node.handler_id,
                title=f'【待审批】{approval.title}',
                content=f'{approval.applicant.real_name or approval.applicant.username} 提交了「{approval.title}」，'
                        f'类型：{approval.approval_type}，请尽快处理。',
                notification_type='approval',
                related_type='approval',
                related_id=approval.id
            )

    @staticmethod
    def notify_approval_processed(approval, action, processor):
        """审批处理结果通知申请人"""
        if not approval.applicant_id:
            return
        action_text = '已通过' if action == 'approve' else '已被拒绝'
        return NotificationService.create_notification(
            user_id=approval.applicant_id,
            title=f'【审批{action_text}】{approval.title}',
            content=f'您的审批「{approval.title}」{action_text}。'
                    f'处理人：{processor.real_name or processor.username}。'
                    f'{f"备注：{approval.process_comment}" if approval.process_comment else ""}',
            notification_type='approval',
            related_type='approval',
            related_id=approval.id
        )

    @staticmethod
    def notify_approval_next_node(approval, next_node):
        """审批流转到下一节点时通知下一处理人"""
        if not next_node or not next_node.handler_id:
            return
        return NotificationService.create_notification(
            user_id=next_node.handler_id,
            title=f'【待审批】{approval.title}',
            content=f'审批「{approval.title}」已流转到您，节点：{next_node.node_name}，请尽快处理。',
            notification_type='approval',
            related_type='approval',
            related_id=approval.id
        )

    # ==================== 评论相关通知 ====================

    @staticmethod
    def notify_comment_added(comment, task):
        """评论添加后通知任务相关人员"""
        notified_users = set()
        # 通知任务负责人
        if task.assignee_id and task.assignee_id != comment.author_id:
            notified_users.add(task.assignee_id)
        # 通知任务创建者
        if task.creator_id and task.creator_id != comment.author_id:
            notified_users.add(task.creator_id)

        author_name = comment.author.real_name or comment.author.username
        for user_id in notified_users:
            NotificationService.create_notification(
                user_id=user_id,
                title=f'【新评论】{task.title}',
                content=f'{author_name} 评论了任务「{task.title}」：{comment.content[:50]}{"..." if len(comment.content) > 50 else ""}',
                notification_type='task',
                related_type='task',
                related_id=task.id
            )

    # ==================== 项目进度预警 ====================

    @staticmethod
    def notify_project_progress_warning(project, expected_progress, actual_progress):
        """项目进度落后预警"""
        if not project.leader_id:
            return
        gap = round(expected_progress - actual_progress, 1)
        return NotificationService.create_notification(
            user_id=project.leader_id,
            title=f'【进度预警】{project.name}',
            content=f'项目「{project.name}」进度落后！当前完成度 {actual_progress}%，'
                    f'预期应完成 {expected_progress}%，落后 {gap}%。'
                    f'请检查任务分配情况，及时调整计划。',
            notification_type='system',
            related_type='project',
            related_id=project.id
        )

    @staticmethod
    def notify_project_deadline_warning(project, actual_progress):
        """项目截止日期当天预警 - 完成度低于75%时发送给所有成员"""
        member_ids = set()
        # 项目负责人
        if project.leader_id:
            member_ids.add(project.leader_id)
        # 所有项目成员
        for member in project.members:
            member_ids.add(member.id)
        
        if not member_ids:
            return
        
        for user_id in member_ids:
            NotificationService.create_notification(
                user_id=user_id,
                title=f'【截止日期预警】{project.name}',
                content=f'项目「{project.name}」今日截止！当前完成度 {actual_progress}%，'
                        f'未达到75%的目标要求。请所有成员尽快处理剩余任务，确保项目按时交付。',
                notification_type='system',
                related_type='project',
                related_id=project.id
            )
        return True

    # ==================== 考勤异常通知 ====================

    @staticmethod
    def notify_attendance_abnormal(user_id, work_date, abnormal_type, detail=''):
        """考勤异常通知"""
        type_map = {
            'late': '迟到',
            'early': '早退',
            'absent': '缺勤'
        }
        type_label = type_map.get(abnormal_type, abnormal_type)
        date_str = work_date.strftime("%m月%d日") if isinstance(work_date, date) else str(work_date)

        # 通知本人
        NotificationService.create_notification(
            user_id=user_id,
            title=f'【考勤异常】{date_str} {type_label}',
            content=f'系统检测到您 {date_str} 存在{type_label}记录。{detail}',
            notification_type='system'
        )

        # 通知直属上级
        user = User.query.get(user_id)
        if user and user.manager_id:
            NotificationService.create_notification(
                user_id=user.manager_id,
                title=f'【下属考勤异常】{user.real_name or user.username} {date_str} {type_label}',
                content=f'您的下属 {user.real_name or user.username} 在 {date_str} 存在{type_label}记录。{detail}',
                notification_type='system'
            )

    # ==================== 日报/周报推送 ====================

    @staticmethod
    def notify_daily_report(user_id, stats):
        """个人日报推送"""
        today_str = datetime.now().strftime("%m月%d日")
        content_lines = [
            f'今日完成任务：{stats.get("completed_tasks", 0)} 个',
            f'今日新增任务：{stats.get("new_tasks", 0)} 个',
            f'待处理审批：{stats.get("pending_approvals", 0)} 个',
        ]
        if stats.get("work_hours") is not None:
            content_lines.append(f'今日工时：{stats["work_hours"]} 小时')
        if stats.get("overdue_tasks", 0) > 0:
            content_lines.append(f'⚠️ 逾期任务：{stats["overdue_tasks"]} 个')

        return NotificationService.create_notification(
            user_id=user_id,
            title=f'【工作日报】{today_str}',
            content='\n'.join(content_lines),
            notification_type='system'
        )

    @staticmethod
    def notify_weekly_report(user_id, stats):
        """团队周报推送（给项目负责人/高管）"""
        week_str = f'{stats.get("week_start", "")} ~ {stats.get("week_end", "")}'
        content_lines = [
            f'本周完成任务：{stats.get("completed_tasks", 0)} 个',
            f'本周新增任务：{stats.get("new_tasks", 0)} 个',
            f'活跃项目数：{stats.get("active_projects", 0)} 个',
        ]
        if stats.get("pending_approvals", 0) > 0:
            content_lines.append(f'待处理审批：{stats["pending_approvals"]} 个')

        return NotificationService.create_notification(
            user_id=user_id,
            title=f'【团队周报】{week_str}',
            content='\n'.join(content_lines),
            notification_type='system'
        )

    # ==================== 费用报表通知 ====================

    @staticmethod
    def notify_expense_report(finance_user_id, report_data):
        """费用报销月度报表通知"""
        month_str = report_data.get('month', '')
        total = report_data.get('total_amount', 0)
        count = report_data.get('total_count', 0)

        content_lines = [
            f'上月报销总额：¥{total:,.2f}',
            f'报销笔数：{count} 笔',
        ]

        # 按类型汇总
        by_category = report_data.get('by_category', {})
        if by_category:
            content_lines.append('按类型分布：')
            category_labels = {
                'travel': '差旅', 'office': '办公', 'entertainment': '招待',
                'training': '培训', 'meal': '餐饮', 'transport': '交通', 'other': '其他'
            }
            for cat, amount in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
                label = category_labels.get(cat, cat)
                content_lines.append(f'  {label}：¥{amount:,.2f}')

        # Top 3 员工
        top_users = report_data.get('top_users', [])
        if top_users:
            content_lines.append('报销金额 Top 3：')
            for i, u in enumerate(top_users[:3], 1):
                content_lines.append(f'  {i}. {u["name"]}：¥{u["amount"]:,.2f}')

        return NotificationService.create_notification(
            user_id=finance_user_id,
            title=f'【费用月报】{month_str} 报销汇总',
            content='\n'.join(content_lines),
            notification_type='finance'
        )

    # ==================== 去重工具 ====================

    @staticmethod
    def is_reminder_sent(key):
        """检查某提醒是否已发送（通过 SystemConfig 记录）"""
        try:
            config = SystemConfig.query.filter_by(key=f'reminder_{key}').first()
            if config:
                # 检查是否是今天的记录
                sent_date = config.value
                today = datetime.now().strftime('%Y-%m-%d')
                return sent_date == today
            return False
        except Exception:
            return False

    @staticmethod
    def mark_reminder_sent(key):
        """标记某提醒已发送"""
        try:
            config = SystemConfig.query.filter_by(key=f'reminder_{key}').first()
            today = datetime.now().strftime('%Y-%m-%d')
            if config:
                config.value = today
            else:
                config = SystemConfig(
                    key=f'reminder_{key}',
                    value=today,
                    description=f'自动提醒去重标记: {key}'
                )
                db.session.add(config)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"[NotificationService] 标记提醒失败: {e}")
