/**
 * 数据备份与恢复 API
 * 第三次迭代陈思言负责
 */
import request from './request'

export const getBackupList = () => {
  return request.get('/backup/list')
}

export const createBackup = () => {
  return request.post('/backup/create')
}

export const downloadBackup = (filename) => {
  return request.get(`/backup/download/${filename}`, {
    responseType: 'blob'
  })
}

export const restoreBackup = (filename) => {
  return request.post(`/backup/restore/${filename}`)
}

export const deleteBackup = (filename) => {
  return request.delete(`/backup/delete/${filename}`)
}
