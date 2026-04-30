<template>
  <div class="client-detail-page">
    <!-- 头部 -->
    <div class="detail-header-bar">
      <div class="header-left">
        <el-button text @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon>返回
        </el-button>
        <div class="client-title">
          <h2>{{ client.name }}</h2>
          <el-tag :type="getStatusType(client.status)" size="small">
            {{ getStatusLabel(client.status) }}
          </el-tag>
          <el-tag :type="getLevelType(client.level)" size="small" style="margin-left: 8px">
            {{ client.level?.toUpperCase() }}级
          </el-tag>
        </div>
      </div>
      <div class="header-right">
        <el-button @click="showEditDialog = true">
          <el-icon><Edit /></el-icon>编辑
        </el-button>
      </div>
    </div>

    <el-row :gutter="20">
      <!-- 左侧基本信息 -->
      <el-col :xs="24" :lg="8">
        <el-card class="info-card">
          <template #header>
            <span>基本信息</span>
          </template>
          <div class="info-list">
            <div class="info-item">
              <span class="label">所属行业</span>
              <span class="value">{{ client.industry || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">联系人</span>
              <span class="value">{{ client.contact_name || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">联系电话</span>
              <span class="value">{{ client.contact_phone || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">联系邮箱</span>
              <span class="value">{{ client.contact_email || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">客户地址</span>
              <span class="value">{{ client.address || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">客户经理</span>
              <span class="value">
                <el-avatar v-if="client.manager" :size="24" :src="client.manager.avatar">
                  {{ client.manager.real_name?.charAt(0) }}
                </el-avatar>
                {{ client.manager?.real_name || '-' }}
              </span>
            </div>
            <div class="info-item">
              <span class="label">创建时间</span>
              <span class="value">{{ formatDate(client.created_at) }}</span>
            </div>
            <div class="info-item">
              <span class="label">备注</span>
              <span class="value">{{ client.remark || '-' }}</span>
            </div>
          </div>
        </el-card>

        <!-- 关联统计 -->
        <el-card class="stats-card">
          <template #header>
            <span>关联数据</span>
          </template>
          <el-row :gutter="16">
            <el-col :span="8">
              <div class="stat-box">
                <div class="stat-num">{{ client.project_count || 0 }}</div>
                <div class="stat-text">关联项目</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="stat-box">
                <div class="stat-num">{{ client.contract_count || 0 }}</div>
                <div class="stat-text">合同数</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="stat-box">
                <div class="stat-num">{{ client.ticket_count || 0 }}</div>
                <div class="stat-text">工单数</div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>

      <!-- 右侧标签页 -->
      <el-col :xs="24" :lg="16">
        <el-card>
          <el-tabs v-model="activeTab">
            <el-tab-pane label="关联项目" name="projects">
              <el-table :data="projects" stripe v-loading="loadingProjects">
                <el-table-column label="项目名称" prop="name" />
                <el-table-column label="状态" width="100">
                  <template #default="{ row }">
                    <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                      {{ row.status === 'active' ? '进行中' : '已归档' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="进度" width="200">
                  <template #default="{ row }">
                    <el-progress :percentage="row.stats?.progress || 0" :show-text="true" :stroke-width="8" />
                  </template>
                </el-table-column>
                <el-table-column label="成员数" width="100">
                  <template #default="{ row }">
                    {{ row.members?.length || 0 }} 人
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="100">
                  <template #default="{ row }">
                    <el-button link type="primary" @click="goToProject(row.id)">查看</el-button>
                  </template>
                </el-table-column>
              </el-table>
              <el-empty v-if="projects.length === 0" description="暂无关联项目" />
            </el-tab-pane>

            <el-tab-pane label="合同记录" name="contracts">
              <el-table :data="contracts" stripe v-loading="loadingContracts">
                <el-table-column label="合同编号" prop="contract_no" width="140" />
                <el-table-column label="合同名称" prop="name" />
                <el-table-column label="金额" width="120">
                  <template #default="{ row }">
                    {{ row.amount ? `¥${row.amount.toLocaleString()}` : '-' }}
                  </template>
                </el-table-column>
                <el-table-column label="状态" width="100">
                  <template #default="{ row }">
                    <el-tag :type="getContractStatusType(row.status)" size="small">
                      {{ getContractStatusLabel(row.status) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="签约日期" width="120">
                  <template #default="{ row }">
                    {{ formatDate(row.sign_date) }}
                  </template>
                </el-table-column>
              </el-table>
              <el-empty v-if="contracts.length === 0" description="暂无合同记录" />
            </el-tab-pane>

            <el-tab-pane label="工单记录" name="tickets">
              <el-table :data="tickets" stripe v-loading="loadingTickets">
                <el-table-column label="工单编号" prop="ticket_no" width="140" />
                <el-table-column label="标题" prop="title" />
                <el-table-column label="优先级" width="100">
                  <template #default="{ row }">
                    <el-tag :type="getTicketPriorityType(row.priority)" size="small">
                      {{ getTicketPriorityLabel(row.priority) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="状态" width="100">
                  <template #default="{ row }">
                    <el-tag :type="getTicketStatusType(row.status)" size="small">
                      {{ getTicketStatusLabel(row.status) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="负责人" width="120">
                  <template #default="{ row }">
                    {{ row.assignee?.real_name || '-' }}
                  </template>
                </el-table-column>
              </el-table>
              <el-empty v-if="tickets.length === 0" description="暂无工单记录" />
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>

    <!-- 编辑对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑客户信息" width="600px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="客户名称">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="所属行业">
          <el-input v-model="editForm.industry" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="editForm.contact_name" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="editForm.contact_phone" />
        </el-form-item>
        <el-form-item label="联系邮箱">
          <el-input v-model="editForm.contact_email" />
        </el-form-item>
        <el-form-item label="客户地址">
          <el-input v-model="editForm.address" type="textarea" rows="2" />
        </el-form-item>
        <el-form-item label="客户等级">
          <el-select v-model="editForm.level" style="width: 100%">
            <el-option label="S级" value="s" />
            <el-option label="A级" value="a" />
            <el-option label="B级" value="b" />
            <el-option label="C级" value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="客户状态">
          <el-select v-model="editForm.status" style="width: 100%">
            <el-option label="潜在客户" value="potential" />
            <el-option label="合作中" value="active" />
            <el-option label="暂停合作" value="inactive" />
            <el-option label="已流失" value="lost" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="editForm.remark" type="textarea" rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleUpdate" :loading="updating">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { getClient, updateClient, getClientProjects, getClientContracts, getClientTickets } from '@/api/clients'

const route = useRoute()
const router = useRouter()
const clientId = route.params.id

const client = ref({})
const projects = ref([])
const contracts = ref([])
const tickets = ref([])
const activeTab = ref('projects')
const loadingProjects = ref(false)
const loadingContracts = ref(false)
const loadingTickets = ref(false)

const showEditDialog = ref(false)
const updating = ref(false)
const editForm = reactive({
  name: '', industry: '', contact_name: '', contact_phone: '',
  contact_email: '', address: '', level: '', status: '', remark: ''
})

const fetchClient = async () => {
  try {
    const res = await getClient(clientId)
    client.value = res.client
    Object.assign(editForm, {
      name: res.client.name,
      industry: res.client.industry || '',
      contact_name: res.client.contact_name || '',
      contact_phone: res.client.contact_phone || '',
      contact_email: res.client.contact_email || '',
      address: res.client.address || '',
      level: res.client.level || '',
      status: res.client.status || '',
      remark: res.client.remark || ''
    })
  } catch (error) {
    console.error('获取客户详情失败', error)
  }
}

const fetchProjects = async () => {
  loadingProjects.value = true
  try {
    const res = await getClientProjects(clientId)
    projects.value = res.projects
  } catch (error) {
    console.error('获取关联项目失败', error)
  } finally {
    loadingProjects.value = false
  }
}

const fetchContracts = async () => {
  loadingContracts.value = true
  try {
    const res = await getClientContracts(clientId)
    contracts.value = res.contracts
  } catch (error) {
    console.error('获取合同记录失败', error)
  } finally {
    loadingContracts.value = false
  }
}

const fetchTickets = async () => {
  loadingTickets.value = true
  try {
    const res = await getClientTickets(clientId)
    tickets.value = res.tickets
  } catch (error) {
    console.error('获取工单记录失败', error)
  } finally {
    loadingTickets.value = false
  }
}

const handleUpdate = async () => {
  updating.value = true
  try {
    await updateClient(clientId, { ...editForm })
    ElMessage.success('客户信息更新成功')
    showEditDialog.value = false
    fetchClient()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '更新失败')
  } finally {
    updating.value = false
  }
}

const goToProject = (id) => {
  router.push(`/projects/${id}`)
}

const formatDate = (date) => {
  return date ? dayjs(date).format('YYYY-MM-DD') : '-'
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

const getContractStatusType = (status) => {
  const map = { draft: 'info', pending: 'warning', active: 'success', completed: '', terminated: 'danger' }
  return map[status] || ''
}

const getContractStatusLabel = (status) => {
  const map = { draft: '草稿', pending: '审批中', active: '生效中', completed: '已完成', terminated: '已终止' }
  return map[status] || status
}

const getTicketPriorityType = (priority) => {
  const map = { low: 'info', medium: '', high: 'warning', urgent: 'danger' }
  return map[priority] || ''
}

const getTicketPriorityLabel = (priority) => {
  const map = { low: '低', medium: '中', high: '高', urgent: '紧急' }
  return map[priority] || priority
}

const getTicketStatusType = (status) => {
  const map = { open: 'danger', in_progress: 'warning', waiting: 'info', resolved: 'success', closed: '' }
  return map[status] || ''
}

const getTicketStatusLabel = (status) => {
  const map = { open: '待处理', in_progress: '处理中', waiting: '等待反馈', resolved: '已解决', closed: '已关闭' }
  return map[status] || status
}

onMounted(() => {
  fetchClient()
  fetchProjects()
  fetchContracts()
  fetchTickets()
})
</script>

<style scoped lang="scss">
.client-detail-page {
  .detail-header-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding: 16px 20px;
    background: #fff;
    border-radius: 8px;
    
    .header-left {
      display: flex;
      align-items: center;
      gap: 16px;
      
      .client-title {
        display: flex;
        align-items: center;
        gap: 8px;
        
        h2 {
          margin: 0;
          font-size: 18px;
        }
      }
    }
  }
  
  .info-card {
    margin-bottom: 20px;
    
    .info-list {
      .info-item {
        display: flex;
        justify-content: space-between;
        padding: 12px 0;
        border-bottom: 1px solid #f0f0f0;
        
        &:last-child {
          border-bottom: none;
        }
        
        .label {
          color: #666;
          font-size: 14px;
        }
        
        .value {
          color: #333;
          font-size: 14px;
          font-weight: 500;
          text-align: right;
          flex: 1;
          margin-left: 16px;
          word-break: break-all;
        }
      }
    }
  }
  
  .stats-card {
    .stat-box {
      text-align: center;
      padding: 16px;
      background: #f5f7fa;
      border-radius: 8px;
      
      .stat-num {
        font-size: 24px;
        font-weight: 600;
        color: #1890ff;
      }
      
      .stat-text {
        font-size: 12px;
        color: #666;
        margin-top: 4px;
      }
    }
  }
}
</style>
