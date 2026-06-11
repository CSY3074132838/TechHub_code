"""
审批中心 API - 【审批流程引擎】支持8种审批流程
根据组织架构部门、角色标签正确分配审批人
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from decimal import Decimal
from app import db
from app.models import Approval, User, Activity, ApprovalNode, Role, LeaveBalance, UserIdentity, Department, Expense
from app.services import AuditService, PermissionService, NotificationService

def parse_approval_type(value):
    """规范化审批类型字符串"""
    valid = {'leave', 'expense', 'purchase', 'overtime', 'permission', 'contract', 'ticket', 'other'}
    return value if value in valid else 'other'

approvals_bp = Blueprint('approvals', __name__)

# ==================== 角色常量 ====================
MANAGER_ROLE_NAMES = {'super_admin', 'deputy_general_manager'}
TECH_DEPTS = {'技术部', '研发部', '测试部'}
OPS_DEPTS = {'运营部', '产品部', '设计部', '行政部', '人力部'}


# ================================================
# 【第三次迭代于然负责】(7) 根据组织架构标签查找审批人
# 审批流程根据部门类型、角色标签正确分配审批人
# 技术/研发/测试部门 → 项目经理/组长
# 运营/产品/设计/行政/人力 → 部门内组长或主管
# ================================================
# ==================== 【修复】根据组织架构标签查找审批人 ====================

def _get_applicant_primary_identity(applicant):
    """获取申请人的主身份（部门、职位信息）"""
    if applicant.identities:
        primary = applicant.identities.filter_by(is_primary=True).first()
        if primary:
            return primary
        # 没有主身份，返回第一个
        first = applicant.identities.first()
        if first:
            return first
    return None


def _get_applicant_department_name(applicant):
    """获取申请人所在部门名称"""
    identity = _get_applicant_primary_identity(applicant)
    if identity and identity.department:
        return identity.department.name
    return applicant.department or ''


def _get_applicant_department_id(applicant):
    """获取申请人所在部门ID"""
    identity = _get_applicant_primary_identity(applicant)
    if identity:
        return identity.department_id
    return applicant.department_id


def _find_users_by_role(role_name, department_id=None):
    """
    查找指定角色的用户
    如果指定了 department_id，优先在同部门中查找
    """
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        return []
    
    seen = set()
    unique_users = []
    
    # 如果指定了部门，优先在部门中查找（通过 identity_roles）
    if department_id:
        identities = UserIdentity.query.filter_by(department_id=department_id).all()
        for identity in identities:
            for r in identity.roles:
                if r.id == role.id and identity.user_id not in seen:
                    user = User.query.get(identity.user_id)
                    if user:
                        seen.add(user.id)
                        unique_users.append(user)
    
    # 通过 user_roles 表查找
    if role.users:
        for u in role.users:
            if u.id not in seen:
                # 如果指定了部门，检查用户是否属于该部门
                if department_id:
                    user_dept_ids = [i.department_id for i in u.identities.all()]
                    if department_id in user_dept_ids or u.department_id == department_id:
                        seen.add(u.id)
                        unique_users.append(u)
                else:
                    seen.add(u.id)
                    unique_users.append(u)
    
    # 通过 identity_roles 表全局查找（如果部门内没找到）
    if not unique_users and role.identities:
        for identity in role.identities:
            if identity.user_id and identity.user_id not in seen:
                # 如果指定了部门，检查身份是否属于该部门
                if department_id and identity.department_id != department_id:
                    continue
                user = User.query.get(identity.user_id)
                if user:
                    seen.add(user.id)
                    unique_users.append(user)
    
    return unique_users


def _find_managers():
    """查找系统中的总经理/副总经理用户"""
    managers = []
    for role_name in MANAGER_ROLE_NAMES:
        managers.extend(_find_users_by_role(role_name))
    seen = set()
    unique_managers = []
    for m in managers:
        if m.id not in seen:
            seen.add(m.id)
            unique_managers.append(m)
    # 按角色等级排序：总经理(super_admin, level=1)在前，副总经理(level=2)在后
    unique_managers.sort(key=lambda u: min(r.level for r in u.roles) if u.roles else 99)
    return unique_managers


def _find_dept_manager(applicant):
    """
    查找申请人的部门负责人
    搜索优先级：
    1. 同部门中拥有 department_manager 角色的用户
    2. 同部门中拥有 tech_director/operations_director 等总监角色的用户
    3. 同部门中拥有 super_admin/deputy_general_manager 角色的用户
    4. 部门的 manager_id 字段指定的用户
    """
    dept_id = _get_applicant_department_id(applicant)
    if not dept_id:
        # 尝试从 department 字符串查找
        if applicant.department:
            dept = Department.query.filter_by(name=applicant.department).first()
            if dept:
                dept_id = dept.id
    
    if not dept_id:
        return None
    
    # 1. 查找 department_manager
    users = _find_users_by_role('department_manager', dept_id)
    if users:
        return users[0]
    
    # 2. 查找总监角色（根据部门类型）
    dept_name = _get_applicant_department_name(applicant)
    is_tech = any(d in dept_name for d in TECH_DEPTS)
    director_role = 'tech_director' if is_tech else 'operations_director'
    users = _find_users_by_role(director_role, dept_id)
    if users:
        return users[0]
    
    # 3. 查找 super_admin / deputy_general_manager
    for role_name in ('super_admin', 'deputy_general_manager'):
        users = _find_users_by_role(role_name, dept_id)
        if users:
            return users[0]
    
    # 4. 查找部门表中的 manager_id
    dept = Department.query.get(dept_id)
    if dept and dept.manager_id:
        manager = User.query.get(dept.manager_id)
        if manager:
            return manager
    
    return None


def _find_direct_manager(applicant):
    """
    查找申请人的直属上级
    根据部门类型区分查找角色标签：
    - 技术/研发/测试部门 → 优先找 project_manager，其次 team_leader
    - 运营/产品/设计/行政/人力 → 优先找 team_leader，其次 department_manager
    回退：找部门负责人
    """
    dept_id = _get_applicant_department_id(applicant)
    dept_name = _get_applicant_department_name(applicant)
    is_tech = any(d in dept_name for d in TECH_DEPTS)
    
    # 优先在同部门中查找
    if dept_id:
        if is_tech:
            # 技术部门：项目经理 → 项目组长
            for role_name in ('project_manager', 'team_leader'):
                users = _find_users_by_role(role_name, dept_id)
                if users:
                    # 排除申请人自己
                    for u in users:
                        if u.id != applicant.id:
                            return u
        else:
            # 运营等部门：项目组长 → 部门负责人
            for role_name in ('team_leader', 'department_manager'):
                users = _find_users_by_role(role_name, dept_id)
                if users:
                    for u in users:
                        if u.id != applicant.id:
                            return u
    
    # 如果 applicant.manager_id 存在，直接使用
    if applicant.manager_id:
        manager = User.query.get(applicant.manager_id)
        if manager and manager.id != applicant.id:
            return manager
    
    # 回退：找部门负责人
    return _find_dept_manager(applicant)


def _find_finance_director():
    """查找财务总监"""
    users = _find_users_by_role('finance_director')
    if users:
        return users[0]
    # 回退：找具有 all 权限的用户
    all_users = User.query.all()
    for u in all_users:
        if u.has_permission('all'):
            return u
    return None


def _find_hr_staff():
    """查找人力部人员"""
    # 1. 通过 identities 的 department 名称查找
    hr_depts = Department.query.filter(Department.name.ilike('%人力%')).all()
    hr_dept_ids = [d.id for d in hr_depts]
    if hr_dept_ids:
        identities = UserIdentity.query.filter(UserIdentity.department_id.in_(hr_dept_ids)).all()
        if identities:
            user = User.query.get(identities[0].user_id)
            if user:
                return user
    
    # 2. 通过 role 查找
    users = _find_users_by_role('hr')
    if users:
        return users[0]
    return None


def _find_legal_staff():
    """查找法务人员"""
    users = _find_users_by_role('legal')
    if users:
        return users[0]
    return None


def _find_security_officer():
    """查找安全员"""
    users = _find_users_by_role('security_officer')
    if users:
        return users[0]
    managers = _find_managers()
    if managers:
        return managers[0]
    return None


def _find_ops_director():
    """查找运营总监"""
    users = _find_users_by_role('ops_director')
    if users:
        return users[0]
    managers = _find_managers()
    if managers:
        return managers[0]
    return None


def _find_tech_director():
    """查找技术总监"""
    users = _find_users_by_role('tech_director')
    if users:
        return users[0]
    managers = _find_managers()
    if managers:
        return managers[0]
    return None


def _find_general_manager():
    """查找总经理（super_admin）"""
    users = _find_users_by_role('super_admin')
    if users:
        return users[0]
    managers = _find_managers()
    if managers:
        return managers[0]
    return None


def _create_node(approval, name, order, handler=None, node_type='serial', condition_expr=None, parallel_handlers=None, is_auto=False, required_pass_count=1):
    """创建审批节点的辅助函数"""
    node = ApprovalNode(
        approval_id=approval.id,
        node_name=name,
        handler_id=handler.id if handler else None,
        status='pending',
        order=order,
        node_type=node_type,
        condition_expr=condition_expr,
        parallel_handlers=parallel_handlers or [],
        is_auto=is_auto,
        required_pass_count=required_pass_count
    )
    db.session.add(node)
    return node


def _check_condition(approval, expr):
    """检查条件表达式是否满足"""
    if not expr:
        return True
    try:
        ctx = {
            'amount': float(approval.amount) if approval.amount else 0,
            'is_urgent': approval.is_urgent,
            'leave_days': approval.leave_days or 0,
            'overtime_days': approval.overtime_days or 0,
            'is_over_budget': approval.is_over_budget,
            'is_standard_template': approval.is_standard_template,
            'need_compensation': approval.need_compensation,
        }
        return eval(expr, {"__builtins__": {}}, ctx)
    except Exception:
        return True


# ================================================
# 【第三次迭代于然负责】(7)(8) 审批流程定义与展示
# (7) 审批流程根据组织架构部门、角色标签分配审批人
# (8) 审批流程展示页面，总经理可修改流程配置
# ================================================
# ==================== 【新增】审批流程定义 ====================

WORKFLOW_DEFINITIONS = {
    'purchase': {
        'name': '采购申请流程',
        'description': '根据部门类型和金额大小进行分级审批',
        'nodes': [
            {'name': '直属上级审批', 'role': '根据部门类型：技术/研发/测试→项目经理/组长；其他→部门内组长或主管', 'type': 'serial'},
            {'name': '金额审核', 'condition': '金额<¥500自动通过', 'type': 'condition'},
            {'name': '部门负责人审批', 'role': '技术总监/运营总监等', 'type': 'serial'},
            {'name': '金额/紧急审核', 'condition': '金额≥¥2000或紧急→副总经理审批', 'type': 'condition'},
            {'name': '副总经理审批', 'role': '副总经理', 'type': 'serial'},
            {'name': '财务总监审批', 'role': '财务总监', 'type': 'serial'},
            {'name': '金额审核', 'condition': '金额≥¥5000→总经理审批', 'type': 'condition'},
            {'name': '总经理审批', 'role': '总经理', 'type': 'serial'},
            {'name': '归档完成', 'type': 'auto'}
        ]
    },
    'expense': {
        'name': '报销申请流程',
        'description': '直属上级→部门负责人→按金额分级→预算审核',
        'nodes': [
            {'name': '直属上级审批', 'role': '直属上级', 'type': 'serial'},
            {'name': '部门负责人审批', 'role': '部门负责人', 'type': 'serial'},
            {'name': '金额审核', 'condition': '金额≥¥1000→副总经理审批', 'type': 'condition'},
            {'name': '副总经理审批', 'role': '副总经理', 'type': 'serial'},
            {'name': '财务总监审批', 'role': '财务总监', 'type': 'serial'},
            {'name': '预算审核', 'condition': '超出预算→返回修改/拒绝', 'type': 'condition'},
            {'name': '财务打款', 'role': '财务总监', 'type': 'auto'}
        ]
    },
    'overtime': {
        'name': '加班申请流程',
        'description': '根据连续加班天数和是否调休进行审批',
        'nodes': [
            {'name': '直属上级审批', 'role': '直属上级', 'type': 'serial'},
            {'name': '连续加班审核', 'condition': '连续加班≥3天→部门负责人+人力部会签', 'type': 'condition'},
            {'name': '部门负责人审批/会签', 'role': '部门负责人/人力部', 'type': 'parallel'},
            {'name': '调休审核', 'condition': '调休→人力部备案', 'type': 'condition'},
            {'name': '人力部备案', 'role': '人力部', 'type': 'serial'},
            {'name': '结束', 'type': 'auto'}
        ]
    },
    'leave': {
        'name': '请假申请流程',
        'description': '根据请假类型和天数进行分级审批',
        'nodes': [
            {'name': '请假类型审核', 'condition': '年假/病假→直属上级；事假/其他→直属上级+部门负责人会签', 'type': 'condition'},
            {'name': '直属上级审批/会签', 'role': '直属上级/部门负责人', 'type': 'serial/parallel'},
            {'name': '请假天数审核', 'condition': '连续天数≥3天→副总经理审批', 'type': 'condition'},
            {'name': '副总经理审批', 'role': '副总经理', 'type': 'serial'},
            {'name': '人力部备案', 'role': '人力部', 'type': 'serial'},
            {'name': '调休抵扣审核', 'condition': '需要调休抵扣→人力部调整考勤', 'type': 'condition'},
            {'name': '人力部调整考勤', 'role': '人力部', 'type': 'serial'},
            {'name': '结束', 'type': 'auto'}
        ]
    },
    'permission': {
        'name': '权限申请流程',
        'description': '技术/研发/数据类权限申请，按权限类型和敏感度审批',
        'nodes': [
            {'name': '权限类型审核', 'condition': '普通只读→直属上级；读写/部署/敏感数据→直属上级+技术总监会签', 'type': 'condition'},
            {'name': '直属上级审批/会签', 'role': '直属上级/技术总监', 'type': 'serial/parallel'},
            {'name': '跨部门审核', 'condition': '跨部门→副总经理审批', 'type': 'condition'},
            {'name': '副总经理审批', 'role': '副总经理', 'type': 'serial'},
            {'name': '敏感权限审核', 'condition': '敏感权限→安全员/副总二次确认', 'type': 'condition'},
            {'name': '安全员/副总二次确认', 'role': '安全员/副总经理', 'type': 'serial'},
            {'name': '系统自动开通', 'type': 'auto'}
        ]
    },
    'contract': {
        'name': '合同管理审批流程',
        'description': '按合同金额和模板类型进行审批',
        'nodes': [
            {'name': '直属上级审批', 'role': '直属上级', 'type': 'serial'},
            {'name': '部门负责人审批', 'role': '部门负责人', 'type': 'serial'},
            {'name': '合同金额审核', 'condition': '金额≥¥5000→副总经理+法务会签', 'type': 'condition'},
            {'name': '副总经理+法务会签/财务总监审批', 'role': '副总经理/法务/财务总监', 'type': 'parallel/serial'},
            {'name': '模板审核', 'condition': '非标准模板→法务审核', 'type': 'condition'},
            {'name': '法务审核', 'role': '法务', 'type': 'serial'},
            {'name': '归档完成', 'type': 'auto'}
        ]
    },
    'ticket': {
        'name': '客户工单审批流程',
        'description': '运营/客服类工单，按级别和赔偿需求审批',
        'nodes': [
            {'name': '工单级别审核', 'condition': '普通→运营总监；重要→运营总监+部门负责人会签；重大客诉→运营总监+副总经理会签', 'type': 'condition'},
            {'name': '运营总监审批/会签', 'role': '运营总监/部门负责人/副总经理', 'type': 'parallel'},
            {'name': '安排处理人', 'role': '运营总监', 'type': 'serial'},
            {'name': '赔偿审核', 'condition': '需要赔偿→财务总监审批', 'type': 'condition'},
            {'name': '财务总监审批', 'role': '财务总监', 'type': 'serial'},
            {'name': '关闭工单', 'type': 'auto'}
        ]
    },
    'other': {
        'name': '紧急申请（通用）流程',
        'description': '紧急申请限时审批，超时自动升级',
        'nodes': [
            {'name': '直属上级审批', 'role': '直属上级（限时15分钟）', 'type': 'serial'},
            {'name': '超时升级审核', 'condition': '超时未批→自动升级到部门负责人', 'type': 'condition'},
            {'name': '部门负责人审批', 'role': '部门负责人', 'type': 'serial'},
            {'name': '二次超时升级审核', 'condition': '部门负责人超时→自动升级到副总经理', 'type': 'condition'},
            {'name': '副总经理审批/执行紧急操作', 'role': '副总经理', 'type': 'serial'}
        ]
    }
}


# ==================== 审批链创建引擎 ====================

def create_approval_chain(approval, approval_type, applicant, data=None):
    """【审批流程引擎】根据审批类型创建审批链"""
    data = data or {}
    nodes = []
    order = 1

    if approval_type == 'purchase':
        nodes, order = _create_purchase_chain(approval, applicant, data, order)
    elif approval_type == 'expense':
        nodes, order = _create_expense_chain(approval, applicant, data, order)
    elif approval_type == 'overtime':
        nodes, order = _create_overtime_chain(approval, applicant, data, order)
    elif approval_type == 'leave':
        nodes, order = _create_leave_chain(approval, applicant, data, order)
    elif approval_type == 'permission':
        nodes, order = _create_permission_chain(approval, applicant, data, order)
    elif approval_type == 'contract':
        nodes, order = _create_contract_chain(approval, applicant, data, order)
    elif approval_type == 'ticket':
        nodes, order = _create_ticket_chain(approval, applicant, data, order)
    else:
        nodes, order = _create_urgent_chain(approval, applicant, data, order)

    db.session.flush()
    if nodes:
        approval.current_node_id = nodes[0].id
    db.session.commit()
    return nodes


def _create_purchase_chain(approval, applicant, data, order):
    """
    采购申请流程
    A[发起采购申请] --> B{部门类型?}
    B -->|技术/研发/测试| C[直属上级审批 - 项目经理/组长]
    B -->|运营/产品/设计/行政/人力| D[直属上级审批 - 部门内组长或主管]
    C --> E{金额<500?}
    D --> E
    E -->|是| F[自动通过 - 结束]
    E -->|否| G[部门负责人审批 - 技术总监/运营总监等]
    G --> H{金额≥2000 或 紧急?}
    H -->|是| I[副总经理审批]
    H -->|否| J[财务总监审批]
    I --> J
    J --> K{金额≥5000?}
    K -->|是| L[总经理审批]
    K -->|否| M[结束]
    """
    nodes = []
    dept_name = _get_applicant_department_name(applicant)
    is_tech = any(d in dept_name for d in TECH_DEPTS)
    dept_id = _get_applicant_department_id(applicant)

    # 节点1: 直属上级审批（根据部门类型匹配不同角色标签）
    manager = _find_direct_manager(applicant)
    if is_tech:
        node1_name = '直属上级审批（项目经理/组长）'
    else:
        node1_name = '直属上级审批（部门内组长或主管）'
    n1 = _create_node(approval, node1_name, order, manager)
    nodes.append(n1)
    order += 1

    # 条件: amount < 500 → 自动通过
    n_auto = _create_node(approval, '金额审核（<¥500自动通过）', order, None, 'condition', 'amount<500', is_auto=True)
    nodes.append(n_auto)
    order += 1

    # 节点2: 部门负责人审批
    dept_mgr = _find_dept_manager(applicant)
    n2 = _create_node(approval, '部门负责人审批', order, dept_mgr)
    nodes.append(n2)
    order += 1

    # 条件: amount >= 2000 或 紧急 → 副总经理审批
    n_cond = _create_node(approval, '金额/紧急审核（≥¥2000或紧急）', order, None, 'condition', 'amount>=2000 or is_urgent')
    nodes.append(n_cond)
    order += 1

    # 节点3: 副总经理审批
    managers = _find_managers()
    if managers:
        n3 = _create_node(approval, '副总经理审批', order, managers[0])
        nodes.append(n3)
        order += 1

    # 节点4: 财务总监审批
    finance = _find_finance_director()
    n4 = _create_node(approval, '财务总监审批', order, finance)
    nodes.append(n4)
    order += 1

    # 条件: amount >= 5000 → 总经理审批
    n_cond2 = _create_node(approval, '金额审核（≥¥5000）', order, None, 'condition', 'amount>=5000')
    nodes.append(n_cond2)
    order += 1

    # 节点5: 总经理审批
    gm = _find_general_manager()
    if gm:
        n5 = _create_node(approval, '总经理审批', order, gm)
        nodes.append(n5)
        order += 1

    # 节点6: 归档完成
    n6 = _create_node(approval, '归档完成', order, None, 'auto', is_auto=True)
    nodes.append(n6)
    return nodes, order + 1


def _create_expense_chain(approval, applicant, data, order):
    """
    报销申请流程
    A[发起报销] --> B[直属上级审批]
    B --> C[部门负责人审批]
    C --> D{金额≥1000?}
    D -->|否| E[财务总监审批]
    D -->|是| F[副总经理审批]
    F --> G[财务总监审批]
    E --> H{是否超出预算?}
    G --> H
    H -->|是| I[返回修改或拒绝]
    H -->|否| J[财务打款 - 结束]
    """
    nodes = []

    # 节点1: 直属上级审批
    manager = _find_direct_manager(applicant)
    n1 = _create_node(approval, '直属上级审批', order, manager)
    nodes.append(n1)
    order += 1

    # 节点2: 部门负责人审批
    dept_mgr = _find_dept_manager(applicant)
    n2 = _create_node(approval, '部门负责人审批', order, dept_mgr)
    nodes.append(n2)
    order += 1

    # 条件: amount >= 1000 → 副总经理审批
    n_cond = _create_node(approval, '金额审核（≥¥1000）', order, None, 'condition', 'amount>=1000')
    nodes.append(n_cond)
    order += 1

    # 节点3: 副总经理审批
    managers = _find_managers()
    if managers:
        n3 = _create_node(approval, '副总经理审批', order, managers[0])
        nodes.append(n3)
        order += 1

    # 节点4: 财务总监审批
    finance = _find_finance_director()
    n4 = _create_node(approval, '财务总监审批', order, finance)
    nodes.append(n4)
    order += 1

    # 条件: 超出预算 → 返回修改/拒绝
    n_cond2 = _create_node(approval, '预算审核', order, None, 'condition', 'is_over_budget')
    nodes.append(n_cond2)
    order += 1

    # 节点5: 财务打款（结束）
    n5 = _create_node(approval, '财务打款', order, finance, 'auto', is_auto=True)
    nodes.append(n5)
    return nodes, order + 1


def _create_overtime_chain(approval, applicant, data, order):
    """
    加班申请流程
    A[发起加班申请] --> B[直属上级审批]
    B --> C{连续加班≥3天?}
    C -->|否| D[部门负责人审批]
    C -->|是| E[部门负责人 + 人力部会签]
    D --> F{是否调休?}
    E --> F
    F -->|是| G[人力部备案]
    F -->|否| H[结束]
    G --> H
    """
    nodes = []

    # 节点1: 直属上级审批
    manager = _find_direct_manager(applicant)
    n1 = _create_node(approval, '直属上级审批', order, manager)
    nodes.append(n1)
    order += 1

    # 条件: 连续加班≥3天 → 部门负责人+人力部会签
    n_cond = _create_node(approval, '连续加班天数审核（≥3天）', order, None, 'condition', 'overtime_days>=3')
    nodes.append(n_cond)
    order += 1

    # 节点2: 部门负责人审批 / 会签
    dept_mgr = _find_dept_manager(applicant)
    hr = _find_hr_staff()
    if dept_mgr and hr:
        n2 = _create_node(approval, '部门负责人+人力部会签', order, dept_mgr, 'parallel',
                          parallel_handlers=[{'user_id': dept_mgr.id, 'status': 'pending'},
                                             {'user_id': hr.id, 'status': 'pending'}],
                          required_pass_count=2)
    elif dept_mgr:
        n2 = _create_node(approval, '部门负责人审批', order, dept_mgr)
    else:
        n2 = _create_node(approval, '部门负责人审批', order, None)
    nodes.append(n2)
    order += 1

    # 条件: 是否调休 → 人力部备案
    n_cond2 = _create_node(approval, '调休审核', order, None, 'condition', 'sub_type=="compensatory"')
    nodes.append(n_cond2)
    order += 1

    # 节点3: 人力部备案
    if hr:
        n3 = _create_node(approval, '人力部备案', order, hr)
        nodes.append(n3)
        order += 1

    # 节点4: 结束
    n4 = _create_node(approval, '结束', order, None, 'auto', is_auto=True)
    nodes.append(n4)
    return nodes, order + 1


def _create_leave_chain(approval, applicant, data, order):
    """
    请假申请流程
    A[发起请假] --> B{请假类型?}
    B -->|年假/病假| C[直属上级审批]
    B -->|事假/其他| D[直属上级 + 部门负责人会签]
    C --> E{连续天数≥3天?}
    D --> E
    E -->|是| F[副总经理审批]
    E -->|否| G[人力部备案]
    F --> G
    G --> H{是否需要调休抵扣?}
    H -->|是| I[人力部调整考勤]
    H -->|否| J[结束]
    """
    nodes = []
    leave_type = approval.sub_type or data.get('sub_type', '')

    # 条件: 年假/病假 → 直属上级审批；事假/其他 → 直属上级+部门负责人会签
    is_simple = leave_type in ('annual', 'sick')

    # 节点1: 直属上级审批 / 会签
    manager = _find_direct_manager(applicant)
    dept_mgr = _find_dept_manager(applicant)
    if not is_simple and manager and dept_mgr:
        n1 = _create_node(approval, '直属上级+部门负责人会签', order, manager, 'parallel',
                          parallel_handlers=[{'user_id': manager.id, 'status': 'pending'},
                                             {'user_id': dept_mgr.id, 'status': 'pending'}],
                          required_pass_count=2)
    else:
        n1 = _create_node(approval, '直属上级审批', order, manager)
    nodes.append(n1)
    order += 1

    # 条件: 连续天数≥3天 → 副总经理审批
    n_cond = _create_node(approval, '请假天数审核（≥3天）', order, None, 'condition', 'leave_days>=3')
    nodes.append(n_cond)
    order += 1

    # 节点2: 副总经理审批
    managers = _find_managers()
    if managers:
        n2 = _create_node(approval, '副总经理审批', order, managers[0])
        nodes.append(n2)
        order += 1

    # 节点3: 人力部备案
    hr = _find_hr_staff()
    if hr:
        n3 = _create_node(approval, '人力部备案', order, hr)
        nodes.append(n3)
        order += 1

    # 条件: 需要调休抵扣 → 人力部调整考勤（年假需要调休抵扣）
    n_cond2 = _create_node(approval, '调休抵扣审核', order, None, 'condition', 'sub_type=="annual"')
    nodes.append(n_cond2)
    order += 1

    # 节点4: 人力部调整考勤
    if hr:
        n4 = _create_node(approval, '人力部调整考勤', order, hr)
        nodes.append(n4)
        order += 1

    # 节点5: 结束
    n5 = _create_node(approval, '结束', order, None, 'auto', is_auto=True)
    nodes.append(n5)
    return nodes, order + 1


def _create_permission_chain(approval, applicant, data, order):
    """
    权限申请流程（技术/研发/数据类）
    A[发起权限申请] --> B{权限类型?}
    B -->|普通只读| C[直属上级审批]
    B -->|读写/部署/敏感数据| D[直属上级 + 技术总监会签]
    C --> E{是否跨部门?}
    D --> E
    E -->|是| F[副总经理审批]
    E -->|否| G{是否为敏感权限?}
    F --> G
    G -->|是| H[安全员/副总二次确认]
    G -->|否| I[系统自动开通]
    H --> I
    """
    nodes = []
    perm_type = approval.sub_type or data.get('sub_type', '')
    is_simple = perm_type == 'read_only'

    # 节点1: 直属上级审批 / 会签
    manager = _find_direct_manager(applicant)
    tech_director = _find_tech_director()
    if not is_simple and manager and tech_director:
        n1 = _create_node(approval, '直属上级+技术总监会签', order, manager, 'parallel',
                          parallel_handlers=[{'user_id': manager.id, 'status': 'pending'},
                                             {'user_id': tech_director.id, 'status': 'pending'}],
                          required_pass_count=2)
    else:
        n1 = _create_node(approval, '直属上级审批', order, manager)
    nodes.append(n1)
    order += 1

    # 条件: 跨部门 → 副总经理审批
    n_cond = _create_node(approval, '跨部门审核', order, None, 'condition', 'data.get("cross_dept", False)')
    nodes.append(n_cond)
    order += 1

    # 节点2: 副总经理审批
    managers = _find_managers()
    if managers:
        n2 = _create_node(approval, '副总经理审批', order, managers[0])
        nodes.append(n2)
        order += 1

    # 条件: 敏感权限 → 安全员/副总二次确认
    n_cond2 = _create_node(approval, '敏感权限审核', order, None, 'condition', 'sub_type=="sensitive"')
    nodes.append(n_cond2)
    order += 1

    # 节点3: 安全员/副总二次确认
    security = _find_security_officer()
    if security:
        n3 = _create_node(approval, '安全员/副总二次确认', order, security)
        nodes.append(n3)
        order += 1

    # 节点4: 系统自动开通
    n4 = _create_node(approval, '系统自动开通', order, None, 'auto', is_auto=True)
    nodes.append(n4)
    return nodes, order + 1


def _create_contract_chain(approval, applicant, data, order):
    """
    合同管理审批流程
    A[发起合同审批] --> B[直属上级审批]
    B --> C[部门负责人审批]
    C --> D{合同金额≥5000?}
    D -->|否| E[财务总监审批]
    D -->|是| F[副总经理 + 法务会签]
    E --> G{是否标准模板?}
    F --> G
    G -->|否| H[法务审核]
    G -->|是| I[归档结束]
    H --> I
    """
    nodes = []

    # 节点1: 直属上级审批
    manager = _find_direct_manager(applicant)
    n1 = _create_node(approval, '直属上级审批', order, manager)
    nodes.append(n1)
    order += 1

    # 节点2: 部门负责人审批
    dept_mgr = _find_dept_manager(applicant)
    n2 = _create_node(approval, '部门负责人审批', order, dept_mgr)
    nodes.append(n2)
    order += 1

    # 条件: amount >= 5000 → 副总经理+法务会签
    n_cond = _create_node(approval, '合同金额审核（≥¥5000）', order, None, 'condition', 'amount>=5000')
    nodes.append(n_cond)
    order += 1

    # 节点3: 副总经理+法务会签 / 财务总监审批
    managers = _find_managers()
    legal = _find_legal_staff()
    finance = _find_finance_director()
    if managers and legal:
        n3 = _create_node(approval, '副总经理+法务会签', order, managers[0], 'parallel',
                          parallel_handlers=[{'user_id': managers[0].id, 'status': 'pending'},
                                             {'user_id': legal.id, 'status': 'pending'}],
                          required_pass_count=2)
    elif finance:
        n3 = _create_node(approval, '财务总监审批', order, finance)
    else:
        n3 = _create_node(approval, '高管审批', order, managers[0] if managers else None)
    nodes.append(n3)
    order += 1

    # 条件: 非标准模板 → 法务审核
    n_cond2 = _create_node(approval, '模板审核（非标准模板）', order, None, 'condition', 'not is_standard_template')
    nodes.append(n_cond2)
    order += 1

    # 节点4: 法务审核
    if legal:
        n4 = _create_node(approval, '法务审核', order, legal)
        nodes.append(n4)
        order += 1

    # 节点5: 归档完成
    n5 = _create_node(approval, '归档完成', order, None, 'auto', is_auto=True)
    nodes.append(n5)
    return nodes, order + 1


def _create_ticket_chain(approval, applicant, data, order):
    """
    客户工单审批流程（运营/客服）
    A[发起客户工单] --> B{工单级别?}
    B -->|普通| C[运营总监审批]
    B -->|重要| D[运营总监 + 部门负责人会签]
    B -->|重大客诉| E[运营总监 + 副总经理会签]
    C --> F[安排处理人]
    D --> F
    E --> F
    F --> G{是否需要赔偿?}
    G -->|是| H[财务总监审批]
    G -->|否| I[关闭工单]
    H --> I
    """
    nodes = []
    level = approval.ticket_level or data.get('ticket_level', 'normal')

    # 节点1: 运营总监审批 / 会签
    ops = _find_ops_director()
    dept_mgr = _find_dept_manager(applicant)
    managers = _find_managers()

    if level == 'critical' and ops and managers:
        n1 = _create_node(approval, '运营总监+副总经理会签', order, ops, 'parallel',
                          parallel_handlers=[{'user_id': ops.id, 'status': 'pending'},
                                             {'user_id': managers[0].id, 'status': 'pending'}],
                          required_pass_count=2)
    elif level == 'important' and ops and dept_mgr:
        n1 = _create_node(approval, '运营总监+部门负责人会签', order, ops, 'parallel',
                          parallel_handlers=[{'user_id': ops.id, 'status': 'pending'},
                                             {'user_id': dept_mgr.id, 'status': 'pending'}],
                          required_pass_count=2)
    else:
        n1 = _create_node(approval, '运营总监审批', order, ops)
    nodes.append(n1)
    order += 1

    # 节点2: 安排处理人
    n2 = _create_node(approval, '安排处理人', order, ops)
    nodes.append(n2)
    order += 1

    # 条件: 需要赔偿 → 财务总监审批
    n_cond = _create_node(approval, '赔偿审核', order, None, 'condition', 'need_compensation')
    nodes.append(n_cond)
    order += 1

    # 节点3: 财务总监审批
    finance = _find_finance_director()
    if finance:
        n3 = _create_node(approval, '财务总监审批', order, finance)
        nodes.append(n3)
        order += 1

    # 节点4: 关闭工单
    n4 = _create_node(approval, '关闭工单', order, ops, 'auto', is_auto=True)
    nodes.append(n4)
    return nodes, order + 1


def _create_urgent_chain(approval, applicant, data, order):
    """
    紧急申请（通用）流程
    A[发起紧急申请] --> B[直属上级审批（限时15分钟）]
    B --> C{超时未批?}
    C -->|是| D[自动升级到部门负责人]
    C -->|否| E[部门负责人审批]
    D --> E
    E --> F{部门负责人超时?}
    F -->|是| G[自动升级到副总经理]
    F -->|否| H[执行紧急操作（事后补流程）]
    G --> H
    """
    nodes = []

    # 节点1: 直属上级审批（限时15分钟）
    manager = _find_direct_manager(applicant)
    n1 = _create_node(approval, '直属上级审批（限时15分钟）', order, manager)
    nodes.append(n1)
    order += 1

    # 条件: 超时未批 → 自动升级到部门负责人
    n_cond = _create_node(approval, '超时升级审核', order, None, 'condition', 'is_urgent')
    nodes.append(n_cond)
    order += 1

    # 节点2: 部门负责人审批
    dept_mgr = _find_dept_manager(applicant)
    n2 = _create_node(approval, '部门负责人审批', order, dept_mgr)
    nodes.append(n2)
    order += 1

    # 条件: 部门负责人超时 → 自动升级到副总经理
    n_cond2 = _create_node(approval, '二次超时升级审核', order, None, 'condition', 'is_urgent')
    nodes.append(n_cond2)
    order += 1

    # 节点3: 副总经理审批 / 执行紧急操作
    managers = _find_managers()
    if managers:
        n3 = _create_node(approval, '副总经理审批/执行紧急操作', order, managers[0])
        nodes.append(n3)
        order += 1

    return nodes, order + 1


# ==================== 审批处理引擎 ====================

def _advance_to_next_node(approval):
    """推进到下一个有效的审批节点"""
    nodes = ApprovalNode.query.filter_by(approval_id=approval.id) \
        .order_by(ApprovalNode.order).all()

    current_idx = -1
    for i, node in enumerate(nodes):
        if node.id == approval.current_node_id:
            current_idx = i
            break

    # 从当前节点之后开始查找下一个有效节点
    for i in range(current_idx + 1, len(nodes)):
        node = nodes[i]

        # 检查条件
        if node.node_type == 'condition' or node.condition_expr:
            if not _check_condition(approval, node.condition_expr):
                node.status = 'skipped'
                db.session.commit()
                continue

        # 自动节点直接完成
        if node.is_auto or node.node_type == 'auto':
            node.status = 'completed'
            node.handled_at = datetime.now()
            db.session.commit()
            continue

        # 找到下一个有效节点
        approval.current_node_id = node.id
        db.session.commit()

        # 通知下一节点处理人
        NotificationService.notify_approval_next_node(approval, node)
        return True

    # 没有更多节点，审批完成
    approval.current_node_id = None
    approval.status = 'approved'
    db.session.commit()
    return False


# ==================== API 路由 ====================

@approvals_bp.route('/', methods=['GET'])
@jwt_required()
def get_approvals():
    """获取审批列表"""
    current_user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')
    approval_type = request.args.get('type')
    is_urgent = request.args.get('is_urgent', type=bool)
    scope = request.args.get('scope', 'all')

    query = Approval.query

    if scope == 'my':
        query = query.filter_by(applicant_id=current_user_id)
    elif scope == 'pending_me':
        # 查找当前用户需要处理的审批（当前节点的处理人）
        can_process = PermissionService.check_permission(current_user_id, 'approval_process') or \
                      PermissionService.check_permission(current_user_id, 'all')
        if can_process:
            query = query.filter_by(status='pending')
        else:
            # 查找当前节点指定了当前用户的审批
            pending_approvals = Approval.query.filter_by(status='pending').all()
            ids = []
            for a in pending_approvals:
                if a.current_node_id:
                    node = ApprovalNode.query.get(a.current_node_id)
                    if node and node.handler_id == current_user_id:
                        ids.append(a.id)
                    # 会签节点
                    if node and node.parallel_handlers:
                        for ph in node.parallel_handlers:
                            if ph.get('user_id') == current_user_id and ph.get('status') == 'pending':
                                ids.append(a.id)
                                break
            if ids:
                query = Approval.query.filter(Approval.id.in_(ids))
            else:
                query = query.filter_by(id=-1)
    else:
        if not PermissionService.check_permission(current_user_id, 'all'):
            scope_level = PermissionService.get_user_data_scope(current_user_id)
            if scope_level.value == 'dept':
                user = User.query.get(current_user_id)
                dept_members = User.query.filter_by(department=user.department).all()
                member_ids = [m.id for m in dept_members]
                query = query.filter(
                    (Approval.applicant_id.in_(member_ids)) |
                    (Approval.processor_id.in_(member_ids))
                )
            else:
                query = query.filter(
                    (Approval.applicant_id == current_user_id) |
                    (Approval.processor_id == current_user_id)
                )

    if status:
        query = query.filter(Approval.status == status)
    if approval_type:
        query = query.filter(Approval.approval_type == approval_type)
    if is_urgent is not None:
        query = query.filter_by(is_urgent=is_urgent)

    query = query.order_by(Approval.is_urgent.desc(), Approval.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    approvals = pagination.items

    return jsonify({
        'approvals': [approval.to_dict(include_chain=True) for approval in approvals],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    }), 200


@approvals_bp.route('/', methods=['POST'])
@jwt_required()
def create_approval():
    """发起审批"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data or not data.get('title') or not data.get('approval_type'):
        return jsonify({'message': '请提供审批标题和类型', 'error': 'missing_fields'}), 400

    approval_type = parse_approval_type(data['approval_type'])

    approval = Approval(
        title=data['title'],
        approval_type=approval_type,
        description=data.get('description', ''),
        amount=data.get('amount'),
        is_urgent=data.get('is_urgent', False),
        applicant_id=current_user_id,
        attachments=data.get('attachments', []),
        sub_type=data.get('sub_type'),
        leave_days=data.get('leave_days'),
        overtime_days=data.get('overtime_days'),
        ticket_level=data.get('ticket_level'),
        is_over_budget=data.get('is_over_budget', False),
        is_standard_template=data.get('is_standard_template', True),
        need_compensation=data.get('need_compensation', False)
    )

    db.session.add(approval)
    db.session.commit()

    applicant = User.query.get(current_user_id)
    create_approval_chain(approval, approval_type, applicant, data)

    activity = Activity(
        activity_type='approval_submitted',
        title=f'提交了审批 "{approval.title}"',
        user_id=current_user_id
    )
    db.session.add(activity)
    db.session.commit()

    NotificationService.notify_approval_submitted(approval)

    return jsonify({
        'message': '审批提交成功',
        'approval': approval.to_dict(include_chain=True)
    }), 201


