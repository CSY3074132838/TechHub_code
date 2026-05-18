/*
 * 【第二次迭代】考勤与工时 API
 * 作者: 于然
 */
import request from './request'

// ==================== 考勤记录 ====================
export const getAttendanceRecords = (params) => {
  return request.get('/attendance/records', { params })
}

export const createAttendanceRecord = (data) => {
  return request.post('/attendance/records', data)
}

export const getAttendanceStats = (params) => {
  return request.get('/attendance/stats', { params })
}

// ==================== 一键打卡/下班 ====================
export const checkIn = () => {
  return request.post('/attendance/check-in')
}

export const checkOut = () => {
  return request.post('/attendance/check-out')
}

// ==================== 假期余额 ====================
export const getLeaveBalances = (params) => {
  return request.get('/attendance/leave-balances', { params })
}

export const updateLeaveBalance = (data) => {
  return request.post('/attendance/leave-balances', data)
}

// ==================== 工时记录 ====================
export const getWorkTimeRecords = (params) => {
  return request.get('/attendance/work-time', { params })
}

export const createWorkTimeRecord = (data) => {
  return request.post('/attendance/work-time', data)
}

export const updateWorkTimeRecord = (id, data) => {
  return request.put(`/attendance/work-time/${id}`, data)
}

export const deleteWorkTimeRecord = (id) => {
  return request.delete(`/attendance/work-time/${id}`)
}

export const getWorkTimeStats = (params) => {
  return request.get('/attendance/work-time/stats', { params })
}

// ==================== 请假记录 ====================
export const getLeaveRecords = (params) => {
  return request.get('/attendance/leaves', { params })
}

export const createLeaveRecord = (data) => {
  return request.post('/attendance/leaves', data)
}

export const updateLeaveRecord = (id, data) => {
  return request.put(`/attendance/leaves/${id}`, data)
}

export const deleteLeaveRecord = (id) => {
  return request.delete(`/attendance/leaves/${id}`)
}

// ==================== 高管考勤概览 ====================
export const getManagerOverview = (params) => {
  return request.get('/attendance/manager/overview', { params })
}
