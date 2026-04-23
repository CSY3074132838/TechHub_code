"""
测试数据填充脚本
"""
from datetime import datetime, timedelta
from faker import Faker
from app import db
from app.models import (
    User, Role, Project, Task, Approval, Activity, Comment,
    TaskStatus, TaskPriority, ApprovalType, ApprovalStatus, ActivityType
)

fake = Faker('zh_CN')

def seed_roles():
    """初始化角色"""
    Role.init_roles()
    print("✓ 角色数据已初始化")

def seed_users(count=20):
    """创建测试用户"""
    departments = ['研发部', '产品部', '设计部', '测试部', '运营部', '行政部']
    positions = ['工程师', '高级工程师', '产品经理', '设计师', '测试工程师', '运营专员']
    
    users = []
    
    # 创建超级管理员（如果不存在）
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@techhub.com',
            real_name='系统管理员',
            department='技术部',
            position='技术总监',
            is_active=True
        )
        admin.set_password('admin123')
        admin_role = Role.query.filter_by(name='super_admin').first()
        if admin_role:
            admin.roles.append(admin_role)
        db.session.add(admin)
        users.append(admin)
    else:
        users.append(admin)
    
    # 创建测试账号（如果不存在）
    test_user = User.query.filter_by(username='test').first()
    if not test_user:
        test_user = User(
            username='test',
            email='test@techhub.com',
            real_name='测试用户',
            department='研发部',
            position='工程师',
            is_active=True
        )
        test_user.set_password('test123')
        member_role = Role.query.filter_by(name='member').first()
        if member_role:
            test_user.roles.append(member_role)
        db.session.add(test_user)
        users.append(test_user)
    else:
        users.append(test_user)
    
    # 获取已有用户数量
    existing_count = User.query.count()
    target_count = count + 2  # 加上 admin 和 test
    
    # 创建随机用户，直到达到目标数量
    i = 0
    while existing_count < target_count:
        username = fake.user_name() + str(i)
        # 避免重复
        if User.query.filter_by(username=username).first():
            i += 1
            continue
            
        user = User(
            username=username,
            email=fake.email(),
            real_name=fake.name(),
            phone=fake.phone_number(),
            department=fake.random_element(departments),
            position=fake.random_element(positions),
            is_active=True
        )
        user.set_password('password123')
        
        # 随机分配角色
        if existing_count < 5:
            role = Role.query.filter_by(name='department_manager').first()
        elif existing_count < 10:
            role = Role.query.filter_by(name='project_manager').first()
        else:
            role = Role.query.filter_by(name='member').first()
        
        if role:
            user.roles.append(role)
        
        db.session.add(user)
        users.append(user)
        existing_count += 1
        i += 1
    
    db.session.commit()
    print(f"✓ 创建了 {len(users)} 个用户")
    return users

def seed_projects(users, count=10):
    """创建测试项目"""
    colors = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#13c2c2']
    
    projects = []
    for i in range(count):
        creator = fake.random_element(users)
        
        start_date = fake.date_between(start_date='-3M', end_date='today')
        end_date = start_date + timedelta(days=fake.random_int(30, 180))
        
        project_name = fake.catch_phrase() + f'项目{i+1}'
        # 避免重复
        if Project.query.filter_by(name=project_name).first():
            continue
            
        project = Project(
            name=project_name,
            description=fake.text(max_nb_chars=200),
            color=fake.random_element(colors),
            start_date=start_date,
            end_date=end_date,
            creator_id=creator.id,
            status='active'
        )
        
        # 添加随机成员
        member_count = min(fake.random_int(2, 6), len(users))
        members = fake.random_sample(elements=users, length=member_count)
        for member in members:
            if member not in project.members:
                project.members.append(member)
        
        # 创建者自动成为成员
        if creator not in project.members:
            project.members.append(creator)
        
        db.session.add(project)
        projects.append(project)
    
    db.session.commit()
    print(f"✓ 创建了 {len(projects)} 个项目")
    return projects

