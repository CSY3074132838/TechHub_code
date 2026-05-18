"""
客户工单/反馈 API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models import Ticket, TicketStatus, TicketPriority, Client, User
from app.decorators import require_permission
from app.services import AuditService, PermissionService

tickets_bp = Blueprint('tickets', __name__)


def generate_ticket_no():
    """生成工单编号"""
    import time
    return f"TK{int(time.time())}"


@tickets_bp.route('/', methods=['GET'])
@jwt_required()
def get_tickets():
    """获取工单列表"""
    current_user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')
    priority = request.args.get('priority')
    client_id = request.args.get('client_id', type=int)
    search = request.args.get('search')
    
    query = Ticket.query
    
    if status:
        query = query.filter(Ticket.status == status)
    if priority:
        query = query.filter(Ticket.priority == priority)
    if client_id:
        query = query.filter_by(client_id=client_id)
    if search:
        query = query.filter(
            (Ticket.title.contains(search)) |
            (Ticket.description.contains(search)) |
            (Ticket.ticket_no.contains(search))
        )
    
    # DataScope
    if not PermissionService.check_permission(current_user_id, 'all'):
        query = query.filter(
            (Ticket.reporter_id == current_user_id) |
            (Ticket.assignee_id == current_user_id) |
            (Ticket.client.has(manager_id=current_user_id))
        )
    
    pagination = query.order_by(Ticket.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'tickets': [t.to_dict() for t in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    }), 200


@tickets_bp.route('/', methods=['POST'])
@jwt_required()
def create_ticket():
    """创建工单"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('title'):
        return jsonify({'message': '工单标题不能为空', 'error': 'missing_title'}), 400
    if not data.get('client_id'):
        return jsonify({'message': '请选择客户', 'error': 'missing_client'}), 400
    
    ticket = Ticket(
        ticket_no=generate_ticket_no(),
        title=data['title'],
        description=data.get('description', ''),
        client_id=data['client_id'],
        priority=data.get('priority', 'medium'),
        assignee_id=data.get('assignee_id'),
        reporter_id=current_user_id
    )
    
    db.session.add(ticket)
    db.session.commit()
    
    AuditService.log_from_current_user(
        action='TICKET_CREATE',
        resource_type='ticket',
        resource_id=ticket.id,
        detail={'title': ticket.title, 'client_id': ticket.client_id},
        status='success'
    )
    
    return jsonify({
        'message': '工单创建成功',
        'ticket': ticket.to_dict()
    }), 201


@tickets_bp.route('/<int:ticket_id>', methods=['GET'])
@jwt_required()
def get_ticket(ticket_id):
    """获取工单详情"""
    ticket = Ticket.query.get_or_404(ticket_id)
    return jsonify({'ticket': ticket.to_dict()}), 200


@tickets_bp.route('/<int:ticket_id>', methods=['PUT'])
@jwt_required()
def update_ticket(ticket_id):
    """更新工单"""
    current_user_id = get_jwt_identity()
    ticket = Ticket.query.get_or_404(ticket_id)
    
    # 权限检查
    can_edit = (
        ticket.reporter_id == current_user_id or
        ticket.assignee_id == current_user_id or
        PermissionService.check_permission(current_user_id, 'all')
    )
    if not can_edit:
        return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    data = request.get_json()
    allowed_fields = ['title', 'description', 'client_id', 'assignee_id']
    for field in allowed_fields:
        if field in data:
            setattr(ticket, field, data[field])
    
    if 'priority' in data and data['priority']:
        ticket.priority = data['priority']
    if 'status' in data and data['status']:
        old_status = ticket.status
        ticket.status = data['status']
        # 解决时记录解决时间
        if ticket.status == 'resolved' and old_status != 'resolved':
            ticket.resolved_at = datetime.now()
            ticket.resolution = data.get('resolution', '')
    
    db.session.commit()
    
    AuditService.log_from_current_user(
        action='TICKET_UPDATE',
        resource_type='ticket',
        resource_id=ticket_id,
        detail={'title': ticket.title, 'status': ticket.status if ticket.status else None},
        status='success'
    )
    
    return jsonify({
        'message': '工单更新成功',
        'ticket': ticket.to_dict()
    }), 200


@tickets_bp.route('/<int:ticket_id>', methods=['DELETE'])
@jwt_required()
def delete_ticket(ticket_id):
    """删除工单"""
    current_user_id = get_jwt_identity()
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if ticket.reporter_id != current_user_id:
        if not PermissionService.check_permission(current_user_id, 'all'):
            return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    db.session.delete(ticket)
    db.session.commit()
    
    AuditService.log_from_current_user(
        action='TICKET_DELETE',
        resource_type='ticket',
        resource_id=ticket_id,
        detail={'title': ticket.title},
        status='success'
    )
    
    return jsonify({'message': '工单已删除'}), 200


@tickets_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_ticket_stats():
    """获取工单统计"""
    from sqlalchemy import func
    current_user_id = get_jwt_identity()
    
    query = Ticket.query
    if not PermissionService.check_permission(current_user_id, 'all'):
        query = query.filter(
            (Ticket.reporter_id == current_user_id) |
            (Ticket.assignee_id == current_user_id) |
            (Ticket.client.has(manager_id=current_user_id))
        )
    
    total = query.count()
    open_count = query.filter_by(status='open').count()
    in_progress_count = query.filter_by(status='in_progress').count()
    resolved_count = query.filter_by(status='resolved').count()
    
    priority_dist = query.with_entities(
        Ticket.priority,
        func.count(Ticket.id).label('count')
    ).group_by(Ticket.priority).all()
    
    return jsonify({
        'total': total,
        'open': open_count,
        'in_progress': in_progress_count,
        'resolved': resolved_count,
        'priority_distribution': [{'priority': p or 'unknown', 'count': c} for p, c in priority_dist]
    }), 200
