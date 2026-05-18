"""
审计日志 API - 操作日志查询与管理
"""
from flask import Blueprint, request, jsonify
from app.services import AuditService
from app.decorators import require_permission

audit_bp = Blueprint('audit', __name__)


@audit_bp.route('/logs', methods=['GET'])
@require_permission('audit_view')
def get_audit_logs():
    """查询审计日志（管理员权限）"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    filters = {
        'user_id': request.args.get('user_id', type=int),
        'action': request.args.get('action'),
        'resource_type': request.args.get('resource_type'),
        'status': request.args.get('status'),
        'username': request.args.get('username')
    }
    
    # 移除None值
    filters = {k: v for k, v in filters.items() if v is not None}
    
    result = AuditService.get_logs(filters=filters, page=page, per_page=per_page)
    return jsonify(result), 200


@audit_bp.route('/actions', methods=['GET'])
@require_permission('audit_view')
def get_action_types():
    """获取所有预定义的操作类型"""
    actions = [
        {'value': AuditService.LOGIN, 'label': '登录'},
        {'value': AuditService.LOGIN_FAILED, 'label': '登录失败'},
        {'value': AuditService.LOGOUT, 'label': '登出'},
        {'value': AuditService.USER_CREATE, 'label': '创建用户'},
        {'value': AuditService.USER_UPDATE, 'label': '更新用户'},
        {'value': AuditService.USER_DELETE, 'label': '删除用户'},
        {'value': AuditService.ROLE_CREATE, 'label': '创建角色'},
        {'value': AuditService.ROLE_UPDATE, 'label': '更新角色'},
        {'value': AuditService.ROLE_DELETE, 'label': '删除角色'},
        {'value': AuditService.ROLE_ASSIGN, 'label': '分配角色'},
        {'value': AuditService.PERMISSION_DENIED, 'label': '权限拒绝'},
        {'value': AuditService.PROJECT_CREATE, 'label': '创建项目'},
        {'value': AuditService.PROJECT_UPDATE, 'label': '更新项目'},
        {'value': AuditService.PROJECT_DELETE, 'label': '删除项目'},
        {'value': AuditService.TASK_CREATE, 'label': '创建任务'},
        {'value': AuditService.TASK_UPDATE, 'label': '更新任务'},
        {'value': AuditService.TASK_DELETE, 'label': '删除任务'},
        {'value': AuditService.APPROVAL_CREATE, 'label': '创建审批'},
        {'value': AuditService.APPROVAL_PROCESS, 'label': '处理审批'},
        {'value': AuditService.DATA_EXPORT, 'label': '数据导出'},
        {'value': AuditService.PASSWORD_CHANGE, 'label': '修改密码'},
        {'value': AuditService.TOKEN_REFRESH, 'label': 'Token刷新'}
    ]
    return jsonify({'actions': actions}), 200


@audit_bp.route('/stats', methods=['GET'])
@require_permission('audit_view')
def get_audit_stats():
    """获取审计统计概览"""
    from app.models import AuditLog
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    
    # 今日操作数
    today_start = datetime.combine(today, datetime.min.time())
    today_count = AuditLog.query.filter(AuditLog.created_at >= today_start).count()
    
    # 本周操作数
    week_start = datetime.combine(week_ago, datetime.min.time())
    week_count = AuditLog.query.filter(AuditLog.created_at >= week_start).count()
    
    # 登录失败数（安全指标）
    failed_logins = AuditLog.query.filter(
        AuditLog.action == AuditService.LOGIN_FAILED,
        AuditLog.created_at >= week_start
    ).count()
    
    # 权限拒绝数（安全指标）
    denied_count = AuditLog.query.filter(
        AuditLog.action == AuditService.PERMISSION_DENIED,
        AuditLog.created_at >= week_start
    ).count()
    
    # 操作类型分布（Top 10）
    action_dist = AuditLog.query.with_entities(
        AuditLog.action,
        func.count(AuditLog.id).label('count')
    ).filter(AuditLog.created_at >= week_start).group_by(AuditLog.action).order_by(func.count(AuditLog.id).desc()).limit(10).all()
    
    return jsonify({
        'today_count': today_count,
        'week_count': week_count,
        'failed_logins': failed_logins,
        'permission_denied': denied_count,
        'action_distribution': [{'action': a, 'count': c} for a, c in action_dist]
    }), 200


@audit_bp.route('/my-logs', methods=['GET'])
@require_permission('audit_view')
def get_my_logs():
    """获取当前用户的操作日志"""
    from flask_jwt_extended import get_jwt_identity
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    filters = {'user_id': user_id}
    result = AuditService.get_logs(filters=filters, page=page, per_page=per_page)
    return jsonify(result), 200