def seed_tasks(users, projects, count_per_project=15):
    """创建测试任务"""
    tasks = []
    
    for project in projects:
        # 跳过没有成员的项目
        if not project.members:
            continue
        for i in range(count_per_project):
            creator = fake.random_element(project.members)
            assignee = fake.random_element(project.members)
            
            status = fake.random_element(list(TaskStatus))
            priority = fake.random_element(list(TaskPriority))
            
            # 根据状态设置完成时间
            completed_at = None
            if status == TaskStatus.DONE:
                completed_at = fake.date_time_between(start_date='-30d', end_date='now')
            
            # 设置截止日期
            due_date = fake.date_time_between(start_date='-7d', end_date='+30d')
            
            task = Task(
                title=fake.sentence(nb_words=6),
                description=fake.text(max_nb_chars=300),
                status=status,
                priority=priority,
                project_id=project.id,
                assignee_id=assignee.id,
                creator_id=creator.id,
                due_date=due_date,
                completed_at=completed_at,
                order=i
            )
            db.session.add(task)
            tasks.append(task)
    
    db.session.commit()
    print(f"✓ 创建了 {len(tasks)} 个任务")
    return tasks

def seed_comments(users, tasks, count_per_task=3):
    """创建测试评论"""
    comments = []
    
    for task in tasks:
        comment_count = fake.random_int(0, count_per_task)
        for _ in range(comment_count):
            author = fake.random_element(task.project.members)
            comment = Comment(
                content=fake.text(max_nb_chars=100),
                task_id=task.id,
                author_id=author.id
            )
            comments.append(comment)
    
    db.session.add_all(comments)
    db.session.commit()
    print(f"✓ 创建了 {len(comments)} 条评论")
    return comments

def seed_approvals(users, count=30):
    """创建测试审批"""
    approvals = []
    
    for i in range(count):
        applicant = fake.random_element(users)
        approval_type = fake.random_element(list(ApprovalType))
        status = fake.random_element(list(ApprovalStatus))
        
        processor = None
        processed_at = None
        process_comment = None
        
        if status != ApprovalStatus.PENDING:
            processor = fake.random_element(users)
            processed_at = fake.date_time_between(start_date='-30d', end_date='now')
            process_comment = fake.sentence()
        
        amount = None
        if approval_type in [ApprovalType.EXPENSE, ApprovalType.PURCHASE]:
            amount = fake.random_int(100, 10000)
        
        approval = Approval(
            title=fake.sentence(nb_words=4),
            approval_type=approval_type,
            status=status,
            is_urgent=fake.boolean(chance_of_getting_true=20),
            amount=amount,
            description=fake.text(max_nb_chars=200),
            applicant_id=applicant.id,
            processor_id=processor.id if processor else None,
            processed_at=processed_at,
            process_comment=process_comment
        )
        db.session.add(approval)
        approvals.append(approval)
    
    db.session.commit()
    print(f"✓ 创建了 {len(approvals)} 条审批")
    return approvals

def seed_activities(users, tasks, projects):
    """创建测试活动记录"""
    activities = []
    
    # 为每个任务创建活动记录
    for task in tasks:
        # 创建活动
        activity = Activity(
            activity_type=ActivityType.TASK_CREATED,
            title=f'创建了任务 "{task.title}"',
            user_id=task.creator_id,
            task_id=task.id,
            project_id=task.project_id
        )
        db.session.add(activity)
        activities.append(activity)
        
        # 如果任务已完成，添加完成活动
        if task.status == TaskStatus.DONE:
            activity = Activity(
                activity_type=ActivityType.TASK_COMPLETED,
                title=f'完成了任务 "{task.title}"',
                user_id=task.assignee_id or task.creator_id,
                task_id=task.id,
                project_id=task.project_id
            )
            db.session.add(activity)
            activities.append(activity)
    
    # 为每个项目创建活动
    for project in projects:
        activity = Activity(
            activity_type=ActivityType.PROJECT_CREATED,
            title=f'创建了新项目 "{project.name}"',
            user_id=project.creator_id,
            project_id=project.id
        )
        db.session.add(activity)
        activities.append(activity)
    
    db.session.commit()
    print(f"✓ 创建了 {len(activities)} 条活动记录")
    return activities

def seed_all():
    """填充所有测试数据"""
    print("=" * 50)
    print("开始填充测试数据...")
    print("=" * 50)
    
    try:
        seed_roles()
        users = seed_users(20)
        projects = seed_projects(users, 8)
        tasks = seed_tasks(users, projects, 12)
        comments = seed_comments(users, tasks, 3)
        approvals = seed_approvals(users, 30)
        activities = seed_activities(users, tasks, projects)
        
        print("=" * 50)
        print("✓ 测试数据填充完成！")
        print("=" * 50)
        print("\n测试账号：")
        print("  管理员: admin / admin123")
        print("  普通用户: test / test123")
        print("  其他用户: <任意用户名> / password123")
        
    except Exception as e:
        db.session.rollback()
        print(f"✗ 填充数据时出错: {e}")
        raise

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        seed_all()
