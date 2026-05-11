"""
【第二次迭代】费用报销管理 API
作者: 郝益墨
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models import Expense, User, Approval
from app.decorators import require_permission
from app.services import AuditService

expenses_bp = Blueprint('expenses', __name__)


@expenses_bp.route('/', methods=['GET'])
@jwt_required()
def get_expenses():
    """获取报销列表（支持筛选）"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')
    category = request.args.get('category')
    user_id = request.args.get('user_id', type=int)
    month = request.args.get('month')  # 格式: 2025-05
    
    query = Expense.query
    
    # 权限控制：非管理员只能看自己的
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user.has_permission('all'):
        query = query.filter_by(user_id=current_user_id)
    elif user_id:
        query = query.filter_by(user_id=user_id)
    
    if status:
        query = query.filter_by(status=status)
    if category:
        query = query.filter_by(category=category)
    if month:
        try:
            year, mon = map(int, month.split('-'))
            query = query.filter(
                db.extract('year', Expense.created_at) == year,
                db.extract('month', Expense.created_at) == mon
            )
        except ValueError:
            pass
    
    pagination = query.order_by(Expense.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'expenses': [e.to_dict() for e in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@expenses_bp.route('/', methods=['POST'])
@jwt_required()
def create_expense():
    """创建报销单"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('title') or not data.get('amount'):
        return jsonify({'message': '请填写报销标题和金额', 'error': 'missing_fields'}), 400
    
    expense = Expense(
        user_id=current_user_id,
        title=data['title'],
        amount=data['amount'],
        category=data.get('category', 'other'),
        description=data.get('description', ''),
        attachments=data.get('attachments', []),
        status='pending'
    )
    
    db.session.add(expense)
    db.session.commit()
    
    AuditService.log_from_current_user(
        action='EXPENSE_CREATE',
        resource_type='expense',
        resource_id=expense.id,
        detail={'title': expense.title, 'amount': str(expense.amount)},
        status='success'
    )
    
    return jsonify({
        'message': '报销单已提交',
        'expense': expense.to_dict()
    }), 201


@expenses_bp.route('/<int:expense_id>', methods=['GET'])
@jwt_required()
def get_expense(expense_id):
    """获取报销单详情"""
    expense = Expense.query.get_or_404(expense_id)
    
    # 权限检查
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if expense.user_id != current_user_id and not current_user.has_permission('all'):
        return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    return jsonify({'expense': expense.to_dict()}), 200


@expenses_bp.route('/<int:expense_id>', methods=['PUT'])
@jwt_required()
def update_expense(expense_id):
    """更新报销单（仅提交人可修改未审批的）"""
    current_user_id = get_jwt_identity()
    expense = Expense.query.get_or_404(expense_id)
    
    # 权限检查：只能修改自己的，且状态为 draft/pending
    if expense.user_id != current_user_id:
        return jsonify({'message': '只能修改自己的报销单', 'error': 'forbidden'}), 403
    
    if expense.status not in ('draft', 'pending'):
        return jsonify({'message': '当前状态不允许修改', 'error': 'status_locked'}), 409
    
    data = request.get_json()
    allowed_fields = ['title', 'amount', 'category', 'description', 'attachments']
    for field in allowed_fields:
        if field in data:
            setattr(expense, field, data[field])
    
    db.session.commit()
    
    AuditService.log_from_current_user(
        action='EXPENSE_UPDATE',
        resource_type='expense',
        resource_id=expense_id,
        detail={'title': expense.title},
        status='success'
    )
    
    return jsonify({
        'message': '报销单已更新',
        'expense': expense.to_dict()
    }), 200


@expenses_bp.route('/<int:expense_id>/approve', methods=['POST'])
@jwt_required()
def approve_expense(expense_id):
    """审批通过报销单（管理员/财务权限）"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user.has_permission('all'):
        return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    expense = Expense.query.get_or_404(expense_id)
    expense.status = 'approved'
    db.session.commit()
    
    AuditService.log_from_current_user(
        action='EXPENSE_APPROVE',
        resource_type='expense',
        resource_id=expense_id,
        detail={'title': expense.title, 'amount': str(expense.amount)},
        status='success'
    )
    
    return jsonify({'message': '报销单已审批通过', 'expense': expense.to_dict()}), 200


@expenses_bp.route('/<int:expense_id>/reject', methods=['POST'])
@jwt_required()
def reject_expense(expense_id):
    """驳回报销单（管理员/财务权限）"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user.has_permission('all'):
        return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    expense = Expense.query.get_or_404(expense_id)
    expense.status = 'rejected'
    db.session.commit()
    
    AuditService.log_from_current_user(
        action='EXPENSE_REJECT',
        resource_type='expense',
        resource_id=expense_id,
        detail={'title': expense.title},
        status='success'
    )
    
    return jsonify({'message': '报销单已驳回', 'expense': expense.to_dict()}), 200


@expenses_bp.route('/<int:expense_id>/reimburse', methods=['POST'])
@jwt_required()
def reimburse_expense(expense_id):
    """标记已打款（管理员/财务权限）"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user.has_permission('all'):
        return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    expense = Expense.query.get_or_404(expense_id)
    expense.status = 'reimbursed'
    expense.reimbursed_at = datetime.utcnow()
    db.session.commit()
    
    AuditService.log_from_current_user(
        action='EXPENSE_REIMBURSE',
        resource_type='expense',
        resource_id=expense_id,
        detail={'title': expense.title, 'amount': str(expense.amount)},
        status='success'
    )
    
    return jsonify({'message': '已标记打款完成', 'expense': expense.to_dict()}), 200


@expenses_bp.route('/<int:expense_id>', methods=['DELETE'])
@jwt_required()
def delete_expense(expense_id):
    """删除报销单（仅提交人可删除未审批的）"""
    current_user_id = get_jwt_identity()
    expense = Expense.query.get_or_404(expense_id)
    
    if expense.user_id != current_user_id:
        current_user = User.query.get(current_user_id)
        if not current_user.has_permission('all'):
            return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    db.session.delete(expense)
    db.session.commit()
    
    AuditService.log_from_current_user(
        action='EXPENSE_DELETE',
        resource_type='expense',
        resource_id=expense_id,
        detail={'title': expense.title},
        status='success'
    )
    
    return jsonify({'message': '报销单已删除'}), 200


@expenses_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_expense_stats():
    """获取报销统计（按月份/类别聚合）"""
    current_user_id = get_jwt_identity()
    user_id = request.args.get('user_id', current_user_id, type=int)
    month = request.args.get('month', datetime.utcnow().strftime('%Y-%m'))
    
    current_user = User.query.get(current_user_id)
    if user_id != current_user_id and not current_user.has_permission('all'):
        return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    try:
        year, mon = map(int, month.split('-'))
    except ValueError:
        return jsonify({'message': '月份格式错误', 'error': 'invalid_month'}), 400
    
    # 按状态统计
    status_stats = db.session.query(
        Expense.status,
        db.func.count(Expense.id),
        db.func.sum(Expense.amount)
    ).filter(
        Expense.user_id == user_id,
        db.extract('year', Expense.created_at) == year,
        db.extract('month', Expense.created_at) == mon
    ).group_by(Expense.status).all()
    
    # 按类别统计
    category_stats = db.session.query(
        Expense.category,
        db.func.count(Expense.id),
        db.func.sum(Expense.amount)
    ).filter(
        Expense.user_id == user_id,
        db.extract('year', Expense.created_at) == year,
        db.extract('month', Expense.created_at) == mon
    ).group_by(Expense.category).all()
    
    total_amount = sum(float(s[2] or 0) for s in status_stats)
    
    return jsonify({
        'month': month,
        'total_amount': round(total_amount, 2),
        'by_status': [
            {'status': s[0], 'count': s[1], 'amount': round(float(s[2] or 0), 2)}
            for s in status_stats
        ],
        'by_category': [
            {'category': c[0], 'count': c[1], 'amount': round(float(c[2] or 0), 2)}
            for c in category_stats
        ]
    }), 200


@expenses_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_expense_categories():
    """获取报销类别选项"""
    categories = [
        {'value': 'travel', 'label': '差旅费'},
        {'value': 'office', 'label': '办公费'},
        {'value': 'entertainment', 'label': '招待费'},
        {'value': 'training', 'label': '培训费'},
        {'value': 'meal', 'label': '餐费'},
        {'value': 'transport', 'label': '交通费'},
        {'value': 'other', 'label': '其他'}
    ]
    return jsonify({'categories': categories}), 200
