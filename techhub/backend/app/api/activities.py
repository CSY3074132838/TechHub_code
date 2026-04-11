"""
活动记录 API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Activity, User, Project

activities_bp = Blueprint('activities', __name__)

@activities_bp.route('/', methods=['GET'])
@jwt_required()
def get_activities():
    """获取活动记录列表"""
    current_user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    activity_type = request.args.get('type')
    project_id = request.args.get('project_id', type=int)
    
    # 获取用户能看到的项目
    user_projects = Project.query.filter(
        (Project.creator_id == current_user_id) |
        (Project.members.any(id=current_user_id))
    ).all()
    project_ids = [p.id for p in user_projects]
    
    query = Activity.query.filter(
        (Activity.project_id.in_(project_ids)) |
        (Activity.user_id == current_user_id)
    )
    
    if activity_type:
        query = query.filter(Activity.activity_type == activity_type)
    
    if project_id:
        query = query.filter_by(project_id=project_id)
    
    pagination = query.order_by(Activity.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    activities = pagination.items
    
    return jsonify({
        'activities': [activity.to_dict() for activity in activities],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

@activities_bp.route('/recent', methods=['GET'])
@jwt_required()
def get_recent_activities():
    """获取最近的动态（用于工作台）"""
    current_user_id = get_jwt_identity()
    limit = request.args.get('limit', 10, type=int)
    
    # 获取用户能看到的项目
    user_projects = Project.query.filter(
        (Project.creator_id == current_user_id) |
        (Project.members.any(id=current_user_id))
    ).all()
    project_ids = [p.id for p in user_projects]
    
    activities = Activity.query.filter(
        (Activity.project_id.in_(project_ids)) |
        (Activity.user_id == current_user_id)
    ).order_by(Activity.created_at.desc()).limit(limit).all()
    
    return jsonify({
        'activities': [activity.to_dict() for activity in activities]
    }), 200
