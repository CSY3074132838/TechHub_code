"""
【第二次迭代】考勤与工时管理 API
作者: 于然
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date, timedelta
import calendar
from collections import defaultdict
from app import db
from app.models import Attendance, LeaveBalance, WorkTimeRecord, User, Approval, ApprovalNode, Role, Project
from app.decorators import require_permission
from app.services import AuditService

attendance_bp = Blueprint('attendance', __name__)


# ==================== 辅助函数 ====================

def _find_managers():
    """查找系统中的总经理/副总经理用户"""
    managers = []
    for role_name in {'super_admin', 'deputy_general_manager'}:
        role = Role.query.filter_by(name=role_name).first()
        if role and role.users:
            managers.extend(role.users)
    seen = set()
    unique_managers = []
    for m in managers:
        if m.id not in seen:
            seen.add(m.id)
            unique_managers.append(m)
    return unique_managers


def _create_leave_approval(user_id, leave_type, start_date, end_date, days, reason):
    """创建请假审批并返回审批对象"""
    leave_type_map = {
        'annual': '年假',
        'sick': '病假',
        'personal': '事假',
        'marriage': '婚假',
        'maternity': '产假'
    }
    type_label = leave_type_map.get(leave_type, leave_type)
    title = f'【请假申请】{type_label} - {days}天'
    description = f'请假类型：{type_label}\n开始日期：{start_date}\n结束日期：{end_date}\n请假天数：{days}天\n请假原因：{reason}'
    
    approval = Approval(
        title=title,
        approval_type='leave',
        description=description,
        applicant_id=user_id,
        attachments=[]
    )
    db.session.add(approval)
    db.session.commit()
    
    # 创建审批链：直属上级 -> 部门负责人 -> 高管
    nodes = []
    nodes.append(ApprovalNode(
        approval_id=approval.id,
        node_name='直属上级审批',
        status='pending',
        order=1
    ))
    nodes.append(ApprovalNode(
        approval_id=approval.id,
        node_name='部门负责人审批',
        status='pending',
        order=2
    ))
    managers = _find_managers()
    if managers:
        nodes.append(ApprovalNode(
            approval_id=approval.id,
            node_name='高管审批',
            handler_id=managers[0].id,
            status='pending',
            order=3
        ))
    else:
        nodes.append(ApprovalNode(
            approval_id=approval.id,
            node_name='高管审批',
            status='pending',
            order=3
        ))
    
    for node in nodes:
        db.session.add(node)
    db.session.flush()
    approval.current_node_id = nodes[0].id
    db.session.commit()
    
    return approval


def _update_leave_approval(approval_id, leave_type, start_date, end_date, days, reason):
    """更新请假审批内容"""
    approval = Approval.query.get(approval_id)
    if not approval:
        return None
    
    leave_type_map = {
        'annual': '年假',
        'sick': '病假',
        'personal': '事假',
        'marriage': '婚假',
        'maternity': '产假'
    }
    type_label = leave_type_map.get(leave_type, leave_type)
    approval.title = f'【请假申请】{type_label} - {days}天'
    approval.description = f'请假类型：{type_label}\n开始日期：{start_date}\n结束日期：{end_date}\n请假天数：{days}天\n请假原因：{reason}'
    db.session.commit()
    return approval


# ==================== 【第二次迭代】考勤记录 API ====================

@attendance_bp.route('/records', methods=['GET'])
@jwt_required()
def get_attendance_records():
    """【第二次迭代】获取考勤记录列表（支持按用户、日期范围筛选）"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    user_id = request.args.get('user_id', type=int)
    month = request.args.get('month')  # 格式: 2025-05
    
    query = Attendance.query
    
    # 权限控制：非管理员只能看自己的
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user.has_permission('all') and not current_user.has_permission('user_manage'):
        query = query.filter_by(user_id=current_user_id)
    elif user_id:
        query = query.filter_by(user_id=user_id)
    
    if month:
        try:
            year, mon = map(int, month.split('-'))
            query = query.filter(
                db.extract('year', Attendance.work_date) == year,
                db.extract('month', Attendance.work_date) == mon
            )
        except ValueError:
            pass
    
    pagination = query.order_by(Attendance.work_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'records': [r.to_dict() for r in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@attendance_bp.route('/records', methods=['POST'])
@jwt_required()
def create_attendance_record():
    """【第二次迭代】填报考勤/工时记录"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('work_date'):
        return jsonify({'message': '请提供工作日期', 'error': 'missing_date'}), 400
    
    try:
        work_date = datetime.strptime(data['work_date'], '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return jsonify({'message': '日期格式错误', 'error': 'invalid_date'}), 400
    
    record = Attendance(
        user_id=current_user_id,
        work_date=work_date,
        check_in=data.get('check_in'),
        check_out=data.get('check_out'),
        work_hours=data.get('work_hours', 0),
        overtime_hours=data.get('overtime_hours', 0),
        status=data.get('status', 'normal'),
        remark=data.get('remark', '')
    )
    db.session.add(record)
    db.session.commit()
    
    return jsonify({
        'message': '考勤记录已保存',
        'record': record.to_dict()
    }), 201


# ==================== 一键打卡/下班 API ====================

@attendance_bp.route('/check-in', methods=['POST'])
@jwt_required()
def check_in():
    """一键上班打卡"""
    current_user_id = get_jwt_identity()
    today = date.today()
    now = datetime.now()
    
    # 查找今天是否已有打卡记录
    record = Attendance.query.filter_by(user_id=current_user_id, work_date=today).first()
    
    if record and record.check_in:
        return jsonify({'message': '今天已经打卡了', 'record': record.to_dict()}), 200
    
    if not record:
        record = Attendance(
            user_id=current_user_id,
            work_date=today,
            status='normal'
        )
        db.session.add(record)
    
    record.check_in = now
    # 判断迟到（假设9:30后算迟到）
    late_threshold = now.replace(hour=9, minute=30, second=0, microsecond=0)
    if now > late_threshold:
        record.status = 'late'
    
    db.session.commit()
    
    return jsonify({
        'message': '打卡成功',
        'record': record.to_dict()
    }), 201


@attendance_bp.route('/check-out', methods=['POST'])
@jwt_required()
def check_out():
    """一键下班打卡"""
    current_user_id = get_jwt_identity()
    today = date.today()
    now = datetime.now()
    
    record = Attendance.query.filter_by(user_id=current_user_id, work_date=today).first()
    
    if not record:
        return jsonify({'message': '今天尚未打卡，请先打卡上班', 'error': 'not_checked_in'}), 400
    
    if record.check_out:
        return jsonify({'message': '今天已经下班打卡了', 'record': record.to_dict()}), 200
    
    record.check_out = now
    
    # 计算工作时长
    if record.check_in:
        work_duration = (now - record.check_in).total_seconds() / 3600
        record.work_hours = round(work_duration, 2)
        # 计算加班（超过8小时算加班）
        if work_duration > 8:
            record.overtime_hours = round(work_duration - 8, 2)
    
    # 判断早退（假设18:00前算早退）
    early_threshold = now.replace(hour=18, minute=0, second=0, microsecond=0)
    if now < early_threshold and record.status != 'late':
        record.status = 'early'
    
    db.session.commit()
    
    return jsonify({
        'message': '下班打卡成功',
        'record': record.to_dict()
    }), 200


# ==================== 考勤统计 API ====================

@attendance_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_attendance_stats():
    """【第二次迭代】获取考勤与工时统计（按月）"""
    current_user_id = get_jwt_identity()
    user_id = request.args.get('user_id', current_user_id, type=int)
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    
    try:
        year, mon = map(int, month.split('-'))
    except ValueError:
        return jsonify({'message': '月份格式错误', 'error': 'invalid_month'}), 400
    
    # 权限检查
    current_user = User.query.get(current_user_id)
    if user_id != current_user_id and not current_user.has_permission('all'):
        return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    # ===== 1. 考勤记录统计（打卡数据） =====
    attendance_records = Attendance.query.filter(
        Attendance.user_id == user_id,
        db.extract('year', Attendance.work_date) == year,
        db.extract('month', Attendance.work_date) == mon
    ).all()
    
    late_days = sum(1 for r in attendance_records if r.status == 'late')
    early_days = sum(1 for r in attendance_records if r.status == 'early')
    absent_days = sum(1 for r in attendance_records if r.status == 'absent')
    
    # ===== 2. 工时记录统计（项目工时填报数据） =====
    work_records = WorkTimeRecord.query.filter(
        WorkTimeRecord.user_id == user_id,
        db.extract('year', WorkTimeRecord.work_date) == year,
        db.extract('month', WorkTimeRecord.work_date) == mon
    ).all()
    
    total_hours = sum(float(r.hours or 0) for r in work_records)
    work_days = len(set(r.work_date for r in work_records))
    
    # 加班工时 = 单日超过8小时的部分累计
    daily_hours = defaultdict(float)
    for r in work_records:
        daily_hours[r.work_date] += float(r.hours or 0)
    total_overtime = sum(max(0, h - 8) for h in daily_hours.values())
    
    # ===== 3. 工时达成率计算 =====
    _, days_in_month = calendar.monthrange(year, mon)
    standard_workdays = 0
    for day in range(1, days_in_month + 1):
        if calendar.weekday(year, mon, day) < 5:
            standard_workdays += 1
    
    standard_monthly_hours = standard_workdays * 8
    completion_rate = round((total_hours / standard_monthly_hours * 100), 1) if standard_monthly_hours > 0 else 0
    remaining_hours = max(0, standard_monthly_hours - total_hours)
    avg_daily_hours = round(total_hours / work_days, 1) if work_days > 0 else 0
    
    return jsonify({
        'month': month,
        'total_hours': round(total_hours, 2),
        'total_overtime': round(total_overtime, 2),
        'work_days': work_days,
        'late_days': late_days,
        'early_days': early_days,
        'absent_days': absent_days,
        'standard_workdays': standard_workdays,
        'standard_monthly_hours': standard_monthly_hours,
        'completion_rate': completion_rate,
        'remaining_hours': remaining_hours,
        'avg_daily_hours': avg_daily_hours
    }), 200


# ==================== 假期余额 API ====================

@attendance_bp.route('/leave-balances', methods=['GET'])
@jwt_required()
def get_leave_balances():
    """【第二次迭代】获取假期余额"""
    current_user_id = get_jwt_identity()
    user_id = request.args.get('user_id', current_user_id, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    
    # 权限检查
    current_user = User.query.get(current_user_id)
    if user_id != current_user_id and not current_user.has_permission('all'):
        return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    balances = LeaveBalance.query.filter_by(user_id=user_id, year=year).all()
    
    # 如果没有记录，初始化默认值
    if not balances:
        default_types = [
            ('annual', 10),
            ('sick', 15),
            ('personal', 7),
        ]
        for leave_type, days in default_types:
            balance = LeaveBalance(
                user_id=user_id,
                leave_type=leave_type,
                total_days=days,
                used_days=0,
                year=year
            )
            db.session.add(balance)
        db.session.commit()
        balances = LeaveBalance.query.filter_by(user_id=user_id, year=year).all()
    
    return jsonify({
        'balances': [b.to_dict() for b in balances],
        'year': year
    }), 200


@attendance_bp.route('/leave-balances', methods=['POST'])
@require_permission('user_manage')
def create_leave_balance():
    """【第二次迭代】HR初始化/调整假期余额（仅管理员）"""
    data = request.get_json()
    if not data:
        return jsonify({'message': '请提供数据', 'error': 'missing_data'}), 400
    
    user_id = data.get('user_id')
    leave_type = data.get('leave_type')
    total_days = data.get('total_days', 0)
    year = data.get('year', datetime.now().year)
    
    if not user_id or not leave_type:
        return jsonify({'message': '用户ID和假期类型不能为空', 'error': 'missing_fields'}), 400
    
    balance = LeaveBalance.query.filter_by(user_id=user_id, leave_type=leave_type, year=year).first()
    if balance:
        balance.total_days = total_days
    else:
        balance = LeaveBalance(
            user_id=user_id,
            leave_type=leave_type,
            total_days=total_days,
            used_days=0,
            year=year
        )
        db.session.add(balance)
    
    db.session.commit()
    
    return jsonify({
        'message': '假期余额已更新',
        'balance': balance.to_dict()
    }), 200


# ==================== 工时记录 API ====================

@attendance_bp.route('/work-time', methods=['GET'])
@jwt_required()
def get_work_time_records():
    """【第二次迭代】获取工时记录列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    user_id = request.args.get('user_id', type=int)
    project_id = request.args.get('project_id', type=int)
    month = request.args.get('month')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    query = WorkTimeRecord.query
    
    # 权限控制
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user.has_permission('all'):
        query = query.filter_by(user_id=current_user_id)
    elif user_id:
        query = query.filter_by(user_id=user_id)
    
    if project_id:
        query = query.filter_by(project_id=project_id)
    
    if month:
        try:
            year, mon = map(int, month.split('-'))
            query = query.filter(
                db.extract('year', WorkTimeRecord.work_date) == year,
                db.extract('month', WorkTimeRecord.work_date) == mon
            )
        except ValueError:
            pass
    
    # 按日期范围搜索
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(WorkTimeRecord.work_date >= from_date)
        except ValueError:
            pass
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(WorkTimeRecord.work_date <= to_date)
        except ValueError:
            pass
    
    pagination = query.order_by(WorkTimeRecord.work_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'records': [r.to_dict() for r in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@attendance_bp.route('/work-time', methods=['POST'])
@jwt_required()
def create_work_time_record():
    """【第二次迭代】填报工时记录（关联项目/任务）"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('work_date') or not data.get('hours'):
        return jsonify({'message': '请提供工作日期和工时', 'error': 'missing_fields'}), 400
    
    try:
        work_date = datetime.strptime(data['work_date'], '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return jsonify({'message': '日期格式错误，应为 YYYY-MM-DD', 'error': 'invalid_date'}), 400
    
    record = WorkTimeRecord(
        user_id=current_user_id,
        project_id=data.get('project_id'),
        task_id=data.get('task_id'),
        work_date=work_date,
        hours=data['hours'],
        description=data.get('description', '')
    )
    db.session.add(record)
    db.session.commit()
    
    return jsonify({
        'message': '工时记录已保存',
        'record': record.to_dict()
    }), 201


@attendance_bp.route('/work-time/<int:record_id>', methods=['PUT'])
@jwt_required()
def update_work_time_record(record_id):
    """更新工时记录"""
    current_user_id = get_jwt_identity()
    record = WorkTimeRecord.query.get_or_404(record_id)
    
    # 只能修改自己的记录，管理员除外
    if record.user_id != current_user_id:
        current_user = User.query.get(current_user_id)
        if not current_user.has_permission('all'):
            return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    data = request.get_json()
    
    if 'work_date' in data:
        try:
            record.work_date = datetime.strptime(data['work_date'], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return jsonify({'message': '日期格式错误', 'error': 'invalid_date'}), 400
    if 'project_id' in data:
        record.project_id = data['project_id']
    if 'hours' in data:
        record.hours = data['hours']
    if 'description' in data:
        record.description = data['description']
    
    db.session.commit()
    
    return jsonify({
        'message': '工时记录已更新',
        'record': record.to_dict()
    }), 200


@attendance_bp.route('/work-time/<int:record_id>', methods=['DELETE'])
@jwt_required()
def delete_work_time_record(record_id):
    """删除工时记录"""
    current_user_id = get_jwt_identity()
    record = WorkTimeRecord.query.get_or_404(record_id)
    
    # 只能删除自己的记录，管理员除外
    if record.user_id != current_user_id:
        current_user = User.query.get(current_user_id)
        if not current_user.has_permission('all'):
            return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    db.session.delete(record)
    db.session.commit()
    
    return jsonify({'message': '工时记录已删除'}), 200


@attendance_bp.route('/work-time/stats', methods=['GET'])
@jwt_required()
def get_work_time_stats():
    """【第二次迭代】获取工时统计（按项目/月份聚合）"""
    current_user_id = get_jwt_identity()
    user_id = request.args.get('user_id', current_user_id, type=int)
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    
    # 权限检查
    current_user = User.query.get(current_user_id)
    if user_id != current_user_id and not current_user.has_permission('all'):
        return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    try:
        year, mon = map(int, month.split('-'))
    except ValueError:
        return jsonify({'message': '月份格式错误', 'error': 'invalid_month'}), 400
    
    # 按项目统计工时
    from sqlalchemy import func
    project_stats = db.session.query(
        WorkTimeRecord.project_id,
        func.sum(WorkTimeRecord.hours),
        func.count(WorkTimeRecord.id)
    ).filter(
        WorkTimeRecord.user_id == user_id,
        db.extract('year', WorkTimeRecord.work_date) == year,
        db.extract('month', WorkTimeRecord.work_date) == mon
    ).group_by(WorkTimeRecord.project_id).all()
    
    total_hours = sum(float(s[1] or 0) for s in project_stats)
    
    # 查询项目名称并组装结果
    result_by_project = []
    for s in project_stats:
        project_id = s[0]
        project_name = '未关联项目'
        if project_id:
            project = Project.query.get(project_id)
            if project:
                project_name = project.name
        result_by_project.append({
            'project_id': project_id,
            'project_name': project_name,
            'hours': round(float(s[1] or 0), 2),
            'record_count': s[2]
        })
    
    return jsonify({
        'month': month,
        'total_hours': round(total_hours, 2),
        'by_project': result_by_project
    }), 200


# ==================== 请假记录 API ====================

@attendance_bp.route('/leaves', methods=['GET'])
@jwt_required()
def get_leave_records():
    """获取请假记录列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    user_id = request.args.get('user_id', type=int)
    month = request.args.get('month')
    leave_type = request.args.get('leave_type')
    status = request.args.get('status')
    
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # 查询关联了请假审批的记录
    query = db.session.query(Approval).filter(Approval.approval_type == 'leave')
    
    # 权限控制
    if not current_user.has_permission('all'):
        query = query.filter_by(applicant_id=current_user_id)
    elif user_id:
        query = query.filter_by(applicant_id=user_id)
    
    if month:
        try:
            year, mon = map(int, month.split('-'))
            query = query.filter(
                db.extract('year', Approval.created_at) == year,
                db.extract('month', Approval.created_at) == mon
            )
        except ValueError:
            pass
    
    if status:
        query = query.filter(Approval.status == status)
    
    query = query.order_by(Approval.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    records = []
    for approval in pagination.items:
        # 从审批描述中解析请假信息
        desc_lines = approval.description.split('\n') if approval.description else []
        leave_info = {}
        for line in desc_lines:
            if '：' in line:
                key, val = line.split('：', 1)
                leave_info[key] = val
        
        records.append({
            'id': approval.id,
            'title': approval.title,
            'leave_type': leave_info.get('请假类型', ''),
            'start_date': leave_info.get('开始日期', ''),
            'end_date': leave_info.get('结束日期', ''),
            'days': leave_info.get('请假天数', ''),
            'reason': leave_info.get('请假原因', ''),
            'status': approval.status,
            'applicant': approval.applicant.to_dict() if approval.applicant else None,
            'created_at': approval.created_at.isoformat() if approval.created_at else None,
            'approval_id': approval.id
        })
    
    return jsonify({
        'records': records,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@attendance_bp.route('/leaves', methods=['POST'])
@jwt_required()
def create_leave_record():
    """创建请假申请（同步创建审批）"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'message': '请提供请假信息', 'error': 'missing_data'}), 400
    
    leave_type = data.get('leave_type')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    days = data.get('days')
    reason = data.get('reason', '')
    
    if not all([leave_type, start_date, end_date, days]):
        return jsonify({'message': '请填写完整的请假信息', 'error': 'missing_fields'}), 400
    
    # 检查假期余额
    year = datetime.strptime(start_date, '%Y-%m-%d').year if start_date else datetime.now().year
    balance = LeaveBalance.query.filter_by(user_id=current_user_id, leave_type=leave_type, year=year).first()
    
    if balance:
        remaining = float(balance.total_days or 0) - float(balance.used_days or 0)
        if remaining < float(days):
            return jsonify({
                'message': f'假期余额不足，剩余 {remaining} 天，申请 {days} 天',
                'error': 'insufficient_balance'
            }), 400
    
    # 创建审批
    approval = _create_leave_approval(current_user_id, leave_type, start_date, end_date, days, reason)
    
    # 扣除假期余额（审批通过后实际扣除，这里先预占）
    # 实际扣除在审批通过时处理
    
    return jsonify({
        'message': '请假申请已提交，请等待审批',
        'approval': approval.to_dict(include_chain=True)
    }), 201


@attendance_bp.route('/leaves/<int:leave_id>', methods=['PUT'])
@jwt_required()
def update_leave_record(leave_id):
    """更新请假申请（同步更新审批内容）"""
    current_user_id = get_jwt_identity()
    approval = Approval.query.get_or_404(leave_id)
    
    # 只能修改自己的请假
    if approval.applicant_id != current_user_id:
        current_user = User.query.get(current_user_id)
        if not current_user.has_permission('all'):
            return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    # 只能修改待审批的请假
    if approval.status != 'pending':
        return jsonify({'message': '只能修改待审批的请假申请', 'error': 'cannot_modify'}), 400
    
    data = request.get_json()
    leave_type = data.get('leave_type')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    days = data.get('days')
    reason = data.get('reason', '')
    
    if not all([leave_type, start_date, end_date, days]):
        return jsonify({'message': '请填写完整的请假信息', 'error': 'missing_fields'}), 400
    
    # 更新审批内容
    _update_leave_approval(leave_id, leave_type, start_date, end_date, days, reason)
    
    return jsonify({
        'message': '请假申请已更新',
        'approval': approval.to_dict(include_chain=True)
    }), 200


@attendance_bp.route('/leaves/<int:leave_id>', methods=['DELETE'])
@jwt_required()
def delete_leave_record(leave_id):
    """删除请假申请（同步删除审批）"""
    current_user_id = get_jwt_identity()
    approval = Approval.query.get_or_404(leave_id)
    
    # 只能删除自己的请假
    if approval.applicant_id != current_user_id:
        current_user = User.query.get(current_user_id)
        if not current_user.has_permission('all'):
            return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    # 只能删除待审批的请假
    if approval.status != 'pending':
        return jsonify({'message': '只能删除待审批的请假申请', 'error': 'cannot_delete'}), 400
    
    # 删除关联的审批节点
    ApprovalNode.query.filter_by(approval_id=approval.id).delete()
    db.session.delete(approval)
    db.session.commit()
    
    return jsonify({'message': '请假申请已删除'}), 200


# ==================== 高管考勤数据 API ====================

@attendance_bp.route('/manager/overview', methods=['GET'])
@jwt_required()
def get_manager_overview():
    """获取高管视角的考勤概览数据"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user.has_permission('all'):
        return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    try:
        year, mon = map(int, month.split('-'))
    except ValueError:
        return jsonify({'message': '月份格式错误', 'error': 'invalid_month'}), 400
    
    # 1. 所有员工打卡情况
    users = User.query.filter_by(is_active=True).all()
    employee_stats = []
    
    for user in users:
        # 打卡记录
        attendance = Attendance.query.filter(
            Attendance.user_id == user.id,
            db.extract('year', Attendance.work_date) == year,
            db.extract('month', Attendance.work_date) == mon
        ).all()
        
        # 工时记录
        work_records = WorkTimeRecord.query.filter(
            WorkTimeRecord.user_id == user.id,
            db.extract('year', WorkTimeRecord.work_date) == year,
            db.extract('month', WorkTimeRecord.work_date) == mon
        ).all()
        
        # 请假记录
        leaves = Approval.query.filter(
            Approval.applicant_id == user.id,
            Approval.approval_type == 'leave',
            db.extract('year', Approval.created_at) == year,
            db.extract('month', Approval.created_at) == mon
        ).all()
        
        total_work_hours = sum(float(r.hours or 0) for r in work_records)
        
        employee_stats.append({
            'user_id': user.id,
            'real_name': user.real_name,
            'department': user.department,
            'check_in_days': len(attendance),
            'late_days': sum(1 for a in attendance if a.status == 'late'),
            'early_days': sum(1 for a in attendance if a.status == 'early'),
            'total_work_hours': round(total_work_hours, 2),
            'leave_days': sum(float(l.title.split('-')[-1].replace('天', '').strip()) for l in leaves if '天' in l.title),
            'leave_count': len(leaves)
        })
    
    # 2. 所有员工工时分布（用于饼图）
    from sqlalchemy import func
    all_work_stats = db.session.query(
        WorkTimeRecord.project_id,
        func.sum(WorkTimeRecord.hours),
        func.count(WorkTimeRecord.id)
    ).filter(
        db.extract('year', WorkTimeRecord.work_date) == year,
        db.extract('month', WorkTimeRecord.work_date) == mon
    ).group_by(WorkTimeRecord.project_id).all()
    
    project_distribution = []
    for s in all_work_stats:
        project_id = s[0]
        project_name = '未关联项目'
        if project_id:
            project = Project.query.get(project_id)
            if project:
                project_name = project.name
        project_distribution.append({
            'project_id': project_id,
            'project_name': project_name,
            'hours': round(float(s[1] or 0), 2),
            'record_count': s[2]
        })
    
    # 3. 所有员工本月总工时
    total_all_hours = sum(float(s[1] or 0) for s in all_work_stats)
    
    return jsonify({
        'month': month,
        'employee_stats': employee_stats,
        'project_distribution': project_distribution,
        'total_all_hours': round(total_all_hours, 2)
    }), 200
