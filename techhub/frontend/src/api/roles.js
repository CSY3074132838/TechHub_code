/*
 * 角色管理 API
 */
import request from './request'

// 获取角色列表
export const getRoles = () => {
  return request.get('/roles/')
}

// 获取角色详情
export const getRole = (id) => {
  return request.get(`/roles/${id}`)
}

// 创建角色
export const createRole = (data) => {
  return request.post('/roles/', data)
}

// 更新角色
export const updateRole = (id, data) => {
  return request.put(`/roles/${id}`, data)
}

// 删除角色
export const deleteRole = (id) => {
  return request.delete(`/roles/${id}`)
}

// 获取角色成员
export const getRoleMembers = (id, params = {}) => {
  return request.get(`/roles/${id}/members`, { params })
}

// 添加成员到角色
export const addRoleMember = (roleId, userId) => {
  return request.post(`/roles/${roleId}/members`, { user_id: userId })
}

// 从角色移除成员
export const removeRoleMember = (roleId, userId) => {
  return request.delete(`/roles/${roleId}/members/${userId}`)
}

// 获取角色统计
export const getRoleStats = () => {
  return request.get('/roles/stats')
}
