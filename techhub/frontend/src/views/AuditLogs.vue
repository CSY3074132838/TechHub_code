<!-- 【第三次迭代陈思言负责】 -->
<!--
  (3) 审计日志详情页面优化：补充丰富内容，更直观展示详细信息 √
  (4) 统计卡片改为可交互按钮，点击后自动填充筛选条件 √
  (5) 数据分析员可查看审计日志页面（与于然(4)协同）
-->
<template>
  <div class="audit-logs-page">
    <div class="page-header">
      <h2>{{ $t('auditLogs.pageTitle') }}</h2>
      <el-button type="primary" @click="exportLogs">
        <el-icon><Download /></el-icon>{{ $t('auditLogs.exportLogs') }}
      </el-button>
    </div>

    <!-- 统计卡片 - 可交互按钮 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card clickable" :class="{ active: isTodayActive }" @click="filterToday">
          <div class="stat-value">{{ stats.today_count || 0 }}</div>
          <div class="stat-label">{{ $t('auditLogs.todayOperations') }}</div>
          <el-icon class="click-hint"><Filter /></el-icon>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card clickable" :class="{ active: isWeekActive }" @click="filterWeek">
          <div class="stat-value">{{ stats.week_count || 0 }}</div>
          <div class="stat-label">{{ $t('auditLogs.weeklyOperations') }}</div>
          <el-icon class="click-hint"><Filter /></el-icon>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card clickable danger-card" :class="{ active: isLoginFailedActive }" @click="filterLoginFailed">
          <div class="stat-value danger">{{ stats.failed_logins || 0 }}</div>
          <div class="stat-label">{{ $t('auditLogs.loginFailures7d') }}</div>
          <el-icon class="click-hint"><Filter /></el-icon>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card clickable warning-card" :class="{ active: isPermissionDeniedActive }" @click="filterPermissionDenied">
          <div class="stat-value warning">{{ stats.permission_denied || 0 }}</div>
          <div class="stat-label">{{ $t('auditLogs.permissionDenied7d') }}</div>
          <el-icon class="click-hint"><Filter /></el-icon>
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
    <!-- 【第三次迭代陈思言负责】按分组格式展示审计日志详情 -->
    <el-drawer
      v-model="detailDrawerVisible"
      :title="$t('auditLogs.logDetail')"
      size="560px"
      :destroy-on-close="true"
      @close="closeDetail"
    >
      <div v-loading="detailLoading" class="detail-drawer-content">
        <template v-if="detailData.id">
          <!-- 基础信息 -->
          <div class="detail-group">
            <div class="detail-group-title">
              <el-icon><Document /></el-icon>
              <span>{{ $t('auditLogs.basicInfo') }}</span>
            </div>
            <div class="detail-group-body">
              <div class="detail-row">
                <span class="detail-row-label">{{ $t('auditLogs.time') }}</span>
                <span class="detail-row-value">{{ formatDateTime(detailData.basic_info?.time) }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-row-label">{{ $t('auditLogs.operator') }}</span>
                <span class="detail-row-value">
                  {{ detailData.basic_info?.operator }}
                  <el-tag v-if="detailData.basic_info?.operator_real_name" size="small" type="info" class="name-tag">
                    {{ detailData.basic_info?.operator_real_name }}
                  </el-tag>
                </span>
              </div>
              <div class="detail-row">
                <span class="detail-row-label">{{ $t('auditLogs.operationType') }}</span>
                <span class="detail-row-value">
                  <el-tag :type="getActionTypeTag(detailData.basic_info?.action)" size="small">
                    {{ getActionLabel(detailData.basic_info?.action) }}
                  </el-tag>
                </span>
              </div>
              <div class="detail-row">
                <span class="detail-row-label">{{ $t('auditLogs.resource') }}</span>
                <span class="detail-row-value">{{ detailData.basic_info?.resource || '-' }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-row-label">{{ $t('auditLogs.ipAddress') }}</span>
                <span class="detail-row-value">{{ detailData.basic_info?.ip_address || '-' }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-row-label">{{ $t('auditLogs.status') }}</span>
                <span class="detail-row-value">
                  <el-tag :type="detailData.basic_info?.status === 'success' ? 'success' : 'danger'" size="small">
                    {{ detailData.basic_info?.status === 'success' ? $t('auditLogs.success') : $t('auditLogs.failed') }}
                  </el-tag>
                </span>
              </div>
            </div>
          </div>

          <!-- 请求详情 -->
          <div class="detail-group">
            <div class="detail-group-title">
              <el-icon><Link /></el-icon>
              <span>{{ $t('auditLogs.requestDetail') }}</span>
            </div>
            <div class="detail-group-body">
              <div class="detail-row">
                <span class="detail-row-label">{{ $t('auditLogs.requestMethod') }}</span>
                <span class="detail-row-value">
                  <el-tag v-if="detailData.request_detail?.method && detailData.request_detail?.method !== '-'" 
                    :type="getMethodTag(detailData.request_detail?.method)" size="small">
                    {{ detailData.request_detail?.method }}
                  </el-tag>
                  <span v-else class="text-muted">-</span>
                </span>
              </div>
              <div class="detail-row">
                <span class="detail-row-label">{{ $t('auditLogs.requestUrl') }}</span>
                <span class="detail-row-value url-value">{{ detailData.request_detail?.url || '-' }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-row-label">{{ $t('auditLogs.userAgent') }}</span>
                <span class="detail-row-value">{{ detailData.request_detail?.user_agent || '-' }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-row-label">{{ $t('auditLogs.requestParams') }}</span>
                <div class="detail-row-value">
                  <pre v-if="detailData.request_detail?.params && Object.keys(detailData.request_detail?.params).length > 0" 
                    class="detail-pre">{{ JSON.stringify(detailData.request_detail?.params, null, 2) }}</pre>
                  <span v-else class="text-muted">-</span>
                </div>
              </div>
              <div class="detail-row">
                <span class="detail-row-label">{{ $t('auditLogs.responseStatus') }}</span>
                <span class="detail-row-value">
                  <el-tag :type="getStatusCodeTag(detailData.request_detail?.response_status)" size="small">
                    {{ detailData.request_detail?.response_status || '-' }}
                  </el-tag>
                </span>
              </div>
            </div>
          </div>

          <!-- 服务端信息 -->
          <div class="detail-group">
            <div class="detail-group-title">
              <el-icon><Cpu /></el-icon>
              <span>{{ $t('auditLogs.serverInfo') }}</span>
            </div>
            <div class="detail-group-body">
              <div class="detail-row">
                <span class="detail-row-label">{{ $t('auditLogs.duration') }}</span>
                <span class="detail-row-value">{{ detailData.server_info?.duration || '-' }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-row-label">{{ $t('auditLogs.backendService') }}</span>
                <span class="detail-row-value">{{ detailData.server_info?.service || '-' }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-row-label">{{ $t('auditLogs.errorMessage') }}</span>
                <span class="detail-row-value error-value">{{ detailData.server_info?.error_message || '-' }}</span>
              </div>
            </div>
          </div>
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
// 第三次迭代陈思言负责
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Download, Document, Link, Cpu, Filter } from '@element-plus/icons-vue'
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

// 【第三次迭代陈思言负责】请求方法对应的标签类型
const getMethodTag = (method) => {
  const methodMap = {
    'GET': 'success',
    'POST': 'primary',
    'PUT': 'warning',
    'DELETE': 'danger',
    'PATCH': 'info'
  }
  return methodMap[method?.toUpperCase()] || ''
}

// 【第三次迭代陈思言负责】HTTP 状态码对应的标签类型
const getStatusCodeTag = (status) => {
  if (!status || status === '-') return 'info'
  const code = parseInt(status)
  if (code >= 200 && code < 300) return 'success'
  if (code >= 300 && code < 400) return 'warning'
  if (code >= 400 && code < 500) return 'warning'
  if (code >= 500) return 'danger'
  return 'info'
}

// 【第三次迭代陈思言负责】统计卡片点击交互：点击后自动填充筛选条件
const isTodayActive = computed(() => {
  const today = dayjs().format('YYYY-MM-DD')
  return filterForm.value.start_time === `${today} 00:00:00` && 
         filterForm.value.end_time === `${today} 23:59:59` &&
         !filterForm.value.action &&
         !filterForm.value.status
})

const isWeekActive = computed(() => {
  const weekAgo = dayjs().subtract(6, 'day').format('YYYY-MM-DD')
  const today = dayjs().format('YYYY-MM-DD')
  return filterForm.value.start_time === `${weekAgo} 00:00:00` && 
         filterForm.value.end_time === `${today} 23:59:59` &&
         !filterForm.value.action &&
         !filterForm.value.status
})

const isLoginFailedActive = computed(() => {
  return filterForm.value.action === 'LOGIN_FAILED'
})

const isPermissionDeniedActive = computed(() => {
  return filterForm.value.action === 'PERMISSION_DENIED'
})

const filterToday = () => {
  if (isTodayActive.value) {
    resetFilter()
    return
  }
  const today = dayjs().format('YYYY-MM-DD')
  filterForm.value = {
    action: '',
    username: '',
    resource_type: '',
    status: '',
    start_time: `${today} 00:00:00`,
    end_time: `${today} 23:59:59`
  }
  page.value = 1
  fetchLogs()
}

const filterWeek = () => {
  if (isWeekActive.value) {
    resetFilter()
    return
  }
  const weekAgo = dayjs().subtract(6, 'day').format('YYYY-MM-DD')
  const today = dayjs().format('YYYY-MM-DD')
  filterForm.value = {
    action: '',
    username: '',
    resource_type: '',
    status: '',
    start_time: `${weekAgo} 00:00:00`,
    end_time: `${today} 23:59:59`
  }
  page.value = 1
  fetchLogs()
}

const filterLoginFailed = () => {
  if (isLoginFailedActive.value) {
    resetFilter()
    return
  }
  filterForm.value = {
    action: 'LOGIN_FAILED',
    username: '',
    resource_type: '',
    status: '',
    start_time: '',
    end_time: ''
  }
  page.value = 1
  fetchLogs()
}

const filterPermissionDenied = () => {
  if (isPermissionDeniedActive.value) {
    resetFilter()
    return
  }
  filterForm.value = {
    action: 'PERMISSION_DENIED',
    username: '',
    resource_type: '',
    status: '',
    start_time: '',
    end_time: ''
  }
  page.value = 1
  fetchLogs()
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

  .stat-card {
    position: relative;
    transition: all 0.2s ease;
    
    &.clickable {
      cursor: pointer;
      
      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        
        .click-hint {
          opacity: 1;
        }
      }
      
      &.active {
        border: 2px solid #1890ff;
        background: #f0f7ff;
        
        .click-hint {
          opacity: 1;
          color: #1890ff;
        }
      }
      
      &.danger-card.active {
        border-color: #f56c6c;
        background: #fef0f0;
        
        .click-hint {
          color: #f56c6c;
        }
      }
      
      &.warning-card.active {
        border-color: #e6a23c;
        background: #fdf6ec;
        
        .click-hint {
          color: #e6a23c;
        }
      }
    }
    
    .click-hint {
      position: absolute;
      top: 8px;
      right: 8px;
      font-size: 14px;
      color: #999;
      opacity: 0;
      transition: opacity 0.2s ease;
    }
  }

  .detail-drawer-content {
    padding: 0 4px;

    // 【第三次迭代陈思言负责】分组卡片样式
    .detail-group {
      margin-bottom: 24px;
      border: 1px solid #e4e7ed;
      border-radius: 8px;
      overflow: hidden;

      &:last-child {
        margin-bottom: 0;
      }

      .detail-group-title {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 12px 16px;
        background: #f5f7fa;
        border-bottom: 1px solid #e4e7ed;
        font-size: 15px;
        font-weight: 600;
        color: #303133;

        .el-icon {
          font-size: 18px;
          color: #409eff;
        }
      }

      .detail-group-body {
        padding: 8px 16px;
      }
    }

    .detail-row {
      display: flex;
      padding: 10px 0;
      border-bottom: 1px solid #f0f0f0;

      &:last-child {
        border-bottom: none;
      }

      .detail-row-label {
        width: 100px;
        flex-shrink: 0;
        font-size: 13px;
        color: #606266;
        line-height: 24px;
      }

      .detail-row-value {
        flex: 1;
        font-size: 14px;
        color: #303133;
        line-height: 24px;
        word-break: break-all;

        &.url-value {
          font-family: 'Courier New', monospace;
          font-size: 13px;
          color: #409eff;
          background: #f0f9ff;
          padding: 2px 8px;
          border-radius: 4px;
          display: inline-block;
        }

        &.error-value {
          color: #f56c6c;
        }

        .name-tag {
          margin-left: 8px;
        }
      }
    }

    .detail-pre {
      background: #f5f7fa;
      padding: 12px;
      border-radius: 4px;
      font-size: 12px;
      max-height: 300px;
      overflow: auto;
      margin: 0;
      width: 100%;
    }
  }
}
</style>
