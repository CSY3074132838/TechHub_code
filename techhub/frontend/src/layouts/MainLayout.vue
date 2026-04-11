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
          <el-badge :value="pendingCount" class="message-badge" v-if="pendingCount > 0">
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
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getPendingCount } from '@/api/approvals'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const pendingCount = ref(0)

const menuItems = computed(() => [
  { path: '/dashboard', title: '工作台', icon: 'HomeFilled' },
  { path: '/projects', title: '项目管理', icon: 'FolderOpened' },
  { path: '/tasks', title: '我的任务', icon: 'List' },
  { path: '/approvals', title: '审批中心', icon: 'DocumentChecked' },
  { path: '/analytics', title: '数据中心', icon: 'TrendCharts' },
  ...(userStore.isAdmin ? [{ path: '/users', title: '用户管理', icon: 'UserFilled' }] : [])
])

const fetchPendingCount = async () => {
  try {
    const res = await getPendingCount()
    pendingCount.value = res.my_pending
  } catch (error) {
    console.error('获取待办数量失败', error)
  }
}

const handleCommand = (command) => {
  switch (command) {
    case 'profile':
      ElMessage.info('个人中心功能开发中')
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
  fetchPendingCount()
})
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
