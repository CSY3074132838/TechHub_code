/*
 * 【第二次迭代】收付款记录 API
 * 作者: 郝益墨
 */
import request from './request'

// ==================== 收付款记录管理 ====================
export const getPayments = (params) => {
  return request.get('/payments/', { params })
}

export const createPayment = (data) => {
  return request.post('/payments/', data)
}

export const getPayment = (id) => {
  return request.get(`/payments/${id}`)
}

export const updatePayment = (id, data) => {
  return request.put(`/payments/${id}`, data)
}

export const deletePayment = (id) => {
  return request.delete(`/payments/${id}`)
}

// ==================== 统计与关联查询 ====================
export const getPaymentStats = (params) => {
  return request.get('/payments/stats', { params })
}

export const getContractPayments = (contractId) => {
  return request.get(`/payments/contract/${contractId}`)
}
