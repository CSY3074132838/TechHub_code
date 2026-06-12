"""
AI 助手 API 路由

【第三次迭代程思同负责】
(1) 接入 AI 大模型 DeepSeek，完善 AI 与员工的交流功能
(2) AI 帮助员工新建任务、生成周报、获取智能提醒
(3) AI 大数据筛选分析：判断最优客户、分析各种大数据

功能：
- /chat: AI 对话接口（支持工具调用循环）
- /conversations: 历史会话管理（创建/查看/更新/删除）
- /tools: 可用工具列表
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import json

from app.ai.services.llm_service import chat_completion, build_system_prompt, process_ai_response
from app.ai.tools import get_all_tools, execute_tool, init_tools
from app.models import User, AIConversation, AIConversationMessage
from app import db

ai_bp = Blueprint('ai', __name__)

# 初始化工具
init_tools()

# 内存缓存（用于当前会话的临时历史）
_conversation_cache = {}
MAX_HISTORY = 20


def get_conversation_history(user_id):
    """获取用户当前会话的临时历史"""
    return _conversation_cache.get(user_id, [])


def add_to_history(user_id, message):
    """添加消息到临时历史"""
    if user_id not in _conversation_cache:
        _conversation_cache[user_id] = []
    
    message["timestamp"] = datetime.now().isoformat()
    _conversation_cache[user_id].append(message)
    
    if len(_conversation_cache[user_id]) > MAX_HISTORY:
        _conversation_cache[user_id] = _conversation_cache[user_id][-MAX_HISTORY:]


def clear_history(user_id):
    """清空用户临时历史"""
    _conversation_cache[user_id] = []


def _save_conversation_message(conversation_id, role, content, tool_calls=None):
    """保存单条消息到数据库"""
    try:
        msg = AIConversationMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tool_calls=tool_calls or []
        )
        db.session.add(msg)
        db.session.commit()
        return msg
    except Exception as e:
        db.session.rollback()
        print(f"保存消息失败: {e}")
        return None


def _update_conversation_messages(conversation_id):
    """更新会话的 messages JSON 字段"""
    try:
        conversation = AIConversation.query.get(conversation_id)
        if conversation:
            msgs = AIConversationMessage.query.filter_by(conversation_id=conversation_id).order_by(AIConversationMessage.created_at).all()
            conversation.messages = [{
                "role": m.role,
                "content": m.content,
                "tool_calls": m.tool_calls or [],
                "timestamp": m.created_at.isoformat() if m.created_at else None
            } for m in msgs]
            conversation.updated_at = datetime.now()
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"更新会话消息失败: {e}")


@ai_bp.route('/chat', methods=['POST'])
@jwt_required()
def chat():
    """
    AI 对话接口
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "用户不存在"}), 404
    
    data = request.get_json() or {}
    user_message = data.get("message", "").strip()
    conversation_id = data.get("conversation_id")
    
    if not user_message:
        return jsonify({"success": False, "message": "消息不能为空"}), 400
    
    # 清空历史（如果指定）
    if data.get("clear_history"):
        clear_history(user_id)
    
    # 获取或创建会话
    conversation = None
    if conversation_id:
        conversation = AIConversation.query.filter_by(id=conversation_id, user_id=user_id).first()
    
    if not conversation:
        # 创建新会话，标题取用户消息的前20字
        title = user_message[:20] + "..." if len(user_message) > 20 else user_message
        conversation = AIConversation(
            user_id=user_id,
            title=title,
            messages=[]
        )
        db.session.add(conversation)
        db.session.commit()
        conversation_id = conversation.id
    
    # 保存用户消息到数据库
    _save_conversation_message(conversation_id, "user", user_message)
    
    # 构建消息列表
    messages = [{"role": "system", "content": build_system_prompt()}]
    
    # 添加用户信息上下文
    user_context = f"当前用户信息：姓名={user.real_name or user.username}，部门={user.department or '未分配'}，职位={user.position or '未分配'}"
    messages.append({"role": "system", "content": user_context})
    
    # 添加历史消息（从数据库读取）
    db_messages = AIConversationMessage.query.filter_by(conversation_id=conversation_id).order_by(AIConversationMessage.created_at).all()
    for msg in db_messages:
        messages.append({"role": msg.role, "content": msg.content})
    
    # 调用 LLM（第一轮）
    response = chat_completion(messages)
    
    if "error" in response and "choices" not in response:
        return jsonify({
            "success": False,
            "message": response.get("error", "AI 服务调用失败")
        }), 500
    
    # 处理响应（解析工具调用）
    content, tool_calls_log = process_ai_response(response, user_id=user_id)
    
    # 如果有工具调用，需要再次调用 LLM 获取最终回复
    max_rounds = 3
    round_count = 0
    
    while content is None and tool_calls_log and round_count < max_rounds:
        round_count += 1
        
        # 添加 assistant 的回复到消息历史
        assistant_raw_content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        messages.append({"role": "assistant", "content": assistant_raw_content})
        
        # 添加 tool 结果到消息历史
        for log in tool_calls_log:
            tool_result = log["result"]
            result_content = json.dumps(tool_result, ensure_ascii=False, default=str) if isinstance(tool_result, dict) else str(tool_result)
            messages.append({
                "role": "user",
                "content": f"[工具 {log['name']} 返回结果]\n{result_content}"
            })
        
        # 再次调用 LLM，让 AI 基于工具结果回复
        response = chat_completion(messages)
        content, new_tool_calls = process_ai_response(response, user_id=user_id)
        
        if new_tool_calls:
            tool_calls_log.extend(new_tool_calls)
        
        if content is None and not new_tool_calls:
            content = "工具调用完成，但未能生成回复。"
    
    # 保存 AI 回复到数据库
    _save_conversation_message(
        conversation_id, 
        "assistant", 
        content,
        tool_calls=[{
            "name": log["name"],
            "arguments": log["arguments"],
            "result": log["result"]
        } for log in tool_calls_log] if tool_calls_log else []
    )
    
    # 更新会话消息汇总
    _update_conversation_messages(conversation_id)
    
    return jsonify({
        "success": True,
        "data": {
            "content": content,
            "tool_calls": tool_calls_log,
            "conversation_id": conversation_id
        }
    })


