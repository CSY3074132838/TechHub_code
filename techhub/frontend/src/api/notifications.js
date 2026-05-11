/*
 * 【第二次迭代】消息通知中心 API
 * 作者: 郝益墨
 */
import request from './request'

export const getNotifications = (params) => {
  return request.get('/notifications/', { params })
}

export const getUnreadCount = () => {
  return request.get('/notifications/unread-count')
}

export const markAsRead = (id) => {
  return request.put(`/notifications/${id}/read`)
}

export const markAllAsRead = () => {
  return request.put('/notifications/read-all')
}

export const createNotification = (data) => {
  return request.post('/notifications/', data)
}
