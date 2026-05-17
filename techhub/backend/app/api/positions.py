"""
职位管理 API - 组织架构中的职位类管理
基于 User.position 字段实现
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User
from app.decorators import require_permission
from app.services import AuditService

positions_bp = Blueprint('positions', __name__)


@positions_bp.route('/', methods=['GET'])
@jwt_required()
def get_positions():
    """获取所有职位列表（基于用户position字段聚合）"""
    # 获取所有非空职位
    position_rows = db.session.query(User.position).filter(
        User.position.isnot(None),
        User.position != ''
    ).distinct().all()
    
    positions = []
    for (pos_name,) in position_rows:
        user_count = User.query.filter_by(position=pos_name).count()
        positions.append({
            'id': pos_name,  # 使用职位名作为ID
            'name': pos_name,
            'user_count': user_count
        })
    
    return jsonify({'positions': positions}), 200


@positions_bp.route('/<string:position_name>/members', methods=['GET'])
@jwt_required()
def get_position_members(position_name):
    """获取职位成员列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    users_query = User.query.filter_by(position=position_name)
    total = users_query.count()
    users = users_query.offset((page - 1) * per_page).limit(per_page).all()
    
    return jsonify({
        'members': [u.to_dict(include_email=True) for u in users],
        'total': total,
        'page': page,
        'per_page': per_page
    }), 200


@positions_bp.route('/', methods=['POST'])
@require_permission('user_manage')
def create_position():
    """创建新职位（通过创建一个带该职位的用户来占位，或仅记录）"""
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'message': '职位名称不能为空', 'error': 'missing_fields'}), 400
    
    # 检查是否已存在
    exists = User.query.filter_by(position=data['name']).first()
    if exists:
        return jsonify({'message': '职位已存在', 'error': 'exists'}), 409
    
    return jsonify({
        'message': '职位创建成功',
        'position': {'name': data['name'], 'description': data.get('description', '')}
    }), 201


@positions_bp.route('/<string:position_name>', methods=['PUT'])
@require_permission('user_manage')
def update_position(position_name):
    """更新职位名称（批量更新所有用户的职位字段）"""
    data = request.get_json()
    new_name = data.get('name')
    
    if not new_name:
        return jsonify({'message': '新职位名称不能为空', 'error': 'missing_fields'}), 400
    
    # 批量更新
    User.query.filter_by(position=position_name).update({'position': new_name})
    db.session.commit()
    
    AuditService.log_from_current_user(
        action='POSITION_UPDATE',
        resource_type='position',
        resource_id=0,
        detail={'from': position_name, 'to': new_name},
        status='success'
    )
    
    return jsonify({'message': f'职位已从 {position_name} 更新为 {new_name}'}), 200


@positions_bp.route('/<string:position_name>', methods=['DELETE'])
@require_permission('user_manage')
def delete_position(position_name):
    """删除职位（清空所有用户的该职位字段）"""
    count = User.query.filter_by(position=position_name).count()
    
    User.query.filter_by(position=position_name).update({'position': None})
    db.session.commit()
    
    AuditService.log_from_current_user(
        action='POSITION_DELETE',
        resource_type='position',
        resource_id=0,
        detail={'name': position_name, 'affected_users': count},
        status='success'
    )
    
    return jsonify({'message': f'已删除职位 {position_name}，影响 {count} 人'}), 200


@positions_bp.route('/<string:position_name>/members', methods=['POST'])
@require_permission('user_manage')
def add_position_member(position_name):
    """将用户分配到职位"""
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'message': '请提供用户ID', 'error': 'missing_fields'}), 400
    
    user = User.query.get_or_404(user_id)
    user.position = position_name
    db.session.commit()
    
    return jsonify({
        'message': f'已将 {user.real_name or user.username} 设置为 {position_name}'
    }), 200


@positions_bp.route('/<string:position_name>/members/<int:user_id>', methods=['DELETE'])
@require_permission('user_manage')
def remove_position_member(position_name, user_id):
    """从职位中移除用户"""
    user = User.query.get_or_404(user_id)
    
    if user.position != position_name:
        return jsonify({'message': '该用户不在此职位', 'error': 'not_in_position'}), 400
    
    user.position = None
    db.session.commit()
    
    return jsonify({
        'message': f'已将 {user.real_name or user.username} 从 {position_name} 移除'
    }), 200


@positions_bp.route('/<string:position_name>/members/transfer', methods=['POST'])
@require_permission('user_manage')
def transfer_position_member(position_name):
    """转移用户到另一个职位"""
    data = request.get_json()
    user_id = data.get('user_id')
    target_position = data.get('target_position')
    
    if not user_id or not target_position:
        return jsonify({'message': '请提供用户ID和目标职位', 'error': 'missing_fields'}), 400
    
    user = User.query.get_or_404(user_id)
    if user.position != position_name:
        return jsonify({'message': '该用户不在当前职位', 'error': 'not_in_source'}), 400
    
    old_position = user.position
    user.position = target_position
    db.session.commit()
    
    return jsonify({
        'message': f'已将 {user.real_name or user.username} 从 {old_position} 转移到 {target_position}'
    }), 200


@positions_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_position_stats():
    """获取职位统计"""
    from sqlalchemy import func
    
    total_with_position = User.query.filter(
        User.position.isnot(None),
        User.position != ''
    ).count()
    
    position_stats = db.session.query(
        User.position, func.count(User.id)
    ).filter(
        User.position.isnot(None),
        User.position != ''
    ).group_by(User.position).all()
    
    return jsonify({
        'total_positions': len(position_stats),
        'total_users_with_position': total_with_position,
        'by_position': [
            {'name': p[0], 'count': p[1]} for p in position_stats
        ]
    }), 200


@positions_bp.route('/users-without-position', methods=['GET'])
@jwt_required()
def get_users_without_position():
    """获取未分配职位的用户"""
    users = User.query.filter(
        db.or_(User.position.is_(None), User.position == '')
    ).all()
    
    return jsonify({
        'users': [u.to_dict(include_email=True) for u in users]
    }), 200
