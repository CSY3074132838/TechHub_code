"""
审批中心 API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models import Approval, User, Activity, ActivityType, ApprovalStatus, ApprovalNode, ApprovalType, Role

def parse_approval_type(value):
    """将字符串转换为 ApprovalType 枚举"""
    if value is None or isinstance(value, ApprovalType):
        return value
    mapping = {
        'leave': ApprovalType.LEAVE,
        'expense': ApprovalType.EXPENSE,
        'purchase': ApprovalType.PURCHASE,
        'overtime': ApprovalType.OVERTIME,
        'other': ApprovalType.OTHER
    }
    return mapping.get(value)

approvals_bp = Blueprint('approvals', __name__)

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
    scope = request.args.get('scope', 'all')  # all, my, pending_me
    
    query = Approval.query
    
    # 根据范围筛选
    if scope == 'my':
        # 我发起的审批
        query = query.filter_by(applicant_id=current_user_id)
    elif scope == 'pending_me':
        # 待我审批的（这里简化处理，实际应根据审批流程配置）
        user = User.query.get(current_user_id)
        if user.has_permission('approval_urgent') or user.has_permission('all'):
            query = query.filter_by(status=ApprovalStatus.PENDING)
        else:
            query = query.filter_by(id=-1)  # 返回空结果
    else:
        # 所有我能看到的审批
        user = User.query.get(current_user_id)
        if not user.has_permission('all'):
            query = query.filter(
                (Approval.applicant_id == current_user_id) |
                (Approval.processor_id == current_user_id)
            )
    
    # 其他筛选条件
    if status:
        query = query.filter(Approval.status == status)
    if approval_type:
        query = query.filter(Approval.approval_type == approval_type)
    if is_urgent is not None:
        query = query.filter_by(is_urgent=is_urgent)
    
    # 紧急审批优先，然后按时间倒序
    query = query.order_by(Approval.is_urgent.desc(), Approval.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    approvals = pagination.items
    
    return jsonify({
        'approvals': [approval.to_dict() for approval in approvals],
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
    
    approval = Approval(
        title=data['title'],
        approval_type=parse_approval_type(data['approval_type']),
        description=data.get('description', ''),
        amount=data.get('amount'),
        is_urgent=data.get('is_urgent', False),
        applicant_id=current_user_id,
        attachments=data.get('attachments', [])
    )
    
    db.session.add(approval)
    db.session.commit()
    
    # 创建审批链
    applicant = User.query.get(current_user_id)
    create_approval_chain(
        approval,
        data['approval_type'],
        data.get('is_urgent', False),
        applicant
    )
    
    # 记录活动
    activity = Activity(
        activity_type=ActivityType.APPROVAL_SUBMITTED,
        title=f'提交了审批 "{approval.title}"',
        user_id=current_user_id
    )
    db.session.add(activity)
    db.session.commit()
    
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

def create_approval_chain(approval, approval_type, is_urgent, applicant):
    """为审批创建审批链节点"""
    nodes = []
    
    # 节点1：直属上级/项目经理审批
    nodes.append(ApprovalNode(
        approval_id=approval.id,
        node_name='直属上级审批',
        status='pending',
        order=1
    ))
    
    # 节点2：部门负责人审批（紧急或金额相关）
    if is_urgent or approval_type in ['expense', 'purchase']:
        nodes.append(ApprovalNode(
            approval_id=approval.id,
            node_name='部门负责人审批',
            status='pending',
            order=2
        ))
    
    # 节点3：财务/管理员终审（采购、报销、紧急）
    if approval_type in ['expense', 'purchase'] or is_urgent:
        nodes.append(ApprovalNode(
            approval_id=approval.id,
            node_name='财务终审',
            status='pending',
            order=3
        ))
    
    # 如果没有额外节点，至少加一个归档节点
    if len(nodes) == 1:
        nodes.append(ApprovalNode(
            approval_id=approval.id,
            node_name='归档完成',
            status='pending',
            order=2
        ))
    
    for node in nodes:
        db.session.add(node)
    
    # 设置当前节点为第一个
    db.session.flush()
    approval.current_node_id = nodes[0].id
    db.session.commit()

@approvals_bp.route('/<int:approval_id>/process', methods=['PUT'])
@jwt_required()
def process_approval(approval_id):
    """处理审批（按审批链推进）"""
    current_user_id = get_jwt_identity()
    approval = Approval.query.get_or_404(approval_id)
    data = request.get_json()
    
    if not data or not data.get('action'):
        return jsonify({'message': '请指定操作', 'error': 'missing_action'}), 400
    
    # 检查权限
    user = User.query.get(current_user_id)
    
    # 获取当前节点
    current_node = None
    if approval.current_node_id:
        current_node = ApprovalNode.query.get(approval.current_node_id)
    
    action = data['action']
    
    if action == 'approve':
        # 推进到下一个节点
        if current_node:
            current_node.status = 'completed'
            current_node.handler_id = current_user_id
            current_node.handled_at = datetime.utcnow()
            current_node.comment = data.get('comment', '')
            
            # 查找下一个待处理节点
            next_node = ApprovalNode.query.filter(
                ApprovalNode.approval_id == approval.id,
                ApprovalNode.order > current_node.order,
                ApprovalNode.status == 'pending'
            ).order_by(ApprovalNode.order).first()
            
            if next_node:
                approval.current_node_id = next_node.id
                approval.status = ApprovalStatus.PENDING
                activity_title = f'审批 "{approval.title}" 通过并进入下一节点'
            else:
                # 所有节点完成
                approval.status = ApprovalStatus.APPROVED
                approval.current_node_id = None
                activity_title = f'批准了审批 "{approval.title}"'
                _handle_permission_approval(approval, granted=True)
        else:
            approval.status = ApprovalStatus.APPROVED
            activity_title = f'批准了审批 "{approval.title}"'
            _handle_permission_approval(approval, granted=True)
            
    elif action == 'reject':
        # 拒绝审批，当前节点标记为拒绝
        if current_node:
            current_node.status = 'rejected'
            current_node.handler_id = current_user_id
            current_node.handled_at = datetime.utcnow()
            current_node.comment = data.get('comment', '')
        
        approval.status = ApprovalStatus.REJECTED
        activity_title = f'拒绝了审批 "{approval.title}"'
        _handle_permission_approval(approval, granted=False)
    else:
        return jsonify({'message': '无效的操作', 'error': 'invalid_action'}), 400
    
    approval.processor_id = current_user_id
    approval.processed_at = datetime.utcnow()
    approval.process_comment = data.get('comment', '')
    
    db.session.commit()
    
    # 记录活动
    activity = Activity(
        activity_type=ActivityType.APPROVAL_APPROVED,
        title=activity_title,
        user_id=current_user_id
    )
    db.session.add(activity)
    db.session.commit()

def _handle_permission_approval(approval, granted=True):
    """处理权限申请审批的结果"""
    if not approval.title or '[权限申请]' not in approval.title:
        return
    
    applicant = User.query.get(approval.applicant_id)
    if not applicant:
        return
    
    data_viewer_role = Role.query.filter_by(name='data_viewer').first()
    if not data_viewer_role:
        return
    
    if granted:
        # 授予 data_viewer 角色
        if data_viewer_role not in applicant.roles:
            applicant.roles.append(data_viewer_role)
            db.session.commit()
    else:
        # 拒绝时移除 data_viewer 角色
        if data_viewer_role in applicant.roles:
            applicant.roles.remove(data_viewer_role)
            db.session.commit()
    
    return jsonify({
        'message': '审批处理成功',
        'approval': approval.to_dict(include_chain=True)
    }), 200

@approvals_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_approval_stats():
    """获取审批统计"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # 基础统计
    total = Approval.query.count()
    pending = Approval.query.filter_by(status=ApprovalStatus.PENDING).count()
    approved = Approval.query.filter_by(status=ApprovalStatus.APPROVED).count()
    rejected = Approval.query.filter_by(status=ApprovalStatus.REJECTED).count()
    
    # 紧急审批统计
    urgent_pending = Approval.query.filter_by(
        status=ApprovalStatus.PENDING, 
        is_urgent=True
    ).count()
    
    # 按类型统计
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
        'by_type': [{"type": t.value, "count": c} for t, c in type_stats]
    }), 200

