"""
TechHub 装饰器集合
"""
from .auth import require_permission, require_any_permission, require_all_permissions, data_scope_required

__all__ = [
    'require_permission',
    'require_any_permission', 
    'require_all_permissions',
    'data_scope_required'
]
