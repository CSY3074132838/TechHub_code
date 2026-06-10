/**
 * AI 助手 API 接口
 */
import request from './request'

/**
 * 发送对话消息
 * @param {string} message - 用户消息
 * @param {number} conversationId - 会话ID
 * @param {boolean} clearHistory - 是否清空历史
 */
export function sendChatMessage(message, conversationId = null, clearHistory = false) {
  return request.post('/ai/chat', {
    message,
    conversation_id: conversationId,
    clear_history: clearHistory
  })
}

/**
 * 获取历史会话列表
 */
export function getConversations() {
  return request.get('/ai/conversations')
}

/**
 * 创建新会话
 * @param {string} title - 会话标题
 */
export function createConversation(title = '新对话') {
  return request.post('/ai/conversations', { title })
}

/**
 * 获取单个会话详情
 * @param {number} id - 会话ID
 */
export function getConversation(id) {
  return request.get(`/ai/conversations/${id}`)
}

/**
 * 更新会话
 * @param {number} id - 会话ID
 * @param {object} data - 更新数据
 */
export function updateConversation(id, data) {
  return request.put(`/ai/conversations/${id}`, data)
}

/**
 * 删除会话
 * @param {number} id - 会话ID
 */
export function deleteConversation(id) {
  return request.delete(`/ai/conversations/${id}`)
}

/**
 * 获取会话消息列表
 * @param {number} id - 会话ID
 */
export function getConversationMessages(id) {
  return request.get(`/ai/conversations/${id}/messages`)
}

/**
 * 获取可用工具列表（调试）
 */
export function getToolList() {
  return request.get('/ai/tools')
}
