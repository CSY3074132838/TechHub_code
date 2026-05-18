/**
 * 【自动化迭代】Socket.IO 客户端封装
 * 处理 WebSocket 连接、认证、重连、事件监听
 */
import { io } from 'socket.io-client'
import { ElNotification } from 'element-plus'

let socket = null
let reconnectAttempts = 0
const MAX_RECONNECT_ATTEMPTS = 5

/**
 * 初始化 WebSocket 连接
 * @param {string} token - JWT token
 */
export function initSocket(token) {
  if (socket) {
    socket.disconnect()
  }

  if (!token) {
    console.warn('[Socket] 缺少 token，跳过 WebSocket 连接')
    return null
  }

  socket = io('http://localhost:5000/notifications', {
    query: { token },
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionAttempts: MAX_RECONNECT_ATTEMPTS,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
  })

  socket.on('connect', () => {
    console.log('[Socket] WebSocket 已连接')
    reconnectAttempts = 0
  })

  socket.on('disconnect', (reason) => {
    console.log('[Socket] WebSocket 断开:', reason)
  })

  socket.on('connect_error', (error) => {
    reconnectAttempts++
    console.error(`[Socket] 连接失败 (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS}):`, error.message)
    if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      console.warn('[Socket] 达到最大重连次数，停止重连')
      socket.disconnect()
    }
  })

  socket.on('connected', (data) => {
    console.log('[Socket] 认证成功:', data)
  })

  // 监听新通知
  socket.on('new_notification', (data) => {
    console.log('[Socket] 收到新通知:', data)
    const notification = data.notification
    if (notification) {
      // 显示桌面通知弹窗
      ElNotification({
        title: notification.title || '新消息',
        message: notification.content || '',
        type: notification.notification_type === 'approval' ? 'warning' :
              notification.notification_type === 'task' ? 'success' : 'info',
        duration: 5000,
        position: 'top-right',
      })

      // 触发全局事件，让通知列表刷新
      window.dispatchEvent(new CustomEvent('new-notification', { detail: notification }))
    }
  })

  // 心跳
  setInterval(() => {
    if (socket && socket.connected) {
      socket.emit('ping', { time: Date.now() })
    }
  }, 30000)

  return socket
}

/**
 * 断开 WebSocket 连接
 */
export function disconnectSocket() {
  if (socket) {
    socket.disconnect()
    socket = null
    console.log('[Socket] WebSocket 已手动断开')
  }
}

/**
 * 获取 socket 实例
 */
export function getSocket() {
  return socket
}

/**
 * 检查是否已连接
 */
export function isConnected() {
  return socket && socket.connected
}