@approvals_bp.route('/<int:approval_id>', methods=['GET'])
@jwt_required()
def get_approval(approval_id):
    """获取审批详情（含审批链）"""
    approval = Approval.query.get_or_404(approval_id)
    return jsonify({'approval': approval.to_dict(include_chain=True)}), 200


@approvals_bp.route('/<int:approval_id>/process', methods=['PUT'])
@jwt_required()
def process_approval(approval_id):
    """处理审批（按审批链逐节点推进）"""
    current_user_id = get_jwt_identity()
    approval = Approval.query.get_or_404(approval_id)
    data = request.get_json()

    if not data or not data.get('action'):
        return jsonify({'message': '请指定操作', 'error': 'missing_action'}), 400

    if approval.status != 'pending':
        return jsonify({'message': '该审批已处理完毕', 'error': 'already_processed'}), 400

    current_node = None
    if approval.current_node_id:
        current_node = ApprovalNode.query.get(approval.current_node_id)

    if not current_node:
        return jsonify({'message': '当前审批没有待处理节点', 'error': 'no_current_node'}), 400

    # 权限检查
    is_handler = False
    if current_node.handler_id == current_user_id:
        is_handler = True
    # 会签节点检查
    if current_node.parallel_handlers:
        for ph in current_node.parallel_handlers:
            if ph.get('user_id') == current_user_id and ph.get('status') == 'pending':
                is_handler = True
                break

    if not is_handler and \
       not PermissionService.check_permission(current_user_id, 'approval_process') and \
       not PermissionService.check_permission(current_user_id, 'all'):
        return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403

    action = data['action']

    if action == 'approve':
        # 处理会签节点
        if current_node.parallel_handlers:
            all_passed = True
            for ph in current_node.parallel_handlers:
                if ph.get('user_id') == current_user_id:
                    ph['status'] = 'completed'
                    ph['comment'] = data.get('comment', '')
                    ph['handled_at'] = datetime.now().isoformat()
                if ph.get('status') != 'completed':
                    all_passed = False

            if all_passed:
                current_node.status = 'completed'
                current_node.handled_at = datetime.now()
                current_node.comment = data.get('comment', '')
            else:
                db.session.commit()
                return jsonify({
                    'message': '已记录您的审批，等待其他会签人',
                    'approval': approval.to_dict(include_chain=True)
                }), 200
        else:
            current_node.status = 'completed'
            current_node.handler_id = current_user_id
            current_node.handled_at = datetime.now()
            current_node.comment = data.get('comment', '')

        # 推进到下一个节点
        has_next = _advance_to_next_node(approval)

        if not has_next:
            # 审批完成
            approval.processor_id = current_user_id
            approval.processed_at = datetime.now()
            approval.process_comment = data.get('comment', '')
            _handle_permission_approval(approval, granted=True)
            _handle_leave_approval(approval, granted=True)
            _handle_expense_approval(approval, granted=True)

            activity_title = f'批准了审批 "{approval.title}"'
            activity = Activity(
                activity_type='approval_approved',
                title=activity_title,
                user_id=current_user_id
            )
            db.session.add(activity)
            db.session.commit()

            processor = User.query.get(current_user_id)
            NotificationService.notify_approval_processed(approval, action, processor)

            AuditService.log_from_current_user(
                action=AuditService.APPROVAL_PROCESS,
                resource_type='approval',
                resource_id=approval_id,
                detail={'action': action, 'title': approval.title},
                status='success'
            )

            return jsonify({
                'message': '审批已通过',
                'approval': approval.to_dict(include_chain=True)
            }), 200

        return jsonify({
            'message': '已审批通过，进入下一节点',
            'approval': approval.to_dict(include_chain=True)
        }), 200

    elif action == 'reject':
        # 拒绝当前节点
        if current_node.parallel_handlers:
            for ph in current_node.parallel_handlers:
                if ph.get('user_id') == current_user_id:
                    ph['status'] = 'rejected'
                    ph['comment'] = data.get('comment', '')
                    ph['handled_at'] = datetime.now().isoformat()

        current_node.status = 'rejected'
        current_node.handler_id = current_user_id
        current_node.handled_at = datetime.now()
        current_node.comment = data.get('comment', '')

        approval.status = 'rejected'
        approval.current_node_id = None
        approval.processor_id = current_user_id
        approval.processed_at = datetime.now()
        approval.process_comment = data.get('comment', '')

        _handle_permission_approval(approval, granted=False)
        _handle_leave_approval(approval, granted=False)
        _handle_expense_approval(approval, granted=False)

        activity_title = f'拒绝了审批 "{approval.title}"'
        activity = Activity(
            activity_type='approval_rejected',
            title=activity_title,
            user_id=current_user_id
        )
        db.session.add(activity)
        db.session.commit()

        processor = User.query.get(current_user_id)
        NotificationService.notify_approval_processed(approval, action, processor)

        AuditService.log_from_current_user(
            action=AuditService.APPROVAL_PROCESS,
            resource_type='approval',
            resource_id=approval_id,
            detail={'action': action, 'title': approval.title},
            status='success'
        )

        return jsonify({
            'message': '审批已拒绝',
            'approval': approval.to_dict(include_chain=True)
        }), 200

    else:
        return jsonify({'message': '无效的操作', 'error': 'invalid_action'}), 400


