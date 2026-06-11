<!-- 第三次迭代陈思言负责 -->
<template>
  <div class="approvals-page">
    <!-- ================================================
         【第三次迭代于然负责】(8) 审批中心页面头部
         增加"审批流程"按钮，跳转至流程展示页面
         ================================================ -->
    <div class="page-header">
      <h2>{{ $t('approvals.pageTitle') }}</h2>
      <div class="header-actions">
        <el-button type="info" plain @click="$router.push('/approval-workflows')">
          <el-icon><Document /></el-icon>{{ $t('approvals.workflowDefinitions') }}
        </el-button>
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>{{ $t('approvals.newApproval') }}
        </el-button>
      </div>
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
        <el-table-column :label="$t('approvals.title')" min-width="220">
          <template #default="{ row }">
            <div class="approval-title">
              <div class="type-icon" :class="`type-${row.approval_type}`">
                <el-icon :size="14"><DocumentChecked /></el-icon>
              </div>
              <el-tag v-if="row.is_urgent" type="danger" size="small" effect="dark">{{ $t('approvals.urgent') }}</el-tag>
              <el-link type="primary" @click="viewDetail(row)">{{ row.title }}</el-link>
            </div>
          </template>
        </el-table-column>
        <el-table-column :label="$t('approvals.approvalType')" width="110">
          <template #default="{ row }">
            <el-tag :type="getWorkflowTypeTag(row.approval_type)" size="small" effect="plain">
              {{ getTypeLabel(row.approval_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('approvals.applicant')" width="120">
          <template #default="{ row }">
            <div class="applicant-cell">
              <el-avatar :size="24" :src="row.applicant?.avatar">{{ row.applicant?.real_name?.charAt(0) }}</el-avatar>
              <span>{{ row.applicant?.real_name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column :label="$t('approvals.amount')" width="110">
          <template #default="{ row }">
            <span class="amount-text">{{ row.amount ? `¥${row.amount}` : '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.status')" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" effect="dark" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="进度" width="120">
          <template #default="{ row }">
            <div class="progress-cell">
              <el-progress
                :percentage="getApprovalProgress(row)"
                :status="row.status === 'approved' ? 'success' : row.status === 'rejected' ? 'exception' : ''"
                :stroke-width="6"
                :show-text="true"
              />
            </div>
          </template>
        </el-table-column>
        <el-table-column :label="$t('approvals.submitTime')" width="150">
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
    <el-dialog v-model="showCreateDialog" :title="$t('approvals.newApproval')" width="600px">
      <el-form :model="form" label-width="120px" :rules="rules" ref="formRef">
        <el-form-item :label="$t('approvals.approvalType')" prop="approval_type">
          <el-select v-model="form.approval_type" :placeholder="$t('approvals.selectType')" style="width: 100%;" @change="onTypeChange">
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
        <!-- 子类型 -->
        <el-form-item :label="$t('approvals.subType')" v-if="showSubType">
          <el-select v-model="form.sub_type" :placeholder="$t('approvals.selectSubType')" style="width: 100%;">
            <el-option v-for="opt in subTypeOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
        <!-- 工单级别 -->
        <el-form-item :label="$t('approvals.ticketLevel')" v-if="form.approval_type === 'ticket'">
          <el-select v-model="form.ticket_level" :placeholder="$t('approvals.selectTicketLevel')" style="width: 100%;">
            <el-option :label="$t('approvals.ticketNormal')" value="normal" />
            <el-option :label="$t('approvals.ticketImportant')" value="important" />
            <el-option :label="$t('approvals.ticketCritical')" value="critical" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('approvals.amount')" v-if="showAmount">
          <el-input-number v-model="form.amount" :min="0" :precision="2" style="width: 100%;" />
        </el-form-item>
        <!-- 请假天数 -->
        <el-form-item :label="$t('approvals.leaveDays')" v-if="form.approval_type === 'leave'">
          <el-input-number v-model="form.leave_days" :min="0.5" :precision="1" :step="0.5" style="width: 100%;" />
        </el-form-item>
        <!-- 加班天数 -->
        <el-form-item :label="$t('approvals.overtimeDays')" v-if="form.approval_type === 'overtime'">
          <el-input-number v-model="form.overtime_days" :min="1" :precision="0" style="width: 100%;" />
        </el-form-item>
        <!-- 是否标准模板 -->
        <el-form-item :label="$t('approvals.isStandardTemplate')" v-if="form.approval_type === 'contract'">
          <el-switch v-model="form.is_standard_template" :active-text="$t('approvals.yes')" :inactive-text="$t('approvals.no')" />
        </el-form-item>
        <!-- 是否超出预算 -->
        <el-form-item :label="$t('approvals.isOverBudget')" v-if="form.approval_type === 'expense'">
          <el-switch v-model="form.is_over_budget" :active-text="$t('approvals.yes')" :inactive-text="$t('approvals.no')" />
        </el-form-item>
        <!-- 是否需要赔偿 -->
        <el-form-item :label="$t('approvals.needCompensation')" v-if="form.approval_type === 'ticket'">
          <el-switch v-model="form.need_compensation" :active-text="$t('approvals.yes')" :inactive-text="$t('approvals.no')" />
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

    <!-- ================================================
         【第三次迭代于然负责】(3) 审批详情对话框
         点击审批标题可查看详情和审批流程
         ================================================ -->
    <!-- 审批详情对话框（含审批链可视化） -->
    <el-dialog v-model="showDetailDialog" :title="$t('approvals.detailDialogTitle')" width="760px">
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

        <!-- 【审批流程引擎】美化审批链展示 -->
        <div class="approval-chain-section">
          <h4>{{ $t('approvals.approvalFlow') }}</h4>
          <div class="flow-timeline">
            <div
              v-for="(node, index) in detailApproval.approval_chain"
              :key="node.id"
              class="flow-node"
              :class="[
                'node-' + getNodeStatus(node, index, detailApproval),
                { 'is-condition': node.node_type === 'condition' || node.condition_expr },
                { 'is-parallel': node.node_type === 'parallel' },
                { 'is-auto': node.is_auto || node.node_type === 'auto' },
                { 'is-current': node.id === detailApproval.current_node }
              ]"
            >
              <div class="node-marker">
                <div class="node-icon">
                  <el-icon v-if="node.status === 'completed'" size="16"><Check /></el-icon>
                  <el-icon v-else-if="node.status === 'rejected'" size="16"><Close /></el-icon>
                  <el-icon v-else-if="node.status === 'skipped'" size="16"><Remove /></el-icon>
                  <span v-else class="node-number">{{ index + 1 }}</span>
                </div>
                <div v-if="index < detailApproval.approval_chain.length - 1" class="node-line"></div>
              </div>
              <div class="node-content">
                <div class="node-header">
                  <span class="node-title">{{ node.node_name }}</span>
                  <el-tag v-if="node.node_type === 'condition' || node.condition_expr" size="small" type="warning" effect="plain">{{ $t('approvals.conditionNode') }}</el-tag>
                  <el-tag v-else-if="node.node_type === 'parallel'" size="small" type="primary" effect="plain">{{ $t('approvals.parallelNode') }}</el-tag>
                  <el-tag v-else-if="node.is_auto || node.node_type === 'auto'" size="small" type="info" effect="plain">{{ $t('approvals.autoNode') }}</el-tag>
                  <el-tag
                    :type="node.status === 'completed' ? 'success' : node.status === 'rejected' ? 'danger' : node.status === 'skipped' ? 'info' : node.id === detailApproval.current_node ? 'warning' : ''"
                    size="small"
                    effect="dark"
                  >
                    {{ getNodeStatusLabel(node) }}
                  </el-tag>
                </div>
                <div class="node-body">
                  <div v-if="node.handler" class="node-handler">
                    <el-avatar :size="24" :src="node.handler.avatar">{{ node.handler.real_name?.charAt(0) }}</el-avatar>
                    <span>{{ node.handler.real_name }}</span>
                  </div>
                  <!-- 会签处理人 -->
                  <div v-else-if="node.parallel_handlers && node.parallel_handlers.length > 0" class="node-parallel-handlers">
                    <div v-for="ph in node.parallel_handlers" :key="ph.user_id" class="parallel-handler">
                      <el-tag :type="ph.status === 'completed' ? 'success' : ph.status === 'rejected' ? 'danger' : 'info'" size="small">
                        {{ ph.real_name || $t('approvals.pending') }}
                      </el-tag>
                    </div>
                  </div>
                  <div v-if="node.handled_at" class="node-time">{{ formatDateTime(node.handled_at) }}</div>
                  <div v-if="node.comment" class="node-comment">
                    <el-icon><ChatDotRound /></el-icon>
                    <span>{{ node.comment }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
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
import { Document } from '@element-plus/icons-vue'

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
  description: '',
  sub_type: '',
  leave_days: 1,
  overtime_days: 1,
  ticket_level: 'normal',
  is_standard_template: true,
  is_over_budget: false,
  need_compensation: false
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
  return ['expense', 'purchase', 'contract'].includes(form.value.approval_type)
})

const showSubType = computed(() => {
  return ['leave', 'permission', 'overtime'].includes(form.value.approval_type)
})

const subTypeOptions = computed(() => {
  const map = {
    leave: [
      { value: 'annual', label: t('approvals.annualLeave') },
      { value: 'sick', label: t('approvals.sickLeave') },
      { value: 'personal', label: t('approvals.personalLeave') },
      { value: 'other', label: t('approvals.otherLeave') }
    ],
    permission: [
      { value: 'read_only', label: t('approvals.readOnly') },
      { value: 'read_write', label: t('approvals.readWrite') },
      { value: 'deploy', label: t('approvals.deploy') },
      { value: 'sensitive', label: t('approvals.sensitiveData') }
    ],
    overtime: [
      { value: 'compensatory', label: t('approvals.compensatory') },
      { value: 'paid', label: t('approvals.paidOvertime') }
    ]
  }
  return map[form.value.approval_type] || []
})

const onTypeChange = () => {
  form.value.sub_type = ''
  form.value.ticket_level = 'normal'
  form.value.leave_days = 1
  form.value.overtime_days = 1
  form.value.is_standard_template = true
  form.value.is_over_budget = false
  form.value.need_compensation = false
}

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
      description: '',
      sub_type: '',
      leave_days: 1,
      overtime_days: 1,
      ticket_level: 'normal',
      is_standard_template: true,
      is_over_budget: false,
      need_compensation: false
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
    if (currentNode) {
      if (currentNode.handler_id === userStore.userInfo?.id) return true
      // 会签节点检查
      if (currentNode.parallel_handlers && currentNode.parallel_handlers.length > 0) {
        const myPh = currentNode.parallel_handlers.find(ph => ph.user_id === userStore.userInfo?.id && ph.status === 'pending')
        if (myPh) return true
      }
    }
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

const getApprovalProgress = (approval) => {
  if (!approval.approval_chain || approval.approval_chain.length === 0) return 0
  if (approval.status === 'approved') return 100
  if (approval.status === 'rejected') return 0
  
  // 过滤掉条件节点，只计算实际审批节点
  const validNodes = approval.approval_chain.filter(n => n.node_type !== 'condition')
  const total = validNodes.length
  // completed 包括 completed 和 skipped（条件判断跳过的也算完成）
  const completed = validNodes.filter(n => n.status === 'completed' || n.status === 'skipped').length
  
  return total > 0 ? Math.round((completed / total) * 100) : 0
}

const getWorkflowTypeTag = (type) => {
  const map = {
    purchase: 'warning',
    expense: 'success',
    leave: 'primary',
    overtime: 'danger',
    permission: 'info',
    contract: 'warning',
    ticket: 'primary',
    other: 'info'
  }
  return map[type] || ''
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
    'permission': t('approvals.permission'),
    'contract': t('approvals.contract'),
    'ticket': t('approvals.ticket'),
    'other': t('approvals.other')
  }
  return typeMap[type] || type
}

const getNodeStatusLabel = (node) => {
  const map = {
    'completed': t('approvals.approved'),
    'rejected': t('approvals.rejected'),
    'skipped': t('approvals.skipped'),
    'pending': node.id === detailApproval.value?.current_node ? t('approvals.processing') : t('approvals.pending')
  }
  return map[node.status] || t('approvals.pending')
}

const formatDateTime = (date) => {
  if (!date) return ''
  return dayjs(date).format('YYYY-MM-DD HH:mm')
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
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;

    h2 {
      margin: 0;
      font-size: 22px;
      color: #303133;
    }

    .header-actions {
      display: flex;
      gap: 12px;
    }
  }

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

      .type-icon {
        width: 28px;
        height: 28px;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #ecf5ff;
        color: #409eff;

        &.type-purchase { background: #fdf6ec; color: #e6a23c; }
        &.type-expense { background: #f0f9eb; color: #67c23a; }
        &.type-leave { background: #ecf5ff; color: #409eff; }
        &.type-overtime { background: #fef0f0; color: #f56c6c; }
        &.type-permission { background: #f4f4f5; color: #909399; }
        &.type-contract { background: #fdf6ec; color: #e6a23c; }
        &.type-ticket { background: #ecf5ff; color: #409eff; }
        &.type-other { background: #f4f4f5; color: #909399; }
      }
    }

    .applicant-cell {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .amount-text {
      font-weight: 500;
      color: #f56c6c;
    }

    .progress-cell {
      width: 100px;
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

  // 【审批流程引擎】美化审批链展示
  .approval-chain-section {
    margin-top: 24px;
    padding-top: 16px;
    border-top: 1px solid #e4e7ed;

    h4 {
      margin: 0 0 16px;
      font-size: 16px;
      color: #303133;
    }

    .flow-timeline {
      display: flex;
      flex-direction: column;
      gap: 0;
    }

    .flow-node {
      display: flex;
      gap: 16px;
      padding: 12px 0;
      position: relative;

      .node-marker {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 32px;
        flex-shrink: 0;

        .node-icon {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #f5f7fa;
          border: 2px solid #dcdfe6;
          color: #909399;
          font-size: 14px;
          font-weight: 600;
          z-index: 1;
        }

        .node-line {
          width: 2px;
          flex: 1;
          min-height: 24px;
          background: #e4e7ed;
          margin-top: 4px;
        }
      }

      .node-content {
        flex: 1;
        padding-bottom: 8px;

        .node-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
          flex-wrap: wrap;

          .node-title {
            font-weight: 600;
            font-size: 14px;
            color: #303133;
          }
        }

        .node-body {
          display: flex;
          flex-direction: column;
          gap: 6px;

          .node-handler {
            display: flex;
            align-items: center;
            gap: 6px;
            color: #606266;
            font-size: 13px;
          }

          .node-parallel-handlers {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
          }

          .node-time {
            font-size: 12px;
            color: #909399;
          }

          .node-comment {
            display: flex;
            align-items: flex-start;
            gap: 4px;
            font-size: 13px;
            color: #606266;
            background: #f5f7fa;
            padding: 8px 12px;
            border-radius: 6px;
            margin-top: 4px;

            .el-icon {
              margin-top: 2px;
              flex-shrink: 0;
            }
          }
        }
      }

      // 状态样式
      &.node-success {
        .node-icon {
          background: #f0f9eb;
          border-color: #67c23a;
          color: #67c23a;
        }
      }

      &.node-error {
        .node-icon {
          background: #fef0f0;
          border-color: #f56c6c;
          color: #f56c6c;
        }
      }

      &.node-process {
        .node-icon {
          background: #ecf5ff;
          border-color: #409eff;
          color: #409eff;
          animation: pulse 2s infinite;
        }
      }

      &.node-wait {
        .node-icon {
          background: #f5f7fa;
          border-color: #dcdfe6;
          color: #c0c4cc;
        }
      }

      &.is-condition {
        .node-title {
          color: #e6a23c;
        }
      }

      &.is-parallel {
        .node-title {
          color: #409eff;
        }
      }

      &.is-auto {
        .node-title {
          color: #909399;
          font-style: italic;
        }
      }

      &.is-current {
        background: #f5f7fa;
        border-radius: 8px;
        padding: 12px;
        margin: 0 -12px;
      }

      &:last-child {
        .node-line {
          display: none;
        }
      }
    }
  }
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(64, 158, 255, 0.4);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(64, 158, 255, 0);
  }
}
</style>
