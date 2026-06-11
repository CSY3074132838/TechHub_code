"""
【第二次迭代】费用报销管理 API
作者: 郝益墨

【第三次迭代郝益墨负责】
(2) 费用报销面板中的本月记录，筛选框增加按人名筛选
(3) admin账号中，本月报销金额显示全部报销金额，本月报销类别分布显示全部报销情况
(4) 报销记录界面，可点击查看每一个报销的详情内容
(5) 新建报销中，加入上传附件功能（图片、文档）
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename
from app import db
from app.models import Expense, User, Approval, Activity
from app.decorators import require_permission
from app.services import AuditService, NotificationService
from app.api.approvals import create_approval_chain

expenses_bp = Blueprint('expenses', __name__)

# 允许上传的文件类型
ALLOWED_EXTENSIONS = {
    'image': {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'},
    'document': {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt'}
}


def allowed_file(filename):
    """检查文件类型是否允许上传"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS['image'] or ext in ALLOWED_EXTENSIONS['document']


def get_file_type(filename):
    """获取文件类型（image/document）"""
    if '.' not in filename:
        return 'other'
    ext = filename.rsplit('.', 1)[1].lower()
    if ext in ALLOWED_EXTENSIONS['image']:
        return 'image'
    if ext in ALLOWED_EXTENSIONS['document']:
        return 'document'
    return 'other'


# 【第三次迭代郝益墨负责】(3) 高管角色列表：可查看全部人员报销
# admin账号中，本月报销金额显示全部报销金额，本月报销类别分布显示全部报销情况
FINANCE_ROLES = {'super_admin', 'deputy_general_manager', 'finance_director'}


