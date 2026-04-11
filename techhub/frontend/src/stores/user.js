import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login, getCurrentUser } from '@/api/auth'
import { ElMessage } from 'element-plus'

export const useUserStore = defineStore('user', () => {
  // State
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(null)
  const loading = ref(false)

  // Getters
  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => {
    if (!userInfo.value || !userInfo.value.roles) return false
    return userInfo.value.roles.some(r => r.name === 'super_admin')
  })
  const canManageTeam = computed(() => {
    if (!userInfo.value || !userInfo.value.roles) return false
    return userInfo.value.roles.some(r => ['super_admin', 'department_manager'].includes(r.name))
  })

  // Actions
  const setToken = (newToken) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  const clearToken = () => {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
  }

  const loginAction = async (credentials) => {
    loading.value = true
    try {
      const res = await login(credentials)
      if (res.access_token) {
        setToken(res.access_token)
        userInfo.value = res.user
        ElMessage.success('登录成功')
        return true
      }
    } catch (error) {
      ElMessage.error(error.response?.data?.message || '登录失败')
      return false
    } finally {
      loading.value = false
    }
  }

  const fetchUserInfo = async () => {
    if (!token.value) return
    try {
      const res = await getCurrentUser()
      userInfo.value = res.user
    } catch (error) {
      clearToken()
    }
  }

  const logout = () => {
    clearToken()
    ElMessage.success('已退出登录')
  }

  return {
    token,
    userInfo,
    loading,
    isLoggedIn,
    isAdmin,
    canManageTeam,
    setToken,
    clearToken,
    loginAction,
    fetchUserInfo,
    logout
  }
})
