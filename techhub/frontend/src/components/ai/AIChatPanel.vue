<template>
  <div class="ai-chat-panel" :class="{ 'is-open': isOpen, 'is-expanded': isExpanded }">
    <!-- 侧边栏：历史会话列表 -->
    <div class="sidebar-conversations" :class="{ 'show': showSidebar }">
      <div class="sidebar-header">
        <span class="sidebar-title">历史会话</span>
        <el-button link size="small" @click="showSidebar = false">
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
      </div>
      <div class="new-chat-btn">
        <el-button type="primary" size="small" @click="startNewChat" :icon="Plus">
          新建对话
        </el-button>
      </div>
      <div class="conversation-list">
        <div
          v-for="conv in sortedConversations"
          :key="conv.id"
          class="conversation-item"
          :class="{ active: currentConversationId === conv.id, pinned: conv.is_pinned }"
          @click="switchConversation(conv.id)"
        >
          <el-icon v-if="conv.is_pinned" class="pin-icon"><Top /></el-icon>
          <span class="conv-title">{{ conv.title }}</span>
          <div class="conv-actions" @click.stop>
            <el-dropdown trigger="click">
              <el-icon class="more-icon"><MoreFilled /></el-icon>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="pinConversation(conv.id, !conv.is_pinned)">
                    {{ conv.is_pinned ? '取消置顶' : '置顶' }}
                  </el-dropdown-item>
                  <el-dropdown-item @click="renameConversation(conv)">重命名</el-dropdown-item>
                  <el-dropdown-item divided @click="deleteConversation(conv.id)" style="color: #f56c6c;">
                    删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
        <div v-if="conversations.length === 0" class="empty-conversations">
          暂无历史会话
        </div>
      </div>
    </div>

    <!-- 主聊天区域 -->
    <div class="chat-main">
      <!-- 头部 -->
      <div class="chat-header">
        <div class="header-left">
          <el-button link class="sidebar-toggle" @click="showSidebar = !showSidebar">
            <el-icon><Expand /></el-icon>
          </el-button>
          <el-icon class="ai-icon"><MagicStick /></el-icon>
          <span class="title">TechHub AI 助手</span>
          <el-tag v-if="isLoading" size="small" type="success" effect="dark">思考中...</el-tag>
        </div>
        <div class="header-actions">
          <!-- 放大/缩小按钮 -->
          <el-tooltip :content="isExpanded ? '缩小' : '放大'" placement="bottom">
            <el-button link @click="toggleExpand">
              <el-icon v-if="!isExpanded"><FullScreen /></el-icon>
              <el-icon v-else><CopyDocument /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="清空当前对话" placement="bottom">
            <el-button link @click="clearChat">
              <el-icon><Delete /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="关闭" placement="bottom">
            <el-button link @click="closePanel">
              <el-icon><Close /></el-icon>
            </el-button>
          </el-tooltip>
        </div>
      </div>

      <!-- 消息列表 -->
      <div class="chat-messages" ref="messagesRef">
        <!-- 欢迎消息 -->
        <div v-if="messages.length === 0" class="welcome-section">
          <div class="welcome-icon">
            <el-icon><MagicStick /></el-icon>
          </div>
          <h3>你好，我是 TechHub AI 助手</h3>
          <p>我可以帮你查询数据、分析业务、辅助工作</p>
          <div class="quick-actions">
            <el-button 
              v-for="action in quickActions" 
              :key="action.text"
              size="small"
              @click="sendQuickMessage(action.text)"
            >
              {{ action.text }}
            </el-button>
          </div>
        </div>

        <!-- 消息气泡 -->
        <div 
          v-for="(msg, index) in messages" 
          :key="index"
          class="message-item"
          :class="msg.role"
        >
          <div class="message-avatar">
            <el-avatar 
              v-if="msg.role === 'user'"
              :size="32"
              :src="userAvatar"
            >
              {{ userInitials }}
            </el-avatar>
            <el-avatar 
              v-else
              :size="32"
              class="ai-avatar"
            >
              <el-icon><MagicStick /></el-icon>
            </el-avatar>
          </div>
          <div class="message-content">
            <div class="message-bubble markdown-body" v-html="renderMarkdown(msg.content)"></div>
            <div class="message-time">{{ formatTime(msg.time || msg.created_at) }}</div>
          </div>
        </div>

        <!-- 加载中 -->
        <div v-if="isLoading" class="message-item assistant">
          <div class="message-avatar">
            <el-avatar :size="32" class="ai-avatar">
              <el-icon><MagicStick /></el-icon>
            </el-avatar>
          </div>
          <div class="message-content">
            <div class="message-bubble">
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="chat-input-area">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="2"
          placeholder="输入你的问题，按 Enter 发送，Shift+Enter 换行..."
          resize="none"
          @keydown.enter.prevent="handleEnter"
        />
        <el-button 
          type="primary" 
          class="send-btn"
          :loading="isLoading"
          :disabled="!inputMessage.trim()"
          @click="sendMessage"
        >
          <el-icon><Promotion /></el-icon>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { sendChatMessage, getConversations, createConversation, getConversation, updateConversation, deleteConversation as apiDeleteConversation } from '@/api/ai'
