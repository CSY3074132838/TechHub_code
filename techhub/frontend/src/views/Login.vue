<!-- 第三次迭代陈思言负责 -->
<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <el-icon size="48" color="#1890ff"><Connection /></el-icon>
        <h1>{{ $t('login.title') }}</h1>
        <p>{{ $t('login.subtitle') }}</p>
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
            :placeholder="$t('login.usernamePlaceholder')"
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            :placeholder="$t('login.passwordPlaceholder')"
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
            {{ $t('login.loginButton') }}
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="register-link">
        <span>{{ $t('login.noAccount') }}</span>
        <el-button link type="primary" @click="$router.push('/register')">{{ $t('login.registerNow') }}</el-button>
      </div>
      
      <div class="language-switcher">
        <el-dropdown @command="handleLanguageChange" trigger="click">
          <div class="lang-current">
            <span class="name">{{ currentLang === 'zh-CN' ? $t('language.zh') : $t('language.en') }}</span>
            <el-icon><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="zh-CN" :class="{ active: currentLang === 'zh-CN' }">
                <span class="name">{{ $t('language.zh') }}</span>
              </el-dropdown-item>
              <el-dropdown-item command="en-US" :class="{ active: currentLang === 'en-US' }">
                <span class="name">{{ $t('language.en') }}</span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
    
  </div>
</template>

<script setup>
/**
 * 登录页面
 * 第三次迭代陈思言负责
 * 
 * 功能说明：
 * - 用户登录表单验证与提交
 * - 语言切换功能：调用 languageStore 切换全局语言
 * - 切换后全站（包括 Element Plus 组件）即时更新
 */
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/stores/user'
import { useLanguageStore } from '@/stores/language'
import { User, Lock, ArrowDown } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const languageStore = useLanguageStore()
const { locale, t } = useI18n()

const loginFormRef = ref(null)
const loading = ref(false)

const currentLang = computed(() => locale.value)

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = {
  username: [
    { required: true, message: t('login.usernameRequired'), trigger: 'blur' }
  ],
  password: [
    { required: true, message: t('login.passwordRequired'), trigger: 'blur' },
    { min: 6, message: t('login.passwordMinLength'), trigger: 'blur' }
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

/**
 * 切换语言
 * 第三次迭代陈思言负责
 * 调用 languageStore 同步更新全局 locale 和 localStorage
 */
const handleLanguageChange = (lang) => {
  languageStore.setLanguage(lang)
  locale.value = lang
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

.register-link {
  margin-top: 16px;
  text-align: center;
  color: #666;
  font-size: 14px;
}

.language-switcher {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: center;
  
  .lang-current {
    display: flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
    padding: 6px 12px;
    border-radius: 6px;
    transition: background 0.2s;
    
    &:hover {
      background: #f5f5f5;
    }
    
    .name {
      font-size: 14px;
      color: #333;
      font-weight: 500;
      line-height: 1;
    }
    
    .el-icon {
      font-size: 12px;
      color: #999;
    }
  }
}

:deep(.el-dropdown-menu__item) {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  
  .name {
    font-size: 14px;
    color: #333;
    font-weight: 500;
    line-height: 1;
  }
  
  &.active {
    background: #ecf5ff;
    color: #409eff;
    font-weight: 500;
  }
}
</style>
