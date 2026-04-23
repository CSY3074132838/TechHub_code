import request from './request'

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
