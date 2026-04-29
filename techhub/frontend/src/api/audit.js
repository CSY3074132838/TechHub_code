import request from './request'

export const getAuditLogs = (params) => {
  return request.get('/audit/logs', { params })
}

export const getAuditStats = () => {
  return request.get('/audit/stats')
}

export const getActionTypes = () => {
  return request.get('/audit/actions')
}
