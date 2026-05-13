import request from './request'

export const getClients = (params) => {
  return request.get('/clients/', { params })
}

export const getClient = (id) => {
  return request.get(`/clients/${id}`)
}

export const createClient = (data) => {
  return request.post('/clients/', data)
}

export const updateClient = (id, data) => {
  return request.put(`/clients/${id}`, data)
}

export const deleteClient = (id) => {
  return request.delete(`/clients/${id}`)
}

export const permanentlyDeleteClient = (id) => {
  return request.delete(`/clients/${id}/permanent`)
}

export const getClientProjects = (id) => {
  return request.get(`/clients/${id}/projects`)
}

export const getClientContracts = (id) => {
  return request.get(`/clients/${id}/contracts`)
}

export const getClientTickets = (id) => {
  return request.get(`/clients/${id}/tickets`)
}

export const getClientOptions = () => {
  return request.get('/clients/options')
}

export const getClientStats = () => {
  return request.get('/clients/stats')
}
