<template>
  <el-container class="main-layout">
    <!-- 侧边栏 -->
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <el-icon size="28" color="#1890ff"><Connection /></el-icon>
        <span class="logo-text">TechHub</span>
      </div>
      
      <el-menu
        :default-active="$route.path"
        router
        class="sidebar-menu"
        background-color="#001529"
        text-color="#a6adb4"
        active-text-color="#fff"
      >
        <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
          <el-icon>
            <component :is="item.icon" />
          </el-icon>
          <span>{{ item.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <!-- 顶部导航 -->
      <el-header class="header">
        <div class="header-left">
          <breadcrumb />
        </div>
        <div class="header-right">
          <!-- 【自动化迭代】消息通知中心 - 点击跳转消息中心页 -->
          <el-badge
            :value="totalUnreadCount"
            :hidden="totalUnreadCount === 0"
            class="message-badge"
            @click="router.push('/notifications')"
          >
            <el-icon size="20"><Bell /></el-icon>
          </el-badge>
          
          <el-dropdown @command="handleCommand">
            <div class="user-info">
              <el-avatar :size="32" :src="userStore.userInfo?.avatar">
                {{ userStore.userInfo?.real_name?.charAt(0) || 'U' }}
              </el-avatar>
              <span class="username">{{ userStore.userInfo?.real_name }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="settings">系统设置</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getPendingCount, getApprovals } from '@/api/approvals'
import { getNotifications, getUnreadCount, markAsRead, markAllAsRead } from '@/api/notifications'
import { initSocket, disconnectSocket } from '@/utils/socket'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const pendingCount = ref(0)
const pendingApprovals = ref([])
const notifications = ref([])
const unreadCount = ref(0)

const totalUnreadCount = computed(() => pendingCount.value + unreadCount.value)

// 高管角色（总经理、副总经理）：拥有 all 权限
const MANAGER_ROLES = ['super_admin', 'deputy_general_manager']
const isManager = computed(() => userStore.userInfo?.roles?.some(r => MANAGER_ROLES.includes(r.name)))

const menuItems = computed(() => [
  { path: '/dashboard', title: '工作台', icon: 'HomeFilled' },
  { path: '/projects', title: '项目管理', icon: 'FolderOpened' },
  { path: '/clients', title: '客户管理', icon: 'OfficeBuilding' },
  { path: '/contracts', title: '合同管理', icon: 'DocumentCopy' },
  { path: '/tickets', title: '客户工单', icon: 'ChatDotSquare' },
  { path: '/tasks', title: '我的任务', icon: 'List' },
  { path: '/approvals', title: '审批中心', icon: 'DocumentChecked' },
  // 数据中心：仅总经理、副总经理、数据分析员可见
  // 部门负责人、项目经理、项目组长、普通成员无法查看，需申请权限
  ...(userStore.userInfo?.roles?.some(r =>
    ['super_admin', 'deputy_general_manager', 'data_analyst'].includes(r.name)
  ) ? [
    { path: '/analytics', title: '数据中心', icon: 'TrendCharts' }
  ] : []),
  // 用户管理、组织架构：高管可见
  ...(isManager.value ? [
    { path: '/users', title: '用户管理', icon: 'UserFilled' },
    { path: '/departments', title: '组织架构', icon: 'OfficeBuilding' }
  ] : []),
  // 【第二次迭代】考勤工时菜单（所有登录用户可见）
  { path: '/attendance', title: '考勤工时', icon: 'Clock' },
  // 审计日志：高管可见
  ...(isManager.value ? [
    { path: '/audit-logs', title: '审计日志', icon: 'Document' }
  ] : []),
  // 财务看板：高管可见
  ...(isManager.value ? [
    { path: '/finance', title: '财务看板', icon: 'TrendCharts' }
  ] : []),
  { path: '/expenses', title: '费用报销', icon: 'Money' },
  { path: '/payments', title: '收付款', icon: 'Wallet' }
])

const fetchPendingCount = async () => {
  try {
    const res = await getPendingCount()
    pendingCount.value = res.my_pending
  } catch (error) {
    console.error('获取待办数量失败', error)
  }
}

const fetchPendingApprovals = async () => {
  try {
    const res = await getApprovals({ scope: 'pending_me', per_page: 5 })
    pendingApprovals.value = res.approvals || []
  } catch (error) {
    console.error('获取待办列表失败', error)
  }
}

const fetchNotifications = async () => {
  try {
    const [listRes, countRes] = await Promise.all([
      getNotifications({ per_page: 5, is_read: false }),
      getUnreadCount()
    ])
    notifications.value = listRes.notifications || []
    unreadCount.value = countRes.unread_count || 0
  } catch (error) {
    console.error('获取通知失败', error)
  }
}

const readNotification = async (item) => {
  try {
    await markAsRead(item.id)
    item.is_read = true
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  } catch (error) {
    console.error('标记已读失败', error)
  }
}

const markAllRead = async () => {
  try {
    await markAllAsRead()
    notifications.value.forEach(n => n.is_read = true)
    unreadCount.value = 0
  } catch (error) {
    console.error('全部已读失败', error)
  }
}

const goToApprovals = () => {
  router.push('/approvals')
}

const goToApprovalDetail = (item) => {
  router.push('/approvals')
}

const formatTime = (date) => {
  return date ? dayjs(date).format('MM-DD HH:mm') : ''
}

const handleCommand = (command) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'settings':
      ElMessage.info('系统设置功能开发中')
      break
    case 'logout':
      ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        userStore.logout()
        router.push('/login')
      })
      break
  }
}

