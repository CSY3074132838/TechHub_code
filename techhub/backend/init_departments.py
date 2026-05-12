#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化部门数据脚本
运行方式: python init_departments.py
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')

from app import create_app, db
from app.models import Department, User

# 预定义部门列表（name -> code）
DEPARTMENT_MAP = {
    '研发部': 'RD',
    '产品部': 'PD',
    '设计部': 'DES',
    '测试部': 'QA',
    '运营部': 'OP',
    '行政部': 'ADM',
    '技术部': 'TECH',
}

app = create_app()
with app.app_context():
    created_depts = {}
    
    # 1. 创建预定义部门（如果不存在）
    for name, code in DEPARTMENT_MAP.items():
        dept = Department.query.filter_by(code=code).first()
        if not dept:
            dept = Department(
                name=name,
                code=code,
                description=f'{name} - 公司核心部门',
                sort_order=len(created_depts)
            )
            db.session.add(dept)
            db.session.flush()
            print(f"  + 创建部门: {name} ({code})")
        created_depts[name] = dept
    
    # 2. 扫描所有已有用户，为未在映射中的部门名创建记录
    all_dept_names = db.session.query(User.department).distinct().all()
    for (dept_name,) in all_dept_names:
        if not dept_name:
            continue
        if dept_name not in created_depts:
            base_code = ''.join([c for c in dept_name if c.isalnum()]).upper()[:10] or 'DEPT'
            code = base_code
            suffix = 1
            while Department.query.filter_by(code=code).first():
                code = f"{base_code}{suffix}"
                suffix += 1
            
            dept = Department(
                name=dept_name,
                code=code,
                description=f'{dept_name}',
                sort_order=len(created_depts)
            )
            db.session.add(dept)
            db.session.flush()
            created_depts[dept_name] = dept
            print(f"  + 创建部门: {dept_name} ({code})")
    
    db.session.commit()
    
    # 3. 同步所有用户的 department_id
    synced = 0
    for user in User.query.all():
        if user.department and user.department in created_depts and not user.department_id:
            user.department_id = created_depts[user.department].id
            synced += 1
    
    if synced > 0:
        db.session.commit()
        print(f"  ↻ 同步 {synced} 位用户的部门关联")
    
    # 输出结果
    total = Department.query.count()
    print(f"\n✓ 部门数据初始化完成，当前共有 {total} 个部门")
    print("\n部门列表:")
    for dept in Department.query.order_by(Department.sort_order).all():
        print(f"  - {dept.name} ({dept.code})")
