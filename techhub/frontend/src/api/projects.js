import request from './request'

export const getProjects = (params) => {
  return request.get('/projects/', { params })
}

export const getProject = (id) => {
  return request.get(`/projects/${id}`)
}

export const createProject = (data) => {
  return request.post('/projects/', data)
}

export const updateProject = (id, data) => {
  return request.put(`/projects/${id}`, data)
}

export const deleteProject = (id) => {
  return request.delete(`/projects/${id}`)
}

export const getProjectTasks = (id) => {
  return request.get(`/projects/${id}/tasks`)
}

export const getProjectStats = (id) => {
  return request.get(`/projects/${id}/stats`)
}

export const addProjectMember = (id, userId) => {
  return request.post(`/projects/${id}/members`, { user_id: userId })
}

export const removeProjectMember = (id, userId) => {
  return request.delete(`/projects/${id}/members/${userId}`)
}