onMounted(() => {
  // 【修复】刷新页面后确保用户信息已加载
  if (!userStore.userInfo && userStore.token) {
    userStore.fetchUserInfo().then(() => {
      fetchPendingCount()
      fetchPendingApprovals()
      fetchNotifications()
      // 【自动化】初始化 WebSocket
      initSocket(userStore.token)
    })
  } else {
    fetchPendingCount()
    fetchPendingApprovals()
    fetchNotifications()
    // 【自动化】初始化 WebSocket
    initSocket(userStore.token)
  }

  // 【自动化】监听新通知事件，刷新通知列表
  window.addEventListener('new-notification', handleNewNotification)
})

onUnmounted(() => {
  disconnectSocket()
  window.removeEventListener('new-notification', handleNewNotification)
})

const handleNewNotification = () => {
  // 收到新通知时刷新未读数和通知列表
  fetchNotifications()
  fetchPendingCount()
}
</script>

<style scoped lang="scss">
.main-layout {
  height: 100vh;
}

.sidebar {
  background-color: #001529;
  
  .logo {
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    
    .logo-text {
      color: #fff;
      font-size: 20px;
      font-weight: 600;
      margin-left: 12px;
    }
  }
  
  .sidebar-menu {
    border-right: none;
    
    :deep(.el-menu-item) {
      height: 48px;
      line-height: 48px;
      
      &:hover {
        background-color: #1890ff !important;
      }
      
      &.is-active {
        background-color: #1890ff !important;
      }
    }
  }
}

.header {
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 24px;
    
    .message-badge {
      cursor: pointer;
      
      &:hover {
        color: #1890ff;
      }
    }
    
    .notification-popover {
      .notification-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 12px;
        border-bottom: 1px solid #eee;
        margin-bottom: 8px;
        font-weight: 500;
      }
      
      .notification-section {
        margin-bottom: 12px;
        .section-title {
          font-size: 12px;
          color: #999;
          margin-bottom: 8px;
          padding-left: 4px;
        }
      }
      
      .notification-list {
        max-height: 300px;
        overflow-y: auto;
        
        .notification-item {
          padding: 10px 0;
          border-bottom: 1px solid #f5f5f5;
          cursor: pointer;
          
          &:last-child {
            border-bottom: none;
          }
          
          &:hover {
            background-color: #f5f7fa;
            margin: 0 -12px;
            padding-left: 12px;
            padding-right: 12px;
          }
          
          &.unread {
            background-color: #f0f5ff;
            margin: 0 -12px;
            padding-left: 12px;
            padding-right: 12px;
          }
          
          .notification-title {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
            margin-bottom: 4px;
          }
          
          .notification-meta {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: #999;
          }
        }
      }
    }
    
    .user-info {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      padding: 4px 8px;
      border-radius: 4px;
      transition: background-color 0.2s;
      
      &:hover {
        background-color: #f5f7fa;
      }
      
      .username {
        font-size: 14px;
        color: #333;
      }
    }
  }
}

.main-content {
  background-color: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
