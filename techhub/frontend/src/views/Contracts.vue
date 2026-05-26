<!-- 第三次迭代陈思言负责 -->
<template>
  <div class="contracts-page">
    <div class="page-header">
      <h2>{{ $t('contracts.pageTitle') }}</h2>
      <el-button type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon>{{ $t('contracts.newContract') }}
      </el-button>
    </div>

    <!-- 筛选 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm">
        <el-form-item :label="$t('common.status')">
          <el-select v-model="filterForm.status" :placeholder="$t('common.all')" clearable style="width: 140px">
            <el-option :label="$t('contracts.draft')" value="draft" />
            <el-option :label="$t('contracts.inApproval')" value="pending" />
            <el-option :label="$t('contracts.active')" value="active" />
            <el-option :label="$t('contracts.completed')" value="completed" />
            <el-option :label="$t('contracts.terminated')" value="terminated" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('contracts.client')">
          <el-select v-model="filterForm.client_id" :placeholder="$t('contracts.allClients')" clearable style="width: 180px">
            <el-option
              v-for="c in clientOptions"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('common.search')">
          <el-input v-model="filterForm.search" :placeholder="$t('contracts.searchPlaceholder')" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">{{ $t('common.query') }}</el-button>
          <el-button @click="resetFilter">{{ $t('common.reset') }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 合同表格 -->
    <el-card>
      <el-table :data="contracts" stripe v-loading="loading">
        <el-table-column :label="$t('contracts.contractNo')" prop="contract_no" width="140" />
        <el-table-column :label="$t('contracts.contractName')" prop="name" min-width="180" />
        <el-table-column :label="$t('contracts.client')" width="150">
          <template #default="{ row }">
            {{ row.client?.name || '-' }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.amount')" width="130">
          <template #default="{ row }">
            <span class="amount">{{ row.amount ? `¥${row.amount.toLocaleString()}` : '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.status')" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('contracts.signDate')" width="120">
          <template #default="{ row }">
            {{ formatDate(row.sign_date) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('contracts.validPeriod')" width="180">
          <template #default="{ row }">
            {{ formatDate(row.start_date) }} ~ {{ formatDate(row.end_date) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('contracts.creator')" width="120">
          <template #default="{ row }">
            {{ row.creator?.real_name || '-' }}
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
        @change="fetchContracts"
      />
    </el-card>

    <!-- 对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? $t('contracts.editContract') : $t('contracts.newContractDialog')" width="650px">
      <el-form :model="form" label-width="100px" :rules="rules" ref="formRef">
        <el-form-item :label="$t('contracts.contractNo')" prop="contract_no">
          <el-input v-model="form.contract_no" :placeholder="$t('contracts.autoGenerate')" />
        </el-form-item>
        <el-form-item :label="$t('contracts.contractName')" prop="name">
          <el-input v-model="form.name" :placeholder="$t('contracts.pleaseEnterName')" />
        </el-form-item>
        <el-form-item :label="$t('contracts.relatedClient')" prop="client_id">
          <el-select v-model="form.client_id" :placeholder="$t('contracts.selectClient')" style="width: 100%">
            <el-option
              v-for="c in clientOptions"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('contracts.relatedProject')">
          <el-select v-model="form.project_id" :placeholder="$t('contracts.selectProjectOptional')" clearable style="width: 100%">
            <el-option
              v-for="p in projectOptions"
              :key="p.id"
              :label="p.name"
              :value="p.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('contracts.contractAmount')">
          <el-input-number v-model="form.amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item :label="$t('contracts.signDate')">
              <el-date-picker v-model="form.sign_date" type="date" :placeholder="$t('contracts.selectDate')" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('contracts.contractStatus')">
              <el-select v-model="form.status" style="width: 100%">
                <el-option :label="$t('contracts.draft')" value="draft" />
                <el-option :label="$t('contracts.inApproval')" value="pending" />
                <el-option :label="$t('contracts.active')" value="active" />
                <el-option :label="$t('contracts.completed')" value="completed" />
                <el-option :label="$t('contracts.terminated')" value="terminated" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item :label="$t('common.startDate')">
              <el-date-picker v-model="form.start_date" type="date" :placeholder="$t('contracts.selectDate')" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('common.endDate')">
              <el-date-picker v-model="form.end_date" type="date" :placeholder="$t('contracts.selectDate')" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item :label="$t('contracts.paymentTerms')">
          <el-input v-model="form.payment_terms" type="textarea" rows="2" :placeholder="$t('contracts.paymentTermsPlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('contracts.contractContent')">
          <el-input v-model="form.content" type="textarea" rows="4" :placeholder="$t('contracts.contractContentPlaceholder')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
// 第三次迭代陈思言负责
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import { getContracts, createContract, updateContract, deleteContract } from '@/api/contracts'
import { getClientOptions } from '@/api/clients'
import { getProjects } from '@/api/projects'

const { t } = useI18n()

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
  name: [{ required: true, message: t('contracts.pleaseEnterName'), trigger: 'blur' }],
  client_id: [{ required: true, message: t('contracts.pleaseSelectClient'), trigger: 'change' }]
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
    console.error(t('contracts.fetchFailed'), error)
  } finally {
    loading.value = false
  }
}

const fetchClientOptions = async () => {
  try {
    const res = await getClientOptions()
    clientOptions.value = res.clients
  } catch (error) {
    console.error(t('contracts.fetchClientFailed'), error)
  }
}

const fetchProjectOptions = async () => {
  try {
    const res = await getProjects({ per_page: 100 })
    projectOptions.value = res.projects
  } catch (error) {
    console.error(t('contracts.fetchProjectFailed'), error)
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
      ElMessage.success(t('contracts.updateSuccess'))
    } else {
      await createContract(data)
      ElMessage.success(t('contracts.createSuccess'))
    }
    dialogVisible.value = false
    pagination.page = 1
    fetchContracts()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || t('common.operationFailed'))
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`${t('contracts.deleteConfirmPrefix')} "${row.name}" ${t('contracts.deleteConfirmSuffix')}`, t('common.tip'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning'
    })
    await deleteContract(row.id)
    ElMessage.success(t('contracts.deleteSuccess'))
    if (contracts.value.length === 1 && pagination.page > 1) {
      pagination.page -= 1
    }
    fetchContracts()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || t('common.operationFailed'))
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
  const map = {
    draft: t('contracts.draft'),
    pending: t('contracts.inApproval'),
    active: t('contracts.active'),
    completed: t('contracts.completed'),
    terminated: t('contracts.terminated')
  }
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
