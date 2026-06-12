<!-- 【第三次迭代陈思言负责】 -->
<!--
  (1) 数据中心查看权限控制：总经理、副总经理、数据分析员可直接查看，其他人需申请
  (2) 数据中心显示全公司数据而非个人数据 √
  (3) 审计日志详情页面优化 √
  (4) 审计日志四个看板改为可交互按钮 √
  (5) 个人中心与用户管理同步，支持多身份
  (6) 中英文语言切换
-->
<template>
  <div class="analytics-page">
    <div class="page-header">
      <h2>{{ $t("menu.analytics") }}</h2>
    </div>

    <!-- 无权限提示 -->
    <div v-if="!hasAccess" class="access-denied">
      <el-result
        icon="warning"
        :title="$t('analytics.noAccess')"
        :sub-title="accessSubtitle"
      >
        <template #extra>
          <el-button v-if="!wasRejected" type="primary" @click="requestAccess" :loading="requesting">
            {{ $t("analytics.applyAccess") }}
          </el-button>
          <el-button v-else type="primary" @click="requestAccess" :loading="requesting">
            {{ $t("analytics.reapply") }}
          </el-button>
        </template>
      </el-result>
    </div>

    <template v-else>
    <el-tabs v-model="activeTab">
      <!-- 团队数据标签页 -->
      <el-tab-pane :label="$t('analytics.teamData')" name="team">
        <!-- 概览统计 -->
        <el-row :gutter="20" class="overview-row">
          <el-col :xs="12" :sm="6" v-for="stat in overviewStats" :key="stat.key">
            <div
              class="overview-card"
              :class="{ clickable: stat.route }"
              @click="stat.route && router.push(stat.route)"
            >
              <div class="card-icon" :style="{ background: stat.bgColor, color: stat.color }">
                <el-icon size="24">
                  <component :is="stat.icon" />
                </el-icon>
              </div>
              <div class="card-info">
                <div class="card-value">{{ stat.value }}</div>
                <div class="card-label">{{ stat.label }}</div>
              </div>
            </div>
          </el-col>
        </el-row>

        <!-- 图表区域 -->
        <el-row :gutter="20" class="charts-row">
          <el-col :xs="24" :lg="12">
            <el-card class="chart-card">
              <template #header>
                <span>{{ $t('analytics.taskTrend') }}</span>
              </template>
              <div ref="trendChart" class="chart-container"></div>
            </el-card>
          </el-col>
          
          <el-col :xs="24" :lg="12">
            <el-card class="chart-card">
              <template #header>
                <span>{{ $t('analytics.taskStatusDistribution') }}</span>
              </template>
              <div ref="statusChart" class="chart-container"></div>
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="20" class="charts-row">
          <el-col :xs="24" :lg="12">
            <el-card class="chart-card">
              <template #header>
                <span>{{ $t('analytics.deptTaskDistribution') }}</span>
              </template>
              <div ref="deptChart" class="chart-container"></div>
            </el-card>
          </el-col>
          
          <el-col :xs="24" :lg="12">
            <el-card class="chart-card">
              <template #header>
                <span>{{ $t('analytics.teamPerformanceTop5') }}</span>
              </template>
              <div class="performance-list">
                <div
                  v-for="(item, index) in topPerformers"
                  :key="item.user.id"
                  class="performance-item"
                >
                  <div class="rank">{{ index + 1 }}</div>
                  <el-avatar :size="40" :src="item.user.avatar">
                    {{ item.user.real_name?.charAt(0) }}
                  </el-avatar>
                  <div class="info">
                    <div class="name">{{ item.user.real_name }}</div>
                    <div class="dept">{{ item.user.department }}</div>
                  </div>
                  <div class="score">
                    <span class="count">{{ item.completed_count }}</span>
                    <span class="label">{{ $t('analytics.completedTasks') }}</span>
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 项目进度 -->
        <el-card class="project-progress">
          <template #header>
            <span>{{ $t('analytics.projectProgressRanking') }}</span>
          </template>
          <el-table :data="projectProgress" stripe>
            <el-table-column type="index" width="60" />
            <el-table-column :label="$t('analytics.projectName')" prop="name" />
            <el-table-column :label="$t('analytics.totalTasks')" prop="total" width="100" />
            <el-table-column :label="$t('analytics.completedTasks')" prop="done" width="100" />
            <el-table-column :label="$t('common.progress')" width="300">
              <template #default="{ row }">
                <el-progress :percentage="row.progress" :color="getProgressColor(row.progress)" />
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- CRM数据标签页 -->
      <el-tab-pane :label="$t('analytics.crmData')" name="crm">
        <el-row :gutter="20" class="overview-row">
          <el-col :xs="12" :sm="6" v-for="stat in crmOverviewStats" :key="stat.key">
            <div
              class="overview-card"
              :class="{ clickable: stat.route }"
              @click="stat.route && router.push(stat.route)"
            >
              <div class="card-icon" :style="{ background: stat.bgColor, color: stat.color }">
                <el-icon size="24">
                  <component :is="stat.icon" />
                </el-icon>
              </div>
              <div class="card-info">
                <div class="card-value">{{ stat.value }}</div>
                <div class="card-label">{{ stat.label }}</div>
              </div>
            </div>
          </el-col>
        </el-row>

        <el-row :gutter="20" class="charts-row">
          <el-col :xs="24" :lg="12">
            <el-card class="chart-card">
              <template #header>
                <span>{{ $t('analytics.clientTicketTrend') }}</span>
              </template>
              <div ref="crmTrendChart" class="chart-container"></div>
            </el-card>
          </el-col>
          
          <el-col :xs="24" :lg="12">
            <el-card class="chart-card">
              <template #header>
                <span>{{ $t('analytics.clientAmountTop10') }}</span>
              </template>
              <div ref="clientRankingChart" class="chart-container"></div>
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="20" class="charts-row">
          <el-col :xs="24" :lg="12">
            <el-card class="chart-card">
              <template #header>
                <span>{{ $t('analytics.clientStatusDistribution') }}</span>
              </template>
              <div class="crm-stats">
                <el-row :gutter="16">
                  <el-col :span="12" v-for="item in clientStatusDist" :key="item.label">
                    <div class="crm-stat-item">
                      <div class="crm-stat-label">{{ item.label }}</div>
                      <div class="crm-stat-value" :style="{ color: item.color }">{{ item.value }}</div>
                    </div>
                  </el-col>
                </el-row>
              </div>
            </el-card>
          </el-col>
          
          <el-col :xs="24" :lg="12">
            <el-card class="chart-card">
              <template #header>
                <span>{{ $t('analytics.managerPerformanceRanking') }}</span>
              </template>
              <div class="performance-list">
                <div
                  v-for="(item, index) in managerRanking"
                  :key="item.user.id"
                  class="performance-item"
                >
                  <div class="rank">{{ index + 1 }}</div>
                  <el-avatar :size="40" :src="item.user.avatar">
                    {{ item.user.real_name?.charAt(0) }}
                  </el-avatar>
                  <div class="info">
                    <div class="name">{{ item.user.real_name }}</div>
                    <div class="dept">{{ item.user.department }}</div>
                  </div>
                  <div class="score">
                    <span class="count">{{ item.total_amount ? `¥${item.total_amount.toLocaleString()}` : '¥0' }}</span>
                    <span class="label">{{ item.contract_count }} {{ $t('analytics.contractsUnit') }}</span>
                  </div>
                </div>
                <el-empty v-if="managerRanking.length === 0" :description="$t('common.noData')" />
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>
    </el-tabs>
    </template>
  </div>
