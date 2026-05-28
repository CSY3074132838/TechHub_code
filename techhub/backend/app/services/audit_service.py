"""
审计日志服务 - 操作行为记录与查询
"""
from flask import request
from app import db
from app.models import AuditLog


class AuditService:
    """审计日志服务"""

    # 预定义的操作类型常量
    LOGIN = 'LOGIN'
    LOGIN_FAILED = 'LOGIN_FAILED'
    LOGOUT = 'LOGOUT'
    USER_CREATE = 'USER_CREATE'
    USER_UPDATE = 'USER_UPDATE'
    USER_DELETE = 'USER_DELETE'
    ROLE_CREATE = 'ROLE_CREATE'
    ROLE_UPDATE = 'ROLE_UPDATE'
    ROLE_DELETE = 'ROLE_DELETE'
    ROLE_ASSIGN = 'ROLE_ASSIGN'
    PERMISSION_DENIED = 'PERMISSION_DENIED'
    PROJECT_CREATE = 'PROJECT_CREATE'
    PROJECT_UPDATE = 'PROJECT_UPDATE'
    PROJECT_DELETE = 'PROJECT_DELETE'
    TASK_CREATE = 'TASK_CREATE'
    TASK_UPDATE = 'TASK_UPDATE'
    TASK_DELETE = 'TASK_DELETE'
    APPROVAL_CREATE = 'APPROVAL_CREATE'
    APPROVAL_PROCESS = 'APPROVAL_PROCESS'
    DATA_EXPORT = 'DATA_EXPORT'
    PASSWORD_CHANGE = 'PASSWORD_CHANGE'
    TOKEN_REFRESH = 'TOKEN_REFRESH'

    @staticmethod
    def log(action, user_id=None, username=None, resource_type=None, resource_id=None,
            detail=None, status='success'):
        """
        记录审计日志
        :param action: 操作类型，建议使用 AuditService 的常量
        :param user_id: 操作用户ID
        :param username: 操作用户名
        :param resource_type: 资源类型
        :param resource_id: 资源ID
        :param detail: 详情字典 {before: ..., after: ...}
        :param status: success / failure
        """
        try:
            # 【第三次迭代陈思言负责】自动填充请求信息到 detail
            merged_detail = dict(detail) if detail else {}
            if request:
                # 自动记录请求方式、请求URL（如果调用方未显式提供）
                if 'method' not in merged_detail:
                    merged_detail['method'] = request.method
                if 'url' not in merged_detail:
                    merged_detail['url'] = request.path
                # 记录后端服务名（从蓝图名称推断）
                if 'service' not in merged_detail:
                    merged_detail['service'] = AuditService._get_service_name(request)
                # 记录处理耗时（从 Flask g 对象获取）
                if 'duration' not in merged_detail:
                    from flask import g
                    duration = getattr(g, 'request_duration_ms', None)
                    if duration:
                        merged_detail['duration'] = duration
                # 记录错误信息（失败时）
                if status == 'failure' and 'error' not in merged_detail and 'reason' in merged_detail:
                    merged_detail['error'] = merged_detail['reason']
            
            # 【第三次迭代陈思言负责】根据 action 自动推断资源类型
            inferred_resource_type, inferred_resource_id = AuditService._infer_resource(action, resource_type, resource_id, merged_detail)
            
            log = AuditLog(
                user_id=user_id or 0,
                username=username or 'anonymous',
                action=action,
                resource_type=inferred_resource_type,
                resource_id=inferred_resource_id,
                detail=merged_detail,
                ip_address=AuditService._get_client_ip(),
                user_agent=request.headers.get('User-Agent', '')[:500] if request else '',
                status=status
            )
            db.session.add(log)
            db.session.commit()
        except Exception:
            # 审计日志记录失败不能影响主业务流程
            db.session.rollback()

    @staticmethod
    def _get_service_name(req):
        """【第三次迭代陈思言负责】从请求路径推断后端服务名"""
        if not req:
            return '-'
        path = req.path
        service_map = {
            '/api/auth': 'auth-service',
            '/api/users': 'user-service',
            '/api/projects': 'project-service',
            '/api/tasks': 'task-service',
            '/api/clients': 'client-service',
            '/api/contracts': 'contract-service',
            '/api/tickets': 'ticket-service',
            '/api/approvals': 'approval-service',
            '/api/departments': 'department-service',
            '/api/expenses': 'expense-service',
            '/api/payments': 'payment-service',
            '/api/roles': 'role-service',
            '/api/audit': 'audit-service',
            '/api/notifications': 'notification-service',
            '/api/dashboard': 'dashboard-service',
            '/api/attendance': 'attendance-service'
        }
        for prefix, service in service_map.items():
            if path.startswith(prefix):
                return service
        return 'techhub-api'

    @staticmethod
    def _infer_resource(action, resource_type, resource_id, detail):
        """【第三次迭代陈思言负责】根据 action 自动推断资源类型和ID"""
        # 如果调用方已提供，直接使用
        if resource_type:
            return resource_type, resource_id
        
        # 根据 action 前缀推断资源类型
        action_resource_map = {
            'LOGIN': ('auth', None),
            'LOGIN_FAILED': ('auth', None),
            'LOGOUT': ('auth', None),
            'TOKEN_REFRESH': ('auth', None),
            'PASSWORD_CHANGE': ('auth', None),
            'USER_CREATE': ('user', None),
            'USER_UPDATE': ('user', None),
            'USER_DELETE': ('user', None),
            'ROLE_CREATE': ('role', None),
            'ROLE_UPDATE': ('role', None),
            'ROLE_DELETE': ('role', None),
            'ROLE_ASSIGN': ('role', None),
            'PROJECT_CREATE': ('project', None),
            'PROJECT_UPDATE': ('project', None),
            'PROJECT_DELETE': ('project', None),
            'TASK_CREATE': ('task', None),
            'TASK_UPDATE': ('task', None),
            'TASK_DELETE': ('task', None),
            'APPROVAL_CREATE': ('approval', None),
            'APPROVAL_PROCESS': ('approval', None),
            'DATA_EXPORT': ('data', None),
            'PERMISSION_DENIED': ('system', None)
        }
        
        inferred = action_resource_map.get(action)
        if inferred:
            # 尝试从 detail 中提取资源ID
            inferred_type, inferred_id = inferred
            if inferred_id is None and detail:
                # 从 detail 中查找可能的 ID 字段
                for key in ['id', 'user_id', 'client_id', 'project_id', 'task_id', 'role_id', 'resource_id']:
                    if key in detail and detail[key] is not None:
                        inferred_id = detail[key]
                        break
            return inferred_type, inferred_id
        
        return resource_type, resource_id

    @staticmethod
    def log_from_current_user(action, resource_type=None, resource_id=None,
                               detail=None, status='success'):
        """
        从当前请求上下文中自动获取用户信息并记录日志
        需要在 jwt_required 保护的接口中调用
        """
        try:
            from flask_jwt_extended import get_jwt_identity
            user_id = get_jwt_identity()
            from app.models import User
            user = User.query.get(user_id) if user_id else None
            AuditService.log(
                action=action,
                user_id=user_id,
                username=user.username if user else 'unknown',
                resource_type=resource_type,
                resource_id=resource_id,
                detail=detail,
                status=status
            )
        except Exception:
            db.session.rollback()

    @staticmethod
    def get_logs(filters=None, page=1, per_page=20):
        """
        查询审计日志
        :param filters: 字典，支持 user_id, action, resource_type, status, start_date, end_date
        """
        query = AuditLog.query
        
        if filters:
            if filters.get('user_id'):
                query = query.filter_by(user_id=filters['user_id'])
            if filters.get('action'):
                query = query.filter_by(action=filters['action'])
            if filters.get('resource_type'):
                query = query.filter_by(resource_type=filters['resource_type'])
            if filters.get('status'):
                query = query.filter_by(status=filters['status'])
            # 【第三次迭代陈思言负责】时间范围筛选字段从 start_date/end_date 改为 start_time/end_time
            if filters.get('start_time'):
                query = query.filter(AuditLog.created_at >= filters['start_time'])
            if filters.get('end_time'):
                query = query.filter(AuditLog.created_at <= filters['end_time'])
            if filters.get('username'):
                query = query.filter(AuditLog.username.contains(filters['username']))
        
        pagination = query.order_by(AuditLog.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return {
            'logs': [log.to_dict() for log in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        }

    @staticmethod
    def get_login_stats(user_id=None, days=7):
        """获取登录统计（用于安全分析）"""
        from datetime import datetime, timedelta
        start = datetime.now() - timedelta(days=days)
        
        query = AuditLog.query.filter(AuditLog.action.in_([AuditService.LOGIN, AuditService.LOGIN_FAILED]))
        query = query.filter(AuditLog.created_at >= start)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        logs = query.order_by(AuditLog.created_at.desc()).all()
        
        success = [l for l in logs if l.action == AuditService.LOGIN and l.status == 'success']
        failed = [l for l in logs if l.action == AuditService.LOGIN_FAILED or l.status == 'failure']
        
        return {
            'total_login': len(success),
            'total_failed': len(failed),
            'recent_ips': list(set([l.ip_address for l in success[-10:]]))
        }

    @staticmethod
    def _get_client_ip():
        """获取客户端真实IP"""
        if not request:
            return ''
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        if request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        return request.remote_addr or ''
