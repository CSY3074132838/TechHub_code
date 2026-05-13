"""
权限校验服务 - 统一的权限判断与数据范围控制
"""
from flask import request, g
from app import db
from app.models import User, Role, DataScope


class PermissionService:
    """权限校验服务"""

    @staticmethod
    def check_permission(user_id, permission_code):
        """
        检查用户是否拥有指定权限
        :param user_id: 用户ID
        :param permission_code: 权限编码，如 'user_manage'
        :return: bool
        """
        # 先查缓存，无则查数据库
        from .cache_service import CacheService
        permissions = CacheService.get_user_permissions(user_id)
        if permissions is None:
            user = User.query.get(user_id)
            if not user:
                return False
            permissions = PermissionService._get_user_permissions_from_db(user)
            CacheService.cache_user_permissions(user_id, permissions)
        
        return 'all' in permissions or permission_code in permissions

    @staticmethod
    def _get_user_permissions_from_db(user):
        """从数据库获取用户合并后的权限列表"""
        permissions = set()
        for role in user.roles:
            role_perms = role.permissions or []
            permissions.update(role_perms)
        return list(permissions)

    @staticmethod
    def get_user_permissions(user_id):
        """获取用户所有权限（带缓存）"""
        from .cache_service import CacheService
        perms = CacheService.get_user_permissions(user_id)
        if perms is None:
            user = User.query.get(user_id)
            if not user:
                return []
            perms = PermissionService._get_user_permissions_from_db(user)
            CacheService.cache_user_permissions(user_id, perms)
        return perms

    @staticmethod
    def check_any_permission(user_id, permission_codes):
        """检查用户是否拥有任一权限"""
        for code in permission_codes:
            if PermissionService.check_permission(user_id, code):
                return True
        return False

    @staticmethod
    def check_all_permissions(user_id, permission_codes):
        """检查用户是否拥有全部权限"""
        for code in permission_codes:
            if not PermissionService.check_permission(user_id, code):
                return False
        return True

    @staticmethod
    def get_user_data_scope(user_id):
        """
        获取用户的数据范围级别（取所有角色中最宽泛的）
        优先级：ALL > DEPT_AND_BELOW > DEPT > CUSTOM > SELF
        :return: DataScope 枚举值
        """
        user = User.query.get(user_id)
        if not user or not user.roles:
            return DataScope.SELF
        
        # 权限映射优先级，数字越大权限越宽
        scope_priority = {
            DataScope.SELF: 1,
            DataScope.CUSTOM: 2,
            DataScope.DEPT: 3,
            DataScope.DEPT_AND_BELOW: 4,
            DataScope.ALL: 5
        }
        
        highest_scope = DataScope.SELF
        highest_priority = 1
        
        for role in user.roles:
            if not role.data_scope:
                continue
            # 支持字符串和枚举两种类型
            scope_key = role.data_scope
            if isinstance(scope_key, str):
                try:
                    scope_key = DataScope(scope_key)
                except ValueError:
                    continue
            p = scope_priority.get(scope_key, 1)
            if p > highest_priority:
                highest_priority = p
                highest_scope = scope_key
        
        return highest_scope

    @staticmethod
    def get_user_custom_depts(user_id):
        """获取用户自定义数据范围的部门列表"""
        user = User.query.get(user_id)
        if not user:
            return []
        depts = set()
        for role in user.roles:
            if role.data_scope == DataScope.CUSTOM and role.data_scope_custom:
                depts.update(role.data_scope_custom)
        return list(depts)

    @staticmethod
    def build_data_scope_query(query, model, user_id, user_dept_field='department'):
        """
        根据用户数据范围自动给 SQLAlchemy query 添加过滤条件
        :param query: 基础 query
        :param model: SQLAlchemy 模型类
        :param user_id: 当前用户ID
        :param user_dept_field: 模型中表示部门的字段名
        :return: 添加过滤后的 query
        """
        scope = PermissionService.get_user_data_scope(user_id)
        
        if scope == DataScope.ALL:
            return query
        
        user = User.query.get(user_id)
        if not user:
            return query.filter_by(id=-1)  # 返回空结果
        
        if scope == DataScope.SELF:
            # 只能看自己的数据，假设模型有 creator_id 或 user_id 字段
            if hasattr(model, 'creator_id'):
                return query.filter_by(creator_id=user_id)
            elif hasattr(model, 'user_id'):
                return query.filter_by(user_id=user_id)
            elif hasattr(model, 'assignee_id'):
                return query.filter_by(assignee_id=user_id)
            else:
                return query
        
        if scope in (DataScope.DEPT, DataScope.DEPT_AND_BELOW):
            user_dept = user.department
            if user_dept and hasattr(model, user_dept_field):
                return query.filter(getattr(model, user_dept_field) == user_dept)
            else:
                return query.filter_by(id=-1)
        
        if scope == DataScope.CUSTOM:
            custom_depts = PermissionService.get_user_custom_depts(user_id)
            if custom_depts and hasattr(model, user_dept_field):
                return query.filter(getattr(model, user_dept_field).in_(custom_depts))
            else:
                return query.filter_by(id=-1)
        
        return query

    @staticmethod
    def invalidate_user_cache(user_id):
        """用户权限变更时清除缓存"""
        from .cache_service import CacheService
        CacheService.invalidate_user_permissions(user_id)
