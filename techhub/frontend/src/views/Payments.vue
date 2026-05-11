<template>
  <!-- 【第二次迭代】收付款记录管理页面 -->
  <div class="payments-page">
    <div class="page-header">
      <h2>收付款管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>新建记录
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value success">¥{{ paymentStats.total_income || 0 }}</div>
          <div class="stat-label">本月收入</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value danger">¥{{ paymentStats.total_expense || 0 }}</div>
          <div class="stat-label">本月支出</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">¥{{ paymentStats.net_profit || 0 }}</div>
          <div class="stat-label">本月净额</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value warning">{{ payments.length }}</div>
          <div class="stat-label">本月记录</div>
        </div>
      </el-col>
    </el-row>

    <!-- 趋势图表（简化表格展示） -->
    <el-card style="margin-top: 20px;" v-if="paymentStats.trend?.length">
      <template #header>
        <span>近6个月收支趋势</span>
      </template>
      <el-table :data="paymentStats.trend" size="small" border>
        <el-table-column label="月份" prop="month" width="120" />
        <el-table-column label="收入" width="150">
          <template #default="{ row }">
            <span style="color: #67c23a; font-weight: 500;">¥{{ row.income }}</span>
          </template>
        </el-table-column>
        <el-table-column label="支出" width="150">
          <template #default="{ row }">
            <span style="color: #f56c6c; font-weight: 500;">¥{{ row.expense }}</span>
          </template>
        </el-table-column>
        <el-table-column label="净额" width="150">
          <template #default="{ row }">
            <span :style="{ color: row.income - row.expense >= 0 ? '#67c23a' : '#f56c6c', fontWeight: 500 }">
              ¥{{ (row.income - row.expense).toFixed(2) }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 筛选与列表 -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>收付款记录</span>
          <div class="filter-bar">
            <el-select v-model="filterType" placeholder="收支类型" clearable size="small" style="width: 120px; margin-right: 8px;">
              <el-option label="收入" value="income" />
              <el-option label="支出" value="expense" />
            </el-select>
            <el-button size="small" @click="resetFilter">重置</el-button>
          </div>
        </div>
      </template>

      <el-table :data="filteredPayments" v-loading="loading" size="small">
        <el-table-column label="标题" prop="title" min-width="180" show-overflow-tooltip />
        <el-table-column label="金额" width="120">
          <template #default="{ row }">
            <span :style="{ color: row.payment_type === 'income' ? '#67c23a' : '#f56c6c', fontWeight: 600 }">
              {{ row.payment_type === 'income' ? '+' : '-' }}¥{{ row.amount }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="row.payment_type === 'income' ? 'success' : 'danger'" size="small">
              {{ row.payment_type === 'income' ? '收入' : '支出' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="关联合同" min-width="150">
          <template #default="{ row }">
            {{ row.contract?.name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="关联项目" min-width="150">
          <template #default="{ row }">
            {{ row.project?.name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="日期" width="120">
          <template #default="{ row }">
            {{ formatDate(row.payment_date) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'completed' ? 'success' : 'info'" size="small">
              {{ row.status === 'completed' ? '已完成' : '待处理' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="fetchPayments"
        />
      </div>
    </el-card>

    <!-- 合同收入排行 -->
    <el-card style="margin-top: 20px;" v-if="paymentStats.contract_ranking?.length">
      <template #header>
        <span>合同收入排行 Top10</span>
      </template>
      <el-table :data="paymentStats.contract_ranking" size="small">
        <el-table-column label="合同名称" prop="contract.name" min-width="200" />
        <el-table-column label="客户" min-width="150">
          <template #default="{ row }">
            {{ row.contract?.client?.name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="已收金额" width="150">
          <template #default="{ row }">
            <span style="color: #67c23a; font-weight: 600;">¥{{ row.amount }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建/编辑对话框 -->
    <el-dialog v-model="showCreateDialog" :title="isEdit ? '编辑记录' : '新建收付款记录'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" placeholder="例如：XX项目首付款" />
        </el-form-item>
        <el-form-item label="金额" required>
          <el-input-number v-model="form.amount" :min="0.01" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="收支类型" required>
          <el-radio-group v-model="form.payment_type">
            <el-radio-button label="income">收入</el-radio-button>
            <el-radio-button label="expense">支出</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="日期" required>
          <el-date-picker v-model="form.payment_date" type="date" placeholder="选择日期" style="width: 100%" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="关联合同">
          <el-select v-model="form.contract_id" placeholder="选择合同" clearable style="width: 100%">
            <el-option v-for="c in contractOptions" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联项目">
          <el-select v-model="form.project_id" placeholder="选择项目" clearable style="width: 100%">
            <el-option v-for="p in projectOptions" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="补充说明" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="savePayment" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import {
  getPayments, createPayment, updatePayment, deletePayment, getPaymentStats
} from '@/api/payments'
import { getContracts } from '@/api/contracts'
import { getProjects } from '@/api/projects'

const loading = ref(false)
const payments = ref([])
const paymentStats = ref({})
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const filterType = ref('')
const contractOptions = ref([])
const projectOptions = ref([])

const showCreateDialog = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const saving = ref(false)
const form = ref({
  title: '',
  amount: 0,
  payment_type: 'income',
  payment_date: dayjs().format('YYYY-MM-DD'),
  contract_id: null,
  project_id: null,
  description: ''
})

const filteredPayments = computed(() => {
  if (!filterType.value) return payments.value
  return payments.value.filter(p => p.payment_type === filterType.value)
})

const fetchPayments = async () => {
  loading.value = true
  try {
    const res = await getPayments({
      page: page.value,
      per_page: pageSize.value,
      month: dayjs().format('YYYY-MM')
    })
    payments.value = res.payments || []
    total.value = res.total || 0
  } catch (error) {
    console.error('获取记录失败', error)
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const res = await getPaymentStats({ month: dayjs().format('YYYY-MM') })
    paymentStats.value = res
  } catch (error) {
    console.error('获取统计失败', error)
  }
}

const fetchOptions = async () => {
  try {
    const [contractsRes, projectsRes] = await Promise.all([
      getContracts(),
      getProjects()
    ])
    contractOptions.value = contractsRes.contracts || []
    projectOptions.value = projectsRes.projects || []
  } catch (error) {
    console.error('获取选项失败', error)
  }
}

const savePayment = async () => {
  if (!form.value.title || form.value.amount <= 0 || !form.value.payment_date) {
    ElMessage.warning('请填写完整信息')
    return
  }
  saving.value = true
  try {
    if (isEdit.value) {
      await updatePayment(editingId.value, form.value)
      ElMessage.success('记录已更新')
    } else {
      await createPayment(form.value)
      ElMessage.success('记录已创建')
    }
    showCreateDialog.value = false
    resetForm()
    fetchPayments()
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
    payment_type: row.payment_type,
    payment_date: row.payment_date,
    contract_id: row.contract_id,
    project_id: row.project_id,
    description: row.description
  }
  showCreateDialog.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定删除该记录吗？', '提示', { type: 'warning' })
    await deletePayment(row.id)
    ElMessage.success('已删除')
    fetchPayments()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败', error)
    }
  }
}

const resetFilter = () => {
  filterType.value = ''
}

const resetForm = () => {
  isEdit.value = false
  editingId.value = null
  form.value = {
    title: '', amount: 0, payment_type: 'income',
    payment_date: dayjs().format('YYYY-MM-DD'),
    contract_id: null, project_id: null, description: ''
  }
}

const formatDate = (date) => {
  return date ? dayjs(date).format('YYYY-MM-DD') : '-'
}

onMounted(() => {
  fetchPayments()
  fetchStats()
  fetchOptions()
})
</script>

<style scoped lang="scss">
.payments-page {
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
      .stat-value {
        font-size: 24px;
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
}
</style>
