<!-- 第三次迭代陈思言负责 -->
<template>
  <div class="audit-logs-page">
    <div class="page-header">
      <h2>{{ $t('auditLogs.pageTitle') }}</h2>
      <el-button type="primary" @click="exportLogs">
        <el-icon><Download /></el-icon>{{ $t('auditLogs.exportLogs') }}
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ stats.today_count || 0 }}</div>
          <div class="stat-label">{{ $t('auditLogs.todayOperations') }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ stats.week_count || 0 }}</div>
          <div class="stat-label">{{ $t('auditLogs.weeklyOperations') }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value danger">{{ stats.failed_logins || 0 }}</div>
          <div class="stat-label">{{ $t('auditLogs.loginFailures7d') }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value warning">{{ stats.permission_denied || 0 }}</div>
          <div class="stat-label">{{ $t('auditLogs.permissionDenied7d') }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 筛选栏 -->
    <el-card class="filter-card">
      <el-form :model="filterForm" inline>
        <el-form-item :label="$t('auditLogs.operationType')">
          <el-select v-model="filterForm.action" :placeholder="$t('auditLogs.allTypes')" clearable style="width: 160px;">
            <el-option
              v-for="item in actionTypes"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('auditLogs.operator')">
          <el-input v-model="filterForm.username" :placeholder="$t('auditLogs.operatorPlaceholder')" clearable style="width: 150px;" />
        </el-form-item>
        <el-form-item :label="$t('auditLogs.resourceType')">
          <el-select v-model="filterForm.resource_type" :placeholder="$t('common.all')" clearable style="width: 140px;">
            <el-option :label="$t('auditLogs.resourceUser')" value="user" />
            <el-option :label="$t('auditLogs.resourceRole')" value="role" />
            <el-option :label="$t('auditLogs.resourceProject')" value="project" />
            <el-option :label="$t('auditLogs.resourceTask')" value="task" />
            <el-option :label="$t('auditLogs.resourceApproval')" value="approval" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('auditLogs.status')">
          <el-select v-model="filterForm.status" :placeholder="$t('common.all')" clearable style="width: 120px;">
            <el-option :label="$t('auditLogs.success')" value="success" />
            <el-option :label="$t('auditLogs.failed')" value="failure" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('auditLogs.startTime')">
          <el-date-picker
            v-model="filterForm.start_time"
            type="datetime"
            :placeholder="$t('auditLogs.selectStartTime')"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 180px;"
          />
        </el-form-item>
        <el-form-item :label="$t('auditLogs.endTime')">
          <el-date-picker
            v-model="filterForm.end_time"
            type="datetime"
            :placeholder="$t('auditLogs.selectEndTime')"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 180px;"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchLogs">{{ $t('common.query') }}</el-button>
          <el-button @click="resetFilter">{{ $t('common.reset') }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 日志表格 -->
    <el-card class="logs-card">
      <el-table :data="logs" v-loading="loading" stripe>
        <el-table-column :label="$t('auditLogs.time')" width="170">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('auditLogs.operator')" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ row.username }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('auditLogs.operationType')" width="140">
          <template #default="{ row }">
            <el-tag :type="getActionTypeTag(row.action)" size="small">
              {{ getActionLabel(row.action) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('auditLogs.resource')" width="150">
          <template #default="{ row }">
            <span v-if="row.resource_type">
              {{ row.resource_type }}#{{ row.resource_id }}
            </span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('auditLogs.ipAddress')" width="130">
          <template #default="{ row }">
            {{ row.ip_address || '-' }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('auditLogs.status')" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
              {{ row.status === 'success' ? $t('auditLogs.success') : $t('auditLogs.failed') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('auditLogs.detail')" min-width="120">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openDetail(row.id)">
              {{ $t('auditLogs.viewDetail') }}
            </el-button>
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

    <!-- 日志详情抽屉 -->
    <el-drawer
      v-model="detailDrawerVisible"
      :title="$t('auditLogs.logDetail')"
      size="500px"
      :destroy-on-close="true"
      @close="closeDetail"
    >
      <div v-loading="detailLoading" class="detail-drawer-content">
        <template v-if="detailData.id">
          <div class="detail-section">
            <div class="detail-label">{{ $t('auditLogs.time') }}</div>
            <div class="detail-value">{{ formatDateTime(detailData.created_at) }}</div>
          </div>
          <div class="detail-section">
            <div class="detail-label">{{ $t('auditLogs.operator') }}</div>
            <div class="detail-value">{{ detailData.username }}</div>
          </div>
          <div class="detail-section">
            <div class="detail-label">{{ $t('auditLogs.operationType') }}</div>
            <div class="detail-value">
              <el-tag :type="getActionTypeTag(detailData.action)" size="small">
                {{ getActionLabel(detailData.action) }}
              </el-tag>
            </div>
          </div>
          <div class="detail-section">
            <div class="detail-label">{{ $t('auditLogs.resourceType') }}</div>
            <div class="detail-value">{{ detailData.resource_type || '-' }}</div>
          </div>
          <div class="detail-section">
            <div class="detail-label">{{ $t('auditLogs.resourceId') }}</div>
            <div class="detail-value">{{ detailData.resource_id || '-' }}</div>
          </div>
          <div class="detail-section">
            <div class="detail-label">{{ $t('auditLogs.ipAddress') }}</div>
            <div class="detail-value">{{ detailData.ip_address || '-' }}</div>
          </div>
          <div class="detail-section">
            <div class="detail-label">{{ $t('auditLogs.status') }}</div>
            <div class="detail-value">
              <el-tag :type="detailData.status === 'success' ? 'success' : 'danger'" size="small">
                {{ detailData.status === 'success' ? $t('auditLogs.success') : $t('auditLogs.failed') }}
              </el-tag>
            </div>
          </div>
          <div class="detail-section">
            <div class="detail-label">{{ $t('auditLogs.detailData') }}</div>
            <pre v-if="detailData.detail && Object.keys(detailData.detail).length > 0" class="detail-pre">{{ JSON.stringify(detailData.detail, null, 2) }}</pre>
            <span v-else class="text-muted">-</span>
          </div>
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
// 第三次迭代陈思言负责
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { getAuditLogs, getAuditStats, getActionTypes, getAuditDetail, exportAuditLogs } from '@/api/audit'

const { t } = useI18n()

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
  status: '',
  start_time: '',
  end_time: ''
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
    console.error(t('auditLogs.fetchFailed'), error)
    ElMessage.error(t('auditLogs.fetchFailed'))
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const res = await getAuditStats()
    stats.value = res
  } catch (error) {
    console.error(t('auditLogs.fetchStatsFailed'), error)
  }
}

const fetchActionTypes = async () => {
  try {
    const res = await getActionTypes()
    actionTypes.value = res.actions || []
  } catch (error) {
    console.error(t('auditLogs.fetchActionTypesFailed'), error)
  }
}

const resetFilter = () => {
  filterForm.value = {
    action: '',
    username: '',
    resource_type: '',
    status: '',
    start_time: '',
    end_time: ''
  }
  page.value = 1
  fetchLogs()
}

const exportLogs = async () => {
  try {
    const params = {
      ...filterForm.value
    }
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null || params[key] === undefined) {
        delete params[key]
      }
    })

    const res = await exportAuditLogs(params)
    const blob = new Blob([res.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    const filename = `audit_logs_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success(t('auditLogs.exportSuccess'))
  } catch (error) {
    console.error(t('auditLogs.exportFailed'), error)
    ElMessage.error(t('auditLogs.exportFailed'))
  }
}

const detailDrawerVisible = ref(false)
const detailLoading = ref(false)
const detailData = ref({})

const openDetail = async (logId) => {
  detailDrawerVisible.value = true
  detailLoading.value = true
  try {
    const res = await getAuditDetail(logId)
    detailData.value = res.log || {}
  } catch (error) {
    console.error(t('auditLogs.fetchDetailFailed'), error)
    ElMessage.error(t('auditLogs.fetchDetailFailed'))
  } finally {
    detailLoading.value = false
  }
}

const closeDetail = () => {
  detailDrawerVisible.value = false
  detailData.value = {}
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

  .detail-drawer-content {
    .detail-section {
      margin-bottom: 20px;

      .detail-label {
        font-size: 13px;
        color: #666;
        margin-bottom: 6px;
      }

      .detail-value {
        font-size: 14px;
        color: #333;
        word-break: break-all;
      }
    }

    .detail-pre {
      background: #f5f7fa;
      padding: 12px;
      border-radius: 4px;
      font-size: 12px;
      max-height: 400px;
      overflow: auto;
    }
  }
}
</style>