</template>

<script setup>
// 第三次迭代陈思言负责
import { ref, onMounted, nextTick, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import { useUserStore } from '@/stores/user'
import { getStatistics, getCrmOverview, getCrmRanking } from '@/api/dashboard'
import { getApprovals, createApproval } from '@/api/approvals'
import { ElMessage } from 'element-plus'

const { t } = useI18n()

const trendChart = ref(null)
const statusChart = ref(null)
const deptChart = ref(null)
const crmTrendChart = ref(null)
const clientRankingChart = ref(null)

const router = useRouter()
const userStore = useUserStore()

const statistics = ref({})
const overviewStats = ref([])
const topPerformers = ref([])
const projectProgress = ref([])
const requesting = ref(false)
const wasRejected = ref(false)
const activeTab = ref('team')

let trendChartInstance = null
let statusChartInstance = null
let deptChartInstance = null
let crmTrendChartInstance = null
let clientRankingChartInstance = null

// CRM数据
const crmOverview = ref({})
const crmRanking = ref({})

// 可直接访问数据中心的角色（无需申请）：总经理、副总经理、数据分析员
// 部门负责人、项目经理、项目组长、普通成员无法查看，需申请
const DIRECT_ACCESS_ROLES = ['super_admin', 'deputy_general_manager', 'data_analyst']

const hasAccess = computed(() => {
  if (!userStore.userInfo) return false
  // 只有指定角色可以直接访问，其他角色即使有 dashboard_view 权限也无法访问
  return userStore.userInfo.roles?.some(r =>
    DIRECT_ACCESS_ROLES.includes(r.name)
  ) || false
})

const accessSubtitle = computed(() => {
  return wasRejected.value
    ? t('analytics.accessRejected')
    : t('analytics.accessDeniedSubtitle')
})

const crmOverviewStats = computed(() => {
  const o = crmOverview.value.overview || {}
  return [
    { key: 'clients', value: o.total_clients || 0, label: t('analytics.totalClients'), icon: 'OfficeBuilding', bgColor: '#e6f7ff', color: '#1890ff', route: '/clients' },
    { key: 'contracts', value: o.total_contracts || 0, label: t('analytics.contractCount'), icon: 'DocumentCopy', bgColor: '#f6ffed', color: '#52c41a', route: '/contracts' },
    { key: 'amount', value: o.total_amount ? `¥${o.total_amount.toLocaleString()}` : '¥0', label: t('analytics.totalContractAmount'), icon: 'Money', bgColor: '#fff7e6', color: '#faad14' },
    { key: 'tickets', value: o.total_tickets || 0, label: t('analytics.totalTickets'), icon: 'ChatDotSquare', bgColor: '#f9f0ff', color: '#722ed1', route: '/tickets' }
  ]
})

const clientStatusDist = computed(() => {
  const o = crmOverview.value.overview || {}
  return [
    { label: t('clients.potential'), value: o.potential_clients || 0, color: '#faad14' },
    { label: t('clients.cooperating'), value: o.active_clients || 0, color: '#52c41a' },
    { label: t('clients.paused'), value: o.inactive_clients || 0, color: '#909399' },
    { label: t('clients.churned'), value: o.lost_clients || 0, color: '#f56c6c' }
  ]
})

const managerRanking = computed(() => {
  return crmRanking.value.manager_ranking || []
})

const fetchStatistics = async () => {
  try {
    const res = await getStatistics()
    statistics.value = res
    
    const overview = res.overview
    overviewStats.value = [
      { key: 'users', value: overview.total_users ?? 0, label: t('analytics.totalUsers'), icon: 'User', bgColor: '#e6f7ff', color: '#1890ff', route: '/users' },
      { key: 'projects', value: overview.total_projects ?? 0, label: t('analytics.projectCount'), icon: 'Folder', bgColor: '#f6ffed', color: '#52c41a', route: '/projects' },
      { key: 'tasks', value: overview.total_tasks ?? 0, label: t('analytics.totalTasks'), icon: 'Document', bgColor: '#fff7e6', color: '#faad14', route: '/tasks' },
      { key: 'rate', value: (overview.task_completion_rate ?? 0) + '%', label: t('analytics.completionRate'), icon: 'TrendCharts', bgColor: '#f9f0ff', color: '#722ed1' }
    ]
    
    topPerformers.value = res.top_performers || []
    projectProgress.value = res.project_progress || []
    
    nextTick(() => {
      initCharts(res)
    })
  } catch (error) {
    console.error(t('analytics.fetchStatsFailed'), error)
  }
}

const fetchCrmData = async () => {
  try {
    const [overviewRes, rankingRes] = await Promise.all([
      getCrmOverview(),
      getCrmRanking()
    ])
    crmOverview.value = overviewRes
    crmRanking.value = rankingRes
    
    nextTick(() => {
      initCrmCharts(overviewRes, rankingRes)
    })
  } catch (error) {
    console.error(t('analytics.fetchCrmFailed'), error)
  }
}

const initCharts = (data) => {
  // 任务趋势图
  if (trendChart.value) {
    if (trendChartInstance) {
      trendChartInstance.dispose()
    }
    trendChartInstance = echarts.init(trendChart.value)
    const trendDates = data.task_trend?.dates || []
    const trendCreated = data.task_trend?.created || []
    const trendCompleted = data.task_trend?.completed || []
    // 如果全是0，显示提示
    const hasData = trendCreated.some(v => v > 0) || trendCompleted.some(v => v > 0)
    trendChartInstance.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: [t('analytics.newTasks'), t('analytics.completedTasks')] },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: trendDates
      },
      yAxis: { type: 'value' },
      series: [
        {
          name: t('analytics.newTasks'),
          type: 'line',
          smooth: true,
          data: trendCreated,
          itemStyle: { color: '#1890ff' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
              { offset: 1, color: 'rgba(24, 144, 255, 0.05)' }
            ])
          }
        },
        {
          name: t('analytics.completedTasks'),
          type: 'line',
          smooth: true,
          data: trendCompleted,
          itemStyle: { color: '#52c41a' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(82, 196, 26, 0.3)' },
              { offset: 1, color: 'rgba(82, 196, 26, 0.05)' }
            ])
          }
        }
      ],
      graphic: hasData ? [] : [{
        type: 'text',
        left: 'center',
        top: 'middle',
        style: {
          text: t('analytics.noTaskActivity'),
          fill: '#999',
          fontSize: 14
        }
      }]
    })
  }
  
  // 任务状态分布图
  if (statusChart.value) {
    if (statusChartInstance) {
      statusChartInstance.dispose()
    }
    statusChartInstance = echarts.init(statusChart.value)
    const statusData = data.task_status_distribution || []
    const pieData = statusData.map(item => ({
      name: getStatusLabel(item.status),
      value: item.count
    })).filter(item => item.value > 0)
    statusChartInstance.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: '5%' },
      series: [
        {
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: { show: false },
          emphasis: {
            label: {
              show: true,
              fontSize: 16,
              fontWeight: 'bold'
            }
          },
          data: pieData.length > 0 ? pieData : [{ name: t('common.noData'), value: 1 }]
        }
      ],
      color: pieData.length > 0 ? ['#909399', '#e6a23c', '#1890ff', '#67c23a'] : ['#e0e0e0']
    })
  }
  
  // 部门分布图
  if (deptChart.value) {
    if (deptChartInstance) {
      deptChartInstance.dispose()
    }
    deptChartInstance = echarts.init(deptChart.value)
    const deptData = (data.department_distribution || []).filter(item => item.department && item.count > 0)
    const hasDeptData = deptData.length > 0
    deptChartInstance.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'value' },
      yAxis: {
        type: 'category',
        data: hasDeptData ? deptData.map(item => item.department).reverse() : [t('common.noData')]
      },
      series: [
        {
          type: 'bar',
          data: hasDeptData ? deptData.map(item => item.count).reverse() : [0],
          itemStyle: {
            color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
              { offset: 0, color: '#1890ff' },
              { offset: 1, color: '#36cfc9' }
            ]),
            borderRadius: [0, 4, 4, 0]
          }
        }
      ],
      graphic: hasDeptData ? [] : [{
        type: 'text',
        left: 'center',
        top: 'middle',
        style: {
          text: t('analytics.noDeptTaskData'),
          fill: '#999',
          fontSize: 14
        }
      }]
    })
  }
}

