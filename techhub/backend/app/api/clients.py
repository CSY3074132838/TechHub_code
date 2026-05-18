"""
客户关系管理 API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models import Client, ClientStatus, Project, Contract, Ticket, User, PaymentRecord
from app.decorators import require_permission, data_scope_required
from app.services import AuditService, PermissionService

clients_bp = Blueprint('clients', __name__)


@clients_bp.route('/', methods=['GET'])
@jwt_required()
def get_clients():
    """获取客户列表 - 带搜索和筛选"""
    current_user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')
    level = request.args.get('level')
    search = request.args.get('search')
    industry = request.args.get('industry')
    
    query = Client.query
    
    # DataScope 过滤
    scope = PermissionService.get_user_data_scope(current_user_id)
    user = User.query.get(current_user_id)
    
    if scope.value == 'all':
        pass
    elif scope.value in ('dept', 'dept_and_below'):
        dept_members = User.query.filter_by(department=user.department).all()
        member_ids = [m.id for m in dept_members]
        query = query.filter(Client.manager_id.in_(member_ids))
    else:
        # 普通用户只看自己负责的客户
        query = query.filter_by(manager_id=current_user_id)
    
    if status:
        query = query.filter(Client.status == status)
    if level:
        query = query.filter_by(level=level)
    if industry:
        query = query.filter_by(industry=industry)
    if search:
        query = query.filter(
            (Client.name.contains(search)) |
            (Client.contact_name.contains(search)) |
            (Client.contact_email.contains(search))
        )
    
    pagination = query.order_by(Client.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    clients = pagination.items
    
    return jsonify({
        'clients': [client.to_dict() for client in clients],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    }), 200


@clients_bp.route('/', methods=['POST'])
@jwt_required()
def create_client():
    """创建新客户"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'message': '客户名称不能为空', 'error': 'missing_name'}), 400
    
    client = Client(
        name=data['name'],
        industry=data.get('industry', ''),
        contact_name=data.get('contact_name', ''),
        contact_phone=data.get('contact_phone', ''),
        contact_email=data.get('contact_email', ''),
        address=data.get('address', ''),
        status=data.get('status', 'potential'),
        level=data.get('level', 'b'),
        remark=data.get('remark', ''),
        manager_id=data.get('manager_id') or current_user_id
    )
    
    db.session.add(client)
    db.session.commit()
    
    AuditService.log_from_current_user(
        action='CLIENT_CREATE',
        resource_type='client',
        resource_id=client.id,
        detail={'name': client.name},
        status='success'
    )
    
    return jsonify({
        'message': '客户创建成功',
        'client': client.to_dict()
    }), 201


@clients_bp.route('/<int:client_id>', methods=['GET'])
@jwt_required()
def get_client(client_id):
    """获取客户详情"""
    client = Client.query.get_or_404(client_id)
    return jsonify({'client': client.to_dict(include_projects=True)}), 200


@clients_bp.route('/<int:client_id>', methods=['PUT'])
@jwt_required()
def update_client(client_id):
    """更新客户信息"""
    current_user_id = get_jwt_identity()
    client = Client.query.get_or_404(client_id)
    
    # 权限检查：客户经理或管理员可修改
    if client.manager_id != current_user_id:
        if not PermissionService.check_permission(current_user_id, 'all'):
            return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    data = request.get_json()
    before = {'name': client.name, 'status': client.status if client.status else None}
    
    allowed_fields = ['name', 'industry', 'contact_name', 'contact_phone', 
                      'contact_email', 'address', 'level', 'remark']
    for field in allowed_fields:
        if field in data:
            setattr(client, field, data[field])
    
    if 'manager_id' in data:
        client.manager_id = data['manager_id'] or client.manager_id
    
    if 'status' in data and data['status']:
        client.status = data['status']
    
    db.session.commit()
    
    AuditService.log_from_current_user(
        action='CLIENT_UPDATE',
        resource_type='client',
        resource_id=client_id,
        detail={'before': before, 'after': {'name': client.name, 'status': client.status if client.status else None}},
        status='success'
    )
    
    return jsonify({
        'message': '客户更新成功',
        'client': client.to_dict()
    }), 200


@clients_bp.route('/<int:client_id>', methods=['DELETE'])
@jwt_required()
def delete_client(client_id):
    """删除客户（软删除：标记为流失）"""
    current_user_id = get_jwt_identity()
    client = Client.query.get_or_404(client_id)
    
    if client.manager_id != current_user_id:
        if not PermissionService.check_permission(current_user_id, 'all'):
            return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    client.status = 'lost'
    db.session.commit()
    
    AuditService.log_from_current_user(
        action='CLIENT_DELETE',
        resource_type='client',
        resource_id=client_id,
        detail={'name': client.name, 'soft_delete': True},
        status='success'
    )
    
    return jsonify({'message': '客户已标记为流失'}), 200