@approvals_bp.route('/<int:approval_id>/chain', methods=['GET'])
@jwt_required()
def get_approval_chain(approval_id):
    """获取审批链详情"""
    approval = Approval.query.get_or_404(approval_id)
    return jsonify({
        'approval_id': approval.id,
        'title': approval.title,
        'status': approval.status.value if approval.status else None,
        'chain': approval.get_approval_chain(),
        'current_node': approval.current_node_id
    }), 200

@approvals_bp.route('/types', methods=['GET'])
@jwt_required()
def get_approval_types():
    """获取审批类型列表"""
    from app.models import ApprovalType
    
    types = [
        {'value': ApprovalType.LEAVE.value, 'label': '请假申请'},
        {'value': ApprovalType.EXPENSE.value, 'label': '报销申请'},
        {'value': ApprovalType.PURCHASE.value, 'label': '采购申请'},
        {'value': ApprovalType.OVERTIME.value, 'label': '加班申请'},
        {'value': ApprovalType.OTHER.value, 'label': '其他申请'}
    ]
    
    return jsonify({'types': types}), 200

@approvals_bp.route('/pending-count', methods=['GET'])
@jwt_required()
def get_pending_count():
    """获取待处理审批数量"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # 普通用户：自己发起的待处理审批
    my_pending = Approval.query.filter_by(
        applicant_id=current_user_id,
        status=ApprovalStatus.PENDING
    ).count()
    
    # 有权限的用户：所有待处理审批
    can_process = user.has_permission('approval_urgent') or user.has_permission('all')
    total_pending = Approval.query.filter_by(status=ApprovalStatus.PENDING).count() if can_process else 0
    
    return jsonify({
        'my_pending': my_pending,
        'total_pending': total_pending,
        'can_process': can_process
    }), 200
