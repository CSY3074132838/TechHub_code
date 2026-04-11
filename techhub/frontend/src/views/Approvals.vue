<template>
  <div class="approvals-page">
    <div class="page-header">
      <h2>审批中心</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>发起审批
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ stats.overview?.pending || 0 }}</div>
          <div class="stat-label">待处理</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value success">{{ stats.overview?.approved || 0 }}</div>
          <div class="stat-label">已通过</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value danger">{{ stats.overview?.rejected || 0 }}</div>
          <div class="stat-label">已拒绝</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value warning">{{ stats.overview?.urgent_pending || 0 }}</div>
          <div class="stat-label">紧急待办</div>
        </div>
      </el-col>
    </el-row>

    <!-- 审批列表 -->
    <el-card class="approvals-list">
      <template #header>
        <div class="list-header">
          <el-radio-group v-model="activeTab" @change="handleTabChange">
            <el-radio-button label="all">全部</el-radio-button>
            <el-radio-button label="my">我发起的</el-radio-button>
            <el-radio-button label="pending">待处理</el-radio-button>
          </el-radio-group>
          
          <el-select v-model="filterType" placeholder="审批类型" clearable @change="fetchApprovals">
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
        <el-table-column label="标题" min-width="200">
          <template #default="{ row }">
            <div class="approval-title">
              <el-tag v-if="row.is_urgent" type="danger" size="small">紧急</el-tag>
              <span>{{ row.title }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="120">
          <template #default="{ row }">
            {{ getTypeLabel(row.approval_type) }}
          </template>
        </el-table-column>
        <el-table-column label="申请人" width="120">
          <template #default="{ row }">
            {{ row.applicant?.real_name }}
          </template>
        </el-table-column>
        <el-table-column label="金额" width="120">
          <template #default="{ row }">
            {{ row.amount ? `¥${row.amount}` : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="提交时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'pending' && canProcess(row)"
              type="primary"
              size="small"
              @click="openProcessDialog(row)"
            >
              处理
            </el-button>
            <el-button v-else text size="small" @click="viewDetail(row)">查看</el-button>
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
    <el-dialog v-model="showCreateDialog" title="发起审批" width="600px">
      <el-form :model="form" label-width="100px" :rules="rules" ref="formRef">
        <el-form-item label="审批类型" prop="approval_type">
          <el-select v-model="form.approval_type" placeholder="选择审批类型" style="width: 100%;">
            <el-option
              v-for="type in approvalTypes"
              :key="type.value"
              :label="type.label"
              :value="type.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入审批标题" />
        </el-form-item>
        <el-form-item label="金额" v-if="showAmount">
          <el-input-number v-model="form.amount" :min="0" :precision="2" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="紧急程度">
          <el-switch v-model="form.is_urgent" active-text="紧急" inactive-text="普通" />
        </el-form-item>
        <el-form-item label="审批说明">
          <el-input
            v-model="form.description"
            type="textarea"
            rows="4"
            placeholder="请输入审批说明"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">提交</el-button>
      </template>
    </el-dialog>

    <!-- 处理审批对话框 -->
    <el-dialog v-model="showProcessDialog" title="处理审批" width="500px">
      <div v-if="currentApproval" class="process-info">
        <p><strong>标题：</strong>{{ currentApproval.title }}</p>
        <p><strong>申请人：</strong>{{ currentApproval.applicant?.real_name }}</p>
        <p><strong>说明：</strong>{{ currentApproval.description || '无' }}</p>
      </div>
      <el-form :model="processForm" label-width="80px">
        <el-form-item label="处理意见">
          <el-radio-group v-model="processForm.action">
            <el-radio-button label="approve">同意</el-radio-button>
            <el-radio-button label="reject">拒绝</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="processForm.comment"
            type="textarea"
            rows="3"
            placeholder="请输入处理备注"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showProcessDialog = false">取消</el-button>
        <el-button type="primary" @click="handleProcess" :loading="processing">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { useUserStore } from '@/stores/user'
import { getApprovals, createApproval, processApproval, getApprovalStats, getApprovalTypes } from '@/api/approvals'

const userStore = useUserStore()

const approvals = ref([])
const stats = ref({})
const approvalTypes = ref([])
const loading = ref(false)
const activeTab = ref('all')
const filterType = ref('')
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

const showCreateDialog = ref(false)
const showProcessDialog = ref(false)
const creating = ref(false)
const processing = ref(false)
const currentApproval = ref(null)

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
  approval_type: [{ required: true, message: '请选择审批类型', trigger: 'change' }],
  title: [{ required: true, message: '请输入审批标题', trigger: 'blur' }]
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
      type: filterType.value
    }
    const res = await getApprovals(params)
    approvals.value = res.approvals
    total.value = res.total
  } catch (error) {
    console.error('获取审批列表失败', error)
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const res = await getApprovalStats()
    stats.value = res.data
  } catch (error) {
    console.error('获取统计失败', error)
  }
}

const fetchTypes = async () => {
  try {
    const res = await getApprovalTypes()
    approvalTypes.value = res.types
  } catch (error) {
    console.error('获取审批类型失败', error)
  }
}

const handleTabChange = () => {
  page.value = 1
  fetchApprovals()
}

const handleCreate = async () => {
  if (!form.value.title || !form.value.approval_type) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  creating.value = true
  try {
    await createApproval(form.value)
    ElMessage.success('审批提交成功')
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
    console.error('提交审批失败', error)
  } finally {
    creating.value = false
  }
}

const canProcess = (approval) => {
  // 简化逻辑：管理员或有权限的用户可以处理
  return userStore.isAdmin || userStore.canManageTeam
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
    ElMessage.success('处理成功')
    showProcessDialog.value = false
    fetchApprovals()
    fetchStats()
  } catch (error) {
    console.error('处理审批失败', error)
  } finally {
    processing.value = false
  }
}

const viewDetail = (approval) => {
  currentApproval.value = approval
  // 可以打开详情对话框
  ElMessage.info('详情功能开发中')
}

const formatDate = (date) => {
  return dayjs(date).format('MM-DD HH:mm')
}

const getTypeLabel = (type) => {
  const typeMap = {
    'leave': '请假',
    'expense': '报销',
    'purchase': '采购',
    'overtime': '加班',
    'other': '其他'
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
    'pending': '待处理',
    'approved': '已通过',
    'rejected': '已拒绝',
    'cancelled': '已取消'
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
