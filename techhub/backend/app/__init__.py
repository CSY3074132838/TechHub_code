"""
TechHub Flask 应用工厂
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from config import config

# 初始化扩展（不绑定应用）
db = SQLAlchemy()
jwt = JWTManager()
ma = Marshmallow()
migrate = Migrate()

def create_app(config_name='default'):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    db.init_app(app)
    jwt.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)
    
    # 启用 CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # 注册蓝图
    from app.api.auth import auth_bp
    from app.api.users import users_bp
    from app.api.projects import projects_bp
    from app.api.tasks import tasks_bp
    from app.api.approvals import approvals_bp
    from app.api.dashboard import dashboard_bp
    from app.api.activities import activities_bp
    from app.api.audit import audit_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(projects_bp, url_prefix='/api/projects')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
    app.register_blueprint(approvals_bp, url_prefix='/api/approvals')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(activities_bp, url_prefix='/api/activities')
    app.register_blueprint(audit_bp, url_prefix='/api/audit')
    
    # JWT Token 黑名单检查 + 权限版本号校验（实现权限即时生效）
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        from app.services import CacheService
        from app.models import User
        
        # 1. 检查Token是否被主动注销
        jti = jwt_payload['jti']
        if CacheService.is_token_revoked(jti):
            return True
        
        # 2. 检查权限版本号是否一致（权限变更即时生效机制）
        user_id = jwt_payload.get('sub')
        token_version = jwt_payload.get('permission_version')
        if user_id and token_version is not None:
            user = User.query.get(user_id)
            if user and user.permission_version != token_version:
                # 版本号不一致，视为Token已失效
                return True
        
        return False
    
    # JWT 错误处理
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {'message': 'Token 已过期', 'error': 'token_expired'}, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {'message': '无效的 Token', 'error': 'invalid_token'}, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {'message': '缺少认证 Token', 'error': 'authorization_required'}, 401
    
    # 根路由
    @app.route('/')
    def index():
        return {
            'message': 'Welcome to TechHub API',
            'version': '1.0.0',
            'docs': '/api/docs'
        }
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
        # 初始化角色数据
        from app.models import Role
        Role.init_roles()
    
    return app
