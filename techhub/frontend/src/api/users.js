import request from './request'

export const getUsers = (params) => {
  return request.get('/users/', { params })
}

export const getUser = (id, detail = false) => {
  return request.get(`/users/${id}`, { params: { detail } })
}

export const updateUser = (id, data) => {
  return request.put(`/users/${id}`, data)
}

export const deleteUser = (id) => {
  return request.delete(`/users/${id}`)
}

export const getDepartments = () => {
  return request.get('/users/departments')
}

export const getRoles = () => {
  return request.get('/users/roles')
}

export const getUserStats = () => {
  return request.get('/users/stats')
}

export const createRole = (data) => {
  return request.post('/users/roles', data)
}

export const updateRole = (id, data) => {
  return request.put(`/users/roles/${id}`, data)
}

export const deleteRole = (id) => {
  return request.delete(`/users/roles/${id}`)
}

export const getPermissions = () => {
  return request.get('/users/permissions')
}

// ==================== 【第二次迭代】新增 API ====================

// 获取当前用户完整档案（员工自助）
export const getMyDetail = () => {
  return request.get('/users/me/detail')
}

// 更新当前用户信息（员工自助）
export const updateMyDetail = (data) => {
  return request.put('/users/me/detail', data)
}

// 获取可作为上级的用户列表
export const getManagers = () => {
  return request.get('/users/managers')
}

// 导出员工数据
export const exportUsers = (format = 'json') => {
  return request.get('/users/export', { params: { format } })
}

// 批量导入员工数据
export const importUsers = (data) => {
  return request.post('/users/import', data)
}
