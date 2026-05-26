/**
 * 全局语言状态管理
 * 第三次迭代陈思言负责
 * 
 * 功能说明：
 * - 存储当前语言设置（zh-CN / en-US）
 * - 提供 setLanguage 方法切换语言
 * - 持久化到 localStorage，刷新后保持
 * - 与 Vue I18n 联动，切换后全站即时更新
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useLanguageStore = defineStore('language', () => {
  // 从 localStorage 读取已保存的语言，默认中文
  const locale = ref(localStorage.getItem('locale') || 'zh-CN')

  /**
   * 设置语言
   * @param {string} lang - 语言代码 'zh-CN' 或 'en-US'
   */
  const setLanguage = (lang) => {
    locale.value = lang
    localStorage.setItem('locale', lang)
  }

  return {
    locale,
    setLanguage
  }
})
