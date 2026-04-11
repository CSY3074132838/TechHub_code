import request from './request'

export const getTasks = (params) => {
  return request.get('/tasks/', { params })
}

export const getTask = (id) => {
  return request.get(`/tasks/${id}`)
}

export const createTask = (data) => {
  return request.post('/tasks/', data)
}

export const updateTask = (id, data) => {
  return request.put(`/tasks/${id}`, data)
}

export const deleteTask = (id) => {
  return request.delete(`/tasks/${id}`)
}

export const getMyTasks = (params) => {
  return request.get('/tasks/my-tasks', { params })
}

export const addComment = (taskId, content) => {
  return request.post(`/tasks/${taskId}/comments`, { content })
}

export const getComments = (taskId) => {
  return request.get(`/tasks/${taskId}/comments`)
}

export const updateBoard = (updates) => {
  return request.put('/tasks/board/update', { updates })
}