import { ElMessage, ElMessageBox } from 'element-plus'
import { marked } from 'marked'
import { Plus } from '@element-plus/icons-vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close'])

const userStore = useUserStore()
const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const messagesRef = ref(null)
const conversations = ref([])
const currentConversationId = ref(null)
const showSidebar = ref(false)
const isExpanded = ref(false) // 是否放大

// 配置 marked
marked.setOptions({
  breaks: true,
  gfm: true
})

// 快捷操作
const quickActions = [
  { text: '我有哪些待办任务？' },
  { text: '查看我负责的客户' },
  { text: '分析客户合作潜力' },
  { text: '生成本周工作周报' },
  { text: '有什么需要我关注的？' }
]

// 用户信息
const userAvatar = computed(() => userStore.userInfo?.avatar || '')
const userInitials = computed(() => {
  const name = userStore.userInfo?.real_name || userStore.userInfo?.username || 'U'
  return name.charAt(0).toUpperCase()
})

// 排序后的会话列表（置顶在前）
const sortedConversations = computed(() => {
  return [...conversations.value].sort((a, b) => {
    if (a.is_pinned !== b.is_pinned) {
      return b.is_pinned ? 1 : -1
    }
    return new Date(b.updated_at) - new Date(a.updated_at)
  })
})

// 监听面板打开
watch(() => props.isOpen, (val) => {
  if (val) {
    nextTick(() => scrollToBottom())
    loadConversations()
  } else {
    // 关闭时恢复默认大小
    isExpanded.value = false
  }
})

// 监听消息变化，自动滚动
watch(() => messages.value.length, () => {
  nextTick(() => scrollToBottom())
})

onMounted(() => {
  loadConversations()
})

