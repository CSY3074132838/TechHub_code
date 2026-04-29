# TechHub 后端开发指南

## 权限系统

### 权限装饰器使用规范

所有受保护接口必须使用以下装饰器之一：

```python
from app.decorators import require_permission, require_any_permission, require_all_permissions, data_scope_required

# 单一权限校验
@require_permission('project_manage')
def update_project(project_id):
    pass

# 满足任一权限
@require_any_permission(['project_manage', 'task_manage'])
def some_endpoint():
    pass

# 必须满足全部权限
@require_all_permissions(['user_view', 'user_edit'])
def sensitive_endpoint():
    pass

# 数据范围注入（配合功能权限使用）
@require_permission('dashboard_view')
@data_scope_required()
def get_statistics():
    # kwargs 中会自动注入:
    # current_data_scope = DataScope 枚举值
    # current_user_dept = 当前用户部门
    # current_user_id = 当前用户ID
    pass
```

### 系统权限点清单

| 权限编码 | 说明 | 所属模块 |
|---------|------|---------|
| `all` | 全部权限（超级管理员） | 系统 |
| `dashboard_view` | 仪表盘/数据中心查看 | 数据 |
| `team_manage` | 团队管理 | 管理 |
| `approval_process` | 审批处理（通过/拒绝） | 审批 |
| `approval_urgent` | 紧急审批 | 审批 |
| `project_manage` | 项目管理（增删改） | 项目 |
| `task_manage` | 任务管理（增删改） | 任务 |
| `task_assign` | 任务分配 | 任务 |
| `team_view` | 团队查看 | 数据 |
| `task_view` | 任务查看 | 任务 |
| `task_execute` | 任务执行 | 任务 |
| `approval_submit` | 审批提交 | 审批 |
| `user_manage` | 用户管理 | 管理 |
| `role_manage` | 角色管理 | 管理 |
| `audit_view` | 审计日志查看 | 系统 |
| `data_export` | 数据导出 | 数据 |

### DataScope 数据范围

| 范围值 | 说明 |
|-------|------|
| `all` | 可查看全部数据 |
| `dept` | 仅可查看本部门数据 |
| `dept_and_below` | 可查看本部门及子部门数据 |
| `self` | 仅可查看自己的数据 |
| `custom` | 自定义部门列表（通过 `data_scope_custom` 指定） |

### 审计日志记录规范

关键操作必须记录审计日志：

```python
from app.services import AuditService

# 方式1：手动指定用户信息
AuditService.log(
    action=AuditService.PROJECT_CREATE,
    user_id=user.id,
    username=user.username,
    resource_type='project',
    resource_id=project.id,
    detail={'name': project.name},
    status='success'
)

# 方式2：从当前 JWT 上下文自动获取（推荐，用于 @jwt_required 接口）
AuditService.log_from_current_user(
    action=AuditService.PROJECT_UPDATE,
    resource_type='project',
    resource_id=project_id,
    detail={'before': before, 'after': after},
    status='success'
)
```

预定义操作类型常量：
- `LOGIN` / `LOGIN_FAILED` / `LOGOUT`
- `USER_CREATE` / `USER_UPDATE` / `USER_DELETE`
- `ROLE_CREATE` / `ROLE_UPDATE` / `ROLE_DELETE` / `ROLE_ASSIGN`
- `PROJECT_CREATE` / `PROJECT_UPDATE` / `PROJECT_DELETE`
- `TASK_CREATE` / `TASK_UPDATE` / `TASK_DELETE`
- `APPROVAL_CREATE` / `APPROVAL_PROCESS`
- `PERMISSION_DENIED`
- `DATA_EXPORT` / `PASSWORD_CHANGE` / `TOKEN_REFRESH`

### 登录安全策略

- 最大失败次数：**5 次**
- 锁定时长：**15 分钟**
- 失败响应会返回 `remaining_attempts` 提示剩余次数
- 达到上限后返回 `account_locked` 错误

### 缓存服务

```python
from app.services import CacheService

# 缓存用户权限（默认 300 秒）
CacheService.cache_user_permissions(user_id, permissions)

# 读取缓存权限
perms = CacheService.get_user_permissions(user_id)

# 清除缓存（权限变更时调用）
CacheService.invalidate_user_permissions(user_id)
```

Redis 配置（可选）：
- 环境变量 `REDIS_URL` 或 `config.py` 中配置
- 未配置时自动降级为应用内存缓存

## API 接口清单

### 认证相关 `/api/auth`
- `POST /login` - 登录（公开）
- `POST /register` - 注册（公开）
- `POST /refresh` - 刷新 Token
- `POST /logout` - 登出
- `GET /me` - 获取当前用户信息
- `PUT /change-password` - 修改密码

### 用户管理 `/api/users`
- `GET /` - 用户列表
- `GET /permissions` - 系统权限点列表
- `GET /roles` - 角色列表
- `POST /roles` - 创建角色（需 `all`）
- `PUT /roles/<id>` - 更新角色（需 `all`）
- `DELETE /roles/<id>` - 删除角色（需 `all`）

### 审计日志 `/api/audit`
- `GET /logs` - 查询日志（需 `audit_view`）
- `GET /stats` - 统计概览（需 `audit_view`）
- `GET /actions` - 操作类型字典（需 `audit_view`）
