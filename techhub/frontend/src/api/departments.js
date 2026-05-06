/*
 * 【第二次迭代】部门管理 API
 * 作者: 于然
 */
import request from './request'

// 获取部门树形列表
export const getDepartments = () => {
  return request.get('/departments/')
}

// 获取扁平化部门列表（下拉选择用）
export const getDepartmentsFlat = () => {
  return request.get('/departments/flat')
}

// 创建部门
export const createDepartment = (data) => {
  return request.post('/departments/', data)
}

// 更新部门
export const updateDepartment = (id, data) => {
  return request.put(`/departments/${id}`, data)
}

// 删除部门
export const deleteDepartment = (id) => {
  return request.delete(`/departments/${id}`)
}

// 获取部门成员
export const getDepartmentMembers = (id, params = {}) => {
  return request.get(`/departments/${id}/members`, { params })
}

// 获取部门统计
export const getDepartmentStats = () => {
  return request.get('/departments/stats')
}
