/**
 * Vue I18n 国际化配置
 * 第三次迭代陈思言负责
 * 
 * 功能说明：
 * - 创建 Vue I18n 实例，支持 Composition API 模式
 * - 加载中英文翻译文件
 * - 初始语言从 localStorage 读取，与 languageStore 保持一致
 * - 提供全局 $t 方法和 useI18n 组合式函数
 */
import { createI18n } from 'vue-i18n'
import zhCN from './locales/zh-CN'
import enUS from './locales/en-US'

const messages = {
  'zh-CN': zhCN,
  'en-US': enUS
}

const i18n = createI18n({
  legacy: false,           // Composition API 模式
  locale: localStorage.getItem('locale') || 'zh-CN',
  fallbackLocale: 'zh-CN',
  messages
})

export default i18n