const getStatusLabel = (status) => {
  const labelMap = {
    'todo': t('tasks.todo'),
    'in_progress': t('tasks.inProgress'),
    'review': t('tasks.inReview'),
    'done': t('tasks.done')
  }
  return labelMap[status] || status
}

const getProgressColor = (progress) => {
  if (progress >= 80) return '#67c23a'
  if (progress >= 50) return '#e6a23c'
  return '#f56c6c'
}

// 窗口大小改变时重新渲染图表
window.addEventListener('resize', () => {
  trendChartInstance?.resize()
  statusChartInstance?.resize()
  deptChartInstance?.resize()
  crmTrendChartInstance?.resize()
  clientRankingChartInstance?.resize()
})

const initCrmCharts = (overviewData, rankingData) => {
  // CRM趋势图
  if (crmTrendChart.value) {
    if (crmTrendChartInstance) {
      crmTrendChartInstance.dispose()
    }
    crmTrendChartInstance = echarts.init(crmTrendChart.value)
    const trend = overviewData.trend || {}
    crmTrendChartInstance.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: [t('analytics.newClients'), t('analytics.newTickets')] },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'category', boundaryGap: false, data: trend.dates || [] },
      yAxis: { type: 'value' },
      series: [
        {
          name: t('analytics.newClients'),
          type: 'line',
          smooth: true,
          data: trend.clients || [],
          itemStyle: { color: '#1890ff' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
              { offset: 1, color: 'rgba(24, 144, 255, 0.05)' }
            ])
          }
        },
        {
          name: t('analytics.newTickets'),
          type: 'line',
          smooth: true,
          data: trend.tickets || [],
          itemStyle: { color: '#faad14' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(250, 173, 20, 0.3)' },
              { offset: 1, color: 'rgba(250, 173, 20, 0.05)' }
            ])
          }
        }
      ]
    })
  }
  
  // 客户金额排行图
  if (clientRankingChart.value) {
    if (clientRankingChartInstance) {
      clientRankingChartInstance.dispose()
    }
    clientRankingChartInstance = echarts.init(clientRankingChart.value)
    const ranking = rankingData.client_ranking || []
    clientRankingChartInstance.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'value' },
      yAxis: {
        type: 'category',
        data: ranking.map(item => item.client?.name || t('common.unknown')).slice(0, 10).reverse()
      },
      series: [
        {
          type: 'bar',
          data: ranking.map(item => item.total_amount || 0).slice(0, 10).reverse(),
          itemStyle: {
            color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
              { offset: 0, color: '#52c41a' },
              { offset: 1, color: '#95de64' }
            ]),
            borderRadius: [0, 4, 4, 0]
          }
        }
      ]
    })
  }
}