function scrollToBottom() {
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

function handleEnter(e) {
  if (!e.shiftKey) {
    sendMessage()
  }
}

function sendQuickMessage(text) {
  inputMessage.value = text
  sendMessage()
}

function renderMarkdown(content) {
  if (!content) return ''
  return marked.parse(content)
}

// 放大/缩小切换
function toggleExpand() {
  isExpanded.value = !isExpanded.value
  nextTick(() => scrollToBottom())
}

async function loadConversations() {
  try {
    const res = await getConversations()
    if (res.success) {
      conversations.value = res.data || []
    }
  } catch (e) {
    console.error('加载会话列表失败:', e)
  }
}

async function startNewChat() {
  messages.value = []
  currentConversationId.value = null
  showSidebar.value = false
}

async function switchConversation(id) {
  if (id === currentConversationId.value) {
    showSidebar.value = false
    return
  }
  
  try {
    const res = await getConversation(id)
    if (res.success) {
      currentConversationId.value = id
      // 转换消息格式
      messages.value = (res.data?.messages || []).map(m => ({
        role: m.role,
        content: m.content,
        time: m.timestamp || m.created_at,
        tool_calls: m.tool_calls || []
      }))
      showSidebar.value = false
    }
  } catch (e) {
    ElMessage.error('加载会话失败')
  }
}

async function pinConversation(id, isPinned) {
  try {
    const res = await updateConversation(id, { is_pinned: isPinned })
    if (res.success) {
      const conv = conversations.value.find(c => c.id === id)
      if (conv) {
        conv.is_pinned = isPinned
      }
    }
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

async function renameConversation(conv) {
  try {
    const { value } = await ElMessageBox.prompt('请输入新标题', '重命名', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputValue: conv.title,
      inputValidator: (val) => val ? true : '标题不能为空'
    })
    
    const res = await updateConversation(conv.id, { title: value })
    if (res.success) {
      conv.title = value
      ElMessage.success('重命名成功')
    }
  } catch {
    // 用户取消
  }
}

async function deleteConversation(id) {
  try {
    await ElMessageBox.confirm('确定要删除这个会话吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const res = await apiDeleteConversation(id)
    if (res.success) {
      conversations.value = conversations.value.filter(c => c.id !== id)
      if (currentConversationId.value === id) {
        messages.value = []
        currentConversationId.value = null
      }
      ElMessage.success('删除成功')
    }
  } catch {
    // 用户取消
  }
}

async function sendMessage() {
  const message = inputMessage.value.trim()
  if (!message || isLoading.value) return

  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: message,
    time: new Date()
  })

  inputMessage.value = ''
  isLoading.value = true

  try {
    // 使用非流式接口（支持工具调用）
    const res = await sendChatMessage(message, currentConversationId.value)
    
    if (res.success) {
      const data = res.data
      messages.value.push({
        role: 'assistant',
        content: data?.content || '暂无回复',
        time: new Date()
      })
      
      // 更新当前会话ID
      if (data?.conversation_id) {
        currentConversationId.value = data.conversation_id
        // 刷新会话列表
        loadConversations()
      }
    } else {
      messages.value.push({
        role: 'assistant',
        content: res.message || '服务异常，请稍后重试',
        time: new Date()
      })
    }
  } catch (error) {
    console.error('AI对话错误:', error)
    messages.value.push({
      role: 'assistant',
      content: '网络异常，请检查连接后重试。',
      time: new Date()
    })
    ElMessage.error('AI 服务调用失败')
  } finally {
    isLoading.value = false
  }
}

async function clearChat() {
  try {
    await ElMessageBox.confirm('确定要清空当前对话吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    messages.value = []
    currentConversationId.value = null
    ElMessage.success('对话已清空')
  } catch {
    // 用户取消
  }
}

function closePanel() {
  emit('close')
}

function formatTime(time) {
  if (!time) return ''
  const date = new Date(time)
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return `${hours}:${minutes}`
}
</script>

<style scoped lang="scss">
.ai-chat-panel {
  position: fixed;
  bottom: 80px;
  right: 20px;
  width: 460px;
  height: 620px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  display: flex;
  overflow: hidden;
  z-index: 2000;
  transform: scale(0.9) translateY(20px);
  opacity: 0;
  pointer-events: none;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);

  &.is-open {
    transform: scale(1) translateY(0);
    opacity: 1;
    pointer-events: auto;
  }

  // 放大状态
  &.is-expanded {
    width: calc(100vw - 240px); // 留出侧边栏空间
    height: calc(100vh - 100px);
    bottom: 20px;
    right: 20px;
    border-radius: 12px;
  }
}

// 侧边栏
.sidebar-conversations {
  width: 0;
  background: #f5f7fa;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: width 0.3s ease;

  &.show {
    width: 200px;
  }

  .sidebar-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px;
    border-bottom: 1px solid #e4e7ed;

    .sidebar-title {
      font-weight: 600;
      font-size: 14px;
      color: #333;
    }
  }

  .new-chat-btn {
    padding: 10px 12px;
    border-bottom: 1px solid #e4e7ed;

    .el-button {
      width: 100%;
    }
  }

  .conversation-list {
    flex: 1;
    overflow-y: auto;
    padding: 8px;

    .conversation-item {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 8px 10px;
      border-radius: 8px;
      cursor: pointer;
      margin-bottom: 4px;
      transition: background 0.2s;

      &:hover {
        background: #e4e7ed;

        .conv-actions {
          opacity: 1;
        }
      }

      &.active {
        background: #667eea;
        color: #fff;

        .conv-actions {
          opacity: 1;
          color: #fff;
        }
      }

      &.pinned {
        .pin-icon {
          color: #f7ba2a;
        }
      }

      .pin-icon {
        font-size: 12px;
        flex-shrink: 0;
      }

      .conv-title {
        flex: 1;
        font-size: 13px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .conv-actions {
        opacity: 0;
        transition: opacity 0.2s;

        .more-icon {
          font-size: 14px;
          cursor: pointer;
          padding: 2px;
          border-radius: 4px;

          &:hover {
            background: rgba(0, 0, 0, 0.1);
          }
        }
      }
    }

    .empty-conversations {
      text-align: center;
      padding: 20px;
      color: #999;
      font-size: 13px;
    }
  }
}

// 主聊天区域
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;

  .header-left {
    display: flex;
    align-items: center;
    gap: 8px;

    .sidebar-toggle {
      color: #fff;
      font-size: 16px;
      padding: 2px;
    }

    .ai-icon {
      font-size: 20px;
    }

    .title {
      font-weight: 600;
      font-size: 15px;
    }
  }

  .header-actions {
    display: flex;
    gap: 4px;

    .el-button {
      color: #fff;
      font-size: 16px;

      &:hover {
        color: rgba(255, 255, 255, 0.8);
      }
    }
  }
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #f8f9fa;

  &::-webkit-scrollbar {
    width: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 2px;
  }
}

