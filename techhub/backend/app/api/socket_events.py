"""
【自动化迭代】WebSocket 事件处理 - Socket.IO 命名空间
处理实时通知推送、用户连接认证
"""
from flask import request
from flask_socketio import Namespace, emit, join_room, disconnect
from flask_jwt_extended import decode_token


class NotificationsNamespace(Namespace):
    """通知命名空间 - 处理实时通知推送"""

    def on_connect(self):
        """客户端连接时验证 JWT"""
        try:
            # 从 query param 获取 token
            token = request.args.get('token')
            if not token:
                print("[SocketIO] 连接失败：缺少 token")
                disconnect()
                return False

            # 解码 token 获取 user_id
            decoded = decode_token(token)
            user_id = decoded.get('sub')

            if not user_id:
                print("[SocketIO] 连接失败：无效的 token")
                disconnect()
                return False

            # 将用户加入以 user_id 命名的 room
            join_room(f'user_{user_id}')
            print(f"[SocketIO] 用户 {user_id} 已连接通知通道")
            emit('connected', {'status': 'ok', 'user_id': user_id})

        except Exception as e:
            print(f"[SocketIO] 连接验证失败: {e}")
            disconnect()
            return False

    def on_disconnect(self):
        """客户端断开连接"""
        print("[SocketIO] 客户端断开连接")

    def on_ping(self, data):
        """心跳检测"""
        emit('pong', {'time': data.get('time')})


def emit_to_user(user_id, event, data):
    """
    向指定用户推送事件
    由 notification_service 调用
    """
    try:
        from app.services.scheduler_service import socketio
        if socketio:
            socketio.emit(event, data, room=f'user_{user_id}', namespace='/notifications')
    except Exception as e:
        print(f"[SocketIO] 推送失败: {e}")
