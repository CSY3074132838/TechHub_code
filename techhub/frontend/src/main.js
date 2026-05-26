/**
 * TechHub 前端应用入口
 * 第三次迭代陈思言负责
 * 
 * 初始化顺序说明：
 * 1. 创建 Vue 应用实例
 * 2. 注册 Element Plus 图标
 * 3. 安装 Pinia（状态管理，必须先于 i18n）
 * 4. 安装 Vue Router
 * 5. 安装 Vue I18n（国际化，依赖 Pinia 中的语言状态）
 * 6. 安装 Element Plus（UI 组件库，语言随 i18n 同步）
 * 7. 挂载应用
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import en from 'element-plus/dist/locale/en.mjs'

import App from './App.vue'
import router from './router'
import i18n from './i18n'
import { useLanguageStore } from './stores/language'
import './styles/main.scss'

const app = createApp(App)

// 注册所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// Element Plus 语言包映射
const elementLocales = {
  'zh-CN': zhCn,
  'en-US': en
}

// 创建 Pinia 实例
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(i18n)

/**
 * 同步 Element Plus 语言与 Vue I18n
 * 第三次迭代陈思言负责
 * 根据当前 i18n 的语言设置 Element Plus 组件语言
 */
const syncElementLocale = () => {
  const currentLocale = i18n.global.locale.value
  app.use(ElementPlus, { locale: elementLocales[currentLocale] || zhCn })
}

syncElementLocale()

// 全局错误处理 —— 捕获组件渲染和生命周期中的未处理错误
app.config.errorHandler = (err, vm, info) => {
  console.error('Vue 全局错误:', err, info)
}

// 捕获 Promise 未处理的 rejection
window.addEventListener('unhandledrejection', (event) => {
  console.error('未处理的 Promise 错误:', event.reason)
})

app.mount('#app')
