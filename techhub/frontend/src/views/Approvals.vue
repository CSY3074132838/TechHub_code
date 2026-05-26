<!-- 第三次迭代陈思言负责 -->
<template>
  <div class="approvals-page">
    <div class="page-header">
      <h2>{{ $t('approvals.pageTitle') }}</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>{{ $t('approvals.newApproval') }}
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card clickable" :class="{ active: filterStatus === 'pending' }" @click="filterByStatus('pending')">
          <div class="stat-value">{{ stats.overview?.pending || 0 }}</div>
          <div class="stat-label">{{ $t('approvals.pending') }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card clickable" :class="{ active: filterStatus === 'approved' }" @click="filterByStatus('approved')">
          <div class="stat-value success">{{ stats.overview?.approved || 0 }}</div>
          <div class="stat-label">{{ $t('approvals.approved') }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card clickable" :class="{ active: filterStatus === 'rejected' }" @click="filterByStatus('rejected')">
          <div class="stat-value danger">{{ stats.overview?.rejected || 0 }}</div>
          <div class="stat-label">{{ $t('approvals.rejected') }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card clickable" :class="{ active: filterUrgent }" @click="filterByUrgent">
          <div class="stat-value warning">{{ stats.overview?.urgent_pending || 0 }}</div>
          <div class="stat-label">{{ $t('approvals.urgentTodo') }}</div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 筛选状态提示 -->
    <div v-if="filterStatus || filterUrgent" class="filter-bar">
      <el-tag closable @close="clearFilter">
        {{ filterUrgent ? $t('approvals.urgentTodo') : statusLabelMap[filterStatus] }}
      </el-tag>
      <el-button link type="primary" size="small" @click="clearFilter">{{ $t('approvals.clearFilter') }}</el-button>
    </div>

    <!-- 审批列表 -->
    <el-card class="approvals-list">
      <template #header>
        <div class="list-header">
          <el-radio-group v-model="activeTab" @change="handleTabChange">
            <el-radio-button label="all">{{ $t('approvals.all') }}</el-radio-button>
            <el-radio-button label="my">{{ $t('approvals.mySubmitted') }}</el-radio-button>
            <el-radio-button label="pending">{{ $t('approvals.pending') }}</el-radio-button>
          </el-radio-group>
          
          <el-select v-model="filterType" :placeholder="$t('approvals.approvalType')" clearable @change="fetchApprovals">
            <el-option
              v-for="type in approvalTypes"
              :key="type.value"
              :label="type.label"
              :value="type.value"
            />
          </el-select>
        </div>
      </template>

      <el-table :data="approvals" v-loading="loading" stripe>
        <el-table-column :label="$t('approvals.title')" min-width="200">
          <template #default="{ row }">
            <div class="approval-title">
              <el-tag v-if="row.is_urgent" type="danger" size="small">{{ $t('approvals.urgent') }}</el-tag>
              <el-link type="primary" @click="viewDetail(row)">{{ row.title }}</el-link>
            </div>
          </template>
        </el-table-column>
        <el-table-column :label="$t('approvals.approvalType')" width="120">
          <template #default="{ row }">
            {{ getTypeLabel(row.approval_type) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('approvals.applicant')" width="120">
          <template #default="{ row }">
            {{ row.applicant?.real_name }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('approvals.amount')" width="120">
          <template #default="{ row }">
            {{ row.amount ? `¥${row.amount}` : '-' }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.status')" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('approvals.submitTime')" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.action')" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'pending' && canProcess(row)"
              type="primary"
              size="small"
              @click="openProcessDialog(row)"
            >
              {{ $t('approvals.process') }}
            </el-button>
            <el-button v-else text size="small" @click="viewDetail(row)">{{ $t('common.view') }}</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchApprovals"
          @current-change="fetchApprovals"
        />
      </div>
    </el-card>

    <!-- 发起审批对话框 -->
    <el-dialog v-model="showCreateDialog" :title="$t('approvals.processDialogTitle')" width="600px">
      <el-form :model="form" label-width="100px" :rules="rules" ref="formRef">
        <el-form-item :label="$t('approvals.approvalType')" prop="approval_type">
          <el-select v-model="form.approval_type" :placeholder="$t('approvals.selectType')" style="width: 100%;">
            <el-option
              v-for="type in approvalTypes"
              :key="type.value"
              :label="type.label"
              :value="type.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('approvals.approvalTitle')" prop="title">
          <el-input v-model="form.title" :placeholder="$t('approvals.approvalTitlePlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('approvals.amount')" v-if="showAmount">
          <el-input-number v-model="form.amount" :min="0" :precision="2" style="width: 100%;" />
        </el-form-item>
        <el-form-item :label="$t('approvals.urgency')">
          <el-switch v-model="form.is_urgent" :active-text="$t('approvals.urgent')" :inactive-text="$t('approvals.normal')" />
        </el-form-item>
        <el-form-item :label="$t('approvals.approvalDesc')">
          <el-input
            v-model="form.description"
            type="textarea"
            rows="4"
            :placeholder="$t('approvals.approvalDescPlaceholder')"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">{{ $t('common.submit') }}</el-button>
      </template>
    </el-dialog>

    <!-- 处理审批对话框 -->
    <el-dialog v-model="showProcessDialog" :title="$t('approvals.processDialogTitle')" width="500px">
      <div v-if="currentApproval" class="process-info">
        <p><strong>{{ $t('approvals.approvalTitle') }}：</strong>{{ currentApproval.title }}</p>
        <p><strong>{{ $t('approvals.applicant') }}：</strong>{{ currentApproval.applicant?.real_name }}</p>
        <p><strong>{{ $t('approvals.approvalDesc') }}：</strong>{{ currentApproval.description || $t('common.none') }}</p>
      </div>
      <el-form :model="processForm" label-width="80px">
        <el-form-item :label="$t('approvals.opinion')">
          <el-radio-group v-model="processForm.action">
            <el-radio-button label="approve">{{ $t('approvals.agree') }}</el-radio-button>
            <el-radio-button label="reject">{{ $t('approvals.reject') }}</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item :label="$t('common.remark')">
          <el-input
            v-model="processForm.comment"
            type="textarea"
            rows="3"
            :placeholder="$t('approvals.processRemarkPlaceholder')"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showProcessDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleProcess" :loading="processing">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <!-- 审批详情对话框（含审批链可视化） -->
    <el-dialog v-model="showDetailDialog" :title="$t('approvals.detailDialogTitle')" width="700px">
      <div v-if="detailApproval" class="approval-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item :label="$t('approvals.approvalTitle')">{{ detailApproval.title }}</el-descriptions-item>
          <el-descriptions-item :label="$t('approvals.approvalType')">{{ getTypeLabel(detailApproval.approval_type) }}</el-descriptions-item>
          <el-descriptions-item :label="$t('approvals.applicant')">{{ detailApproval.applicant?.real_name }}</el-descriptions-item>
          <el-descriptions-item :label="$t('common.status')">
            <el-tag :type="getStatusType(detailApproval.status)">
              {{ getStatusLabel(detailApproval.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('approvals.amount')">{{ detailApproval.amount ? `¥${detailApproval.amount}` : '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('approvals.urgency')">
            <el-tag v-if="detailApproval.is_urgent" type="danger">{{ $t('approvals.urgent') }}</el-tag>
            <el-tag v-else type="info">{{ $t('approvals.normal') }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('approvals.approvalDesc')" :span="2">{{ detailApproval.description || $t('common.none') }}</el-descriptions-item>
        </el-descriptions>

        <div class="approval-chain-section">
          <h4>{{ $t('approvals.approvalFlow') }}</h4>
          <el-steps :active="getActiveStep(detailApproval)" finish-status="success" direction="vertical">
            <el-step
              v-for="(node, index) in detailApproval.approval_chain"
              :key="node.id"
              :title="node.node_name"
              :status="getNodeStatus(node, index, detailApproval)"
            >
              <template #description>
                <div class="step-desc">
                  <span v-if="node.handler">{{ $t('approvals.handler') }}：{{ node.handler.real_name }}</span>
                  <span v-if="node.status === 'completed'" class="text-success">{{ $t('approvals.approved') }}</span>
                  <span v-if="node.status === 'rejected'" class="text-danger">{{ $t('approvals.rejected') }}</span>
                  <span v-if="node.status === 'pending'" class="text-warning">{{ $t('approvals.pending') }}</span>
                  <span v-if="node.comment" class="comment">{{ $t('approvals.flowRemark') }}：{{ node.comment }}</span>
                </div>
              </template>
            </el-step>
          </el-steps>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
// 第三次迭代陈思言负责
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/stores/user'
import { getApprovals, createApproval, processApproval, getApprovalStats, getApprovalTypes, getApprovalChain, getApproval } from '@/api/approvals'

const { t } = useI18n()
const userStore = useUserStore()

const approvals = ref([])
const stats = ref({})
const approvalTypes = ref([])
const loading = ref(false)
const activeTab = ref('all')
const filterType = ref('')
const filterStatus = ref('')
const filterUrgent = ref(false)

const statusLabelMap = {
  pending: t('approvals.pending'),
  approved: t('approvals.approved'),
  rejected: t('approvals.rejected')
}
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

const showCreateDialog = ref(false)
const showProcessDialog = ref(false)
const showDetailDialog = ref(false)
const creating = ref(false)
const processing = ref(false)
const currentApproval = ref(null)
const detailApproval = ref(null)

const form = ref({
  approval_type: '',
  title: '',
  amount: 0,
  is_urgent: false,
  description: ''
})

const processForm = ref({
  action: 'approve',
  comment: ''
})

const rules = {
  approval_type: [{ required: true, message: t('approvals.pleaseSelectType'), trigger: 'change' }],
  title: [{ required: true, message: t('approvals.pleaseEnterTitle'), trigger: 'blur' }]
}

const showAmount = computed(() => {
  return ['expense', 'purchase'].includes(form.value.approval_type)
})

const fetchApprovals = async () => {
  loading.value = true
  try {
    const params = {
      page: page.value,
      per_page: pageSize.value,
      scope: activeTab.value,
      type: filterType.value,
      status: filterStatus.value,
      is_urgent: filterUrgent.value || undefined
    }
    const res = await getApprovals(params)
    approvals.value = res.approvals
    total.value = res.total
  } catch (error) {
    console.error(t('approvals.fetchListFailed'), error)
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const res = await getApprovalStats()
    stats.value = res
  } catch (error) {
    console.error(t('approvals.fetchStatsFailed'), error)
  }
}

const fetchTypes = async () => {
  try {
    const res = await getApprovalTypes()
    approvalTypes.value = res.types
  } catch (error) {
    console.error(t('approvals.fetchTypesFailed'), error)
  }
}

const filterByStatus = (status) => {
  if (filterStatus.value === status && !filterUrgent.value) {
    filterStatus.value = ''
  } else {
    filterStatus.value = status
    filterUrgent.value = false
  }
  page.value = 1
  fetchApprovals()
}

const filterByUrgent = () => {
  if (filterUrgent.value) {
    filterUrgent.value = false
  } else {
    filterUrgent.value = true
    filterStatus.value = ''
  }
  page.value = 1
  fetchApprovals()
}

const clearFilter = () => {
  filterStatus.value = ''
  filterUrgent.value = false
  page.value = 1
  fetchApprovals()
}

const handleTabChange = () => {
  page.value = 1
  fetchApprovals()
}

const handleCreate = async () => {
  if (!form.value.title || !form.value.approval_type) {
    ElMessage.warning(t('common.pleaseFillInCompleteInfo'))
    return
  }
  
  creating.value = true
  try {
    await createApproval(form.value)
    ElMessage.success(t('approvals.submitSuccess'))
    showCreateDialog.value = false
    fetchApprovals()
    fetchStats()
    form.value = {
      approval_type: '',
      title: '',
      amount: 0,
      is_urgent: false,
      description: ''
    }
  } catch (error) {
    console.error(t('approvals.submitFailed'), error)
  } finally {
    creating.value = false
  }
}

// 高管角色（总经理、副总经理）
const MANAGER_ROLES = ['super_admin', 'deputy_general_manager']
const isManager = computed(() => userStore.userInfo?.roles?.some(r => MANAGER_ROLES.includes(r.name)))

const canProcess = (approval) => {
  // 高管可以处理所有审批
  if (isManager.value) return true
  // 有审批处理权限的可以处理
  if (userStore.hasPermission('approval_process') || userStore.hasPermission('all')) return true
  // 是当前节点指定处理人的可以处理
  if (approval.approval_chain && approval.current_node) {
    const currentNode = approval.approval_chain.find(n => n.id === approval.current_node)
    if (currentNode && currentNode.handler_id === userStore.userInfo?.id) return true
  }
  return false
}

const openProcessDialog = (approval) => {
  currentApproval.value = approval
  processForm.value = { action: 'approve', comment: '' }
  showProcessDialog.value = true
}

const handleProcess = async () => {
  if (!currentApproval.value) return
  
  processing.value = true
  try {
    await processApproval(currentApproval.value.id, processForm.value)
    ElMessage.success(t('approvals.processSuccess'))
    showProcessDialog.value = false
    fetchApprovals()
    fetchStats()
  } catch (error) {
    console.error(t('approvals.processFailed'), error)
  } finally {
    processing.value = false
  }
}

const viewDetail = async (approval) => {
  try {
    const res = await getApproval(approval.id)
    detailApproval.value = res.approval
    showDetailDialog.value = true
  } catch (error) {
    console.error(t('approvals.fetchDetailFailed'), error)
    ElMessage.error(t('approvals.fetchDetailFailed'))
  }
}

const getActiveStep = (approval) => {
  if (!approval.approval_chain) return 0
  const completed = approval.approval_chain.filter(n => n.status === 'completed').length
  return completed
}

const getNodeStatus = (node, index, approval) => {
  if (node.status === 'completed') return 'success'
  if (node.status === 'rejected') return 'error'
  if (node.status === 'pending') {
    // 当前激活的节点
    const prevCompleted = index === 0 || approval.approval_chain[index - 1]?.status === 'completed'
    if (prevCompleted) return 'process'
    return 'wait'
  }
  return 'wait'
}

const formatDate = (date) => {
  return dayjs(date).format('MM-DD HH:mm')
}

const getTypeLabel = (type) => {
  const typeMap = {
    'leave': t('approvals.leave'),
    'expense': t('approvals.expense'),
    'purchase': t('approvals.purchase'),
    'overtime': t('approvals.overtime'),
    'other': t('approvals.other')
  }
  return typeMap[type] || type
}

const getStatusType = (status) => {
  const typeMap = {
    'pending': 'warning',
    'approved': 'success',
    'rejected': 'danger',
    'cancelled': 'info'
  }
  return typeMap[status] || ''
}

const getStatusLabel = (status) => {
  const labelMap = {
    'pending': t('approvals.pending'),
    'approved': t('approvals.approved'),
    'rejected': t('approvals.rejected'),
    'cancelled': t('approvals.cancelled')
  }
  return labelMap[status] || status
}

onMounted(() => {
  fetchApprovals()
  fetchStats()
  fetchTypes()
})
</script>

<style scoped lang="scss">
.approvals-page {
  .stats-row {
    margin-bottom: 20px;
    
    .stat-card {
      background: #fff;
      border-radius: 8px;
      padding: 20px;
      text-align: center;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
      transition: all 0.2s;
      
      &.clickable {
        cursor: pointer;
        
        &:hover {
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
          transform: translateY(-2px);
        }
        
        &.active {
          border: 2px solid #1890ff;
          background: #e6f7ff;
        }
      }
      
      .stat-value {
        font-size: 28px;
        font-weight: 600;
        color: #1890ff;
        margin-bottom: 8px;
        
        &.success {
          color: #67c23a;
        }
        
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
  
  .filter-bar {
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .approvals-list {
    .list-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .approval-title {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    .pagination {
      margin-top: 20px;
      display: flex;
      justify-content: flex-end;
    }
  }
  
  .process-info {
    margin-bottom: 20px;
    padding-bottom: 20px;
    border-bottom: 1px solid #eee;
    
    p {
      margin: 8px 0;
    }
  }
}
</style>
