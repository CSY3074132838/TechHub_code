"""
TechHub 数据库模型定义
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
import enum

# ==================== 枚举类型定义 ====================

class TaskStatus(enum.Enum):
    """任务状态枚举"""
    TODO = 'todo'
    IN_PROGRESS = 'in_progress'
    REVIEW = 'review'
    DONE = 'done'

class TaskPriority(enum.Enum):
    """任务优先级枚举"""
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    URGENT = 'urgent'

class ApprovalStatus(enum.Enum):
    """审批状态枚举"""
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    CANCELLED = 'cancelled'

class ApprovalType(enum.Enum):
    """审批类型枚举"""
    LEAVE = 'leave'
    EXPENSE = 'expense'
    PURCHASE = 'purchase'
    OVERTIME = 'overtime'
    PERMISSION = 'permission'
    OTHER = 'other'

class ActivityType(enum.Enum):
    """活动类型枚举"""
    TASK_CREATED = 'task_created'
    TASK_UPDATED = 'task_updated'
    TASK_COMPLETED = 'task_completed'
    PROJECT_CREATED = 'project_created'
    COMMENT_ADDED = 'comment_added'
    APPROVAL_SUBMITTED = 'approval_submitted'
    APPROVAL_APPROVED = 'approval_approved'

class DataScope(enum.Enum):
    """数据范围枚举 - 行级数据权限控制"""
    ALL = 'all'           # 全部数据
    DEPT = 'dept'         # 本部门数据
    DEPT_AND_BELOW = 'dept_and_below'  # 本部门及子部门数据
    SELF = 'self'         # 仅自己的数据
    CUSTOM = 'custom'     # 自定义（指定部门列表）

class ClientStatus(enum.Enum):
    """客户状态枚举"""
    POTENTIAL = 'potential'    # 潜在客户
    ACTIVE = 'active'          # 合作中
    INACTIVE = 'inactive'      # 暂停合作
    LOST = 'lost'              # 已流失

class ContractStatus(enum.Enum):
    """合同状态枚举"""
    DRAFT = 'draft'            # 草稿
    PENDING = 'pending'        # 审批中
    ACTIVE = 'active'          # 生效中
    COMPLETED = 'completed'    # 已完成
    TERMINATED = 'terminated'  # 已终止

class TicketStatus(enum.Enum):
    """工单状态枚举"""
    OPEN = 'open'              # 待处理
    IN_PROGRESS = 'in_progress'# 处理中
    WAITING = 'waiting'        # 等待反馈
    RESOLVED = 'resolved'      # 已解决
    CLOSED = 'closed'          # 已关闭

class TicketPriority(enum.Enum):
    """工单优先级枚举"""
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    URGENT = 'urgent'


# ==================== 【第二次迭代】员工状态枚举 ====================
class EmployeeStatus(enum.Enum):
    """员工在职状态枚举"""
    PROBATION = 'probation'      # 试用期
    ACTIVE = 'active'            # 正式员工
    PENDING_LEAVE = 'pending_leave'  # 待离职
    LEFT = 'left'                # 已离职
    SUSPENDED = 'suspended'      # 停薪留职


# ==================== 关联表定义 ====================

# 用户-角色关联表
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)

# 项目-成员关联表
project_members = db.Table('project_members',
    db.Column('project_id', db.Integer, db.ForeignKey('projects.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)

# ==================== 模型类定义 ====================

class Role(db.Model):
    """角色模型 - RBAC权限控制"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    level = db.Column(db.Integer, default=4)  # 1-超级管理员, 2-部门负责人, 3-项目经理, 4-普通成员
    permissions = db.Column(db.JSON, default=list)
    data_scope = db.Column(db.String(20), default='self')
    data_scope_custom = db.Column(db.JSON, default=list)  # CUSTOM模式下的部门列表
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    users = db.relationship('User', secondary=user_roles, back_populates='roles')
    
    @staticmethod
    def init_roles():
        """初始化系统默认角色"""
        roles = [
            {'name': 'super_admin', 'description': '总经理', 'level': 1,
             'permissions': ['all']},
            {'name': 'deputy_general_manager', 'description': '副总经理', 'level': 2,
             'permissions': ['all']},
            {'name': 'data_analyst', 'description': '数据分析员', 'level': 3,
             'permissions': ['dashboard_view', 'data_export']},
            {'name': 'operations_director', 'description': '运营总监', 'level': 3,
             'permissions': ['dashboard_view', 'team_manage', 'data_export', 'audit_view']},
            {'name': 'finance_director', 'description': '财务总监', 'level': 3,
             'permissions': ['dashboard_view', 'audit_view', 'data_export', 'approval_urgent']},
            {'name': 'tech_director', 'description': '技术总监', 'level': 3,
             'permissions': ['dashboard_view', 'team_manage', 'project_manage', 'task_manage']},
            {'name': 'department_manager', 'description': '部门负责人', 'level': 4,
             'permissions': ['team_manage', 'approval_urgent']},
            {'name': 'project_manager', 'description': '项目经理', 'level': 5,
             'permissions': ['project_manage', 'task_assign', 'team_view']},
            {'name': 'team_leader', 'description': '项目组长', 'level': 6,
             'permissions': ['task_view', 'task_execute', 'task_assign', 'team_view']},
            {'name': 'member', 'description': '普通成员', 'level': 7,
             'permissions': ['task_view', 'task_execute', 'approval_submit']}
        ]
        
        for role_data in roles:
            if not Role.query.filter_by(name=role_data['name']).first():
                role = Role(**role_data)
                db.session.add(role)
        
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'level': self.level,
            'permissions': self.permissions,
            'data_scope': self.data_scope,
            'data_scope_custom': self.data_scope_custom
        }

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    real_name = db.Column(db.String(50))
    avatar = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    department = db.Column(db.String(50))
    position = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    permission_version = db.Column(db.Integer, default=1)  # 权限版本号，用于Token即时失效
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ==================== 【第二次迭代】员工档案扩展字段 ====================
    employee_no = db.Column(db.String(50), unique=True, index=True)  # 工号
    employee_status = db.Column(db.String(20), default='probation')  # 员工状态：probation/active/pending_leave/left/suspended
    entry_date = db.Column(db.Date)           # 入职日期
    probation_end_date = db.Column(db.Date)   # 转正日期
    leave_date = db.Column(db.Date)           # 离职日期
    id_card = db.Column(db.String(18))        # 身份证号
    gender = db.Column(db.String(10))         # 性别
    birthday = db.Column(db.Date)             # 生日
    native_place = db.Column(db.String(100))  # 籍贯
    address = db.Column(db.Text)              # 现居地址
    education = db.Column(db.String(50))      # 学历
    school = db.Column(db.String(100))        # 毕业院校
    major = db.Column(db.String(100))         # 专业
    emergency_contact = db.Column(db.String(50))   # 紧急联系人
    emergency_phone = db.Column(db.String(20))     # 紧急联系人电话
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # 直属上级ID
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))  # 所属部门ID
    attachments = db.Column(db.JSON, default=list)   # 附件列表（入职材料、证书等）
    # ==================== 【第二次迭代】扩展字段结束 ====================
    
    # 关联关系
    roles = db.relationship('Role', secondary=user_roles, back_populates='users')
    created_projects = db.relationship('Project', foreign_keys='Project.creator_id', backref='creator', lazy='dynamic')
    assigned_tasks = db.relationship('Task', foreign_keys='Task.assignee_id', backref='assignee', lazy='dynamic')
    created_tasks = db.relationship('Task', foreign_keys='Task.creator_id', backref='task_creator', lazy='dynamic')
    approvals = db.relationship('Approval', foreign_keys='Approval.applicant_id', backref='applicant', lazy='dynamic')
    processed_approvals = db.relationship('Approval', foreign_keys='Approval.processor_id', backref='processor', lazy='dynamic')
    activities = db.relationship('Activity', backref='user', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    # ==================== 【第二次迭代】自关联：直属上级与下属 ====================
    manager = db.relationship('User', remote_side=[id], backref='subordinates')
    department_ref = db.relationship('Department', foreign_keys=[department_id], backref='members')
    # ==================== 【第二次迭代】自关联结束 ====================
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission):
        """检查用户是否有指定权限"""
        for role in self.roles:
            if 'all' in role.permissions or permission in role.permissions:
                return True
        return False
    
    def get_highest_role_level(self):
        """获取用户最高角色等级"""
        if not self.roles:
            return 4
        return min(role.level for role in self.roles)
    
    def to_dict(self, include_email=False, include_detail=False):
        data = {
            'id': self.id,
            'username': self.username,
            'real_name': self.real_name or self.username,
            'avatar': self.avatar,
            'department': self.department,
            'position': self.position,
            'is_active': self.is_active,
            'roles': [role.to_dict() for role in self.roles],
            'permission_version': self.permission_version,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_email:
            data['email'] = self.email
            data['phone'] = self.phone
        # ==================== 【第二次迭代】员工档案详情序列化 ====================
        if include_detail:
            data.update({
                'employee_no': self.employee_no,
                'employee_status': self.employee_status,
                'entry_date': self.entry_date.isoformat() if self.entry_date else None,
                'probation_end_date': self.probation_end_date.isoformat() if self.probation_end_date else None,
                'leave_date': self.leave_date.isoformat() if self.leave_date else None,
                'id_card': self.id_card,
                'gender': self.gender,
                'birthday': self.birthday.isoformat() if self.birthday else None,
                'native_place': self.native_place,
                'address': self.address,
                'education': self.education,
                'school': self.school,
                'major': self.major,
                'emergency_contact': self.emergency_contact,
                'emergency_phone': self.emergency_phone,
                'manager_id': self.manager_id,
                'manager': self.manager.to_dict() if self.manager else None,
                'department_id': self.department_id,
                'attachments': self.attachments or []
            })
        # ==================== 【第二次迭代】详情序列化结束 ====================
        return data

# ==================== 【第二次迭代】部门模型 ====================
class Department(db.Model):
    """部门模型 - 支持层级组织架构"""
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)   # 部门编码，如 DEV-001
    description = db.Column(db.String(200))
    parent_id = db.Column(db.Integer, db.ForeignKey('departments.id'))  # 父部门ID
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'))       # 部门负责人ID
    sort_order = db.Column(db.Integer, default=0)                       # 排序号
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    manager = db.relationship('User', foreign_keys=[manager_id])
    parent = db.relationship('Department', remote_side=[id], backref='children')
    
    def get_member_count(self):
        """获取部门成员数量（仅直属成员）"""
        return User.query.filter_by(department_id=self.id).count()
    
    def get_total_member_count(self):
        """获取部门及所有子部门成员数量"""
        count = self.get_member_count()
        for child in self.children:
            count += child.get_total_member_count()
        return count
    
    def to_dict(self, include_children=False):
        data = {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'parent_id': self.parent_id,
            'manager_id': self.manager_id,
            'manager': self.manager.to_dict() if self.manager else None,
            'sort_order': self.sort_order,
            'member_count': self.get_member_count(),
            'total_member_count': self.get_total_member_count(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_children:
            data['children'] = [child.to_dict(include_children=True) for child in self.children]
        return data


class Project(db.Model):
    """项目模型"""
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')  # active, archived, deleted
    color = db.Column(db.String(7), default='#1890ff')  # 项目颜色标识
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    leader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # 项目负责人
    tasks = db.relationship('Task', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    members = db.relationship('User', secondary=project_members, backref='projects')
    client = db.relationship('Client', backref='projects')
    leader = db.relationship('User', foreign_keys=[leader_id])
    
    def get_task_stats(self):
        """获取项目任务统计"""
        total = self.tasks.count()
        todo = self.tasks.filter_by(status='todo').count()
        in_progress = self.tasks.filter_by(status='in_progress').count()
        done = self.tasks.filter_by(status='done').count()
        return {
            'total': total,
            'todo': todo,
            'in_progress': in_progress,
            'done': done,
            'progress': round((done / total * 100), 1) if total > 0 else 0
        }
    
    def to_dict(self, include_tasks=False):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'color': self.color,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'creator': self.creator.to_dict() if self.creator else None,
            'leader_id': self.leader_id,
            'leader': self.leader.to_dict() if self.leader else None,
            'members': [member.to_dict() for member in self.members],
            'stats': self.get_task_stats(),
            'client_id': self.client_id,
            'client': self.client.to_dict() if self.client else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_tasks:
            data['tasks'] = [task.to_dict() for task in self.tasks]
        return data

class Task(db.Model):
    """任务模型"""
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='todo')
    priority = db.Column(db.String(20), default='medium')
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    due_date = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    order = db.Column(db.Integer, default=0)  # 看板排序
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    comments = db.relationship('Comment', backref='task', lazy='dynamic', cascade='all, delete-orphan')
    activities = db.relationship('Activity', backref='task', lazy='dynamic')
    
    def to_dict(self, include_comments=False):
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'project_id': self.project_id,
            'assignee': self.assignee.to_dict() if self.assignee else None,
            'creator': self.task_creator.to_dict() if self.task_creator else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'order': self.order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_comments:
            data['comments'] = [comment.to_dict() for comment in self.comments.order_by(Comment.created_at.desc())]
        return data

class Comment(db.Model):
    """评论模型"""
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'author': self.author.to_dict() if self.author else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Approval(db.Model):
    """审批模型"""
    __tablename__ = 'approvals'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    approval_type = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending')
    is_urgent = db.Column(db.Boolean, default=False)
    amount = db.Column(db.Numeric(10, 2))  # 金额（报销/采购）
    description = db.Column(db.Text)
    applicant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    processor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    processed_at = db.Column(db.DateTime)
    process_comment = db.Column(db.Text)
    attachments = db.Column(db.JSON, default=list)
    current_node_id = db.Column(db.Integer, db.ForeignKey('approval_nodes.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    nodes = db.relationship('ApprovalNode', backref='approval', lazy='dynamic', 
                            foreign_keys='ApprovalNode.approval_id',
                            cascade='all, delete-orphan', order_by='ApprovalNode.order')
    
    def get_approval_chain(self):
        """获取审批链状态"""
        nodes = self.nodes.order_by(ApprovalNode.order).all()
        return [node.to_dict() for node in nodes]
    
    def to_dict(self, include_chain=False):
        data = {
            'id': self.id,
            'title': self.title,
            'approval_type': self.approval_type,
            'status': self.status,
            'is_urgent': self.is_urgent,
            'amount': float(self.amount) if self.amount else None,
            'description': self.description,
            'applicant': self.applicant.to_dict() if self.applicant else None,
            'processor': self.processor.to_dict() if self.processor else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'process_comment': self.process_comment,
            'attachments': self.attachments,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_chain:
            data['approval_chain'] = self.get_approval_chain()
            data['current_node'] = self.current_node_id
        return data

class Activity(db.Model):
    """活动记录模型 - 团队动态"""
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    activity_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    meta_data = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'activity_type': self.activity_type,
            'title': self.title,
            'description': self.description,
            'user': self.user.to_dict() if self.user else None,
            'task_id': self.task_id,
            'project_id': self.project_id,
            'meta_data': self.meta_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ApprovalNode(db.Model):
    """审批节点模型 - 审批链可视化"""
    __tablename__ = 'approval_nodes'
    
    id = db.Column(db.Integer, primary_key=True)
    approval_id = db.Column(db.Integer, db.ForeignKey('approvals.id'), nullable=False)
    node_name = db.Column(db.String(100), nullable=False)  # 节点名称，如"部门经理审批"
    handler_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # 指定处理人
    status = db.Column(db.String(20), default='pending')  # pending, completed, skipped, rejected
    order = db.Column(db.Integer, default=0)  # 节点顺序
    comment = db.Column(db.Text)
    handled_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    handler = db.relationship('User', foreign_keys=[handler_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'node_name': self.node_name,
            'handler': self.handler.to_dict() if self.handler else None,
            'status': self.status,
            'order': self.order,
            'comment': self.comment,
            'handled_at': self.handled_at.isoformat() if self.handled_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AuditLog(db.Model):
    """审计日志模型 - 安全审计与操作追溯"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    username = db.Column(db.String(80), nullable=False)
    action = db.Column(db.String(50), nullable=False, index=True)  # LOGIN, LOGOUT, USER_CREATE, ROLE_UPDATE, etc.
    resource_type = db.Column(db.String(50))  # user, role, project, task, approval
    resource_id = db.Column(db.Integer)
    detail = db.Column(db.JSON, default=dict)  # {before: ..., after: ...}
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    status = db.Column(db.String(20), default='success')  # success / failure
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'detail': self.detail,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Client(db.Model):
    """客户模型 - 客户关系管理"""
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    industry = db.Column(db.String(50))
    contact_name = db.Column(db.String(50))
    contact_phone = db.Column(db.String(20))
    contact_email = db.Column(db.String(120))
    address = db.Column(db.Text)
    status = db.Column(db.String(20), default='potential')
    level = db.Column(db.String(20), default='b')  # s/a/b/c
    remark = db.Column(db.Text)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # 客户经理
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    manager = db.relationship('User', foreign_keys=[manager_id])
    contracts = db.relationship('Contract', backref='client', lazy='dynamic', cascade='all, delete-orphan')
    tickets = db.relationship('Ticket', backref='client', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self, include_projects=False):
        data = {
            'id': self.id,
            'name': self.name,
            'industry': self.industry,
            'contact_name': self.contact_name,
            'contact_phone': self.contact_phone,
            'contact_email': self.contact_email,
            'address': self.address,
            'status': self.status,
            'level': self.level,
            'remark': self.remark,
            'manager': self.manager.to_dict() if self.manager else None,
            'manager_id': self.manager_id,
            'project_count': len(self.projects) if self.projects else 0,
            'contract_count': self.contracts.count() if self.contracts else 0,
            'ticket_count': self.tickets.count() if self.tickets else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_projects:
            data['projects'] = [p.to_dict() for p in self.projects]
        return data


class Contract(db.Model):
    """合同模型 - 客户合同管理"""
    __tablename__ = 'contracts'
    
    id = db.Column(db.Integer, primary_key=True)
    contract_no = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    amount = db.Column(db.Numeric(12, 2))
    sign_date = db.Column(db.Date)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='draft')
    payment_terms = db.Column(db.Text)
    content = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    creator = db.relationship('User', foreign_keys=[created_by])
    project = db.relationship('Project', backref='contracts')
    
    def to_dict(self):
        return {
            'id': self.id,
            'contract_no': self.contract_no,
            'name': self.name,
            'client_id': self.client_id,
            'client': self.client.to_dict() if self.client else None,
            'project_id': self.project_id,
            'project': self.project.to_dict() if self.project else None,
            'amount': float(self.amount) if self.amount else None,
            'sign_date': self.sign_date.isoformat() if self.sign_date else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'payment_terms': self.payment_terms,
            'content': self.content,
            'created_by': self.created_by,
            'creator': self.creator.to_dict() if self.creator else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Ticket(db.Model):
    """工单模型 - 客户反馈/问题跟踪"""
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_no = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    status = db.Column(db.String(20), default='open')
    priority = db.Column(db.String(20), default='medium')
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    resolved_at = db.Column(db.DateTime)
    resolution = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    assignee = db.relationship('User', foreign_keys=[assignee_id])
    reporter = db.relationship('User', foreign_keys=[reporter_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'ticket_no': self.ticket_no,
            'title': self.title,
            'description': self.description,
            'client_id': self.client_id,
            'client': self.client.to_dict() if self.client else None,
            'status': self.status,
            'priority': self.priority,
            'assignee_id': self.assignee_id,
            'assignee': self.assignee.to_dict() if self.assignee else None,
            'reporter_id': self.reporter_id,
            'reporter': self.reporter.to_dict() if self.reporter else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolution': self.resolution,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class SystemConfig(db.Model):
    """系统配置模型"""
    __tablename__ = 'system_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.String(200))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ==================== 【第二次迭代】考勤与工时模型 ====================
class Attendance(db.Model):
    """考勤记录模型 - 工时填报"""
    __tablename__ = 'attendances'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    work_date = db.Column(db.Date, nullable=False)           # 工作日期
    check_in = db.Column(db.DateTime)                        # 上班打卡时间
    check_out = db.Column(db.DateTime)                       # 下班打卡时间
    work_hours = db.Column(db.Numeric(4, 2), default=0)      # 工作时长（小时）
    overtime_hours = db.Column(db.Numeric(4, 2), default=0)  # 加班时长
    status = db.Column(db.String(20), default='normal')      # normal/late/early/leave/absent
    remark = db.Column(db.Text)                              # 备注
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user': self.user.to_dict() if self.user else None,
            'work_date': self.work_date.isoformat() if self.work_date else None,
            'check_in': self.check_in.isoformat() if self.check_in else None,
            'check_out': self.check_out.isoformat() if self.check_out else None,
            'work_hours': float(self.work_hours) if self.work_hours else 0,
            'overtime_hours': float(self.overtime_hours) if self.overtime_hours else 0,
            'status': self.status,
            'remark': self.remark,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class LeaveBalance(db.Model):
    """假期余额模型"""
    __tablename__ = 'leave_balances'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    leave_type = db.Column(db.String(20), nullable=False)    # annual/sick/personal/marriage/maternity
    total_days = db.Column(db.Numeric(5, 1), default=0)      # 总天数
    used_days = db.Column(db.Numeric(5, 1), default=0)       # 已用天数
    year = db.Column(db.Integer, nullable=False)             # 所属年份
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'leave_type': self.leave_type,
            'total_days': float(self.total_days) if self.total_days else 0,
            'used_days': float(self.used_days) if self.used_days else 0,
            'remaining_days': float(self.total_days or 0) - float(self.used_days or 0),
            'year': self.year,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class WorkTimeRecord(db.Model):
    """工时记录模型 - 关联项目/任务"""
    __tablename__ = 'work_time_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    work_date = db.Column(db.Date, nullable=False)
    hours = db.Column(db.Numeric(4, 2), default=0)           # 投入工时
    description = db.Column(db.Text)                         # 工作内容描述
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User')
    project = db.relationship('Project')
    task = db.relationship('Task')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user': self.user.to_dict() if self.user else None,
            'project_id': self.project_id,
            'project': self.project.to_dict() if self.project else None,
            'task_id': self.task_id,
            'task': self.task.to_dict() if self.task else None,
            'work_date': self.work_date.isoformat() if self.work_date else None,
            'hours': float(self.hours) if self.hours else 0,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
# ==================== 【第二次迭代】考勤与工时模型结束 ====================


# ==================== 【第二次迭代】财务管理模型 ====================
class Expense(db.Model):
    """费用报销模型"""
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(50), default='other')  # travel/office/entertainment/training/meal/transport/other
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # draft/pending/approved/rejected/reimbursed
    attachments = db.Column(db.JSON, default=list)
    approval_id = db.Column(db.Integer, db.ForeignKey('approvals.id'))  # 关联审批
    reimbursed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', foreign_keys=[user_id])
    approval = db.relationship('Approval', foreign_keys=[approval_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user': self.user.to_dict() if self.user else None,
            'title': self.title,
            'amount': float(self.amount) if self.amount else 0,
            'category': self.category,
            'description': self.description,
            'status': self.status,
            'attachments': self.attachments or [],
            'approval_id': self.approval_id,
            'reimbursed_at': self.reimbursed_at.isoformat() if self.reimbursed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PaymentRecord(db.Model):
    """收付款记录模型 - 合同/项目资金跟踪"""
    __tablename__ = 'payment_records'
    
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contracts.id'), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    payment_type = db.Column(db.String(20), nullable=False)  # income/expense
    payment_method = db.Column(db.String(50), default='bank_transfer')  # bank_transfer/alipay/wechat/cash
    status = db.Column(db.String(20), default='pending')  # pending/completed/cancelled
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    contract = db.relationship('Contract', foreign_keys=[contract_id])
    project = db.relationship('Project', foreign_keys=[project_id])
    client = db.relationship('Client', foreign_keys=[client_id])
    creator = db.relationship('User', foreign_keys=[created_by])
    
    def to_dict(self):
        return {
            'id': self.id,
            'contract_id': self.contract_id,
            'contract': self.contract.to_dict() if self.contract else None,
            'project_id': self.project_id,
            'project': self.project.to_dict() if self.project else None,
            'client_id': self.client_id,
            'client': self.client.to_dict() if self.client else None,
            'title': self.title,
            'amount': float(self.amount) if self.amount else 0,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'payment_type': self.payment_type,
            'payment_method': self.payment_method,
            'status': self.status,
            'description': self.description,
            'created_by': self.created_by,
            'creator': self.creator.to_dict() if self.creator else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Notification(db.Model):
    """消息通知模型"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    notification_type = db.Column(db.String(50), default='system')  # approval/task/finance/system
    is_read = db.Column(db.Boolean, default=False)
    related_type = db.Column(db.String(50))  # approval/task/expense/payment
    related_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'content': self.content,
            'notification_type': self.notification_type,
            'is_read': self.is_read,
            'related_type': self.related_type,
            'related_id': self.related_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
# ==================== 【第二次迭代】财务管理模型结束 ====================