@clients_bp.route('/<int:client_id>/permanent', methods=['DELETE'])
@jwt_required()
def permanently_delete_client(client_id):
    """彻底删除客户（从数据库中永久删除）"""
    current_user_id = get_jwt_identity()
    client = Client.query.get_or_404(client_id)
    
    # 权限检查：仅允许该客户的负责人或管理员
    if client.manager_id != current_user_id:
        if not PermissionService.check_permission(current_user_id, 'all'):
            return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    # 解除关联数据的外键引用，避免外键约束错误
    Project.query.filter_by(client_id=client_id).update({'client_id': None})
    PaymentRecord.query.filter_by(client_id=client_id).update({'client_id': None})
    
    client_name = client.name
    
    # 删除客户（关联的 contracts 和 tickets 会级联删除）
    db.session.delete(client)
    db.session.commit()
    
    AuditService.log_from_current_user(
        action='CLIENT_PERMANENT_DELETE',
        resource_type='client',
        resource_id=client_id,
        detail={'name': client_name, 'permanent_delete': True},
        status='success'
    )
    
    return jsonify({'message': '客户已彻底删除'}), 200


@clients_bp.route('/<int:client_id>/projects', methods=['GET'])
@jwt_required()
def get_client_projects(client_id):
    """获取客户关联的项目"""
    client = Client.query.get_or_404(client_id)
    projects = Project.query.filter_by(client_id=client_id).all()
    return jsonify({
        'projects': [p.to_dict() for p in projects]
    }), 200


@clients_bp.route('/<int:client_id>/contracts', methods=['GET'])
@jwt_required()
def get_client_contracts(client_id):
    """获取客户关联的合同"""
    client = Client.query.get_or_404(client_id)
    contracts = Contract.query.filter_by(client_id=client_id).order_by(Contract.created_at.desc()).all()
    return jsonify({
        'contracts': [c.to_dict() for c in contracts]
    }), 200


@clients_bp.route('/<int:client_id>/tickets', methods=['GET'])
@jwt_required()
def get_client_tickets(client_id):
    """获取客户关联的工单"""
    client = Client.query.get_or_404(client_id)
    tickets = Ticket.query.filter_by(client_id=client_id).order_by(Ticket.created_at.desc()).all()
    return jsonify({
        'tickets': [t.to_dict() for t in tickets]
    }), 200


@clients_bp.route('/options', methods=['GET'])
@jwt_required()
def get_client_options():
    """获取客户下拉选项（用于项目关联）"""
    clients = Client.query.filter(Client.status != 'lost').all()
    return jsonify({
        'clients': [{'id': c.id, 'name': c.name, 'level': c.level} for c in clients]
    }), 200


@clients_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_client_stats():
    """获取客户统计概览"""
    from sqlalchemy import func
    
    current_user_id = get_jwt_identity()
    scope = PermissionService.get_user_data_scope(current_user_id)
    user = User.query.get(current_user_id)
    
    base_query = Client.query
    if scope.value == 'all':
        pass
    elif scope.value in ('dept', 'dept_and_below'):
        dept_members = User.query.filter_by(department=user.department).all() 
        member_ids = [m.id for m in dept_members]
        base_query = base_query.filter(Client.manager_id.in_(member_ids))
    else:
        base_query = base_query.filter_by(manager_id=current_user_id)
    
    total = base_query.count()
    potential = base_query.filter_by(status='potential').count()
    active = base_query.filter_by(status='active').count()
    inactive = base_query.filter_by(status='inactive').count()
    lost = base_query.filter_by(status='lost').count()
    
    # 行业分布
    industry_dist = base_query.with_entities(
        Client.industry,
        func.count(Client.id).label('count')
    ).group_by(Client.industry).all()
    
    # 等级分布
    level_dist = base_query.with_entities(
        Client.level,
        func.count(Client.id).label('count')
    ).group_by(Client.level).all()
    
    return jsonify({
        'total': total,
        'potential': potential,
        'active': active,
        'inactive': inactive,
        'lost': lost,
        'industry_distribution': [{'industry': i or '未分类', 'count': c} for i, c in industry_dist],
        'level_distribution': [{'level': l, 'count': c} for l, c in level_dist]
    }), 200
