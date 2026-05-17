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

// ==================== 部门成员管理 ====================

// 添加成员到部门
export const addDepartmentMember = (deptId, userId) => {
  return request.post(`/departments/${deptId}/members`, { user_id: userId })
}

// 从部门移除成员
export const removeDepartmentMember = (deptId, userId) => {
  return request.delete(`/departments/${deptId}/members/${userId}`)
}

// 转移部门成员到另一个部门
export const transferDepartmentMember = (deptId, userId, targetDeptId) => {
  return request.post(`/departments/${deptId}/members/transfer`, {
    user_id: userId,
    target_dept_id: targetDeptId
  })
}
