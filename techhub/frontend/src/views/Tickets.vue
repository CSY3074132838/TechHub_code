<!-- 第三次迭代陈思言负责 -->
<template>
  <div class="tickets-page">
    <div class="page-header">
      <h2>{{ $t('tickets.pageTitle') }}</h2>
      <el-button type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon>{{ $t('tickets.newTicket') }}
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6" v-for="stat in statsCards" :key="stat.key">
        <div
          class="stat-card"
          :class="{ active: filterForm.status === stat.filterStatus }"
          :style="{ borderLeft: `4px solid ${stat.color}` }"
          @click="handleStatClick(stat.filterStatus)"
        >
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 筛选 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm">
        <el-form-item :label="$t('common.status')">
          <el-select v-model="filterForm.status" :placeholder="$t('common.all')" clearable style="width: 140px">
            <el-option :label="$t('tickets.open')" value="open" />
            <el-option :label="$t('tickets.inProgress')" value="in_progress" />
            <el-option :label="$t('tickets.waitingFeedback')" value="waiting" />
            <el-option :label="$t('tickets.resolved')" value="resolved" />
            <el-option :label="$t('tickets.closed')" value="closed" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('common.priority')">
          <el-select v-model="filterForm.priority" :placeholder="$t('common.all')" clearable style="width: 140px">
            <el-option :label="$t('common.urgent')" value="urgent" />
            <el-option :label="$t('common.high')" value="high" />
            <el-option :label="$t('common.medium')" value="medium" />
            <el-option :label="$t('common.low')" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('tickets.client')">
          <el-select v-model="filterForm.client_id" :placeholder="$t('tickets.allClients')" clearable style="width: 180px">
            <el-option
              v-for="c in clientOptions"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('common.search')">
          <el-input v-model="filterForm.search" :placeholder="$t('tickets.searchPlaceholder')" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">{{ $t('common.query') }}</el-button>
          <el-button @click="resetFilter">{{ $t('common.reset') }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 工单表格 -->
    <el-card>
      <el-table :data="tickets" stripe v-loading="loading">
        <el-table-column :label="$t('tickets.ticketNo')" prop="ticket_no" width="130" />
        <el-table-column :label="$t('common.title')" prop="title" min-width="180">
          <template #default="{ row }">
            <el-link type="primary" @click="openDetail(row)">{{ row.title }}</el-link>
          </template>
        </el-table-column>
        <el-table-column :label="$t('tickets.client')" width="140">
          <template #default="{ row }">
            {{ row.client?.name || '-' }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.priority')" width="90">
          <template #default="{ row }">
            <el-tag :type="getPriorityType(row.priority)" size="small">
              {{ getPriorityLabel(row.priority) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.status')" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('tickets.assignee')" width="120">
          <template #default="{ row }">
            <div class="user-cell">
              <el-avatar v-if="row.assignee" :size="24" :src="row.assignee.avatar">
                {{ (row.assignee.real_name || row.assignee.username)?.charAt(0) }}
              </el-avatar>
              <span>{{ row.assignee?.real_name || $t('tickets.unassigned') }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column :label="$t('tickets.createTime')" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.operation')" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDialog(row)">{{ $t('common.edit') }}</el-button>
            <el-button link type="danger" @click="handleDelete(row)">{{ $t('common.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.per_page"
        :total="pagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        class="pagination"
        @change="fetchTickets"
      />
    </el-card>

    <!-- 新建/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? $t('tickets.editTicket') : $t('tickets.newTicketDialog')" width="600px">
      <el-form :model="form" label-width="100px" :rules="rules" ref="formRef">
        <el-form-item :label="$t('tickets.ticketTitle')" prop="title">
          <el-input v-model="form.title" :placeholder="$t('tickets.ticketTitlePlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('tickets.relatedClient')" prop="client_id">
          <el-select v-model="form.client_id" :placeholder="$t('tickets.selectClient')" style="width: 100%">
            <el-option
              v-for="c in clientOptions"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('common.priority')">
          <el-select v-model="form.priority" style="width: 100%">
            <el-option :label="$t('common.urgent')" value="urgent" />
            <el-option :label="$t('common.high')" value="high" />
            <el-option :label="$t('common.medium')" value="medium" />
            <el-option :label="$t('common.low')" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('tickets.assignee')">
          <el-select v-model="form.assignee_id" :placeholder="$t('tickets.selectAssignee')" clearable style="width: 100%">
            <el-option
              v-for="u in users"
              :key="u.id"
              :label="u.real_name || u.username"
              :value="u.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('tickets.issueDesc')">
          <el-input v-model="form.description" type="textarea" rows="4" :placeholder="$t('tickets.issueDescPlaceholder')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>

    <!-- 详情/处理对话框 -->
    <el-dialog v-model="detailVisible" :title="$t('tickets.ticketProcess')" width="600px">
      <div v-if="currentTicket" class="ticket-detail">
        <div class="detail-meta">
          <el-descriptions :column="2" border>
            <el-descriptions-item :label="$t('tickets.ticketNo')">{{ currentTicket.ticket_no }}</el-descriptions-item>
            <el-descriptions-item :label="$t('tickets.relatedClient')">{{ currentTicket.client?.name }}</el-descriptions-item>
            <el-descriptions-item :label="$t('common.priority')">
              <el-tag :type="getPriorityType(currentTicket.priority)" size="small">
                {{ getPriorityLabel(currentTicket.priority) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item :label="$t('tickets.currentStatus')">
              <el-tag :type="getStatusType(currentTicket.status)" size="small">
                {{ getStatusLabel(currentTicket.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item :label="$t('tickets.creator')">{{ currentTicket.reporter?.real_name || currentTicket.reporter?.username || '-' }}</el-descriptions-item>
            <el-descriptions-item :label="$t('tickets.assignee')">{{ currentTicket.assignee?.real_name || currentTicket.assignee?.username || $t('tickets.unassigned') }}</el-descriptions-item>
          </el-descriptions>
        </div>
        
        <div class="detail-desc">
          <h4>{{ $t('tickets.issueDesc') }}</h4>
          <p>{{ currentTicket.description || $t('common.noData') }}</p>
        </div>
        
        <el-divider />
        
        <el-form :model="resolveForm" label-width="100px">
          <el-form-item :label="$t('tickets.updateStatus')">
            <el-select v-model="resolveForm.status" style="width: 100%">
              <el-option :label="$t('tickets.open')" value="open" />
              <el-option :label="$t('tickets.inProgress')" value="in_progress" />
              <el-option :label="$t('tickets.waitingFeedback')" value="waiting" />
              <el-option :label="$t('tickets.resolved')" value="resolved" />
              <el-option :label="$t('tickets.closed')" value="closed" />
            </el-select>
          </el-form-item>
          <el-form-item :label="$t('tickets.solution')">
            <el-input v-model="resolveForm.resolution" type="textarea" rows="3" :placeholder="$t('tickets.solutionPlaceholder')" />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleResolve" :loading="resolving">{{ $t('common.submit') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
// 第三次迭代陈思言负责
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import { getTickets, getTicket, createTicket, updateTicket, deleteTicket, getTicketStats } from '@/api/tickets'
import { getClientOptions } from '@/api/clients'
import { getUsers } from '@/api/users'

const { t } = useI18n()

const loading = ref(false)
const submitting = ref(false)
const resolving = ref(false)
const dialogVisible = ref(false)
const detailVisible = ref(false)
const isEdit = ref(false)
const currentId = ref(null)
const currentTicket = ref(null)
const formRef = ref(null)

const tickets = ref([])
const clientOptions = ref([])
const users = ref([])
const stats = ref({})

const pagination = reactive({
  page: 1,
  per_page: 10,
  total: 0,
  pages: 0
})

const filterForm = reactive({
  status: '',
  priority: '',
  client_id: '',
  search: ''
})

const form = reactive({
  title: '',
  client_id: '',
  priority: 'medium',
  assignee_id: '',
  description: ''
})

const resolveForm = reactive({
  status: '',
  resolution: ''
})

const rules = {
  title: [{ required: true, message: t('tickets.pleaseEnterTitle'), trigger: 'blur' }],
  client_id: [{ required: true, message: t('tickets.pleaseSelectClient'), trigger: 'change' }]
}

const statsCards = computed(() => {
  const s = stats.value
  return [
    { key: 'total', value: s.total || 0, label: t('tickets.totalTickets'), color: '#1890ff', filterStatus: '' },
    { key: 'open', value: s.open || 0, label: t('tickets.open'), color: '#f56c6c', filterStatus: 'open' },
    { key: 'in_progress', value: s.in_progress || 0, label: t('tickets.inProgress'), color: '#faad14', filterStatus: 'in_progress' },
    { key: 'resolved', value: s.resolved || 0, label: t('tickets.resolved'), color: '#52c41a', filterStatus: 'resolved' }
  ]
})

const handleStatClick = (status) => {
  filterForm.status = status
  handleSearch()
}

const fetchTickets = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.per_page,
      ...filterForm
    }
    const res = await getTickets(params)
    tickets.value = res.tickets
    pagination.total = res.total
    pagination.pages = res.pages
  } catch (error) {
    console.error(t('tickets.fetchFailed'), error)
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const res = await getTicketStats()
    stats.value = res
  } catch (error) {
    console.error(t('tickets.fetchStatsFailed'), error)
  }
}

const fetchClientOptions = async () => {
  try {
    const res = await getClientOptions()
    clientOptions.value = res.clients
  } catch (error) {
    console.error(t('tickets.fetchClientFailed'), error)
  }
}

const fetchUsers = async () => {
  try {
    const res = await getUsers({ per_page: 100 })
    users.value = res.users
  } catch (error) {
    console.error(t('tickets.fetchUserFailed'), error)
  }
}

const resetFilter = () => {
  filterForm.status = ''
  filterForm.priority = ''
  filterForm.client_id = ''
  filterForm.search = ''
  pagination.page = 1
  fetchTickets()
}

const openDialog = (row = null) => {
  isEdit.value = !!row
  currentId.value = row?.id || null
  if (row) {
    Object.assign(form, {
      title: row.title,
      client_id: row.client_id,
      priority: row.priority || 'medium',
      assignee_id: row.assignee_id || '',
      description: row.description || ''
    })
  } else {
    Object.assign(form, {
      title: '', client_id: '', priority: 'medium', assignee_id: '', description: ''
    })
  }
  dialogVisible.value = true
}

const openDetail = async (row) => {
  try {
    const res = await getTicket(row.id)
    currentTicket.value = res.ticket
    resolveForm.status = res.ticket.status
    resolveForm.resolution = res.ticket.resolution || ''
    detailVisible.value = true
  } catch (error) {
    console.error(t('tickets.fetchDetailFailed'), error)
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchTickets()
}

const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    if (isEdit.value) {
      await updateTicket(currentId.value, { ...form })
      ElMessage.success(t('tickets.updateSuccess'))
    } else {
      await createTicket({ ...form })
      ElMessage.success(t('tickets.createSuccess'))
    }
    dialogVisible.value = false
    pagination.page = 1
    fetchTickets()
    fetchStats()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || t('common.operationFailed'))
  } finally {
    submitting.value = false
  }
}

const handleResolve = async () => {
  if (!currentTicket.value) return
  resolving.value = true
  try {
    await updateTicket(currentTicket.value.id, {
      status: resolveForm.status,
      resolution: resolveForm.resolution
    })
    ElMessage.success(t('tickets.statusUpdated'))
    detailVisible.value = false
    fetchTickets()
    fetchStats()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || t('common.operationFailed'))
  } finally {
    resolving.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`${t('tickets.deleteConfirmPrefix')} "${row.title}" ${t('tickets.deleteConfirmSuffix')}`, t('common.tip'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning'
    })
    await deleteTicket(row.id)
    ElMessage.success(t('tickets.deleteSuccess'))
    if (tickets.value.length === 1 && pagination.page > 1) {
      pagination.page -= 1
    }
    fetchTickets()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || t('common.operationFailed'))
    }
  }
}

const formatDateTime = (date) => {
  return date ? dayjs(date).format('MM-DD HH:mm') : '-'
}

const getPriorityType = (priority) => {
  const map = { low: 'info', medium: '', high: 'warning', urgent: 'danger' }
  return map[priority] || ''
}

const getPriorityLabel = (priority) => {
  const map = {
    low: t('common.low'),
    medium: t('common.medium'),
    high: t('common.high'),
    urgent: t('common.urgent')
  }
  return map[priority] || priority
}

const getStatusType = (status) => {
  const map = { open: 'danger', in_progress: 'warning', waiting: 'info', resolved: 'success', closed: '' }
  return map[status] || ''
}

const getStatusLabel = (status) => {
  const map = {
    open: t('tickets.open'),
    in_progress: t('tickets.inProgress'),
    waiting: t('tickets.waitingFeedback'),
    resolved: t('tickets.resolved'),
    closed: t('tickets.closed')
  }
  return map[status] || status
}

onMounted(() => {
  fetchTickets()
  fetchStats()
  fetchClientOptions()
  fetchUsers()
})
</script>

<style scoped lang="scss">
.tickets-page {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    h2 {
      margin: 0;
    }
  }
  
  .stats-row {
    margin-bottom: 20px;
    
    .stat-card {
      background: #fff;
      border-radius: 8px;
      padding: 20px;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
      cursor: pointer;
      transition: all 0.2s ease;
      
      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
      }
      
      &.active {
        background-color: #f0f7ff;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
      }
      
      .stat-value {
        font-size: 28px;
        font-weight: 600;
        color: #333;
      }
      
      .stat-label {
        font-size: 14px;
        color: #666;
        margin-top: 4px;
      }
    }
  }
  
  .filter-card {
    margin-bottom: 20px;
  }
  
  .user-cell {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .pagination {
    margin-top: 20px;
    justify-content: flex-end;
  }
  
  .ticket-detail {
    .detail-desc {
      margin-top: 16px;
      
      h4 {
        font-size: 14px;
        margin-bottom: 8px;
      }
      
      p {
        color: #666;
        line-height: 1.6;
        background: #f5f7fa;
        padding: 12px;
        border-radius: 4px;
      }
    }
  }
}
</style>
