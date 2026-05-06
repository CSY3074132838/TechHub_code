"""
【第二次迭代】考勤与工时管理 API
作者: 于然
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date
from app import db
from app.models import Attendance, LeaveBalance, WorkTimeRecord, User
from app.decorators import require_permission
from app.services import AuditService

attendance_bp = Blueprint('attendance', __name__)


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
    
    record = Attendance(
        user_id=current_user_id,
        work_date=data['work_date'],
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


@attendance_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_attendance_stats():
    """【第二次迭代】获取考勤统计（按月）"""
    current_user_id = get_jwt_identity()
    user_id = request.args.get('user_id', current_user_id, type=int)
    month = request.args.get('month', datetime.utcnow().strftime('%Y-%m'))
    
    try:
        year, mon = map(int, month.split('-'))
    except ValueError:
        return jsonify({'message': '月份格式错误', 'error': 'invalid_month'}), 400
    
    # 权限检查
    current_user = User.query.get(current_user_id)
    if user_id != current_user_id and not current_user.has_permission('all'):
        return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    records = Attendance.query.filter(
        Attendance.user_id == user_id,
        db.extract('year', Attendance.work_date) == year,
        db.extract('month', Attendance.work_date) == mon
    ).all()
    
    total_days = len(records)
    total_hours = sum(float(r.work_hours or 0) for r in records)
    total_overtime = sum(float(r.overtime_hours or 0) for r in records)
    late_days = sum(1 for r in records if r.status == 'late')
    early_days = sum(1 for r in records if r.status == 'early')
    absent_days = sum(1 for r in records if r.status == 'absent')
    
    return jsonify({
        'month': month,
        'total_days': total_days,
        'total_hours': round(total_hours, 2),
        'total_overtime': round(total_overtime, 2),
        'late_days': late_days,
        'early_days': early_days,
        'absent_days': absent_days
    }), 200


# ==================== 【第二次迭代】假期余额 API ====================

@attendance_bp.route('/leave-balances', methods=['GET'])
@jwt_required()
def get_leave_balances():
    """【第二次迭代】获取假期余额"""
    current_user_id = get_jwt_identity()
    user_id = request.args.get('user_id', current_user_id, type=int)
    year = request.args.get('year', datetime.utcnow().year, type=int)
    
    # 权限检查
    current_user = User.query.get(current_user_id)
    if user_id != current_user_id and not current_user.has_permission('all'):
        return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    balances = LeaveBalance.query.filter_by(user_id=user_id, year=year).all()
    
    # 如果没有记录，初始化默认值
    if not balances:
        default_types = [
            ('annual', 5),    # 年假默认5天
            ('sick', 10),     # 病假默认10天
            ('personal', 3),  # 事假默认3天
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
    year = data.get('year', datetime.utcnow().year)
    
    if not user_id or not leave_type:
        return jsonify({'message': '用户ID和假期类型不能为空', 'error': 'missing_fields'}), 400
    
    # 查找是否已存在
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


# ==================== 【第二次迭代】工时记录 API（关联项目/任务） ====================

@attendance_bp.route('/work-time', methods=['GET'])
@jwt_required()
def get_work_time_records():
    """【第二次迭代】获取工时记录列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    user_id = request.args.get('user_id', type=int)
    project_id = request.args.get('project_id', type=int)
    month = request.args.get('month')
    
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
    
    record = WorkTimeRecord(
        user_id=current_user_id,
        project_id=data.get('project_id'),
        task_id=data.get('task_id'),
        work_date=data['work_date'],
        hours=data['hours'],
        description=data.get('description', '')
    )
    db.session.add(record)
    db.session.commit()
    
    return jsonify({
        'message': '工时记录已保存',
        'record': record.to_dict()
    }), 201


@attendance_bp.route('/work-time/stats', methods=['GET'])
@jwt_required()
def get_work_time_stats():
    """【第二次迭代】获取工时统计（按项目/月份聚合）"""
    current_user_id = get_jwt_identity()
    user_id = request.args.get('user_id', current_user_id, type=int)
    month = request.args.get('month', datetime.utcnow().strftime('%Y-%m'))
    
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
    
    return jsonify({
        'month': month,
        'total_hours': round(total_hours, 2),
        'by_project': [
            {'project_id': s[0], 'hours': round(float(s[1] or 0), 2), 'record_count': s[2]}
            for s in project_stats
        ]
    }), 200
