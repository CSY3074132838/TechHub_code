import request from './request'

export const getContracts = (params) => {
  return request.get('/contracts/', { params })
}

export const getContract = (id) => {
  return request.get(`/contracts/${id}`)
}

export const createContract = (data) => {
  return request.post('/contracts/', data)
}

export const updateContract = (id, data) => {
  return request.put(`/contracts/${id}`, data)
}

export const deleteContract = (id) => {
  return request.delete(`/contracts/${id}`)
}
