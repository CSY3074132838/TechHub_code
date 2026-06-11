/*
 * 【第二次迭代】费用报销 API
 * 作者: 郝益墨
 *
 * 【第三次迭代郝益墨负责】
 * (2) 费用报销面板中的本月记录，筛选框增加按人名筛选
 * (4) 报销记录界面，可点击查看每一个报销的详情内容
 * (5) 新建报销中，加入上传附件功能（图片、文档）
 */
import request from './request'

// ==================== 报销单管理 ====================
export const getExpenses = (params) => {
  return request.get('/expenses/', { params })
}

export const createExpense = (data) => {
  return request.post('/expenses/', data)
}

export const getExpense = (id) => {
  return request.get(`/expenses/${id}`)
}

export const updateExpense = (id, data) => {
  return request.put(`/expenses/${id}`, data)
}

export const deleteExpense = (id) => {
  return request.delete(`/expenses/${id}`)
}

// ==================== 审批操作 ====================
export const approveExpense = (id) => {
  return request.post(`/expenses/${id}/approve`)
}

export const rejectExpense = (id) => {
  return request.post(`/expenses/${id}/reject`)
}

export const reimburseExpense = (id) => {
  return request.post(`/expenses/${id}/reimburse`)
}

// ==================== 统计与选项 ====================
export const getExpenseStats = (params) => {
  return request.get('/expenses/stats', { params })
}

export const getExpenseCategories = () => {
  return request.get('/expenses/categories')
}

// ==================== 附件上传 ====================
export const uploadExpenseAttachment = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/expenses/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}