# ==================== 历史会话管理接口 ====================

@ai_bp.route('/conversations', methods=['GET'])
@jwt_required()
def list_conversations():
    """获取当前用户的历史会话列表"""
    user_id = get_jwt_identity()
    
    conversations = AIConversation.query.filter_by(user_id=user_id).order_by(
        AIConversation.is_pinned.desc(),
        AIConversation.updated_at.desc()
    ).all()
    
    return jsonify({
        "success": True,
        "data": [c.to_dict() for c in conversations]
    })


@ai_bp.route('/conversations', methods=['POST'])
@jwt_required()
def create_conversation():
    """创建新会话"""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    
    title = data.get("title", "新对话")
    
    conversation = AIConversation(
        user_id=user_id,
        title=title,
        messages=[]
    )
    db.session.add(conversation)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "data": conversation.to_dict()
    })


@ai_bp.route('/conversations/<int:conversation_id>', methods=['GET'])
@jwt_required()
def get_conversation(conversation_id):
    """获取单个会话的详情（包含消息）"""
    user_id = get_jwt_identity()
    
    conversation = AIConversation.query.filter_by(id=conversation_id, user_id=user_id).first()
    if not conversation:
        return jsonify({"success": False, "message": "会话不存在"}), 404
    
    return jsonify({
        "success": True,
        "data": conversation.to_dict_with_messages()
    })


@ai_bp.route('/conversations/<int:conversation_id>', methods=['PUT'])
@jwt_required()
def update_conversation(conversation_id):
    """更新会话（修改标题、置顶等）"""
    user_id = get_jwt_identity()
    
    conversation = AIConversation.query.filter_by(id=conversation_id, user_id=user_id).first()
    if not conversation:
        return jsonify({"success": False, "message": "会话不存在"}), 404
    
    data = request.get_json() or {}
    
    if "title" in data:
        conversation.title = data["title"]
    if "is_pinned" in data:
        conversation.is_pinned = data["is_pinned"]
    
    db.session.commit()
    
    return jsonify({
        "success": True,
        "data": conversation.to_dict()
    })


@ai_bp.route('/conversations/<int:conversation_id>', methods=['DELETE'])
@jwt_required()
def delete_conversation(conversation_id):
    """删除会话"""
    user_id = get_jwt_identity()
    
    conversation = AIConversation.query.filter_by(id=conversation_id, user_id=user_id).first()
    if not conversation:
        return jsonify({"success": False, "message": "会话不存在"}), 404
    
    # 删除关联的消息
    AIConversationMessage.query.filter_by(conversation_id=conversation_id).delete()
    db.session.delete(conversation)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "会话已删除"
    })


@ai_bp.route('/conversations/<int:conversation_id>/messages', methods=['GET'])
@jwt_required()
def get_conversation_messages(conversation_id):
    """获取会话的消息列表"""
    user_id = get_jwt_identity()
    
    conversation = AIConversation.query.filter_by(id=conversation_id, user_id=user_id).first()
    if not conversation:
        return jsonify({"success": False, "message": "会话不存在"}), 404
    
    messages = AIConversationMessage.query.filter_by(conversation_id=conversation_id).order_by(
        AIConversationMessage.created_at
    ).all()
    
    return jsonify({
        "success": True,
        "data": [m.to_dict() for m in messages]
    })


# ==================== 兼容旧接口 ====================

@ai_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    """获取当前用户的对话历史（兼容旧接口，返回当前会话历史）"""
    user_id = get_jwt_identity()
    history = get_conversation_history(user_id)
    return jsonify({
        "success": True,
        "data": history
    })


@ai_bp.route('/history', methods=['DELETE'])
@jwt_required()
def delete_history():
    """清空当前用户的临时对话历史"""
    user_id = get_jwt_identity()
    clear_history(user_id)
    return jsonify({
        "success": True,
        "message": "对话历史已清空"
    })


@ai_bp.route('/tools', methods=['GET'])
@jwt_required()
def list_tools():
    """获取可用的 AI 工具列表（调试用）"""
    tools = get_all_tools()
    return jsonify({
        "success": True,
        "data": tools
    })
