<template>
  <!-- 第三次迭代陈思言负责 -->
  <div class="notifications-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>{{ $t('notifications.pageTitle') }}</h2>
        <el-tag v-if="unreadCount > 0" type="danger" size="small" effect="dark" round>
          {{ unreadCount }} {{ $t('notifications.unreadSuffix') }}
        </el-tag>
      </div>
      <div class="header-right">
        <el-button type="primary" :disabled="unreadCount === 0" @click="handleMarkAllRead">
          <el-icon><Check /></el-icon>
          {{ $t('notifications.markAllRead') }}
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card" :class="{ active: activeFilter === 'all' }" @click="setFilter('all')">
          <div class="stat-icon all">
            <el-icon><Bell /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.all }}</div>
            <div class="stat-label">{{ $t('notifications.allMessages') }}</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card" :class="{ active: activeFilter === 'unread' }" @click="setFilter('unread')">
          <div class="stat-icon unread">
            <el-icon><Message /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.unread }}</div>
            <div class="stat-label">{{ $t('notifications.unreadMessages') }}</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card" :class="{ active: activeFilter === 'task' }" @click="setFilter('task')">
          <div class="stat-icon task">
            <el-icon><List /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.task }}</div>
            <div class="stat-label">{{ $t('notifications.taskMessages') }}</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card" :class="{ active: activeFilter === 'approval' }" @click="setFilter('approval')">
          <div class="stat-icon approval">
            <el-icon><DocumentChecked /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.approval }}</div>
            <div class="stat-label">{{ $t('notifications.approvalMessages') }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 消息列表 -->
    <el-card class="notifications-card" v-loading="loading">
      <div v-if="filteredNotifications.length === 0" class="empty-state">
        <el-empty :description="$t('notifications.noMessages')">
          <template #image>
            <el-icon :size="80" color="#dcdfe6"><Bell /></el-icon>
          </template>
        </el-empty>
      </div>

      <div v-else class="notification-list">
        <div
          v-for="item in filteredNotifications"
          :key="item.id"
          class="notification-item"
          :class="{ unread: !item.is_read }"
          @click="handleClick(item)"
        >
          <!-- 左侧：类型图标 -->
          <div class="item-left">
            <div class="type-icon" :class="item.notification_type">
              <el-icon size="20">
                <component :is="getTypeIcon(item.notification_type)" />
              </el-icon>
            </div>
            <div v-if="!item.is_read" class="unread-dot"></div>
          </div>

          <!-- 中间：内容 -->
          <div class="item-content">
            <div class="item-header">
              <span class="item-title">{{ item.title }}</span>
              <el-tag :type="getTypeTag(item.notification_type)" size="small" effect="light">
                {{ getTypeLabel(item.notification_type) }}
              </el-tag>
            </div>
            <div class="item-body">
              <pre class="item-text">{{ item.content }}</pre>
            </div>
            <div class="item-footer">
              <span class="item-time">
                <el-icon><Clock /></el-icon>
                {{ formatTime(item.created_at) }}
              </span>
              <span v-if="item.related_type && item.related_id" class="item-link">
                <el-icon><Link /></el-icon>
                {{ $t('notifications.viewDetail') }}
              </span>
            </div>
          </div>

          <!-- 右侧：操作 -->
          <div class="item-actions">
            <el-button
              v-if="!item.is_read"
              type="primary"
              link
              size="small"
              @click.stop="handleMarkRead(item)"
            >
              {{ $t('notifications.markRead') }}
            </el-button>
            <el-icon v-else class="read-check"><Check /></el-icon>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchNotifications"
          @current-change="fetchNotifications"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
// 第三次迭代陈思言负责
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Bell, Message, List, DocumentChecked, Check,
  Clock, Link, TrendCharts, Money, Warning, Plus
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import {
  getNotifications,
  getUnreadCount,
  markAsRead,
  markAllAsRead
} from '@/api/notifications'

const router = useRouter()
const { t } = useI18n()

const loading = ref(false)
const notifications = ref([])
const unreadCount = ref(0)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const activeFilter = ref('all')

// 统计
const stats = computed(() => {
  const all = notifications.value.length
  const unread = notifications.value.filter(n => !n.is_read).length
  const task = notifications.value.filter(n => n.notification_type === 'task').length
  const approval = notifications.value.filter(n => n.notification_type === 'approval').length
  return { all, unread, task, approval }
})

// 过滤后的列表
const filteredNotifications = computed(() => {
  if (activeFilter.value === 'all') return notifications.value
  if (activeFilter.value === 'unread') return notifications.value.filter(n => !n.is_read)
  return notifications.value.filter(n => n.notification_type === activeFilter.value)
})

const fetchNotifications = async () => {
  loading.value = true
  try {
    const params = {
      page: page.value,
      per_page: pageSize.value
    }
    const res = await getNotifications(params)
    notifications.value = res.notifications || []
    total.value = res.total || 0
    unreadCount.value = res.unread_count || 0
  } catch (error) {
    console.error(t('notifications.fetchFailed'), error)
    ElMessage.error(t('notifications.fetchFailed'))
  } finally {
    loading.value = false
  }
}

const setFilter = (filter) => {
  activeFilter.value = filter
}

const handleMarkRead = async (item) => {
  try {
    await markAsRead(item.id)
    item.is_read = true
    unreadCount.value = Math.max(0, unreadCount.value - 1)
    ElMessage.success(t('notifications.markedAsRead'))
  } catch (error) {
    console.error(t('notifications.markReadFailed'), error)
  }
}

const handleMarkAllRead = async () => {
  try {
    await ElMessageBox.confirm(t('notifications.markAllReadConfirm'), t('common.tip'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning'
    })
    await markAllAsRead()
    notifications.value.forEach(n => n.is_read = true)
    unreadCount.value = 0
    ElMessage.success(t('notifications.allMarkedAsRead'))
  } catch (error) {
    if (error !== 'cancel') {
      console.error(t('notifications.markAllReadFailed'), error)
    }
  }
}

const handleClick = (item) => {
  // 标记已读
  if (!item.is_read) {
    handleMarkRead(item)
  }
  // 跳转到相关页面
  if (item.related_type === 'task' && item.related_id) {
    router.push('/tasks')
  } else if (item.related_type === 'approval' && item.related_id) {
    router.push('/approvals')
  } else if (item.related_type === 'project' && item.related_id) {
    router.push(`/projects/${item.related_id}`)
  }
}

const getTypeIcon = (type) => {
  const map = {
    task: List,
    approval: DocumentChecked,
    finance: Money,
    system: Bell
  }
  return map[type] || Bell
}

const getTypeTag = (type) => {
  const map = {
    task: 'success',
    approval: 'warning',
    finance: 'danger',
    system: 'info'
  }
  return map[type] || 'info'
}

const getTypeLabel = (type) => {
  const map = {
    task: t('notifications.task'),
    approval: t('notifications.approval'),
    finance: t('notifications.financial'),
    system: t('notifications.system')
  }
  return map[type] || t('notifications.system')
}

const formatTime = (time) => {
  if (!time) return ''
  const date = dayjs(time)
  const now = dayjs()
  if (date.isSame(now, 'day')) {
    return date.format(t('notifications.todayFormat'))
  } else if (date.isSame(now.subtract(1, 'day'), 'day')) {
    return date.format(t('notifications.yesterdayFormat'))
  } else if (date.isSame(now, 'year')) {
    return date.format('MM-DD HH:mm')
  }
  return date.format('YYYY-MM-DD HH:mm')
}

onMounted(() => {
  fetchNotifications()
})
</script>

<style scoped lang="scss">
.notifications-page {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    .header-left {
      display: flex;
      align-items: center;
      gap: 12px;

      h2 {
        margin: 0;
        font-size: 20px;
        font-weight: 600;
      }
    }
  }

  .stats-row {
    margin-bottom: 20px;

    .stat-card {
      background: #fff;
      border-radius: 12px;
      padding: 16px 20px;
      display: flex;
      align-items: center;
      gap: 14px;
      cursor: pointer;
      border: 2px solid transparent;
      transition: all 0.3s;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);

      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
      }

      &.active {
        border-color: #1890ff;
        background: #f0f5ff;
      }

      .stat-icon {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;

        &.all { background: #e6f7ff; color: #1890ff; }
        &.unread { background: #fff2f0; color: #ff4d4f; }
        &.task { background: #f6ffed; color: #52c41a; }
        &.approval { background: #fff7e6; color: #fa8c16; }
      }

      .stat-info {
        .stat-value {
          font-size: 24px;
          font-weight: 700;
          color: #1f1f1f;
          line-height: 1;
        }
        .stat-label {
          font-size: 13px;
          color: #999;
          margin-top: 4px;
        }
      }
    }
  }

  .notifications-card {
    border-radius: 12px;

    .empty-state {
      padding: 60px 0;
    }

    .notification-list {
      .notification-item {
        display: flex;
        align-items: flex-start;
        gap: 16px;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 8px;
        transition: all 0.2s;
        cursor: pointer;
        border: 1px solid #f0f0f0;

        &:hover {
          background: #fafafa;
          border-color: #d9d9d9;
        }

        &.unread {
          background: #f0f5ff;
          border-color: #bae0ff;

          &:hover {
            background: #e6f0ff;
          }

          .item-title {
            font-weight: 600;
            color: #1f1f1f;
          }
        }

        .item-left {
          position: relative;
          flex-shrink: 0;

          .type-icon {
            width: 44px;
            height: 44px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;

            &.task { background: #f6ffed; color: #52c41a; }
            &.approval { background: #fff7e6; color: #fa8c16; }
            &.finance { background: #fff2f0; color: #ff4d4f; }
            &.system { background: #e6f7ff; color: #1890ff; }
          }

          .unread-dot {
            position: absolute;
            top: -2px;
            right: -2px;
            width: 10px;
            height: 10px;
            background: #ff4d4f;
            border-radius: 50%;
            border: 2px solid #fff;
          }
        }

        .item-content {
          flex: 1;
          min-width: 0;

          .item-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 8px;

            .item-title {
              font-size: 15px;
              color: #333;
              flex: 1;
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
            }
          }

          .item-body {
            margin-bottom: 8px;

            .item-text {
              margin: 0;
              font-size: 13px;
              color: #666;
              line-height: 1.6;
              white-space: pre-wrap;
              word-break: break-word;
              font-family: inherit;
            }
          }

          .item-footer {
            display: flex;
            align-items: center;
            gap: 16px;
            font-size: 12px;
            color: #999;

            .item-time, .item-link {
              display: flex;
              align-items: center;
              gap: 4px;
            }

            .item-link {
              color: #1890ff;
            }
          }
        }

        .item-actions {
          flex-shrink: 0;
          padding-top: 4px;

          .read-check {
            color: #52c41a;
            font-size: 16px;
          }
        }
      }
    }

    .pagination-wrapper {
      margin-top: 20px;
      display: flex;
      justify-content: flex-end;
    }
  }
}
</style>
