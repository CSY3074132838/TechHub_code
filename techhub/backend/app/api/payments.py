"""
【第二次迭代】收付款记录管理 API
作者: 郝益墨
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models import PaymentRecord, Contract, Project, Client, User
from app.decorators import require_permission
from app.services import AuditService

payments_bp = Blueprint('payments', __name__)


def parse_date(date_str):
    """解析日期字符串"""
    if not date_str:
        return None
    if isinstance(date_str, str):
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return None
    return date_str


@payments_bp.route('/', methods=['GET'])
@jwt_required()
def get_payments():
    """获取收付款记录列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    payment_type = request.args.get('payment_type')
    status = request.args.get('status')
    contract_id = request.args.get('contract_id', type=int)
    project_id = request.args.get('project_id', type=int)
    client_id = request.args.get('client_id', type=int)
    month = request.args.get('month')
    
    query = PaymentRecord.query
    
    if payment_type:
        query = query.filter_by(payment_type=payment_type)
    if status:
        query = query.filter_by(status=status)
    if contract_id:
        query = query.filter_by(contract_id=contract_id)
    if project_id:
        query = query.filter_by(project_id=project_id)
    if client_id:
        query = query.filter_by(client_id=client_id)
    if month:
        try:
            year, mon = map(int, month.split('-'))
            query = query.filter(
                db.extract('year', PaymentRecord.payment_date) == year,
                db.extract('month', PaymentRecord.payment_date) == mon
            )
        except ValueError:
            pass
    
    pagination = query.order_by(PaymentRecord.payment_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'payments': [p.to_dict() for p in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@payments_bp.route('/', methods=['POST'])
@jwt_required()
def create_payment():
    """创建收付款记录"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('title') or not data.get('amount') or not data.get('payment_date'):
        return jsonify({'message': '请填写标题、金额和日期', 'error': 'missing_fields'}), 400
    
    if data.get('payment_type') not in ('income', 'expense'):
        return jsonify({'message': '收支类型不正确', 'error': 'invalid_type'}), 400
    
    payment = PaymentRecord(
        title=data['title'],
        amount=data['amount'],
        payment_date=parse_date(data['payment_date']),
        payment_type=data['payment_type'],
        payment_method=data.get('payment_method', 'bank_transfer'),
        contract_id=data.get('contract_id'),
        project_id=data.get('project_id'),
        client_id=data.get('client_id'),
        description=data.get('description', ''),
        status=data.get('status', 'completed'),
        created_by=current_user_id
    )
    
    db.session.add(payment)
    db.session.commit()
    
    AuditService.log_from_current_user(
        action='PAYMENT_CREATE',
        resource_type='payment',
        resource_id=payment.id,
        detail={
            'title': payment.title,
            'amount': str(payment.amount),
            'type': payment.payment_type
        },
        status='success'
    )
    
    return jsonify({
        'message': '记录创建成功',
        'payment': payment.to_dict()
    }), 201


@payments_bp.route('/<int:payment_id>', methods=['GET'])
@jwt_required()
def get_payment(payment_id):
    """获取收付款详情"""
    payment = PaymentRecord.query.get_or_404(payment_id)
    return jsonify({'payment': payment.to_dict()}), 200


@payments_bp.route('/<int:payment_id>', methods=['PUT'])
@jwt_required()
def update_payment(payment_id):
    """更新收付款记录"""
    current_user_id = get_jwt_identity()
    payment = PaymentRecord.query.get_or_404(payment_id)
    
    if payment.created_by != current_user_id:
        current_user = User.query.get(current_user_id)
        if not current_user.has_permission('all'):
            return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    data = request.get_json()
    allowed_fields = ['title', 'amount', 'payment_type', 'payment_method', 
                      'contract_id', 'project_id', 'client_id', 'description', 'status']
    for field in allowed_fields:
        if field in data:
            setattr(payment, field, data[field])
    
    if 'payment_date' in data:
        payment.payment_date = parse_date(data['payment_date'])
    
    db.session.commit()
    
    AuditService.log_from_current_user(
        action='PAYMENT_UPDATE',
        resource_type='payment',
        resource_id=payment_id,
        detail={'title': payment.title},
        status='success'
    )
    
    return jsonify({
        'message': '记录更新成功',
        'payment': payment.to_dict()
    }), 200


@payments_bp.route('/<int:payment_id>', methods=['DELETE'])
@jwt_required()
def delete_payment(payment_id):
    """删除收付款记录"""
    current_user_id = get_jwt_identity()
    payment = PaymentRecord.query.get_or_404(payment_id)
    
    if payment.created_by != current_user_id:
        current_user = User.query.get(current_user_id)
        if not current_user.has_permission('all'):
            return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    db.session.delete(payment)
    db.session.commit()
    
    AuditService.log_from_current_user(
        action='PAYMENT_DELETE',
        resource_type='payment',
        resource_id=payment_id,
        detail={'title': payment.title},
        status='success'
    )
    
    return jsonify({'message': '记录已删除'}), 200


@payments_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_payment_stats():
    """获取收付款统计"""
    current_user_id = get_jwt_identity()
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    
    try:
        year, mon = map(int, month.split('-'))
    except ValueError:
        return jsonify({'message': '月份格式错误', 'error': 'invalid_month'}), 400
    
    # 收入统计
    income_query = PaymentRecord.query.filter(
        PaymentRecord.payment_type == 'income',
        PaymentRecord.status == 'completed',
        db.extract('year', PaymentRecord.payment_date) == year,
        db.extract('month', PaymentRecord.payment_date) == mon
    )
    total_income = db.session.query(db.func.sum(PaymentRecord.amount)).filter(
        PaymentRecord.payment_type == 'income',
        PaymentRecord.status == 'completed',
        db.extract('year', PaymentRecord.payment_date) == year,
        db.extract('month', PaymentRecord.payment_date) == mon
    ).scalar() or 0
    
    # 支出统计
    total_expense = db.session.query(db.func.sum(PaymentRecord.amount)).filter(
        PaymentRecord.payment_type == 'expense',
        PaymentRecord.status == 'completed',
        db.extract('year', PaymentRecord.payment_date) == year,
        db.extract('month', PaymentRecord.payment_date) == mon
    ).scalar() or 0
    
    # 按合同统计收入 Top10
    contract_income = db.session.query(
        Contract,
        db.func.sum(PaymentRecord.amount).label('total_amount')
    ).join(PaymentRecord, PaymentRecord.contract_id == Contract.id).filter(
        PaymentRecord.payment_type == 'income',
        PaymentRecord.status == 'completed',
        db.extract('year', PaymentRecord.payment_date) == year,
        db.extract('month', PaymentRecord.payment_date) == mon
    ).group_by(Contract.id).order_by(db.func.sum(PaymentRecord.amount).desc()).limit(10).all()
    
    # 近6个月趋势
    from datetime import timedelta
    trend = []
    for i in range(5, -1, -1):
        d = datetime.now().replace(day=1) - timedelta(days=i*30)
        trend_year, trend_mon = d.year, d.month
        inc = db.session.query(db.func.sum(PaymentRecord.amount)).filter(
            PaymentRecord.payment_type == 'income',
            PaymentRecord.status == 'completed',
            db.extract('year', PaymentRecord.payment_date) == trend_year,
            db.extract('month', PaymentRecord.payment_date) == trend_mon
        ).scalar() or 0
        exp = db.session.query(db.func.sum(PaymentRecord.amount)).filter(
            PaymentRecord.payment_type == 'expense',
            PaymentRecord.status == 'completed',
            db.extract('year', PaymentRecord.payment_date) == trend_year,
            db.extract('month', PaymentRecord.payment_date) == trend_mon
        ).scalar() or 0
        trend.append({
            'month': f'{trend_year}-{trend_mon:02d}',
            'income': round(float(inc), 2),
            'expense': round(float(exp), 2)
        })
    
    return jsonify({
        'month': month,
        'total_income': round(float(total_income), 2),
        'total_expense': round(float(total_expense), 2),
        'net_profit': round(float(total_income) - float(total_expense), 2),
        'contract_ranking': [
            {'contract': c.to_dict() if c else None, 'amount': round(float(a or 0), 2)}
            for c, a in contract_income
        ],
        'trend': trend
    }), 200


@payments_bp.route('/contract/<int:contract_id>', methods=['GET'])
@jwt_required()
def get_contract_payments(contract_id):
    """获取合同关联的收付款记录"""
    payments = PaymentRecord.query.filter_by(contract_id=contract_id).order_by(
        PaymentRecord.payment_date.desc()
    ).all()
    return jsonify({
        'payments': [p.to_dict() for p in payments]
    }), 200
