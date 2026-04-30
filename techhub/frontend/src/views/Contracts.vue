<template>
  <div class="contracts-page">
    <div class="page-header">
      <h2>合同管理</h2>
      <el-button type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon>新建合同
      </el-button>
    </div>

    <!-- 筛选 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="全部" clearable style="width: 140px">
            <el-option label="草稿" value="draft" />
            <el-option label="审批中" value="pending" />
            <el-option label="生效中" value="active" />
            <el-option label="已完成" value="completed" />
            <el-option label="已终止" value="terminated" />
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
          <el-input v-model="filterForm.search" placeholder="合同名称/编号" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 合同表格 -->
    <el-card>
      <el-table :data="contracts" stripe v-loading="loading">
        <el-table-column label="合同编号" prop="contract_no" width="140" />
        <el-table-column label="合同名称" prop="name" min-width="180" />
        <el-table-column label="客户" width="150">
          <template #default="{ row }">
            {{ row.client?.name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="金额" width="130">
          <template #default="{ row }">
            <span class="amount">{{ row.amount ? `¥${row.amount.toLocaleString()}` : '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="签约日期" width="120">
          <template #default="{ row }">
            {{ formatDate(row.sign_date) }}
          </template>
        </el-table-column>
        <el-table-column label="有效期" width="180">
          <template #default="{ row }">
            {{ formatDate(row.start_date) }} ~ {{ formatDate(row.end_date) }}
          </template>
        </el-table-column>
        <el-table-column label="创建人" width="120">
          <template #default="{ row }">
            {{ row.creator?.real_name || '-' }}
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
        @change="fetchContracts"
      />
    </el-card>

    <!-- 对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑合同' : '新建合同'" width="650px">
      <el-form :model="form" label-width="100px" :rules="rules" ref="formRef">
        <el-form-item label="合同编号" prop="contract_no">
          <el-input v-model="form.contract_no" placeholder="留空自动生成" />
        </el-form-item>
        <el-form-item label="合同名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入合同名称" />
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
        <el-form-item label="关联项目">
          <el-select v-model="form.project_id" placeholder="选择项目（可选）" clearable style="width: 100%">
            <el-option
              v-for="p in projectOptions"
              :key="p.id"
              :label="p.name"
              :value="p.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="合同金额">
          <el-input-number v-model="form.amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="签约日期">
              <el-date-picker v-model="form.sign_date" type="date" placeholder="选择日期" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="合同状态">
              <el-select v-model="form.status" style="width: 100%">
                <el-option label="草稿" value="draft" />
                <el-option label="审批中" value="pending" />
                <el-option label="生效中" value="active" />
                <el-option label="已完成" value="completed" />
                <el-option label="已终止" value="terminated" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始日期">
              <el-date-picker v-model="form.start_date" type="date" placeholder="选择日期" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束日期">
              <el-date-picker v-model="form.end_date" type="date" placeholder="选择日期" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="付款条款">
          <el-input v-model="form.payment_terms" type="textarea" rows="2" placeholder="付款方式、账期等" />
        </el-form-item>
        <el-form-item label="合同内容">
          <el-input v-model="form.content" type="textarea" rows="4" placeholder="合同主要内容摘要" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import { getContracts, createContract, updateContract, deleteContract } from '@/api/contracts'
import { getClientOptions } from '@/api/clients'
import { getProjects } from '@/api/projects'

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentId = ref(null)
const formRef = ref(null)

const contracts = ref([])
const clientOptions = ref([])
const projectOptions = ref([])

const pagination = reactive({
  page: 1,
  per_page: 10,
  total: 0,
  pages: 0
})

const filterForm = reactive({
  status: '',
  client_id: '',
  search: ''
})

const form = reactive({
  contract_no: '',
  name: '',
  client_id: '',
  project_id: '',
  amount: 0,
  sign_date: '',
  start_date: '',
  end_date: '',
  status: 'draft',
  payment_terms: '',
  content: ''
})

const rules = {
  name: [{ required: true, message: '请输入合同名称', trigger: 'blur' }],
  client_id: [{ required: true, message: '请选择客户', trigger: 'change' }]
}

const fetchContracts = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.per_page,
      ...filterForm
    }
    const res = await getContracts(params)
    contracts.value = res.contracts
    pagination.total = res.total
    pagination.pages = res.pages
  } catch (error) {
    console.error('获取合同列表失败', error)
  } finally {
    loading.value = false
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

const fetchProjectOptions = async () => {
  try {
    const res = await getProjects({ per_page: 100 })
    projectOptions.value = res.projects
  } catch (error) {
    console.error('获取项目选项失败', error)
  }
}

const resetFilter = () => {
  filterForm.status = ''
  filterForm.client_id = ''
  filterForm.search = ''
  pagination.page = 1
  fetchContracts()
}

const openDialog = (row = null) => {
  isEdit.value = !!row
  currentId.value = row?.id || null
  if (row) {
    Object.assign(form, {
      contract_no: row.contract_no,
      name: row.name,
      client_id: row.client_id,
      project_id: row.project_id || '',
      amount: row.amount || 0,
      sign_date: row.sign_date || '',
      start_date: row.start_date || '',
      end_date: row.end_date || '',
      status: row.status || 'draft',
      payment_terms: row.payment_terms || '',
      content: row.content || ''
    })
  } else {
    Object.assign(form, {
      contract_no: '', name: '', client_id: '', project_id: '', amount: 0,
      sign_date: '', start_date: '', end_date: '', status: 'draft',
      payment_terms: '', content: ''
    })
  }
  dialogVisible.value = true
}

const formatFormDates = (data) => {
  const formatted = { ...data }
  if (formatted.sign_date) formatted.sign_date = dayjs(formatted.sign_date).format('YYYY-MM-DD')
  if (formatted.start_date) formatted.start_date = dayjs(formatted.start_date).format('YYYY-MM-DD')
  if (formatted.end_date) formatted.end_date = dayjs(formatted.end_date).format('YYYY-MM-DD')
  return formatted
}

const handleSearch = () => {
  pagination.page = 1
  fetchContracts()
}

const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const data = formatFormDates({ ...form })
    if (isEdit.value) {
      await updateContract(currentId.value, data)
      ElMessage.success('合同更新成功')
    } else {
      await createContract(data)
      ElMessage.success('合同创建成功')
    }
    dialogVisible.value = false
    pagination.page = 1
    fetchContracts()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除合同 "${row.name}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteContract(row.id)
    ElMessage.success('合同已删除')
    if (contracts.value.length === 1 && pagination.page > 1) {
      pagination.page -= 1
    }
    fetchContracts()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '操作失败')
    }
  }
}

const formatDate = (date) => {
  return date ? dayjs(date).format('YYYY-MM-DD') : '-'
}

const getStatusType = (status) => {
  const map = { draft: 'info', pending: 'warning', active: 'success', completed: '', terminated: 'danger' }
  return map[status] || ''
}

const getStatusLabel = (status) => {
  const map = { draft: '草稿', pending: '审批中', active: '生效中', completed: '已完成', terminated: '已终止' }
  return map[status] || status
}

onMounted(() => {
  fetchContracts()
  fetchClientOptions()
  fetchProjectOptions()
})
</script>

<style scoped lang="scss">
.contracts-page {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    h2 {
      margin: 0;
    }
  }
  
  .filter-card {
    margin-bottom: 20px;
  }
  
  .amount {
    color: #f56c6c;
    font-weight: 500;
  }
  
  .pagination {
    margin-top: 20px;
    justify-content: flex-end;
  }
}
</style>
