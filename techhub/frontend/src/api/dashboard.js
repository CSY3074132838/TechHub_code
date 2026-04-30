import request from './request'

export const getOverview = () => {
  return request.get('/dashboard/overview')
}

export const getActivities = (params) => {
  return request.get('/dashboard/activities', { params })
}

export const getStatistics = () => {
  return request.get('/dashboard/statistics')
}

export const getPerformance = () => {
  return request.get('/dashboard/performance')
}

export const getTodos = (params) => {
  return request.get('/dashboard/todos', { params })
}

export const getCrmOverview = () => {
  return request.get('/dashboard/crm-overview')
}

export const getCrmRanking = () => {
  return request.get('/dashboard/crm-ranking')
}
