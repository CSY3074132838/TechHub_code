<template>
  <div class="audit-logs-page">
    <div class="page-header">
      <h2>审计日志</h2>
      <el-button type="primary" @click="exportLogs">
        <el-icon><Download /></el-icon>导出日志
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ stats.today_count || 0 }}</div>
          <div class="stat-label">今日操作</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ stats.week_count || 0 }}</div>
          <div class="stat-label">本周操作</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value danger">{{ stats.failed_logins || 0 }}</div>
          <div class="stat-label">登录失败（7天）</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value warning">{{ stats.permission_denied || 0 }}</div>
          <div class="stat-label">权限拒绝（7天）</div>
        </div>
      </el-col>
    </el-row>

    <!-- 筛选栏 -->
    <el-card class="filter-card">
      <el-form :model="filterForm" inline>
        <el-form-item label="操作类型">
          <el-select v-model="filterForm.action" placeholder="全部类型" clearable style="width: 160px;">
            <el-option
              v-for="item in actionTypes"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="操作人">
          <el-input v-model="filterForm.username" placeholder="用户名" clearable style="width: 150px;" />
        </el-form-item>
        <el-form-item label="资源类型">
          <el-select v-model="filterForm.resource_type" placeholder="全部" clearable style="width: 140px;">
            <el-option label="用户" value="user" />
            <el-option label="角色" value="role" />
            <el-option label="项目" value="project" />
            <el-option label="任务" value="task" />
            <el-option label="审批" value="approval" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="全部" clearable style="width: 120px;">
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failure" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchLogs">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 日志表格 -->
    <el-card class="logs-card">
      <el-table :data="logs" v-loading="loading" stripe>
        <el-table-column label="时间" width="170">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作人" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ row.username }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作类型" width="140">
          <template #default="{ row }">
            <el-tag :type="getActionTypeTag(row.action)" size="small">
              {{ getActionLabel(row.action) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="资源" width="150">
          <template #default="{ row }">
            <span v-if="row.resource_type">
              {{ row.resource_type }}#{{ row.resource_id }}
            </span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="IP地址" width="130">
          <template #default="{ row }">
            {{ row.ip_address || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="详情" min-width="200">
          <template #default="{ row }">
            <el-popover
              v-if="row.detail && Object.keys(row.detail).length > 0"
              placement="top-start"
              :width="400"
              trigger="hover"
            >
              <template #reference>
                <el-button link type="primary" size="small">查看详情</el-button>
              </template>
              <pre class="detail-pre">{{ JSON.stringify(row.detail, null, 2) }}</pre>
            </el-popover>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchLogs"
          @current-change="fetchLogs"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { getAuditLogs, getAuditStats, getActionTypes } from '@/api/audit'

const logs = ref([])
const stats = ref({})
const actionTypes = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const filterForm = ref({
  action: '',
  username: '',
  resource_type: '',
  status: ''
})

const fetchLogs = async () => {
  loading.value = true
  try {
    const params = {
      page: page.value,
      per_page: pageSize.value,
      ...filterForm.value
    }
    // 移除空值
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null || params[key] === undefined) {
        delete params[key]
      }
    })
    
    const res = await getAuditLogs(params)
    logs.value = res.logs || []
    total.value = res.total || 0
  } catch (error) {
    console.error('获取审计日志失败', error)
    ElMessage.error('获取审计日志失败')
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const res = await getAuditStats()
    stats.value = res
  } catch (error) {
    console.error('获取审计统计失败', error)
  }
}

const fetchActionTypes = async () => {
  try {
    const res = await getActionTypes()
    actionTypes.value = res.actions || []
  } catch (error) {
    console.error('获取操作类型失败', error)
  }
}

const resetFilter = () => {
  filterForm.value = {
    action: '',
    username: '',
    resource_type: '',
    status: ''
  }
  page.value = 1
  fetchLogs()
}

const exportLogs = () => {
  ElMessage.info('导出功能开发中，可先使用浏览器打印')
}

const formatDateTime = (time) => {
  if (!time) return '-'
  return dayjs(time).format('MM-DD HH:mm:ss')
}

const getActionLabel = (action) => {
  const found = actionTypes.value.find(a => a.value === action)
  return found ? found.label : action
}

const getActionTypeTag = (action) => {
  const typeMap = {
    'LOGIN': 'success',
    'LOGIN_FAILED': 'danger',
    'LOGOUT': 'info',
    'PERMISSION_DENIED': 'danger',
    'USER_CREATE': 'primary',
    'USER_UPDATE': 'primary',
    'USER_DELETE': 'danger',
    'ROLE_CREATE': 'warning',
    'ROLE_UPDATE': 'warning',
    'ROLE_DELETE': 'danger'
  }
  return typeMap[action] || ''
}

onMounted(() => {
  fetchLogs()
  fetchStats()
  fetchActionTypes()
})
</script>

<style scoped lang="scss">
.audit-logs-page {
  .stats-row {
    margin-bottom: 20px;
    
    .stat-card {
      background: #fff;
      border-radius: 8px;
      padding: 20px;
      text-align: center;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
      
      .stat-value {
        font-size: 28px;
        font-weight: 600;
        color: #1890ff;
        margin-bottom: 8px;
        
        &.danger {
          color: #f56c6c;
        }
        
        &.warning {
          color: #e6a23c;
        }
      }
      
      .stat-label {
        font-size: 14px;
        color: #666;
      }
    }
  }
  
  .filter-card {
    margin-bottom: 20px;
  }
  
  .logs-card {
    .detail-pre {
      background: #f5f7fa;
      padding: 12px;
      border-radius: 4px;
      font-size: 12px;
      max-height: 300px;
      overflow: auto;
    }
    
    .text-muted {
      color: #999;
    }
    
    .pagination {
      margin-top: 20px;
      display: flex;
      justify-content: flex-end;
    }
  }
}
</style>
