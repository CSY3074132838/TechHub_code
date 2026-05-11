"""
【第二次迭代】消息通知中心 API
作者: 郝益墨
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Notification, User

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/', methods=['GET'])
@jwt_required()
def get_notifications():
    """获取当前用户的消息列表"""
    current_user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    is_read = request.args.get('is_read')
    notification_type = request.args.get('type')
    
    query = Notification.query.filter_by(user_id=current_user_id)
    
    if is_read is not None:
        query = query.filter_by(is_read=is_read.lower() == 'true')
    if notification_type:
        query = query.filter_by(notification_type=notification_type)
    
    pagination = query.order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'notifications': [n.to_dict() for n in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'unread_count': Notification.query.filter_by(user_id=current_user_id, is_read=False).count()
    }), 200


@notifications_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    """获取未读消息数量"""
    current_user_id = get_jwt_identity()
    count = Notification.query.filter_by(user_id=current_user_id, is_read=False).count()
    return jsonify({'unread_count': count}), 200


@notifications_bp.route('/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_as_read(notification_id):
    """标记单条消息为已读"""
    current_user_id = get_jwt_identity()
    notification = Notification.query.filter_by(
        id=notification_id, user_id=current_user_id
    ).first_or_404()
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'message': '已标记为已读'}), 200


@notifications_bp.route('/read-all', methods=['PUT'])
@jwt_required()
def mark_all_as_read():
    """标记所有消息为已读"""
    current_user_id = get_jwt_identity()
    Notification.query.filter_by(user_id=current_user_id, is_read=False).update({'is_read': True})
    db.session.commit()
    
    return jsonify({'message': '全部已标记为已读'}), 200


@notifications_bp.route('/', methods=['POST'])
@jwt_required()
def create_notification():
    """创建消息通知（内部使用或管理员广播）"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user.has_permission('all'):
        return jsonify({'message': '权限不足', 'error': 'forbidden'}), 403
    
    data = request.get_json()
    if not data or not data.get('user_id') or not data.get('title'):
        return jsonify({'message': '请提供用户ID和标题', 'error': 'missing_fields'}), 400
    
    notification = Notification(
        user_id=data['user_id'],
        title=data['title'],
        content=data.get('content', ''),
        notification_type=data.get('notification_type', 'system'),
        related_type=data.get('related_type'),
        related_id=data.get('related_id')
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({
        'message': '通知已发送',
        'notification': notification.to_dict()
    }), 201
