<template>
  <div class="tickets-page">
    <div class="page-header">
      <h2>客户工单</h2>
      <el-button type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon>新建工单
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6" v-for="stat in statsCards" :key="stat.key">
        <div class="stat-card" :style="{ borderLeft: `4px solid ${stat.color}` }">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 筛选 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="全部" clearable style="width: 140px">
            <el-option label="待处理" value="open" />
            <el-option label="处理中" value="in_progress" />
            <el-option label="等待反馈" value="waiting" />
            <el-option label="已解决" value="resolved" />
            <el-option label="已关闭" value="closed" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="filterForm.priority" placeholder="全部" clearable style="width: 140px">
            <el-option label="紧急" value="urgent" />
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="客户">
          <el-select v-model="filterForm.client_id" placeholder="全部客户" clearable style="width: 180px">
            <el-option
              v-for="c in clientOptions"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input v-model="filterForm.search" placeholder="标题/编号" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 工单表格 -->
    <el-card>
      <el-table :data="tickets" stripe v-loading="loading">
        <el-table-column label="工单编号" prop="ticket_no" width="130" />
        <el-table-column label="标题" prop="title" min-width="180">
          <template #default="{ row }">
            <el-link type="primary" @click="openDetail(row)">{{ row.title }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="客户" width="140">
          <template #default="{ row }">
            {{ row.client?.name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="优先级" width="90">
          <template #default="{ row }">
            <el-tag :type="getPriorityType(row.priority)" size="small">
              {{ getPriorityLabel(row.priority) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="负责人" width="120">
          <template #default="{ row }">
            <div class="user-cell">
              <el-avatar v-if="row.assignee" :size="24" :src="row.assignee.avatar">
                {{ (row.assignee.real_name || row.assignee.username)?.charAt(0) }}
              </el-avatar>
              <span>{{ row.assignee?.real_name || '未分配' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
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
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑工单' : '新建工单'" width="600px">
      <el-form :model="form" label-width="100px" :rules="rules" ref="formRef">
        <el-form-item label="工单标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入工单标题" />
        </el-form-item>
        <el-form-item label="关联客户" prop="client_id">
          <el-select v-model="form.client_id" placeholder="选择客户" style="width: 100%">
            <el-option
              v-for="c in clientOptions"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="form.priority" style="width: 100%">
            <el-option label="紧急" value="urgent" />
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="负责人">
          <el-select v-model="form.assignee_id" placeholder="选择负责人" clearable style="width: 100%">
            <el-option
              v-for="u in users"
              :key="u.id"
              :label="u.real_name || u.username"
              :value="u.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="问题描述">
          <el-input v-model="form.description" type="textarea" rows="4" placeholder="详细描述问题或需求" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>

    <!-- 详情/处理对话框 -->
    <el-dialog v-model="detailVisible" title="工单处理" width="600px">
      <div v-if="currentTicket" class="ticket-detail">
        <div class="detail-meta">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="工单编号">{{ currentTicket.ticket_no }}</el-descriptions-item>
            <el-descriptions-item label="关联客户">{{ currentTicket.client?.name }}</el-descriptions-item>
            <el-descriptions-item label="优先级">
              <el-tag :type="getPriorityType(currentTicket.priority)" size="small">
                {{ getPriorityLabel(currentTicket.priority) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="当前状态">
              <el-tag :type="getStatusType(currentTicket.status)" size="small">
                {{ getStatusLabel(currentTicket.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="创建人">{{ currentTicket.reporter?.real_name || currentTicket.reporter?.username || '-' }}</el-descriptions-item>
            <el-descriptions-item label="负责人">{{ currentTicket.assignee?.real_name || currentTicket.assignee?.username || '未分配' }}</el-descriptions-item>
          </el-descriptions>
        </div>
        
        <div class="detail-desc">
          <h4>问题描述</h4>
          <p>{{ currentTicket.description || '暂无描述' }}</p>
        </div>
        
        <el-divider />
        
        <el-form :model="resolveForm" label-width="100px">
          <el-form-item label="更新状态">
            <el-select v-model="resolveForm.status" style="width: 100%">
              <el-option label="待处理" value="open" />
              <el-option label="处理中" value="in_progress" />
              <el-option label="等待反馈" value="waiting" />
              <el-option label="已解决" value="resolved" />
              <el-option label="已关闭" value="closed" />
            </el-select>
          </el-form-item>
          <el-form-item label="解决方案">
            <el-input v-model="resolveForm.resolution" type="textarea" rows="3" placeholder="填写解决方案（解决时必填）" />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">取消</el-button>
        <el-button type="primary" @click="handleResolve" :loading="resolving">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import { getTickets, getTicket, createTicket, updateTicket, deleteTicket, getTicketStats } from '@/api/tickets'
import { getClientOptions } from '@/api/clients'
import { getUsers } from '@/api/users'

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
  title: [{ required: true, message: '请输入工单标题', trigger: 'blur' }],
  client_id: [{ required: true, message: '请选择客户', trigger: 'change' }]
}

const statsCards = computed(() => {
  const s = stats.value
  return [
    { key: 'total', value: s.total || 0, label: '工单总数', color: '#1890ff' },
    { key: 'open', value: s.open || 0, label: '待处理', color: '#f56c6c' },
    { key: 'in_progress', value: s.in_progress || 0, label: '处理中', color: '#faad14' },
    { key: 'resolved', value: s.resolved || 0, label: '已解决', color: '#52c41a' }
  ]
})

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
    console.error('获取工单列表失败', error)
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const res = await getTicketStats()
    stats.value = res
  } catch (error) {
    console.error('获取工单统计失败', error)
  }
}

const fetchClientOptions = async () => {
  try {
    const res = await getClientOptions()
    clientOptions.value = res.clients
  } catch (error) {
    console.error('获取客户选项失败', error)
  }
}

const fetchUsers = async () => {
  try {
    const res = await getUsers({ per_page: 100 })
    users.value = res.users
  } catch (error) {
    console.error('获取用户失败', error)
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
    console.error('获取工单详情失败', error)
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
      ElMessage.success('工单更新成功')
    } else {
      await createTicket({ ...form })
      ElMessage.success('工单创建成功')
    }
    dialogVisible.value = false
    pagination.page = 1
    fetchTickets()
    fetchStats()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '操作失败')
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
    ElMessage.success('工单状态已更新')
    detailVisible.value = false
    fetchTickets()
    fetchStats()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '操作失败')
  } finally {
    resolving.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除工单 "${row.title}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteTicket(row.id)
    ElMessage.success('工单已删除')
    if (tickets.value.length === 1 && pagination.page > 1) {
      pagination.page -= 1
    }
    fetchTickets()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '操作失败')
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
  const map = { low: '低', medium: '中', high: '高', urgent: '紧急' }
  return map[priority] || priority
}

const getStatusType = (status) => {
  const map = { open: 'danger', in_progress: 'warning', waiting: 'info', resolved: 'success', closed: '' }
  return map[status] || ''
}

const getStatusLabel = (status) => {
  const map = { open: '待处理', in_progress: '处理中', waiting: '等待反馈', resolved: '已解决', closed: '已关闭' }
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
