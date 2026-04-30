import request from './request'

export const getTickets = (params) => {
  return request.get('/tickets/', { params })
}

export const getTicket = (id) => {
  return request.get(`/tickets/${id}`)
}

export const createTicket = (data) => {
  return request.post('/tickets/', data)
}

export const updateTicket = (id, data) => {
  return request.put(`/tickets/${id}`, data)
}

export const deleteTicket = (id) => {
  return request.delete(`/tickets/${id}`)
}

export const getTicketStats = () => {
  return request.get('/tickets/stats')
}
