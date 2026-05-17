<template>
  <!-- 【第二次迭代】费用报销管理页面 -->
  <div class="expenses-page">
    <div class="page-header">
      <h2>费用报销</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>新建报销
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ expenseStats.total_amount || 0 }}</div>
          <div class="stat-label">本月报销金额</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div
          class="stat-card clickable"
          :class="{ active: filterStatus === 'pending' }"
          @click="filterStatus = 'pending'"
        >
          <div class="stat-value success">{{ pendingCount }}</div>
          <div class="stat-label">待审批</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div
          class="stat-card clickable"
          :class="{ active: filterStatus === 'approved' }"
          @click="filterStatus = 'approved'"
        >
          <div class="stat-value warning">{{ approvedCount }}</div>
          <div class="stat-label">已审批</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div
          class="stat-card clickable"
          :class="{ active: !filterStatus && !filterCategory }"
          @click="resetFilter"
        >
          <div class="stat-value">{{ expenses.length }}</div>
          <div class="stat-label">本月记录</div>
        </div>
      </el-col>
    </el-row>

    <!-- 筛选与列表 -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>报销记录</span>
          <div class="filter-bar">
            <el-select v-model="filterStatus" placeholder="状态" clearable size="small" style="width: 120px; margin-right: 8px;">
              <el-option label="待审批" value="pending" />
              <el-option label="已审批" value="approved" />
              <el-option label="已驳回" value="rejected" />
              <el-option label="已打款" value="reimbursed" />
            </el-select>
            <el-select v-model="filterCategory" placeholder="类别" clearable size="small" style="width: 120px; margin-right: 8px;">
              <el-option v-for="c in categories" :key="c.value" :label="c.label" :value="c.value" />
            </el-select>
            <el-input
              v-model="filterUserName"
              placeholder="按人名筛选"
              clearable
              size="small"
              style="width: 140px; margin-right: 8px;"
            />
            <el-button size="small" @click="resetFilter">重置</el-button>
          </div>
        </div>
      </template>

      <el-table :data="filteredExpenses" v-loading="loading" size="small">
        <el-table-column label="报销人" width="120">
          <template #default="{ row }">
            <div style="display: flex; align-items: center; gap: 8px;">
              <el-avatar :size="24">{{ row.user?.real_name?.charAt(0) || 'U' }}</el-avatar>
              <span>{{ row.user?.real_name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="标题" prop="title" min-width="180" show-overflow-tooltip />
        <el-table-column label="金额" width="120">
          <template #default="{ row }">
            <span style="color: #f56c6c; font-weight: 600;">¥{{ row.amount }}</span>
          </template>
        </el-table-column>
        <el-table-column label="类别" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ categoryLabel(row.category) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="提交时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleViewDetail(row)">查看详情</el-button>
            <el-button v-if="canApprove(row)" type="primary" link size="small" @click="handleApprove(row)">通过</el-button>
            <el-button v-if="canApprove(row)" type="danger" link size="small" @click="handleReject(row)">驳回</el-button>
            <el-button v-if="canReimburse(row)" type="success" link size="small" @click="handleReimburse(row)">打款</el-button>
            <el-button v-if="canEdit(row)" type="primary" link size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button v-if="canDelete(row)" type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
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
        <span>本月报销类别分布</span>
      </template>
      <el-row :gutter="20">
        <el-col :xs="24" :md="12" v-for="item in expenseStats.by_category" :key="item.category">
          <div class="category-stat">
            <div class="category-info">
              <span class="category-name">{{ categoryLabel(item.category) }}</span>
              <span class="category-amount">¥{{ item.amount }} ({{ item.count }}笔)</span>
            </div>
            <el-progress :percentage="Math.round((item.amount / (expenseStats.total_amount || 1)) * 100)" />
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 报销详情抽屉 -->
    <el-drawer v-model="showDetailDrawer" title="报销详情" size="500px" :destroy-on-close="true">
      <div v-if="detailExpense" class="expense-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="报销标题">{{ detailExpense.title }}</el-descriptions-item>
          <el-descriptions-item label="报销金额">
            <span style="color: #f56c6c; font-weight: 600; font-size: 18px;">¥{{ detailExpense.amount }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="报销类别">
            <el-tag size="small">{{ categoryLabel(detailExpense.category) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="当前状态">
            <el-tag :type="statusType(detailExpense.status)" size="small">
              {{ statusLabel(detailExpense.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="报销人">
            <div style="display: flex; align-items: center; gap: 8px;">
              <el-avatar :size="32">{{ detailExpense.user?.real_name?.charAt(0) || 'U' }}</el-avatar>
              <span>{{ detailExpense.user?.real_name || detailExpense.user?.username }}</span>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="费用说明" :span="1">
            <div style="white-space: pre-wrap; line-height: 1.6;">{{ detailExpense.description || '无' }}</div>
          </el-descriptions-item>
          <el-descriptions-item label="附件">
            <div v-if="detailExpense.attachments?.length">
              <el-link
                v-for="(file, idx) in detailExpense.attachments"
                :key="idx"
                type="primary"
                :href="file.url"
                target="_blank"
                style="display: block; margin-bottom: 4px;"
              >
                {{ file.name || '附件' + (idx + 1) }}
              </el-link>
            </div>
            <span v-else style="color: #999;">无附件</span>
          </el-descriptions-item>
          <el-descriptions-item label="提交时间">{{ formatDateTime(detailExpense.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatDateTime(detailExpense.updated_at) }}</el-descriptions-item>
          <el-descriptions-item v-if="detailExpense.reimbursed_at" label="打款时间">{{ formatDateTime(detailExpense.reimbursed_at) }}</el-descriptions-item>
        </el-descriptions>

        <!-- 操作按钮 -->
        <div style="margin-top: 24px; display: flex; gap: 12px; justify-content: center;">
          <el-button v-if="canApprove(detailExpense)" type="primary" @click="handleApprove(detailExpense); showDetailDrawer = false">通过</el-button>
          <el-button v-if="canApprove(detailExpense)" type="danger" @click="handleReject(detailExpense); showDetailDrawer = false">驳回</el-button>
          <el-button v-if="canReimburse(detailExpense)" type="success" @click="handleReimburse(detailExpense); showDetailDrawer = false">标记打款</el-button>
          <el-button v-if="canEdit(detailExpense)" type="primary" plain @click="handleEdit(detailExpense); showDetailDrawer = false">编辑</el-button>
        </div>
      </div>
    </el-drawer>

    <!-- 新建/编辑对话框 -->
    <el-dialog v-model="showCreateDialog" :title="isEdit ? '编辑报销单' : '新建报销单'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="报销标题" required>
          <el-input v-model="form.title" placeholder="例如：北京出差差旅费" />
        </el-form-item>
        <el-form-item label="报销金额" required>
          <el-input-number v-model="form.amount" :min="0.01" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="报销类别">
          <el-select v-model="form.category" placeholder="选择类别" style="width: 100%">
            <el-option v-for="c in categories" :key="c.value" :label="c.label" :value="c.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="费用说明">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请描述费用明细" />
        </el-form-item>
        <el-form-item label="附件上传">
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
              <el-icon><Upload /></el-icon>选择文件
            </el-button>
            <template #tip>
              <div class="upload-tip">支持图片(png/jpg/jpeg/gif/bmp/webp)和文档(pdf/doc/docx/xls/xlsx/ppt/pptx/txt)，单个文件不超过16MB</div>
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
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveExpense" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Picture, Document, Delete } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import {
  getExpenses, createExpense, updateExpense, deleteExpense,
  approveExpense, rejectExpense, reimburseExpense,
  getExpenseStats, getExpenseCategories, uploadExpenseAttachment
} from '@/api/expenses'
import { useUserStore } from '@/stores/user'

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
const filterUserName = ref('')  // 按人名筛选
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
    console.error('获取报销列表失败', error)
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const res = await getExpenseStats({ month: dayjs().format('YYYY-MM') })
    expenseStats.value = res
  } catch (error) {
    console.error('获取报销统计失败', error)
  }
}

const fetchCategories = async () => {
  try {
    const res = await getExpenseCategories()
    categories.value = res.categories || []
  } catch (error) {
    console.error('获取类别失败', error)
  }
}

const saveExpense = async () => {
  if (!form.value.title || form.value.amount <= 0) {
    ElMessage.warning('请填写标题和金额')
    return
  }
  saving.value = true
  try {
    if (isEdit.value) {
      await updateExpense(editingId.value, form.value)
      ElMessage.success('报销单已更新')
    } else {
      await createExpense(form.value)
      ElMessage.success('报销单已提交')
    }
    showCreateDialog.value = false
    resetForm()
    fetchExpenses()
    fetchStats()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '保存失败')
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
    await ElMessageBox.confirm('确定删除该报销单吗？', '提示', { type: 'warning' })
    await deleteExpense(row.id)
    ElMessage.success('已删除')
    fetchExpenses()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败', error)
    }
  }
}

const handleApprove = async (row) => {
  try {
    await approveExpense(row.id)
    ElMessage.success('已通过')
    fetchExpenses()
    fetchStats()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '操作失败')
  }
}

const handleReject = async (row) => {
  try {
    await rejectExpense(row.id)
    ElMessage.success('已驳回')
    fetchExpenses()
    fetchStats()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '操作失败')
  }
}

const handleReimburse = async (row) => {
  try {
    await reimburseExpense(row.id)
    ElMessage.success('已标记打款')
    fetchExpenses()
    fetchStats()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '操作失败')
  }
}

// 查看报销详情
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

// 上传附件
const handleUpload = async (file) => {
  uploading.value = true
  try {
    const res = await uploadExpenseAttachment(file.raw)
    if (res.file) {
      form.value.attachments.push(res.file)
      ElMessage.success('上传成功')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '上传失败')
  } finally {
    uploading.value = false
  }
}

// 删除附件
const removeAttachment = (index) => {
  form.value.attachments.splice(index, 1)
}

// 上传前校验
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
    ElMessage.error('仅支持图片(png/jpg/jpeg/gif/bmp/webp)和文档(pdf/doc/docx/xls/xlsx/ppt/pptx/txt)')
  }
  return isAllowed
}

const categoryLabel = (value) => {
  const c = categories.value.find(item => item.value === value)
  return c ? c.label : value
}

const statusLabel = (status) => {
  const map = { pending: '待审批', approved: '已审批', rejected: '已驳回', reimbursed: '已打款', draft: '草稿' }
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
}
</style>
