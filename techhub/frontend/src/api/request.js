import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 创建 axios 实例
const request = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 是否正在刷新 Token
let isRefreshing = false
// 等待刷新成功的请求队列
let refreshSubscribers = []

// 订阅 Token 刷新
function subscribeTokenRefresh(callback) {
  refreshSubscribers.push(callback)
}

// 通知所有等待的请求继续
function onTokenRefreshed(newToken) {
  refreshSubscribers.forEach(callback => callback(newToken))
  refreshSubscribers = []
}

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    // 如果是blob响应，返回完整response，让调用方处理blob
    if (response.config.responseType === 'blob') {
      return response
    }
    return response.data
  },
  async (error) => {
    const { response, config } = error
    
    if (response) {
      // Token 过期，尝试自动刷新
      if (response.status === 401 && response.data?.error === 'token_expired') {
        const refreshToken = localStorage.getItem('refresh_token')
        if (!refreshToken) {
          ElMessage.error('登录已过期，请重新登录')
          localStorage.removeItem('token')
          router.push('/login')
          return Promise.reject(error)
        }
        
        // 如果已经在刷新中，加入等待队列
        if (isRefreshing) {
          return new Promise((resolve) => {
            subscribeTokenRefresh((newToken) => {
              config.headers.Authorization = `Bearer ${newToken}`
              resolve(request(config))
            })
          })
        }
        
        isRefreshing = true
        
        try {
          const refreshRes = await axios.post('/api/auth/refresh', {}, {
            headers: { Authorization: `Bearer ${refreshToken}` }
          })
          
          if (refreshRes.data.access_token) {
            const newToken = refreshRes.data.access_token
            localStorage.setItem('token', newToken)
            request.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
            onTokenRefreshed(newToken)
            config.headers.Authorization = `Bearer ${newToken}`
            return request(config)
          }
        } catch (refreshError) {
          ElMessage.error('登录已过期，请重新登录')
          localStorage.removeItem('token')
          localStorage.removeItem('refresh_token')
          router.push('/login')
          return Promise.reject(refreshError)
        } finally {
          isRefreshing = false
        }
      }
      
      // 对于blob响应，尝试解析错误信息
      let errorMessage = '请求失败'
      if (response.config?.responseType === 'blob') {
        try {
          const blobText = await response.data.text()
          const errorData = JSON.parse(blobText)
          errorMessage = errorData.message || '请求失败'
        } catch (e) {
          errorMessage = response.statusText || '请求失败'
        }
      } else {
        errorMessage = response.data?.message || '请求失败'
      }
      
      switch (response.status) {
        case 401:
          if (!response.config?.responseType || response.data?.error !== 'token_expired') {
            ElMessage.error('登录已过期，请重新登录')
            localStorage.removeItem('token')
            router.push('/login')
          }
          break
        case 403:
          ElMessage.error(errorMessage || '权限不足')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          ElMessage.error(errorMessage || '服务器错误')
          break
        default:
          ElMessage.error(errorMessage)
      }
    } else {
      ElMessage.error('网络错误')
    }
    
    return Promise.reject(error)
  }
)

export default request