const checkRejectedStatus = async () => {
  try {
    const res = await getApprovals({ scope: 'my', per_page: 1, status: 'rejected' })
    const rejectedPermissions = (res.approvals || []).filter(a =>
      a.title && a.title.includes(t('analytics.permissionApplyPrefix'))
    )
    if (rejectedPermissions.length > 0) {
      wasRejected.value = true
    }
  } catch (error) {
    console.error(error)
  }
}

const requestAccess = async () => {
  requesting.value = true
  try {
    await createApproval({
      title: t('analytics.permissionApplyTitle'),
      approval_type: 'permission',
      description: t('analytics.permissionApplyDesc'),
      is_urgent: false
    })
    ElMessage.success(t('analytics.applySubmitted'))
    wasRejected.value = false
  } catch (error) {
    ElMessage.error(error.response?.data?.message || t('analytics.applyFailed'))
  } finally {
    requesting.value = false
  }
}

// 监听标签切换，初始化对应图表
watch(activeTab, (tab) => {
  if (tab === 'crm' && crmOverview.value.trend) {
    nextTick(() => {
      initCrmCharts(crmOverview.value, crmRanking.value)
    })
  } else if (tab === 'team' && statistics.value.task_trend) {
    nextTick(() => {
      initCharts(statistics.value)
      // 重新调整大小以确保图表正确显示
      trendChartInstance?.resize()
      statusChartInstance?.resize()
      deptChartInstance?.resize()
    })
  }
})