def _handle_permission_approval(approval, granted=True):
    """处理权限申请审批的结果"""
    if approval.approval_type != 'permission':
        return
    applicant = User.query.get(approval.applicant_id)
    if not applicant:
        return
    data_analyst_role = Role.query.filter_by(name='data_analyst').first()
    if not data_analyst_role:
        return
    if granted:
        if data_analyst_role not in applicant.roles:
            applicant.roles.append(data_analyst_role)
            db.session.commit()
    else:
        if data_analyst_role in applicant.roles:
            applicant.roles.remove(data_analyst_role)
            db.session.commit()


def _handle_leave_approval(approval, granted=True):
    """处理请假审批的结果：同步更新假期余额"""
    if approval.approval_type != 'leave':
        return
    try:
        days = approval.leave_days or 0
    except (ValueError, TypeError):
        return
    leave_type_map = {'annual': 'annual', 'sick': 'sick', 'personal': 'personal'}
    leave_type = leave_type_map.get(approval.sub_type)
    if not leave_type:
        return
    year = approval.created_at.year if approval.created_at else datetime.now().year
    balance = LeaveBalance.query.filter_by(
        user_id=approval.applicant_id,
        leave_type=leave_type,
        year=year
    ).first()
    if not balance:
        return
    if granted:
        current_used = float(balance.used_days or 0)
        balance.used_days = current_used + days
        db.session.commit()


