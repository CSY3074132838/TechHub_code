import request from './request'

export const getUsers = (params) => {
  return request.get('/users/', { params })
}

export const getUser = (id) => {
  return request.get(`/users/${id}`)
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
