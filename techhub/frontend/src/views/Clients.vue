<template>
  <div class="clients-page">
    <div class="page-header">
      <h2>客户管理</h2>
      <el-button type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon>新建客户
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

    <!-- 筛选栏 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="全部状态" clearable style="width: 140px">
            <el-option label="潜在客户" value="potential" />
            <el-option label="合作中" value="active" />
            <el-option label="暂停合作" value="inactive" />
            <el-option label="已流失" value="lost" />
          </el-select>
        </el-form-item>
        <el-form-item label="等级">
          <el-select v-model="filterForm.level" placeholder="全部等级" clearable style="width: 140px">
            <el-option label="S级" value="s" />
            <el-option label="A级" value="a" />
            <el-option label="B级" value="b" />
            <el-option label="C级" value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input v-model="filterForm.search" placeholder="客户名称/联系人" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 客户表格 -->
    <el-card>
      <el-table :data="clients" stripe v-loading="loading">
        <el-table-column label="客户名称" prop="name" min-width="160">
          <template #default="{ row }">
            <el-link type="primary" @click="goToDetail(row.id)">{{ row.name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="等级" width="80">
          <template #default="{ row }">
            <el-tag :type="getLevelType(row.level)" size="small">{{ row.level?.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="行业" prop="industry" width="120" />
        <el-table-column label="联系人" width="140">
          <template #default="{ row }">
            <div>{{ row.contact_name }}</div>
            <div class="text-gray">{{ row.contact_phone }}</div>
          </template>
        </el-table-column>
        <el-table-column label="客户经理" width="120">
          <template #default="{ row }">
            {{ row.manager?.real_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="关联数据" width="180">
          <template #default="{ row }">
            <el-space>
              <el-tag size="small" type="info">项目 {{ row.project_count }}</el-tag>
              <el-tag size="small" type="info">合同 {{ row.contract_count }}</el-tag>
            </el-space>
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
        @change="fetchClients"
      />
    </el-card>

    <!-- 新建/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑客户' : '新建客户'" width="600px">
      <el-form :model="form" label-width="100px" :rules="rules" ref="formRef">
        <el-form-item label="客户名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入客户名称" />
        </el-form-item>
        <el-form-item label="所属行业">
          <el-input v-model="form.industry" placeholder="如：互联网、金融、制造" />
        </el-form-item>
        <el-form-item label="客户等级">
          <el-select v-model="form.level" style="width: 100%">
            <el-option label="S级 - 战略客户" value="s" />
            <el-option label="A级 - 重要客户" value="a" />
            <el-option label="B级 - 普通客户" value="b" />
            <el-option label="C级 - 小客户" value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="form.contact_name" placeholder="联系人姓名" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="form.contact_phone" placeholder="联系电话" />
        </el-form-item>
        <el-form-item label="联系邮箱">
          <el-input v-model="form.contact_email" placeholder="联系邮箱" />
        </el-form-item>
        <el-form-item label="客户地址">
          <el-input v-model="form.address" type="textarea" rows="2" placeholder="客户地址" />
        </el-form-item>
        <el-form-item label="客户经理">
          <el-select v-model="form.manager_id" placeholder="选择客户经理" style="width: 100%">
            <el-option
              v-for="user in users"
              :key="user.id"
              :label="user.real_name"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="客户状态">
          <el-select v-model="form.status" style="width: 100%">
            <el-option label="潜在客户" value="potential" />
            <el-option label="合作中" value="active" />
            <el-option label="暂停合作" value="inactive" />
            <el-option label="已流失" value="lost" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" rows="3" placeholder="备注信息" />
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
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { getClients, createClient, updateClient, deleteClient, getClientStats } from '@/api/clients'
import { getUsers } from '@/api/users'

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
  name: [{ required: true, message: '请输入客户名称', trigger: 'blur' }]
}

const statsCards = computed(() => {
  const s = stats.value
  return [
    { key: 'total', value: s.total || 0, label: '客户总数', color: '#1890ff' },
    { key: 'active', value: s.active || 0, label: '合作中', color: '#52c41a' },
    { key: 'potential', value: s.potential || 0, label: '潜在客户', color: '#faad14' },
    { key: 'lost', value: s.lost || 0, label: '已流失', color: '#f56c6c' }
  ]
})

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
    console.error('获取客户列表失败', error)
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const res = await getClientStats()
    stats.value = res
  } catch (error) {
    console.error('获取客户统计失败', error)
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
      ElMessage.success('客户更新成功')
    } else {
      await createClient({ ...form })
      ElMessage.success('客户创建成功')
    }
    dialogVisible.value = false
    pagination.page = 1
    fetchClients()
    fetchStats()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要将客户 "${row.name}" 标记为流失吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteClient(row.id)
    ElMessage.success('操作成功')
    if (clients.value.length === 1 && pagination.page > 1) {
      pagination.page -= 1
    }
    fetchClients()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '操作失败')
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
  const map = { potential: '潜在客户', active: '合作中', inactive: '暂停合作', lost: '已流失' }
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
