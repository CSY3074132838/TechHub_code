<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <el-icon size="48" color="#1890ff"><Connection /></el-icon>
        <h1>TechHub</h1>
        <p>研发协同管理平台</p>
      </div>
      
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="用户名/邮箱"
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="密码"
            size="large"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-button"
            :loading="loading"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="register-link">
        <span>还没有账号？</span>
        <el-button link type="primary" @click="$router.push('/register')">立即注册</el-button>
      </div>
      
      <div class="login-tips">
        <p>测试账号：admin / admin123</p>
        <p>普通账号：test / test123</p>
      </div>
    </div>
    
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { User, Lock } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

const loginFormRef = ref(null)
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  const valid = await loginFormRef.value.validate().catch(() => false)
  if (!valid) return
  
  loading.value = true
  const success = await userStore.loginAction(loginForm)
  loading.value = false
  
  if (success) {
    router.push('/')
  }
}
</script>

<style scoped lang="scss">
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-container {
  width: 100%;
  max-width: 400px;
  background: #fff;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
  
  h1 {
    font-size: 28px;
    color: #333;
    margin: 16px 0 8px;
  }
  
  p {
    color: #666;
    font-size: 14px;
  }
}

.login-form {
  .login-button {
    width: 100%;
  }
}

.login-tips {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #eee;
  text-align: center;
  
  p {
    color: #999;
    font-size: 12px;
    margin: 4px 0;
  }
}

.register-link {
  margin-top: 16px;
  text-align: center;
  color: #666;
  font-size: 14px;
}

.login-footer {
  position: fixed;
  bottom: 20px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
}
</style>
