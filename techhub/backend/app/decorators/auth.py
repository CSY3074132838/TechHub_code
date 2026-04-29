"""
权限装饰器 - 统一的接口权限控制与数据范围拦截
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import User, DataScope
from app.services import PermissionService, AuditService


def require_permission(permission_code):
    """
    要求当前用户拥有指定权限
    用法: @require_permission('user_manage')
    """
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user:
                AuditService.log(
                    action=AuditService.PERMISSION_DENIED,
                    user_id=user_id,
                    username='unknown',
                    detail={'permission': permission_code, 'reason': 'user_not_found'},
                    status='failure'
                )
                return jsonify({'message': '用户不存在', 'error': 'user_not_found'}), 401
            
            if not PermissionService.check_permission(user_id, permission_code):
                AuditService.log_from_current_user(
                    action=AuditService.PERMISSION_DENIED,
                    detail={'permission': permission_code, 'path': str(__import__('flask').request.path)},
                    status='failure'
                )
                return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(permission_codes):
    """
    要求当前用户拥有任一指定权限
    用法: @require_any_permission(['user_manage', 'team_manage'])
    """
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({'message': '用户不存在', 'error': 'user_not_found'}), 401
            
            if not PermissionService.check_any_permission(user_id, permission_codes):
                AuditService.log_from_current_user(
                    action=AuditService.PERMISSION_DENIED,
                    detail={'permissions': permission_codes, 'path': str(__import__('flask').request.path)},
                    status='failure'
                )
                return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_all_permissions(permission_codes):
    """
    要求当前用户拥有全部指定权限
    用法: @require_all_permissions(['user_view', 'user_edit'])
    """
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({'message': '用户不存在', 'error': 'user_not_found'}), 401
            
            if not PermissionService.check_all_permissions(user_id, permission_codes):
                return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def data_scope_required(default_scope=None):
    """
    数据范围装饰器 - 将用户数据范围注入到视图函数中
    用法:
        @data_scope_required()
        def get_users():
            # 装饰器会在 kwargs 中注入 current_data_scope 和 current_user_dept
            pass
    
    或者配合 require_permission 使用:
        @require_permission('user_view')
        @data_scope_required()
        def get_users():
            pass
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            from flask_jwt_extended import verify_jwt_in_request
            try:
                verify_jwt_in_request()
                user_id = get_jwt_identity()
            except Exception:
                return jsonify({'message': '未授权', 'error': 'unauthorized'}), 401
            
            user = User.query.get(user_id)
            if not user:
                return jsonify({'message': '用户不存在', 'error': 'user_not_found'}), 401
            
            scope = PermissionService.get_user_data_scope(user_id)
            custom_depts = []
            if scope == DataScope.CUSTOM:
                custom_depts = PermissionService.get_user_custom_depts(user_id)
            
            # 将数据范围信息注入到 kwargs，供视图函数使用
            kwargs['current_data_scope'] = scope
            kwargs['current_user_dept'] = user.department
            kwargs['current_user_id'] = user_id
            kwargs['data_scope_custom_depts'] = custom_depts
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator
