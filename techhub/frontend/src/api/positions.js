/*
 * 职位管理 API
 */
import request from './request'

// 获取职位列表
export const getPositions = () => {
  return request.get('/positions/')
}

// 获取职位成员
export const getPositionMembers = (name, params = {}) => {
  return request.get(`/positions/${encodeURIComponent(name)}/members`, { params })
}

// 创建职位
export const createPosition = (data) => {
  return request.post('/positions/', data)
}

// 更新职位
export const updatePosition = (name, data) => {
  return request.put(`/positions/${encodeURIComponent(name)}`, data)
}

// 删除职位
export const deletePosition = (name) => {
  return request.delete(`/positions/${encodeURIComponent(name)}`)
}

// 添加成员到职位
export const addPositionMember = (name, userId) => {
  return request.post(`/positions/${encodeURIComponent(name)}/members`, { user_id: userId })
}

// 从职位移除成员
export const removePositionMember = (name, userId) => {
  return request.delete(`/positions/${encodeURIComponent(name)}/members/${userId}`)
}

// 转移职位成员
export const transferPositionMember = (name, userId, targetName) => {
  return request.post(`/positions/${encodeURIComponent(name)}/members/transfer`, {
    user_id: userId,
    target_position: targetName
  })
}

// 获取职位统计
export const getPositionStats = () => {
  return request.get('/positions/stats')
}

// 获取未分配职位的用户
export const getUsersWithoutPosition = () => {
  return request.get('/positions/users-without-position')
}
