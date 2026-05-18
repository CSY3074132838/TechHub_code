import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { public: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile.vue'),
    meta: { title: '个人中心', icon: 'User' }
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '工作台', icon: 'HomeFilled' }
      },
      {
        path: '/projects',
        name: 'Projects',
        component: () => import('@/views/Projects.vue'),
        meta: { title: '项目管理', icon: 'FolderOpened' }
      },
      {
        path: '/projects/:id',
        name: 'ProjectDetail',
        component: () => import('@/views/ProjectDetail.vue'),
        meta: { title: '项目详情', hidden: true }
      },
      {
        path: '/tasks',
        name: 'Tasks',
        component: () => import('@/views/Tasks.vue'),
        meta: { title: '我的任务', icon: 'List' }
      },
      {
        path: '/approvals',
        name: 'Approvals',
        component: () => import('@/views/Approvals.vue'),
        meta: { title: '审批中心', icon: 'DocumentChecked' }
      },
      {
        path: '/analytics',
        name: 'Analytics',
        component: () => import('@/views/Analytics.vue'),
        meta: { title: '数据中心', icon: 'TrendCharts' }
      },
      {
        path: '/clients',
        name: 'Clients',
        component: () => import('@/views/Clients.vue'),
        meta: { title: '客户管理', icon: 'OfficeBuilding' }
      },
      {
        path: '/clients/:id',
        name: 'ClientDetail',
        component: () => import('@/views/ClientDetail.vue'),
        meta: { title: '客户详情', hidden: true }
      },
      {
        path: '/contracts',
        name: 'Contracts',
        component: () => import('@/views/Contracts.vue'),
        meta: { title: '合同管理', icon: 'DocumentCopy' }
      },
      {
        path: '/tickets',
        name: 'Tickets',
        component: () => import('@/views/Tickets.vue'),
        meta: { title: '客户工单', icon: 'ChatDotSquare' }
      },
      {
        path: '/users',
        name: 'Users',
        component: () => import('@/views/Users.vue'),
        meta: { title: '用户管理', icon: 'UserFilled', admin: true }
      },
      // 【第二次迭代】组织架构管理
      {
        path: '/departments',
        name: 'Departments',
        component: () => import('@/views/Departments.vue'),
        meta: { title: '组织架构', icon: 'OfficeBuilding', admin: true }
      },
      // 【第二次迭代】考勤与工时
      {
        path: '/attendance',
        name: 'Attendance',
        component: () => import('@/views/Attendance.vue'),
        meta: { title: '考勤工时', icon: 'Clock' }
      },
      {
        path: '/audit-logs',
        name: 'AuditLogs',
        component: () => import('@/views/AuditLogs.vue'),
        meta: { title: '审计日志', icon: 'Document', admin: true }
      },
      // 【第二次迭代】财务管理路由
      {
        path: '/finance',
        name: 'Finance',
        component: () => import('@/views/Finance.vue'),
        meta: { title: '财务看板', icon: 'TrendCharts', admin: true }
      },
      {
        path: '/expenses',
        name: 'Expenses',
        component: () => import('@/views/Expenses.vue'),
        meta: { title: '费用报销', icon: 'Money' }
      },
      {
        path: '/payments',
        name: 'Payments',
        component: () => import('@/views/Payments.vue'),
        meta: { title: '收付款', icon: 'Wallet' }
      },
      // 【自动化迭代】消息中心
      {
        path: '/notifications',
        name: 'Notifications',
        component: () => import('@/views/Notifications.vue'),
        meta: { title: '消息中心', icon: 'Bell' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()

  // 公开页面直接放行
  if (to.meta.public) {
    next()
    return
  }

  // 检查登录状态
  if (!userStore.token) {
    next('/login')
    return
  }

  // 如果已登录但用户信息未加载（如刷新页面），先加载用户信息
  if (!userStore.userInfo) {
    try {
      await userStore.fetchUserInfo()
    } catch (error) {
      console.error('获取用户信息失败', error)
    }
  }

  // 加载后再次检查（可能 token 已过期）
  if (!userStore.token) {
    next('/login')
    return
  }

  // 检查管理员权限
  if (to.meta.admin && !userStore.isAdmin) {
    next('/')
    return
  }

  next()
})

// 捕获路由懒加载失败（如代码分割 chunk 更新后旧缓存失效），自动刷新页面
router.onError((error) => {
  const isChunkLoadError = error.message?.includes('Failed to fetch dynamically imported module')
    || error.message?.includes('Loading chunk')
    || error.message?.includes('Loading CSS chunk')

  if (isChunkLoadError) {
    console.warn('路由组件加载失败，尝试刷新页面', error)
    window.location.reload()
  } else {
    console.error('路由错误', error)
  }
})

export default router