.welcome-section {
  text-align: center;
  padding: 40px 20px;

  .welcome-icon {
    font-size: 48px;
    color: #667eea;
    margin-bottom: 16px;
  }

  h3 {
    margin: 0 0 8px;
    color: #333;
    font-size: 18px;
  }

  p {
    margin: 0 0 24px;
    color: #666;
    font-size: 14px;
  }

  .quick-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;

    .el-button {
      border-radius: 16px;
    }
  }
}

.message-item {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;

  &.user {
    flex-direction: row-reverse;

    .message-content {
      align-items: flex-end;
    }

    .message-bubble {
      background: #667eea;
      color: #fff;
      border-radius: 16px 16px 4px 16px;
    }
  }

  &.assistant {
    .message-bubble {
      background: #fff;
      color: #333;
      border-radius: 16px 16px 16px 4px;
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    }
  }
}

.message-avatar {
  flex-shrink: 0;

  .ai-avatar {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
  }
}

.message-content {
  display: flex;
  flex-direction: column;
  max-width: 75%;
}

.message-bubble {
  padding: 10px 14px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;

  // Markdown 样式
  :deep(h1), :deep(h2), :deep(h3), :deep(h4) {
    margin: 8px 0 6px;
    font-weight: 600;
  }

  :deep(p) {
    margin: 4px 0;
  }

  :deep(ul), :deep(ol) {
    margin: 4px 0;
    padding-left: 20px;
  }

  :deep(li) {
    margin: 2px 0;
  }

  :deep(table) {
    width: 100%;
    border-collapse: collapse;
    margin: 8px 0;
    font-size: 13px;
  }

  :deep(th), :deep(td) {
    border: 1px solid #e0e0e0;
    padding: 6px 10px;
    text-align: left;
  }

  :deep(th) {
    background: #f5f5f5;
    font-weight: 600;
  }

  :deep(tr:nth-child(even)) {
    background: #fafafa;
  }

  :deep(code) {
    background: rgba(0, 0, 0, 0.06);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
    font-size: 13px;
  }

  :deep(pre) {
    background: #f5f5f5;
    padding: 10px;
    border-radius: 6px;
    overflow-x: auto;
    margin: 8px 0;

    code {
      background: none;
      padding: 0;
    }
  }

  :deep(blockquote) {
    border-left: 3px solid #667eea;
    margin: 8px 0;
    padding-left: 12px;
    color: #666;
  }

  :deep(strong) {
    font-weight: 600;
  }

  :deep(em) {
    font-style: italic;
  }

  :deep(a) {
    color: #667eea;
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }

  :deep(hr) {
    border: none;
    border-top: 1px solid #eee;
    margin: 10px 0;
  }
}

.message-time {
  font-size: 11px;
  color: #999;
  margin-top: 4px;
  padding: 0 4px;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 0;

  span {
    width: 8px;
    height: 8px;
    background: #999;
    border-radius: 50%;
    animation: typing 1.4s infinite ease-in-out both;

    &:nth-child(1) { animation-delay: -0.32s; }
    &:nth-child(2) { animation-delay: -0.16s; }
  }
}

@keyframes typing {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

.chat-input-area {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  background: #fff;
  border-top: 1px solid #eee;

  .el-textarea {
    flex: 1;

    :deep(.el-textarea__inner) {
      border-radius: 12px;
      resize: none;
    }
  }

  .send-btn {
    align-self: flex-end;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;

    .el-icon {
      font-size: 18px;
    }
  }
}

// 响应式
@media (max-width: 768px) {
  .ai-chat-panel {
    width: calc(100vw - 40px);
    height: calc(100vh - 100px);
    bottom: 20px;
    right: 20px;

    &.is-expanded {
      width: calc(100vw - 40px);
      height: calc(100vh - 100px);
      bottom: 20px;
      right: 20px;
    }
  }
}

@media (max-width: 480px) {
  .ai-chat-panel {
    width: 100%;
    height: 100%;
    bottom: 0;
    right: 0;
    border-radius: 0;

    &.is-expanded {
      width: 100%;
      height: 100%;
      bottom: 0;
      right: 0;
      border-radius: 0;
    }
  }
}
</style>
