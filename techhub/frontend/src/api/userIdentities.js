import request from './request'

// 获取用户的所有身份
export const getUserIdentities = (userId) => {
  return request.get(`/users/${userId}/identities`)
}

// 为用户添加新身份
export const createUserIdentity = (userId, data) => {
  return request.post(`/users/${userId}/identities`, data)
}

// 更新用户身份
export const updateUserIdentity = (userId, identityId, data) => {
  return request.put(`/users/${userId}/identities/${identityId}`, data)
}

// 删除用户身份
export const deleteUserIdentity = (userId, identityId) => {
  return request.delete(`/users/${userId}/identities/${identityId}`)
}

// 设为主身份
export const setPrimaryIdentity = (userId, identityId) => {
  return request.post(`/users/${userId}/identities/${identityId}/set-primary`)
}
