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
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(projects_bp, url_prefix='/api/projects')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
    app.register_blueprint(approvals_bp, url_prefix='/api/approvals')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(activities_bp, url_prefix='/api/activities')
    
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
