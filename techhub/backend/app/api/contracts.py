"""
合同管理 API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Contract, ContractStatus, Client, Project, User
from app.decorators import require_permission
from app.services import AuditService, PermissionService

contracts_bp = Blueprint('contracts', __name__)


def parse_date(date_str):
    """解析日期字符串"""
    if not date_str:
        return None
    if isinstance(date_str, str):
        from datetime import datetime
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return None
    return date_str


@contracts_bp.route('/', methods=['GET'])
@jwt_required()
def get_contracts():
    """获取合同列表"""
    current_user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')
    client_id = request.args.get('client_id', type=int)
    search = request.args.get('search')
    
    query = Contract.query
    
    if status:
        query = query.filter(Contract.status == status)
    if client_id:
        query = query.filter_by(client_id=client_id)
    if search:
        query = query.filter(
            (Contract.name.contains(search)) |
            (Contract.contract_no.contains(search))
        )
    
    # DataScope：非管理员只能看自己创建或关联项目的合同
    if not PermissionService.check_permission(current_user_id, 'all'):
        user = User.query.get(current_user_id)
        query = query.filter(
            (Contract.created_by == current_user_id) |
            (Contract.client.has(manager_id=current_user_id))
        )
    
    pagination = query.order_by(Contract.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'contracts': [c.to_dict() for c in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    }), 200


@contracts_bp.route('/', methods=['POST'])
@jwt_required()
def create_contract():
    """创建合同"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'message': '合同名称不能为空', 'error': 'missing_name'}), 400
    if not data.get('client_id'):
        return jsonify({'message': '请选择客户', 'error': 'missing_client'}), 400
    
    # 生成合同编号
    import time
    contract_no = data.get('contract_no') or f"HT{int(time.time())}"
    
    contract = Contract(
        contract_no=contract_no,
        name=data['name'],
        client_id=data['client_id'],
        project_id=data.get('project_id'),
        amount=data.get('amount'),
        sign_date=parse_date(data.get('sign_date')),
        start_date=parse_date(data.get('start_date')),
        end_date=parse_date(data.get('end_date')),
        status=data.get('status', 'draft'),
        payment_terms=data.get('payment_terms', ''),
        content=data.get('content', ''),
        created_by=current_user_id
    )
    
    db.session.add(contract)
    db.session.commit()
    
    AuditService.log_from_current_user(
        action='CONTRACT_CREATE',
        resource_type='contract',
        resource_id=contract.id,
        detail={'name': contract.name, 'amount': str(contract.amount)},
        status='success'
    )
    
    return jsonify({
        'message': '合同创建成功',
        'contract': contract.to_dict()
    }), 201


@contracts_bp.route('/<int:contract_id>', methods=['GET'])
@jwt_required()
def get_contract(contract_id):
    """获取合同详情"""
    contract = Contract.query.get_or_404(contract_id)
    return jsonify({'contract': contract.to_dict()}), 200


@contracts_bp.route('/<int:contract_id>', methods=['PUT'])
@jwt_required()
def update_contract(contract_id):
    """更新合同"""
    current_user_id = get_jwt_identity()
    contract = Contract.query.get_or_404(contract_id)
    
    if contract.created_by != current_user_id:
        if not PermissionService.check_permission(current_user_id, 'all'):
            return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    data = request.get_json()
    allowed_fields = ['name', 'client_id', 'project_id', 'amount', 'payment_terms', 'content']
    for field in allowed_fields:
        if field in data:
            setattr(contract, field, data[field])
    
    if 'sign_date' in data:
        contract.sign_date = parse_date(data['sign_date'])
    if 'start_date' in data:
        contract.start_date = parse_date(data['start_date'])
    if 'end_date' in data:
        contract.end_date = parse_date(data['end_date'])
    if 'status' in data and data['status']:
        contract.status = data['status']
    
    db.session.commit()
    
    AuditService.log_from_current_user(
        action='CONTRACT_UPDATE',
        resource_type='contract',
        resource_id=contract_id,
        detail={'name': contract.name},
        status='success'
    )
    
    return jsonify({
        'message': '合同更新成功',
        'contract': contract.to_dict()
    }), 200


@contracts_bp.route('/<int:contract_id>', methods=['DELETE'])
@jwt_required()
def delete_contract(contract_id):
    """删除合同"""
    current_user_id = get_jwt_identity()
    contract = Contract.query.get_or_404(contract_id)
    
    if contract.created_by != current_user_id:
        if not PermissionService.check_permission(current_user_id, 'all'):
            return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    db.session.delete(contract)
    db.session.commit()
    
    AuditService.log_from_current_user(
        action='CONTRACT_DELETE',
        resource_type='contract',
        resource_id=contract_id,
        detail={'name': contract.name},
        status='success'
    )
    
    return jsonify({'message': '合同已删除'}), 200
