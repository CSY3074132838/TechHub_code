#!/usr/bin/env python3
"""
TechHub 后端启动脚本
"""
import os
from app import create_app, db
from app.models import User, Role, Project, Task, Approval, Activity
from flask_migrate import Migrate

# 创建应用实例
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    """配置 Flask shell 上下文"""
    return {
        'db': db,
        'User': User,
        'Role': Role,
        'Project': Project,
        'Task': Task,
        'Approval': Approval,
        'Activity': Activity
    }

@app.cli.command()
def init_db():
    """初始化数据库"""
    db.create_all()
    print('数据库表创建成功！')

@app.cli.command()
def seed_db():
    """填充测试数据"""
    from app.utils.seed_data import seed_all
    seed_all()
    print('测试数据填充成功！')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
