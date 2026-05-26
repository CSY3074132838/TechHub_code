<!-- 第三次迭代陈思言负责 -->
<template>
  <div class="client-detail-page">
    <!-- 头部 -->
    <div class="detail-header-bar">
      <div class="header-left">
        <el-button text @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon>{{ $t('common.back') }}
        </el-button>
        <div class="client-title">
          <h2>{{ client.name }}</h2>
          <el-tag :type="getStatusType(client.status)" size="small">
            {{ getStatusLabel(client.status) }}
          </el-tag>
          <el-tag :type="getLevelType(client.level)" size="small" style="margin-left: 8px">
            {{ client.level?.toUpperCase() }}{{ $t('clients.levelSuffix') }}
          </el-tag>
        </div>
      </div>
      <div class="header-right">
        <el-button @click="showEditDialog = true">
          <el-icon><Edit /></el-icon>{{ $t('common.edit') }}
        </el-button>
      </div>
    </div>

    <el-row :gutter="20">
      <!-- 左侧基本信息 -->
      <el-col :xs="24" :lg="8">
        <el-card class="info-card">
          <template #header>
            <span>{{ $t('clients.basicInfo') }}</span>
          </template>
          <div class="info-list">
            <div class="info-item">
              <span class="label">{{ $t('clients.industryLabel') }}</span>
              <span class="value">{{ client.industry || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">{{ $t('clients.contact') }}</span>
              <span class="value">{{ client.contact_name || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">{{ $t('clients.phone') }}</span>
              <span class="value">{{ client.contact_phone || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">{{ $t('clients.email') }}</span>
              <span class="value">{{ client.contact_email || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">{{ $t('clients.address') }}</span>
              <span class="value">{{ client.address || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">{{ $t('clients.accountManager') }}</span>
              <span class="value">
                <el-avatar v-if="client.manager" :size="24" :src="client.manager.avatar">
                  {{ client.manager.real_name?.charAt(0) }}
                </el-avatar>
                {{ client.manager?.real_name || '-' }}
              </span>
            </div>
            <div class="info-item">
              <span class="label">{{ $t('clients.createdAt') }}</span>
              <span class="value">{{ formatDate(client.created_at) }}</span>
            </div>
            <div class="info-item">
              <span class="label">{{ $t('common.remark') }}</span>
              <span class="value">{{ client.remark || '-' }}</span>
            </div>
          </div>
        </el-card>

        <!-- 关联统计 -->
        <el-card class="stats-card">
          <template #header>
            <span>{{ $t('clients.relatedData') }}</span>
          </template>
          <el-row :gutter="16">
            <el-col :span="8">
              <div class="stat-box">
                <div class="stat-num">{{ client.project_count || 0 }}</div>
                <div class="stat-text">{{ $t('clients.relatedProjects') }}</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="stat-box">
                <div class="stat-num">{{ client.contract_count || 0 }}</div>
                <div class="stat-text">{{ $t('clients.contractCount') }}</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="stat-box">
                <div class="stat-num">{{ client.ticket_count || 0 }}</div>
                <div class="stat-text">{{ $t('clients.ticketCount') }}</div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>

      <!-- 右侧标签页 -->
      <el-col :xs="24" :lg="16">
        <el-card>
          <el-tabs v-model="activeTab">
            <el-tab-pane :label="$t('clients.relatedProjects')" name="projects">
              <el-table :data="projects" stripe v-loading="loadingProjects">
                <el-table-column :label="$t('projects.projectName')" prop="name" />
                <el-table-column :label="$t('common.status')" width="100">
                  <template #default="{ row }">
                    <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                      {{ row.status === 'active' ? $t('clients.statusActive') : $t('projects.archived') }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column :label="$t('common.progress')" width="200">
                  <template #default="{ row }">
                    <el-progress :percentage="row.stats?.progress || 0" :show-text="true" :stroke-width="8" />
                  </template>
                </el-table-column>
                <el-table-column :label="$t('common.memberCount')" width="100">
                  <template #default="{ row }">
                    {{ row.members?.length || 0 }} {{ $t('common.unitPeople') }}
                  </template>
                </el-table-column>
                <el-table-column :label="$t('common.operation')" width="100">
                  <template #default="{ row }">
                    <el-button link type="primary" @click="goToProject(row.id)">{{ $t('common.view') }}</el-button>
                  </template>
                </el-table-column>
              </el-table>
              <el-empty v-if="projects.length === 0" :description="$t('clients.noRelatedProjects')" />
            </el-tab-pane>

            <el-tab-pane :label="$t('contracts.contractRecords')" name="contracts">
              <el-table :data="contracts" stripe v-loading="loadingContracts">
                <el-table-column :label="$t('contracts.contractNo')" prop="contract_no" width="140" />
                <el-table-column :label="$t('contracts.contractName')" prop="name" />
                <el-table-column :label="$t('common.amount')" width="120">
                  <template #default="{ row }">
                    {{ row.amount ? `¥${row.amount.toLocaleString()}` : '-' }}
                  </template>
                </el-table-column>
                <el-table-column :label="$t('common.status')" width="100">
                  <template #default="{ row }">
                    <el-tag :type="getContractStatusType(row.status)" size="small">
                      {{ getContractStatusLabel(row.status) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column :label="$t('contracts.signDate')" width="120">
                  <template #default="{ row }">
                    {{ formatDate(row.sign_date) }}
                  </template>
                </el-table-column>
              </el-table>
              <el-empty v-if="contracts.length === 0" :description="$t('contracts.noContracts')" />
            </el-tab-pane>

            <el-tab-pane :label="$t('tickets.ticketRecords')" name="tickets">
              <el-table :data="tickets" stripe v-loading="loadingTickets">
                <el-table-column :label="$t('tickets.ticketNo')" prop="ticket_no" width="140" />
                <el-table-column :label="$t('common.title')" prop="title" />
                <el-table-column :label="$t('common.priority')" width="100">
                  <template #default="{ row }">
                    <el-tag :type="getTicketPriorityType(row.priority)" size="small">
                      {{ getTicketPriorityLabel(row.priority) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column :label="$t('common.status')" width="100">
                  <template #default="{ row }">
                    <el-tag :type="getTicketStatusType(row.status)" size="small">
                      {{ getTicketStatusLabel(row.status) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column :label="$t('tickets.assignee')" width="120">
                  <template #default="{ row }">
                    {{ row.assignee?.real_name || '-' }}
                  </template>
                </el-table-column>
              </el-table>
              <el-empty v-if="tickets.length === 0" :description="$t('tickets.noTickets')" />
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>

    <!-- 编辑对话框 -->
    <el-dialog v-model="showEditDialog" :title="$t('clients.editClientInfo')" width="600px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item :label="$t('clients.clientName')">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item :label="$t('clients.industryLabel')">
          <el-input v-model="editForm.industry" />
        </el-form-item>
        <el-form-item :label="$t('clients.contact')">
          <el-input v-model="editForm.contact_name" />
        </el-form-item>
        <el-form-item :label="$t('clients.phone')">
          <el-input v-model="editForm.contact_phone" />
        </el-form-item>
        <el-form-item :label="$t('clients.email')">
          <el-input v-model="editForm.contact_email" />
        </el-form-item>
        <el-form-item :label="$t('clients.address')">
          <el-input v-model="editForm.address" type="textarea" rows="2" />
        </el-form-item>
        <el-form-item :label="$t('clients.clientLevel')">
          <el-select v-model="editForm.level" style="width: 100%">
            <el-option :label="$t('clients.levelS')" value="s" />
            <el-option :label="$t('clients.levelA')" value="a" />
            <el-option :label="$t('clients.levelB')" value="b" />
            <el-option :label="$t('clients.levelC')" value="c" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('clients.clientStatus')">
          <el-select v-model="editForm.status" style="width: 100%">
            <el-option :label="$t('clients.statusPotential')" value="potential" />
            <el-option :label="$t('clients.statusActive')" value="active" />
            <el-option :label="$t('clients.statusInactive')" value="inactive" />
            <el-option :label="$t('clients.statusLost')" value="lost" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('common.remark')">
          <el-input v-model="editForm.remark" type="textarea" rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleUpdate" :loading="updating">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
// 第三次迭代陈思言负责
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { getClient, updateClient, getClientProjects, getClientContracts, getClientTickets } from '@/api/clients'

const { t } = useI18n()

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
    console.error(t('clients.fetchDetailFailed'), error)
  }
}

const fetchProjects = async () => {
  loadingProjects.value = true
  try {
    const res = await getClientProjects(clientId)
    projects.value = res.projects
  } catch (error) {
    console.error(t('clients.fetchProjectsFailed'), error)
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
    console.error(t('contracts.fetchFailed'), error)
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
    console.error(t('tickets.fetchFailed'), error)
  } finally {
    loadingTickets.value = false
  }
}

const handleUpdate = async () => {
  updating.value = true
  try {
    await updateClient(clientId, { ...editForm })
    ElMessage.success(t('clients.updateSuccess'))
    showEditDialog.value = false
    fetchClient()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || t('common.updateFailed'))
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
  const map = {
    potential: t('clients.statusPotential'),
    active: t('clients.statusActive'),
    inactive: t('clients.statusInactive'),
    lost: t('clients.statusLost')
  }
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
  const map = {
    draft: t('contracts.draft'),
    pending: t('contracts.inApproval'),
    active: t('contracts.active'),
    completed: t('contracts.completed'),
    terminated: t('contracts.terminated')
  }
  return map[status] || status
}

const getTicketPriorityType = (priority) => {
  const map = { low: 'info', medium: '', high: 'warning', urgent: 'danger' }
  return map[priority] || ''
}

const getTicketPriorityLabel = (priority) => {
  const map = {
    low: t('tickets.low'),
    medium: t('tickets.medium'),
    high: t('tickets.high'),
    urgent: t('tickets.urgent')
  }
  return map[priority] || priority
}

const getTicketStatusType = (status) => {
  const map = { open: 'danger', in_progress: 'warning', waiting: 'info', resolved: 'success', closed: '' }
  return map[status] || ''
}

const getTicketStatusLabel = (status) => {
  const map = {
    open: t('tickets.open'),
    in_progress: t('tickets.inProgress'),
    waiting: t('tickets.waitingFeedback'),
    resolved: t('tickets.resolved'),
    closed: t('tickets.closed')
  }
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