onMounted(() => {
  if (hasAccess.value) {
    fetchStatistics()
    fetchCrmData()
  } else {
    checkRejectedStatus()
  }
})
</script>

<style scoped lang="scss">
.analytics-page {
  .overview-row {
    margin-bottom: 20px;
    
    .overview-card {
      background: #fff;
      border-radius: 8px;
      padding: 20px;
      display: flex;
      align-items: center;
      gap: 16px;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
      transition: all 0.2s ease;
      
      &.clickable {
        cursor: pointer;
        
        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        }
      }
      
      .card-icon {
        width: 56px;
        height: 56px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      
      .card-info {
        .card-value {
          font-size: 24px;
          font-weight: 600;
          color: #333;
        }
        
        .card-label {
          font-size: 14px;
          color: #666;
          margin-top: 4px;
        }
      }
    }
  }
  
  .charts-row {
    margin-bottom: 20px;
    
    .chart-card {
      .chart-container {
        height: 300px;
      }
      
      .performance-list {
        .performance-item {
          display: flex;
          align-items: center;
          padding: 12px 0;
          border-bottom: 1px solid #eee;
          
          &:last-child {
            border-bottom: none;
          }
          
          .rank {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: #f5f7fa;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            margin-right: 12px;
            
            &:nth-child(1) {
              background: #ffd700;
              color: #fff;
            }
            
            &:nth-child(2) {
              background: #c0c0c0;
              color: #fff;
            }
            
            &:nth-child(3) {
              background: #cd7f32;
              color: #fff;
            }
          }
          
          .el-avatar {
            margin-right: 12px;
          }
          
          .info {
            flex: 1;
            
            .name {
              font-weight: 500;
            }
            
            .dept {
              font-size: 12px;
              color: #999;
            }
          }
          
          .score {
            text-align: right;
            
            .count {
              display: block;
              font-size: 20px;
              font-weight: 600;
              color: #1890ff;
            }
            
            .label {
              font-size: 12px;
              color: #999;
            }
          }
        }
      }
    }
  }
  
  .project-progress {
    margin-top: 20px;
  }
  
  .access-denied {
    padding: 60px 0;
  }
}
</style>
