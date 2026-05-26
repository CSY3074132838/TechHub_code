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

/**
 * 获取审计日志详情
 * 第三次迭代陈思言负责
 */
export const getAuditDetail = (logId) => {
  return request.get(`/audit/detail/${logId}`)
}

/**
 * 导出审计日志为Excel
 * 第三次迭代陈思言负责
 */
export const exportAuditLogs = (params) => {
  return request.get('/audit/export', {
    params,
    responseType: 'blob'
  })
}