def _handle_expense_approval(approval, granted=True):
    """【新增】处理费用报销审批的结果：反向同步更新 Expense 状态"""
    if approval.approval_type != 'expense':
        return
    # 通过 approval_id 查找关联的 Expense
    expense = Expense.query.filter_by(approval_id=approval.id).first()
    if not expense:
        return
    try:
        if granted:
            expense.status = 'approved'
        else:
            expense.status = 'rejected'
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        # 记录错误但不影响审批流程
        import traceback
        traceback.print_exc()


# ================================================
# 【第三次迭代于然负责】(8) 审批流程定义 API
# 提供所有审批流程的查看和修改接口（仅总经理可修改）
# ================================================
# ==================== 【新增】审批流程定义 API ====================

@approvals_bp.route('/workflow-definitions', methods=['GET'])
@jwt_required()
def get_workflow_definitions():
    """获取所有审批流程定义"""
    return jsonify({
        'definitions': WORKFLOW_DEFINITIONS
    }), 200


@approvals_bp.route('/workflow-definitions/<string:workflow_type>', methods=['PUT'])
@jwt_required()
def update_workflow_definition(workflow_type):
    """更新审批流程定义（仅总经理可修改）"""
    current_user_id = get_jwt_identity()
    
    # 权限检查：仅总经理(super_admin)可修改
    user = User.query.get(current_user_id)
    is_gm = any(r.name == 'super_admin' for r in user.roles)
    if not is_gm:
        return jsonify({'message': '仅总经理可修改审批流程', 'error': 'forbidden'}), 403
    
    if workflow_type not in WORKFLOW_DEFINITIONS:
        return jsonify({'message': '无效的流程类型', 'error': 'invalid_type'}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({'message': '请提供更新数据', 'error': 'missing_data'}), 400
    
    wf = WORKFLOW_DEFINITIONS[workflow_type]
    if 'name' in data:
        wf['name'] = data['name']
    if 'description' in data:
        wf['description'] = data['description']
    if 'nodes' in data:
        wf['nodes'] = data['nodes']
    
    return jsonify({
        'message': '流程定义更新成功',
        'definition': wf
    }), 200


@approvals_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_approval_stats():
    """获取审批统计"""
    total = Approval.query.count()
    pending = Approval.query.filter_by(status='pending').count()
    approved = Approval.query.filter_by(status='approved').count()
    rejected = Approval.query.filter_by(status='rejected').count()
    urgent_pending = Approval.query.filter_by(status='pending', is_urgent=True).count()
    type_stats = db.session.query(
        Approval.approval_type,
        db.func.count(Approval.id)
    ).group_by(Approval.approval_type).all()
    return jsonify({
        'overview': {
            'total': total,
            'pending': pending,
            'approved': approved,
            'rejected': rejected,
            'urgent_pending': urgent_pending
        },
        'by_type': [{"type": t, "count": c} for t, c in type_stats]
    }), 200


@approvals_bp.route('/<int:approval_id>/chain', methods=['GET'])
@jwt_required()
def get_approval_chain(approval_id):
    """获取审批链详情"""
    approval = Approval.query.get_or_404(approval_id)
    return jsonify({
        'approval_id': approval.id,
        'title': approval.title,
        'status': approval.status if approval.status else None,
        'chain': approval.get_approval_chain(),
        'current_node': approval.current_node_id
    }), 200


@approvals_bp.route('/types', methods=['GET'])
@jwt_required()
def get_approval_types():
    """获取审批类型列表"""
    types = [
        {'value': 'leave', 'label': '请假申请'},
        {'value': 'expense', 'label': '报销申请'},
        {'value': 'purchase', 'label': '采购申请'},
        {'value': 'overtime', 'label': '加班申请'},
        {'value': 'permission', 'label': '权限申请'},
        {'value': 'contract', 'label': '合同审批'},
        {'value': 'ticket', 'label': '客户工单'},
        {'value': 'other', 'label': '其他申请'}
    ]
    return jsonify({'types': types}), 200


@approvals_bp.route('/pending-count', methods=['GET'])
@jwt_required()
def get_pending_count():
    """获取待处理审批数量"""
    current_user_id = get_jwt_identity()
    my_pending = Approval.query.filter_by(applicant_id=current_user_id, status='pending').count()
    can_process = PermissionService.check_permission(current_user_id, 'approval_process') or \
                  PermissionService.check_permission(current_user_id, 'all')
    total_pending = Approval.query.filter_by(status='pending').count() if can_process else 0
    return jsonify({
        'my_pending': my_pending,
        'total_pending': total_pending,
        'can_process': can_process
    }), 200
