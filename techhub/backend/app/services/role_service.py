"""
角色管理服务 - 角色CRUD与用户角色绑定
"""
from app import db
from app.models import User, Role, DataScope
from .permission_service import PermissionService


class RoleService:
    """角色管理服务"""

    @staticmethod
    def create_role(name, description='', level=4, permissions=None, data_scope=None, data_scope_custom=None):
        """创建新角色"""
        if Role.query.filter_by(name=name).first():
            raise ValueError('角色名称已存在')
        
        role = Role(
            name=name,
            description=description,
            level=level,
            permissions=permissions or [],
            data_scope=data_scope or DataScope.SELF,
            data_scope_custom=data_scope_custom or []
        )
        db.session.add(role)
        db.session.commit()
        return role

    @staticmethod
    def update_role(role_id, **kwargs):
        """更新角色信息"""
        role = Role.query.get(role_id)
        if not role:
            raise ValueError('角色不存在')
        
        allowed_fields = ['name', 'description', 'level', 'permissions', 'data_scope', 'data_scope_custom']
        for field in allowed_fields:
            if field in kwargs:
                setattr(role, field, kwargs[field])
        
        db.session.commit()
        
        # 级联更新该角色下所有用户的权限版本号（实现权限即时生效）
        for user in role.users:
            user.permission_version = (user.permission_version or 1) + 1
            PermissionService.invalidate_user_cache(user.id)
        
        db.session.commit()
        return role

    @staticmethod
    def delete_role(role_id):
        """删除角色"""
        role = Role.query.get(role_id)
        if not role:
            raise ValueError('角色不存在')
        if role.users:
            raise ValueError('该角色下还有用户，无法删除')
        
        db.session.delete(role)
        db.session.commit()
        return True

    @staticmethod
    def assign_roles_to_user(user_id, role_ids):
        """
        给用户分配角色（覆盖式）
        :param user_id: 用户ID
        :param role_ids: 角色ID列表
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError('用户不存在')
        
        roles = Role.query.filter(Role.id.in_(role_ids)).all()
        user.roles = roles
        user.permission_version = (user.permission_version or 1) + 1
        db.session.commit()
        
        # 清除用户权限缓存
        PermissionService.invalidate_user_cache(user_id)
        
        return user

    @staticmethod
    def add_role_to_user(user_id, role_id):
        """给用户追加一个角色"""
        user = User.query.get(user_id)
        role = Role.query.get(role_id)
        if not user or not role:
            raise ValueError('用户或角色不存在')
        
        if role not in user.roles:
            user.roles.append(role)
            user.permission_version = (user.permission_version or 1) + 1
            db.session.commit()
            PermissionService.invalidate_user_cache(user_id)
        
        return user

    @staticmethod
    def remove_role_from_user(user_id, role_id):
        """移除用户的某个角色"""
        user = User.query.get(user_id)
        role = Role.query.get(role_id)
        if not user or not role:
            raise ValueError('用户或角色不存在')
        
        if role in user.roles:
            user.roles.remove(role)
            user.permission_version = (user.permission_version or 1) + 1
            db.session.commit()
            PermissionService.invalidate_user_cache(user_id)
        
        return user

    @staticmethod
    def get_user_roles(user_id):
        """获取用户的角色列表"""
        user = User.query.get(user_id)
        if not user:
            return []
        return [role.to_dict() for role in user.roles]

    @staticmethod
    def get_role_users(role_id):
        """获取角色下的用户列表"""
        role = Role.query.get(role_id)
        if not role:
            return []
        return [user.to_dict() for user in role.users]
