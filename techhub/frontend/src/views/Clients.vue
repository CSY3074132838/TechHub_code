<!-- 第三次迭代陈思言负责 -->
<template>
  <div class="clients-page">
    <div class="page-header">
      <h2>{{ $t('clients.pageTitle') }}</h2>
      <el-button type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon>{{ $t('clients.newClient') }}
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

    <!-- 筛选栏 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm">
        <el-form-item :label="$t('common.status')">
          <el-select v-model="filterForm.status" :placeholder="$t('clients.allStatus')" clearable style="width: 140px">
            <el-option :label="$t('clients.potential')" value="potential" />
            <el-option :label="$t('clients.cooperating')" value="active" />
            <el-option :label="$t('clients.paused')" value="inactive" />
            <el-option :label="$t('clients.churned')" value="lost" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('clients.clientLevel')">
          <el-select v-model="filterForm.level" :placeholder="$t('clients.allLevel')" clearable style="width: 140px">
            <el-option :label="$t('clients.levelS')" value="s" />
            <el-option :label="$t('clients.levelA')" value="a" />
            <el-option :label="$t('clients.levelB')" value="b" />
            <el-option :label="$t('clients.levelC')" value="c" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('common.search')">
          <el-input v-model="filterForm.search" :placeholder="$t('clients.searchPlaceholder')" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">{{ $t('common.query') }}</el-button>
          <el-button @click="resetFilter">{{ $t('common.reset') }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 客户表格 -->
    <el-card>
      <el-table :data="clients" stripe v-loading="loading">
        <el-table-column :label="$t('clients.clientName')" prop="name" min-width="160">
          <template #default="{ row }">
            <el-link type="primary" @click="goToDetail(row.id)">{{ row.name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.status')" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('clients.clientLevel')" width="80">
          <template #default="{ row }">
            <el-tag :type="getLevelType(row.level)" size="small">{{ row.level?.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('clients.industry')" prop="industry" width="120" />
        <el-table-column :label="$t('clients.contact')" width="140">
          <template #default="{ row }">
            <div>{{ row.contact_name }}</div>
            <div class="text-gray">{{ row.contact_phone }}</div>
          </template>
        </el-table-column>
        <el-table-column :label="$t('clients.accountManager')" width="120">
          <template #default="{ row }">
            {{ row.manager?.real_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('clients.relatedData')" width="180">
          <template #default="{ row }">
            <el-space>
              <el-tag size="small" type="info">{{ $t('clients.projects') }} {{ row.project_count }}</el-tag>
              <el-tag size="small" type="info">{{ $t('clients.contracts') }} {{ row.contract_count }}</el-tag>
            </el-space>
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.operation')" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDialog(row)">{{ $t('clients.edit') }}</el-button>
            <el-button v-if="row.status === 'lost'" link type="danger" @click="handleDelete(row)">{{ $t('clients.deleteCompletely') }}</el-button>
            <el-button v-else link type="danger" @click="handleDelete(row)">{{ $t('common.delete') }}</el-button>
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
        @change="fetchClients"
      />
    </el-card>

    <!-- 新建/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? $t('clients.editClient') : $t('clients.newClientDialog')" width="600px">
      <el-form :model="form" label-width="100px" :rules="rules" ref="formRef">
        <el-form-item :label="$t('clients.clientName')" prop="name">
          <el-input v-model="form.name" :placeholder="$t('clients.pleaseEnterName')" />
        </el-form-item>
        <el-form-item :label="$t('clients.industryLabel')">
          <el-input v-model="form.industry" :placeholder="$t('clients.industryPlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('clients.clientLevel')">
          <el-select v-model="form.level" style="width: 100%">
            <el-option :label="$t('clients.levelSOption')" value="s" />
            <el-option :label="$t('clients.levelAOption')" value="a" />
            <el-option :label="$t('clients.levelBOption')" value="b" />
            <el-option :label="$t('clients.levelCOption')" value="c" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('clients.contactName')">
          <el-input v-model="form.contact_name" :placeholder="$t('clients.contactName')" />
        </el-form-item>
        <el-form-item :label="$t('clients.phone')">
          <el-input v-model="form.contact_phone" :placeholder="$t('clients.phone')" />
        </el-form-item>
        <el-form-item :label="$t('clients.email')">
          <el-input v-model="form.contact_email" :placeholder="$t('clients.email')" />
        </el-form-item>
        <el-form-item :label="$t('clients.address')">
          <el-input v-model="form.address" type="textarea" rows="2" :placeholder="$t('clients.address')" />
        </el-form-item>
        <el-form-item :label="$t('clients.accountManager')">
          <el-select v-model="form.manager_id" :placeholder="$t('clients.selectManager')" style="width: 100%">
            <el-option
              v-for="user in users"
              :key="user.id"
              :label="user.real_name || user.username"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('clients.clientStatus')">
          <el-select v-model="form.status" style="width: 100%">
            <el-option :label="$t('clients.potential')" value="potential" />
            <el-option :label="$t('clients.cooperating')" value="active" />
            <el-option :label="$t('clients.paused')" value="inactive" />
            <el-option :label="$t('clients.churned')" value="lost" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('clients.remark')">
          <el-input v-model="form.remark" type="textarea" rows="3" :placeholder="$t('clients.remarkPlaceholder')" />
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
import { useI18n } from 'vue-i18n'
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { getClients, createClient, updateClient, deleteClient, permanentlyDeleteClient, getClientStats } from '@/api/clients'
import { getUsers } from '@/api/users'

const { t } = useI18n()
const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentId = ref(null)
const formRef = ref(null)

const clients = ref([])
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
  level: '',
  search: ''
})

const form = reactive({
  name: '',
  industry: '',
  level: 'b',
  contact_name: '',
  contact_phone: '',
  contact_email: '',
  address: '',
  manager_id: '',
  status: 'potential',
  remark: ''
})

const rules = {
  name: [{ required: true, message: t('clients.pleaseEnterName'), trigger: 'blur' }]
}

const statsCards = computed(() => {
  const s = stats.value
  return [
    { key: 'total', value: s.total || 0, label: t('clients.totalClients'), color: '#1890ff', filterStatus: '' },
    { key: 'active', value: s.active || 0, label: t('clients.cooperating'), color: '#52c41a', filterStatus: 'active' },
    { key: 'potential', value: s.potential || 0, label: t('clients.potential'), color: '#faad14', filterStatus: 'potential' },
    { key: 'lost', value: s.lost || 0, label: t('clients.churned'), color: '#f56c6c', filterStatus: 'lost' }
  ]
})

const handleStatClick = (status) => {
  filterForm.status = status
  handleSearch()
}

const fetchClients = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.per_page,
      ...filterForm
    }
    const res = await getClients(params)
    clients.value = res.clients
    pagination.total = res.total
    pagination.pages = res.pages
  } catch (error) {
    console.error(t('clients.operationFailed'), error)
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const res = await getClientStats()
    stats.value = res
  } catch (error) {
    console.error(t('clients.operationFailed'), error)
  }
}

const fetchUsers = async () => {
  try {
    const res = await getUsers({ per_page: 100 })
    users.value = res.users
  } catch (error) {
    console.error(t('clients.operationFailed'), error)
  }
}

const resetFilter = () => {
  filterForm.status = ''
  filterForm.level = ''
  filterForm.search = ''
  pagination.page = 1
  fetchClients()
}

const openDialog = (row = null) => {
  isEdit.value = !!row
  currentId.value = row?.id || null
  if (row) {
    Object.assign(form, {
      name: row.name,
      industry: row.industry || '',
      level: row.level || 'b',
      contact_name: row.contact_name || '',
      contact_phone: row.contact_phone || '',
      contact_email: row.contact_email || '',
      address: row.address || '',
      manager_id: row.manager_id || '',
      status: row.status || 'potential',
      remark: row.remark || ''
    })
  } else {
    Object.assign(form, {
      name: '', industry: '', level: 'b', contact_name: '', contact_phone: '',
      contact_email: '', address: '', manager_id: userStore.userInfo?.id || '', status: 'potential', remark: ''
    })
  }
  dialogVisible.value = true
}

const handleSearch = () => {
  pagination.page = 1
  fetchClients()
}

const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    if (isEdit.value) {
      await updateClient(currentId.value, { ...form })
      ElMessage.success(t('clients.updateSuccess'))
    } else {
      await createClient({ ...form })
      ElMessage.success(t('clients.createSuccess'))
    }
    dialogVisible.value = false
    pagination.page = 1
    fetchClients()
    fetchStats()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || t('clients.operationFailed'))
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (row) => {
  try {
    const isLost = row.status === 'lost'
    const message = isLost
      ? t('clients.deleteConfirm')
      : `${t('clients.markChurnConfirmPrefix')} "${row.name}" ${t('clients.markChurnConfirmSuffix')}`
    const title = isLost ? t('clients.deleteDialogTitle') : t('clients.markChurnDialogTitle')
    await ElMessageBox.confirm(message, title, {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning'
    })
    if (isLost) {
      await permanentlyDeleteClient(row.id)
      ElMessage.success(t('clients.deleteSuccess'))
    } else {
      await deleteClient(row.id)
      ElMessage.success(t('clients.markChurnSuccess'))
    }
    if (clients.value.length === 1 && pagination.page > 1) {
      pagination.page -= 1
    }
    fetchClients()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || t('clients.operationFailed'))
    }
  }
}

const goToDetail = (id) => {
  router.push(`/clients/${id}`)
}

const getStatusType = (status) => {
  const map = { potential: 'warning', active: 'success', inactive: 'info', lost: 'danger' }
  return map[status] || ''
}

const getStatusLabel = (status) => {
  const map = {
    potential: t('clients.potential'),
    active: t('clients.cooperating'),
    inactive: t('clients.paused'),
    lost: t('clients.churned')
  }
  return map[status] || status
}

const getLevelType = (level) => {
  const map = { s: 'danger', a: 'warning', b: '', c: 'info' }
  return map[level] || ''
}

onMounted(() => {
  fetchClients()
  fetchStats()
  fetchUsers()
})
</script>

<style scoped lang="scss">
.clients-page {
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
  
  .pagination {
    margin-top: 20px;
    justify-content: flex-end;
  }
  
  .text-gray {
    color: #999;
    font-size: 12px;
  }
}
</style>
