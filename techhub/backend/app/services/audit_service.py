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
            log = AuditLog(
                user_id=user_id or 0,
                username=username or 'anonymous',
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                detail=detail or {},
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
            if filters.get('start_date'):
                query = query.filter(AuditLog.created_at >= filters['start_date'])
            if filters.get('end_date'):
                query = query.filter(AuditLog.created_at <= filters['end_date'])
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
