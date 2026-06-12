<template>
  <!-- 【第三次迭代郝益墨负责】 -->
  <!--
    (1) 财务看板整合到收付款页面，仅admin可查看
    (2) 本月记录筛选框增加按人名筛选 √
    (3) admin账号显示全部报销统计 √
    (4) 报销记录可点击查看详情 √
    (5) 新建报销支持上传附件（图片、文档） √
    (6) 支持打款方式选择（微信、支付宝、PayPal）
  -->
  <div class="expenses-page">
    <div class="page-header">
      <h2>{{ $t('expenses.pageTitle') }}</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>{{ $t('expenses.newExpense') }}
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ expenseStats.total_amount || 0 }}</div>
          <div class="stat-label">{{ $t('expenses.monthlyAmount') }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div
          class="stat-card clickable"
          :class="{ active: filterStatus === 'pending' }"
          @click="filterStatus = 'pending'"
        >
          <div class="stat-value success">{{ pendingCount }}</div>
          <div class="stat-label">{{ $t('expenses.pendingApproval') }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div
          class="stat-card clickable"
          :class="{ active: filterStatus === 'approved' }"
          @click="filterStatus = 'approved'"
        >
          <div class="stat-value warning">{{ approvedCount }}</div>
          <div class="stat-label">{{ $t('expenses.approved') }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div
          class="stat-card clickable"
          :class="{ active: !filterStatus && !filterCategory }"
          @click="resetFilter"
        >
          <div class="stat-value">{{ expenses.length }}</div>
          <div class="stat-label">{{ $t('expenses.monthlyRecords') }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 筛选与列表 -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>{{ $t('expenses.expenseRecords') }}</span>
          <div class="filter-bar">
            <el-select v-model="filterStatus" :placeholder="$t('expenses.status')" clearable size="small" style="width: 120px; margin-right: 8px;">
              <el-option :label="$t('expenses.pendingApproval')" value="pending" />
              <el-option :label="$t('expenses.approved')" value="approved" />
              <el-option :label="$t('expenses.rejected')" value="rejected" />
              <el-option :label="$t('expenses.paid')" value="reimbursed" />
            </el-select>
            <el-select v-model="filterCategory" :placeholder="$t('expenses.category')" clearable size="small" style="width: 120px; margin-right: 8px;">
              <el-option v-for="c in categories" :key="c.value" :label="categoryLabel(c.value)" :value="c.value" />
            </el-select>
            <!-- 【第三次迭代郝益墨负责】(2) 按人名筛选报销记录 -->
            <el-input
              v-model="filterUserName"
              :placeholder="$t('expenses.filterByPerson')"
              clearable
              size="small"
              style="width: 140px; margin-right: 8px;"
            />
            <el-button size="small" @click="resetFilter">{{ $t('common.reset') }}</el-button>
          </div>
        </div>
      </template>

      <el-table :data="filteredExpenses" v-loading="loading" size="small">
        <el-table-column :label="$t('expenses.expensePerson')" width="120">
          <template #default="{ row }">
            <div style="display: flex; align-items: center; gap: 8px;">
              <el-avatar :size="24">{{ row.user?.real_name?.charAt(0) || 'U' }}</el-avatar>
              <span>{{ row.user?.real_name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column :label="$t('expenses.title')" prop="title" min-width="180" show-overflow-tooltip />
        <el-table-column :label="$t('expenses.amount')" width="120">
          <template #default="{ row }">
            <span style="color: #f56c6c; font-weight: 600;">¥{{ row.amount }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('expenses.category')" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ categoryLabel(row.category) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.status')" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('expenses.submitTime')" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.operation')" width="240" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleViewDetail(row)">{{ $t('expenses.viewDetail') }}</el-button>
            <el-button v-if="canApprove(row)" type="primary" link size="small" @click="handleApprove(row)">{{ $t('expenses.pass') }}</el-button>
            <el-button v-if="canApprove(row)" type="danger" link size="small" @click="handleReject(row)">{{ $t('expenses.reject') }}</el-button>
            <el-button v-if="canReimburse(row)" type="success" link size="small" @click="handleReimburse(row)">{{ $t('expenses.pay') }}</el-button>
            <el-button v-if="canEdit(row)" type="primary" link size="small" @click="handleEdit(row)">{{ $t('common.edit') }}</el-button>
            <el-button v-if="canDelete(row)" type="danger" link size="small" @click="handleDelete(row)">{{ $t('common.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="fetchExpenses"
        />
      </div>
    </el-card>

    <!-- 类别分布 -->
    <el-card style="margin-top: 20px;" v-if="expenseStats.by_category?.length">
      <template #header>
        <span>{{ $t('expenses.monthlyCategoryDistribution') }}</span>
      </template>
      <el-row :gutter="20">
        <el-col :xs="24" :md="12" v-for="item in expenseStats.by_category" :key="item.category">
          <div class="category-stat">
            <div class="category-info">
              <span class="category-name">{{ categoryLabel(item.category) }}</span>
              <span class="category-amount">¥{{ item.amount }} ({{ item.count }}{{ $t('common.unitPiece') }})</span>
            </div>
            <el-progress :percentage="Math.round((item.amount / (expenseStats.total_amount || 1)) * 100)" />
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 【第三次迭代郝益墨负责】(4) 报销详情抽屉 -->
    <!-- 报销详情抽屉 -->
    <el-drawer v-model="showDetailDrawer" :title="$t('expenses.expenseDetail')" size="500px" :destroy-on-close="true">
      <div v-if="detailExpense" class="expense-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item :label="$t('expenses.expenseTitle')">{{ detailExpense.title }}</el-descriptions-item>
          <el-descriptions-item :label="$t('expenses.expenseAmount')">
            <span style="color: #f56c6c; font-weight: 600; font-size: 18px;">¥{{ detailExpense.amount }}</span>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('expenses.expenseCategory')">
            <el-tag size="small">{{ categoryLabel(detailExpense.category) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('expenses.currentStatus')">
            <el-tag :type="statusType(detailExpense.status)" size="small">
              {{ statusLabel(detailExpense.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('expenses.expensePersonLabel')">
            <div style="display: flex; align-items: center; gap: 8px;">
              <el-avatar :size="32">{{ detailExpense.user?.real_name?.charAt(0) || 'U' }}</el-avatar>
              <span>{{ detailExpense.user?.real_name || detailExpense.user?.username }}</span>
            </div>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('expenses.expenseDesc')" :span="1">
            <div style="white-space: pre-wrap; line-height: 1.6;">{{ detailExpense.description || $t('expenses.none') }}</div>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('expenses.attachment')">
            <div v-if="detailExpense.attachments?.length">
              <el-link
                v-for="(file, idx) in detailExpense.attachments"
                :key="idx"
                type="primary"
                :href="file.url"
                target="_blank"
                style="display: block; margin-bottom: 4px;"
              >
                {{ file.name || $t('expenses.attachmentName') + (idx + 1) }}
              </el-link>
            </div>
            <span v-else style="color: #999;">{{ $t('expenses.noAttachment') }}</span>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('expenses.submitTimeLabel')">{{ formatDateTime(detailExpense.created_at) }}</el-descriptions-item>
          <el-descriptions-item :label="$t('expenses.updateTime')">{{ formatDateTime(detailExpense.updated_at) }}</el-descriptions-item>
          <el-descriptions-item v-if="detailExpense.reimbursed_at" :label="$t('expenses.payTime')">{{ formatDateTime(detailExpense.reimbursed_at) }}</el-descriptions-item>
        </el-descriptions>

        <!-- 操作按钮 -->
        <div style="margin-top: 24px; display: flex; gap: 12px; justify-content: center;">
          <el-button v-if="canApprove(detailExpense)" type="primary" @click="handleApprove(detailExpense); showDetailDrawer = false">{{ $t('expenses.pass') }}</el-button>
          <el-button v-if="canApprove(detailExpense)" type="danger" @click="handleReject(detailExpense); showDetailDrawer = false">{{ $t('expenses.reject') }}</el-button>
          <el-button v-if="canReimburse(detailExpense)" type="success" @click="handleReimburse(detailExpense); showDetailDrawer = false">{{ $t('expenses.markPaid') }}</el-button>
          <el-button v-if="canEdit(detailExpense)" type="primary" plain @click="handleEdit(detailExpense); showDetailDrawer = false">{{ $t('common.edit') }}</el-button>
        </div>
      </div>
    </el-drawer>

    <!-- 新建/编辑对话框 -->
    <el-dialog v-model="showCreateDialog" :title="isEdit ? $t('expenses.editExpense') : $t('expenses.newExpenseDialog')" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item :label="$t('expenses.expenseTitle')" required>
          <el-input v-model="form.title" :placeholder="$t('expenses.expenseTitlePlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('expenses.expenseAmount')" required>
          <el-input-number v-model="form.amount" :min="0.01" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="$t('expenses.expenseCategory')">
          <el-select v-model="form.category" :placeholder="$t('expenses.selectCategory')" style="width: 100%">
            <el-option v-for="c in categories" :key="c.value" :label="categoryLabel(c.value)" :value="c.value" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('expenses.expenseDesc')">
          <el-input v-model="form.description" type="textarea" :rows="3" :placeholder="$t('expenses.expenseDescPlaceholder')" />
        </el-form-item>
        <!-- 【第三次迭代郝益墨负责】(5) 上传附件功能（图片、文档） -->
        <el-form-item :label="$t('expenses.attachmentUpload')">
          <el-upload
            action="#"
            :auto-upload="false"
            :on-change="handleUpload"
            :before-upload="beforeUpload"
            :show-file-list="false"
            :disabled="uploading"
            accept=".png,.jpg,.jpeg,.gif,.bmp,.webp,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt"
          >
            <el-button type="primary" :loading="uploading" size="small">
              <el-icon><Upload /></el-icon>{{ $t('expenses.selectFile') }}
            </el-button>
            <template #tip>
              <div class="upload-tip">{{ $t('expenses.uploadTip') }}</div>
            </template>
          </el-upload>
          <!-- 已上传文件列表 -->
          <div v-if="form.attachments?.length" class="attachment-list">
            <div v-for="(file, idx) in form.attachments" :key="idx" class="attachment-item">
              <el-icon v-if="file.type === 'image'" class="file-icon"><Picture /></el-icon>
              <el-icon v-else-if="file.type === 'document'" class="file-icon"><Document /></el-icon>
              <el-icon v-else class="file-icon"><Document /></el-icon>
              <span class="file-name">{{ file.name }}</span>
              <el-button type="danger" link size="small" @click="removeAttachment(idx)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="saveExpense" :loading="saving">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>

    <!-- 【新增】打款支付方式选择弹窗 -->
    <el-dialog
      v-model="showPaymentDialog"
      title="选择支付方式"
      width="420px"
      :close-on-click-modal="false"
      align-center
    >
      <div class="payment-options">
        <div class="payment-option wechat" @click="handlePaymentSelect('wechat')">
          <img src="@/assets/payment/wechat-pay.png" alt="微信支付" class="payment-logo" />
          <span class="payment-name">微信支付</span>
          <el-icon class="payment-arrow"><ArrowRight /></el-icon>
        </div>
        <div class="payment-option paypal" @click="handlePaymentSelect('paypal')">
          <img src="@/assets/payment/paypal.png" alt="PayPal" class="payment-logo" />
          <span class="payment-name">PayPal</span>
          <el-icon class="payment-arrow"><ArrowRight /></el-icon>
        </div>
        <div class="payment-option alipay" @click="handlePaymentSelect('alipay')">
          <img src="@/assets/payment/alipay.png" alt="支付宝" class="payment-logo" />
          <span class="payment-name">支付宝</span>
          <el-icon class="payment-arrow"><ArrowRight /></el-icon>
        </div>
      </div>
      <template #footer>
        <el-button @click="showPaymentDialog = false">取消</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
// 第三次迭代陈思言负责
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Picture, Document, Delete, Plus, ArrowRight } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import {
  getExpenses, createExpense, updateExpense, deleteExpense,
  approveExpense, rejectExpense, reimburseExpense,
  getExpenseStats, getExpenseCategories, uploadExpenseAttachment
} from '@/api/expenses'
import { useUserStore } from '@/stores/user'

const { t } = useI18n()
const userStore = useUserStore()

const loading = ref(false)
const expenses = ref([])
const expenseStats = ref({})
const categories = ref([])
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const filterStatus = ref('')
const filterCategory = ref('')
// 【第三次迭代郝益墨负责】(2) 按人名筛选报销记录
const filterUserName = ref('')  // 按人名筛选
// 【第三次迭代郝益墨负责】(3) admin账号中显示全部报销金额和类别分布
const allUsers = ref([])  // 高管模式下全部用户列表

const showCreateDialog = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const saving = ref(false)
const uploading = ref(false)
const form = ref({
  title: '',
  amount: 0,
  category: 'other',
  description: '',
  attachments: []
})

// 详情抽屉
const showDetailDrawer = ref(false)
const detailExpense = ref(null)

// 【新增】支付选择弹窗
const showPaymentDialog = ref(false)
const currentReimburseRow = ref(null)

const filteredExpenses = computed(() => {
  let result = expenses.value
  if (filterStatus.value) {
    result = result.filter(e => e.status === filterStatus.value)
  }
  if (filterCategory.value) {
    result = result.filter(e => e.category === filterCategory.value)
  }
  if (filterUserName.value) {
    const keyword = filterUserName.value.toLowerCase()
    result = result.filter(e => {
      const name = (e.user?.real_name || e.user?.username || '').toLowerCase()
      return name.includes(keyword)
    })
  }
  return result
})

const pendingCount = computed(() => expenses.value.filter(e => e.status === 'pending').length)
const approvedCount = computed(() => expenses.value.filter(e => e.status === 'approved').length)

// 高管角色：总经理、副总经理（拥有 all 权限）
const isAdmin = computed(() => userStore.isAdmin)

const canEdit = (row) => {
  return row.user_id === userStore.userInfo?.id && ['draft', 'pending'].includes(row.status)
}

const canDelete = (row) => {
  return row.user_id === userStore.userInfo?.id && ['draft', 'pending'].includes(row.status)
}

// 财务高管角色：总经理、副总经理、财务总监
const FINANCE_ROLES = ['super_admin', 'deputy_general_manager', 'finance_director']
const isFinanceManager = computed(() => {
  return userStore.userInfo?.roles?.some(r => FINANCE_ROLES.includes(r.name))
})

const canApprove = (row) => {
  return isFinanceManager.value && row.status === 'pending'
}

const canReimburse = (row) => {
  return isFinanceManager.value && row.status === 'approved'
}

const fetchExpenses = async () => {
  loading.value = true
  try {
    const res = await getExpenses({
      page: page.value,
      per_page: pageSize.value,
      month: dayjs().format('YYYY-MM')
    })
    expenses.value = res.expenses || []
    total.value = res.total || 0
    // 高管模式下收集全部用户列表（用于人名筛选提示）
    if (isFinanceManager.value) {
      const users = res.expenses?.map(e => e.user).filter(Boolean) || []
      const uniqueUsers = []
      const seen = new Set()
      for (const u of users) {
        if (u.id && !seen.has(u.id)) {
          seen.add(u.id)
          uniqueUsers.push(u)
        }
      }
      allUsers.value = uniqueUsers
    }
  } catch (error) {
    console.error(t('expenses.fetchFailed'), error)
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const res = await getExpenseStats({ month: dayjs().format('YYYY-MM') })
    expenseStats.value = res
  } catch (error) {
    console.error(t('expenses.fetchStatsFailed'), error)
  }
}

const fetchCategories = async () => {
  try {
    const res = await getExpenseCategories()
    categories.value = res.categories || []
  } catch (error) {
    console.error(t('expenses.fetchCategoriesFailed'), error)
  }
}

const saveExpense = async () => {
  if (!form.value.title || form.value.amount <= 0) {
    ElMessage.warning(t('expenses.pleaseFillTitleAmount'))
    return
  }
  saving.value = true
  try {
    if (isEdit.value) {
      await updateExpense(editingId.value, form.value)
      ElMessage.success(t('expenses.expenseUpdated'))
    } else {
      await createExpense(form.value)
      ElMessage.success(t('expenses.expenseSubmitted'))
    }
    showCreateDialog.value = false
    resetForm()
    fetchExpenses()
    fetchStats()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || t('common.saveFailed'))
  } finally {
    saving.value = false
  }
}

const handleEdit = (row) => {
  isEdit.value = true
  editingId.value = row.id
  form.value = {
    title: row.title,
    amount: row.amount,
    category: row.category,
    description: row.description,
    attachments: row.attachments || []
  }
  showCreateDialog.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(t('expenses.deleteConfirm'), t('common.tip'), { type: 'warning' })
    await deleteExpense(row.id)
    ElMessage.success(t('expenses.deleted'))
    fetchExpenses()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(t('expenses.deleteFailed'), error)
    }
  }
}

const handleApprove = async (row) => {
  try {
    await approveExpense(row.id)
    ElMessage.success(t('expenses.approved'))
    fetchExpenses()
    fetchStats()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || t('common.operationFailed'))
  }
}

const handleReject = async (row) => {
  try {
    await rejectExpense(row.id)
    ElMessage.success(t('expenses.rejected'))
    fetchExpenses()
    fetchStats()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || t('common.operationFailed'))
  }
}

const handleReimburse = (row) => {
  // 【新增】打开支付方式选择弹窗
  currentReimburseRow.value = row
  showPaymentDialog.value = true
}

const handlePaymentSelect = async (paymentType) => {
  // 跳转到对应支付官网
  const paymentUrls = {
    wechat: 'https://pay.weixin.qq.com/',
    paypal: 'https://www.paypal.com/',
    alipay: 'https://www.alipay.com/'
  }
  
  if (paymentUrls[paymentType]) {
    window.open(paymentUrls[paymentType], '_blank')
  }
  
  // 关闭弹窗并标记已打款
  showPaymentDialog.value = false
  
  if (!currentReimburseRow.value) return
  
  try {
    await reimburseExpense(currentReimburseRow.value.id)
    ElMessage.success(t('expenses.paidMarked'))
    fetchExpenses()
    fetchStats()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || t('common.operationFailed'))
  } finally {
    currentReimburseRow.value = null
  }
}

// 【第三次迭代郝益墨负责】(4) 查看报销详情
const handleViewDetail = (row) => {
  detailExpense.value = row
  showDetailDrawer.value = true
}

const resetFilter = () => {
  filterStatus.value = ''
  filterCategory.value = ''
  filterUserName.value = ''
}

const resetForm = () => {
  isEdit.value = false
  editingId.value = null
  form.value = { title: '', amount: 0, category: 'other', description: '', attachments: [] }
}

// 【第三次迭代郝益墨负责】(5) 上传附件
const handleUpload = async (file) => {
  uploading.value = true
  try {
    const res = await uploadExpenseAttachment(file.raw)
    if (res.file) {
      form.value.attachments.push(res.file)
      ElMessage.success(t('expenses.uploadSuccess'))
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.message || t('expenses.uploadFailed'))
  } finally {
    uploading.value = false
  }
}

// 【第三次迭代郝益墨负责】(5) 删除附件
const removeAttachment = (index) => {
  form.value.attachments.splice(index, 1)
}

// 【第三次迭代郝益墨负责】(5) 上传前校验
const beforeUpload = (file) => {
  const allowedTypes = [
    'image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/bmp', 'image/webp',
    'application/pdf',
    'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'text/plain'
  ]
  const isAllowed = allowedTypes.includes(file.type)
  if (!isAllowed) {
    ElMessage.error(t('expenses.uploadTypeError'))
  }
  return isAllowed
}

const categoryLabel = (value) => {
  const map = {
    travel: t('expenses.categoryTravel'),
    office: t('expenses.categoryOffice'),
    entertainment: t('expenses.categoryEntertainment'),
    training: t('expenses.categoryTraining'),
    meal: t('expenses.categoryMeal'),
    transport: t('expenses.categoryTransport'),
    other: t('expenses.categoryOther')
  }
  return map[value] || value
}

const statusLabel = (status) => {
  const map = {
    pending: t('expenses.pendingApproval'),
    approved: t('expenses.approved'),
    rejected: t('expenses.rejected'),
    reimbursed: t('expenses.paid'),
    draft: t('expenses.draft')
  }
  return map[status] || status
}

const statusType = (status) => {
  const map = { pending: 'warning', approved: 'success', rejected: 'danger', reimbursed: 'primary', draft: 'info' }
  return map[status] || ''
}

const formatDateTime = (date) => {
  return date ? dayjs(date).format('MM-DD HH:mm') : '-'
}

onMounted(() => {
  fetchExpenses()
  fetchStats()
  fetchCategories()
})
</script>

<style scoped lang="scss">
.expenses-page {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    h2 { margin: 0; }
  }

  .stats-row {
    margin-bottom: 0;
    .stat-card {
      background: #fff;
      border-radius: 8px;
      padding: 20px;
      text-align: center;
      box-shadow: 0 2px 12px rgba(0,0,0,0.05);
      transition: all 0.2s ease;
      &.clickable {
        cursor: pointer;
        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        }
        &.active {
          box-shadow: 0 0 0 2px #1890ff, 0 4px 16px rgba(0,0,0,0.1);
        }
      }
      .stat-value {
        font-size: 28px;
        font-weight: 600;
        color: #1890ff;
        margin-bottom: 8px;
        &.success { color: #67c23a; }
        &.warning { color: #e6a23c; }
        &.danger { color: #f56c6c; }
      }
      .stat-label {
        font-size: 14px;
        color: #666;
      }
    }
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    .filter-bar {
      display: flex;
      align-items: center;
    }
  }

  .pagination {
    margin-top: 16px;
    display: flex;
    justify-content: flex-end;
  }

  .category-stat {
    margin-bottom: 16px;
    .category-info {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
      .category-name { font-size: 14px; color: #333; }
      .category-amount { font-size: 14px; color: #666; }
    }
  }

  .upload-tip {
    font-size: 12px;
    color: #999;
    margin-top: 4px;
  }

  .attachment-list {
    margin-top: 12px;
    .attachment-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      background: #f5f7fa;
      border-radius: 4px;
      margin-bottom: 8px;
      .file-icon {
        color: #409eff;
        font-size: 18px;
      }
      .file-name {
        flex: 1;
        font-size: 13px;
        color: #333;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }
  }

  // 【新增】支付方式选择弹窗样式
  .payment-options {
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding: 10px 0;
  }

  .payment-option {
    display: flex;
    align-items: center;
    padding: 16px 20px;
    border-radius: 12px;
    border: 2px solid #e4e7ed;
    cursor: pointer;
    transition: all 0.3s ease;
    background: #fff;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
    }

    &.wechat {
      border-color: #07c160;
      background: linear-gradient(135deg, #f0fff4 0%, #ffffff 100%);
      &:hover { box-shadow: 0 4px 16px rgba(7, 193, 96, 0.2); }
    }

    &.paypal {
      border-color: #003087;
      background: linear-gradient(135deg, #f0f5ff 0%, #ffffff 100%);
      &:hover { box-shadow: 0 4px 16px rgba(0, 48, 135, 0.2); }
    }

    &.alipay {
      border-color: #1677ff;
      background: linear-gradient(135deg, #f0f7ff 0%, #ffffff 100%);
      &:hover { box-shadow: 0 4px 16px rgba(22, 119, 255, 0.2); }
    }

    .payment-logo {
      width: 48px;
      height: 48px;
      object-fit: contain;
      margin-right: 16px;
      border-radius: 8px;
    }

    .payment-name {
      flex: 1;
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }

    .payment-arrow {
      font-size: 18px;
      color: #909399;
    }
  }
}
</style>
