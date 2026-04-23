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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    users = db.relationship('User', secondary=user_roles, back_populates='roles')
    
    @staticmethod
    def init_roles():
        """初始化系统默认角色"""
        roles = [
            {'name': 'super_admin', 'description': '超级管理员', 'level': 1, 
             'permissions': ['all']},
            {'name': 'department_manager', 'description': '部门负责人', 'level': 2,
             'permissions': ['dashboard_view', 'team_manage', 'approval_urgent']},
            {'name': 'project_manager', 'description': '项目经理', 'level': 3,
             'permissions': ['project_manage', 'task_assign', 'team_view']},
            {'name': 'member', 'description': '普通成员', 'level': 4,
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
            'permissions': self.permissions
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
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    roles = db.relationship('Role', secondary=user_roles, back_populates='users')
    created_projects = db.relationship('Project', backref='creator', lazy='dynamic')
    assigned_tasks = db.relationship('Task', foreign_keys='Task.assignee_id', backref='assignee', lazy='dynamic')
    created_tasks = db.relationship('Task', foreign_keys='Task.creator_id', backref='task_creator', lazy='dynamic')
    approvals = db.relationship('Approval', foreign_keys='Approval.applicant_id', backref='applicant', lazy='dynamic')
    processed_approvals = db.relationship('Approval', foreign_keys='Approval.processor_id', backref='processor', lazy='dynamic')
    activities = db.relationship('Activity', backref='user', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    
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
    
    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            'real_name': self.real_name,
            'avatar': self.avatar,
            'department': self.department,
            'position': self.position,
            'is_active': self.is_active,
            'roles': [role.to_dict() for role in self.roles],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_email:
            data['email'] = self.email
            data['phone'] = self.phone
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
    tasks = db.relationship('Task', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    members = db.relationship('User', secondary=project_members, backref='projects')
    
    def get_task_stats(self):
        """获取项目任务统计"""
        total = self.tasks.count()
        todo = self.tasks.filter_by(status=TaskStatus.TODO).count()
        in_progress = self.tasks.filter_by(status=TaskStatus.IN_PROGRESS).count()
        done = self.tasks.filter_by(status=TaskStatus.DONE).count()
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
            'members': [member.to_dict() for member in self.members],
            'stats': self.get_task_stats(),
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
    status = db.Column(db.Enum(TaskStatus), default=TaskStatus.TODO)
    priority = db.Column(db.Enum(TaskPriority), default=TaskPriority.MEDIUM)
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
            'status': self.status.value if self.status else None,
            'priority': self.priority.value if self.priority else None,
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
    approval_type = db.Column(db.Enum(ApprovalType), nullable=False)
    status = db.Column(db.Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    is_urgent = db.Column(db.Boolean, default=False)
    amount = db.Column(db.Numeric(10, 2))  # 金额（报销/采购）
    description = db.Column(db.Text)
    applicant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    processor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    processed_at = db.Column(db.DateTime)
    process_comment = db.Column(db.Text)
    attachments = db.Column(db.JSON, default=list)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'approval_type': self.approval_type.value if self.approval_type else None,
            'status': self.status.value if self.status else None,
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

class Activity(db.Model):
    """活动记录模型 - 团队动态"""
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    activity_type = db.Column(db.Enum(ActivityType), nullable=False)
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
            'activity_type': self.activity_type.value if self.activity_type else None,
            'title': self.title,
            'description': self.description,
            'user': self.user.to_dict() if self.user else None,
            'task_id': self.task_id,
            'project_id': self.project_id,
            'meta_data': self.meta_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class SystemConfig(db.Model):
    """系统配置模型"""
    __tablename__ = 'system_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.String(200))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
