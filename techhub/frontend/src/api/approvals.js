import request from './request'

// ================================================
// 【第三次迭代于然负责】(8) 审批流程定义 API
// 新增审批流程查看和修改接口
// ================================================

export const getApprovals = (params) => {
  return request.get('/approvals/', { params })
}

export const getApproval = (id) => {
  return request.get(`/approvals/${id}`)
}

export const createApproval = (data) => {
  return request.post('/approvals/', data)
}

export const processApproval = (id, data) => {
  return request.put(`/approvals/${id}/process`, data)
}

export const getApprovalStats = () => {
  return request.get('/approvals/stats')
}

export const getApprovalTypes = () => {
  return request.get('/approvals/types')
}

export const getPendingCount = () => {
  return request.get('/approvals/pending-count')
}

export const getApprovalChain = (id) => {
  return request.get(`/approvals/${id}/chain`)
}

// 【第三次迭代于然负责】(8) 审批流程定义 API
export const getWorkflowDefinitions = () => {
  return request.get('/approvals/workflow-definitions')
}

export const updateWorkflowDefinition = (type, data) => {
  return request.put(`/approvals/workflow-definitions/${type}`, data)
}
