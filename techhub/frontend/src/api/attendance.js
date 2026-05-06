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

export const getWorkTimeStats = (params) => {
  return request.get('/attendance/work-time/stats', { params })
}