def _is_finance_manager(user):
    """判断用户是否为财务高管（可查看全部报销）
    【第三次迭代郝益墨负责】(3) admin账号显示全部报销统计"""
    return any(r.name in FINANCE_ROLES for r in user.roles)


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
    
    # 权限控制：高管角色可看全部，普通用户只能看自己的
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not _is_finance_manager(current_user):
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
    
    # 【修复】同步检查：如果 expense 关联了 approval，但状态不一致，自动同步
    expenses_data = []
    for e in pagination.items:
        if e.approval_id:
            approval = Approval.query.get(e.approval_id)
            if approval and approval.status != e.status:
                # 审批中心状态与费用报销状态不一致，以审批中心为准
                if approval.status in ('approved', 'rejected'):
                    e.status = approval.status
                    db.session.commit()
        expenses_data.append(e.to_dict())
    
    return jsonify({
        'expenses': expenses_data,
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
    db.session.flush()
    
    # 【新增】同步创建审批中心审批单
    applicant = User.query.get(current_user_id)
    approval = Approval(
        title=data['title'],
        approval_type='expense',
        description=data.get('description', ''),
        amount=data['amount'],
        applicant_id=current_user_id,
        attachments=data.get('attachments', []),
        is_over_budget=data.get('is_over_budget', False)
    )
    db.session.add(approval)
    db.session.flush()
    
    # 关联审批单到报销记录
    expense.approval_id = approval.id
    
    # 创建审批链
    create_approval_chain(approval, 'expense', applicant, data)
    
    db.session.commit()
    
    # 记录活动
    activity = Activity(
        activity_type='approval_submitted',
        title=f'提交了报销审批 "{approval.title}"',
        user_id=current_user_id
    )
    db.session.add(activity)
    db.session.commit()
    
    # 发送通知
    NotificationService.notify_approval_submitted(approval)
    
    AuditService.log_from_current_user(
        action='EXPENSE_CREATE',
        resource_type='expense',
        resource_id=expense.id,
        detail={'title': expense.title, 'amount': str(expense.amount), 'approval_id': approval.id},
        status='success'
    )
    
    return jsonify({
        'message': '报销单已提交，已同步到审批中心',
        'expense': expense.to_dict(),
        'approval': approval.to_dict(include_chain=True)
    }), 201


@expenses_bp.route('/<int:expense_id>', methods=['GET'])
@jwt_required()
def get_expense(expense_id):
    """获取报销单详情"""
    expense = Expense.query.get_or_404(expense_id)
    
    # 权限检查：本人或高管可查看
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if expense.user_id != current_user_id and not _is_finance_manager(current_user):
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
    """审批通过报销单（管理员/财务权限）
    【新增】同步更新关联的审批中心审批单状态"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not _is_finance_manager(current_user):
        return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    expense = Expense.query.get_or_404(expense_id)
    expense.status = 'approved'
    db.session.commit()
    
    # 【新增】同步更新审批中心审批单状态
    if expense.approval_id:
        approval = Approval.query.get(expense.approval_id)
        if approval and approval.status == 'pending':
            approval.status = 'approved'
            approval.processor_id = current_user_id
            approval.processed_at = datetime.now()
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
    """驳回报销单（管理员/财务权限）
    【新增】同步更新关联的审批中心审批单状态"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not _is_finance_manager(current_user):
        return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    expense = Expense.query.get_or_404(expense_id)
    expense.status = 'rejected'
    db.session.commit()
    
    # 【新增】同步更新审批中心审批单状态
    if expense.approval_id:
        approval = Approval.query.get(expense.approval_id)
        if approval and approval.status == 'pending':
            approval.status = 'rejected'
            approval.processor_id = current_user_id
            approval.processed_at = datetime.now()
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
    
    if not _is_finance_manager(current_user):
        return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    expense = Expense.query.get_or_404(expense_id)
    expense.status = 'reimbursed'
    expense.reimbursed_at = datetime.now()
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
        if not _is_finance_manager(current_user):
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
    """【第三次迭代郝益墨负责】(3) 获取报销统计（按月份/类别聚合）
    高管角色查看全部人员统计，普通用户只看自己的
    admin账号中，本月报销金额显示全部报销金额，本月报销类别分布显示全部报销情况
    """
    current_user_id = get_jwt_identity()
    user_id = request.args.get('user_id', type=int)
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    
    current_user = User.query.get(current_user_id)
    is_manager = _is_finance_manager(current_user)
    
    # 权限检查：非高管且指定了其他用户ID
    if user_id and user_id != current_user_id and not is_manager:
        return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    try:
        year, mon = map(int, month.split('-'))
    except ValueError:
        return jsonify({'message': '月份格式错误', 'error': 'invalid_month'}), 400
    
    # 构建基础查询条件
    base_filters = [
        db.extract('year', Expense.created_at) == year,
        db.extract('month', Expense.created_at) == mon
    ]
    
    # 非高管只能看自己的
    if not is_manager:
        base_filters.append(Expense.user_id == current_user_id)
    elif user_id:
        base_filters.append(Expense.user_id == user_id)
    
    # 按状态统计
    status_query = db.session.query(
        Expense.status,
        db.func.count(Expense.id),
        db.func.sum(Expense.amount)
    ).filter(*base_filters).group_by(Expense.status)
    status_stats = status_query.all()
    
    # 按类别统计
    category_query = db.session.query(
        Expense.category,
        db.func.count(Expense.id),
        db.func.sum(Expense.amount)
    ).filter(*base_filters).group_by(Expense.category)
    category_stats = category_query.all()
    
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


@expenses_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_attachment():
    """【第三次迭代郝益墨负责】(5) 上传报销附件（图片/文档）"""
    current_user_id = get_jwt_identity()
    
    if 'file' not in request.files:
        return jsonify({'message': '未找到文件', 'error': 'no_file'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': '文件名为空', 'error': 'empty_filename'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({
            'message': '不支持的文件类型，仅允许图片(png/jpg/jpeg/gif/bmp/webp)和文档(pdf/doc/docx/xls/xlsx/ppt/pptx/txt)',
            'error': 'invalid_file_type'
        }), 400
    
    try:
        # 生成唯一文件名
        ext = file.filename.rsplit('.', 1)[1].lower()
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        
        # 按日期创建子目录
        today = datetime.now().strftime('%Y%m%d')
        upload_dir = os.path.join(current_app.root_path, '..', 'uploads', 'expenses', today)
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        filepath = os.path.join(upload_dir, unique_name)
        file.save(filepath)
        
        # 返回文件URL
        file_url = f"/uploads/expenses/{today}/{unique_name}"
        
        return jsonify({
            'message': '上传成功',
            'file': {
                'name': secure_filename(file.filename),
                'url': file_url,
                'type': get_file_type(file.filename),
                'size': os.path.getsize(filepath)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'上传失败: {str(e)}', 'error': 'upload_failed'}), 500
