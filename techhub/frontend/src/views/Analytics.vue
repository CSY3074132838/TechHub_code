<template>
  <div class="analytics-page">
    <div class="page-header">
      <h2>数据中心</h2>
    </div>

    <!-- 无权限提示 -->
    <div v-if="!hasAccess" class="access-denied">
      <el-result
        icon="warning"
        title="暂无访问权限"
        :sub-title="accessSubtitle"
      >
        <template #extra>
          <el-button v-if="!wasRejected" type="primary" @click="requestAccess" :loading="requesting">
            申请查看权限
          </el-button>
          <el-button v-else type="primary" @click="requestAccess" :loading="requesting">
            重新申请
          </el-button>
        </template>
      </el-result>
    </div>

    <template v-else>
    <!-- 概览统计 -->
    <el-row :gutter="20" class="overview-row">
      <el-col :xs="12" :sm="6" v-for="stat in overviewStats" :key="stat.key">
        <div class="overview-card">
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
            <span>任务趋势</span>
          </template>
          <div ref="trendChart" class="chart-container"></div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card">
          <template #header>
            <span>任务状态分布</span>
          </template>
          <div ref="statusChart" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="charts-row">
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card">
          <template #header>
            <span>部门任务分布</span>
          </template>
          <div ref="deptChart" class="chart-container"></div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card">
          <template #header>
            <span>团队绩效 TOP5</span>
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
                <span class="label">完成任务</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 项目进度 -->
    <el-card class="project-progress">
      <template #header>
        <span>项目进度排行</span>
      </template>
      <el-table :data="projectProgress" stripe>
        <el-table-column type="index" width="60" />
        <el-table-column label="项目名称" prop="name" />
        <el-table-column label="总任务" prop="total" width="100" />
        <el-table-column label="已完成" prop="done" width="100" />
        <el-table-column label="进度" width="300">
          <template #default="{ row }">
            <el-progress :percentage="row.progress" :color="getProgressColor(row.progress)" />
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import * as echarts from 'echarts'
import { useUserStore } from '@/stores/user'
import { getStatistics } from '@/api/dashboard'
import { getApprovals, createApproval } from '@/api/approvals'
import { ElMessage } from 'element-plus'

const trendChart = ref(null)
const statusChart = ref(null)
const deptChart = ref(null)

const userStore = useUserStore()

const statistics = ref({})
const overviewStats = ref([])
const topPerformers = ref([])
const projectProgress = ref([])
const requesting = ref(false)
const wasRejected = ref(false)

let trendChartInstance = null
let statusChartInstance = null
let deptChartInstance = null

const hasAccess = computed(() => {
  if (!userStore.userInfo) return false
  return userStore.userInfo.roles?.some(r =>
    r.permissions?.includes('all') || r.permissions?.includes('dashboard_view')
  ) || false
})

const accessSubtitle = computed(() => {
  return wasRejected.value
    ? '您已被拒绝访问，请尝试重新申请'
    : '您暂无数据中心查看权限，请向管理员申请'
})

const fetchStatistics = async () => {
  try {
    const res = await getStatistics()
    statistics.value = res
    
    // 设置概览数据
    const overview = res.overview
    overviewStats.value = [
      { key: 'users', value: overview.total_users, label: '总用户', icon: 'User', bgColor: '#e6f7ff', color: '#1890ff' },
      { key: 'projects', value: overview.total_projects, label: '项目数', icon: 'Folder', bgColor: '#f6ffed', color: '#52c41a' },
      { key: 'tasks', value: overview.total_tasks, label: '总任务', icon: 'Document', bgColor: '#fff7e6', color: '#faad14' },
      { key: 'rate', value: overview.task_completion_rate + '%', label: '完成率', icon: 'TrendCharts', bgColor: '#f9f0ff', color: '#722ed1' }
    ]
    
    topPerformers.value = res.top_performers || []
    projectProgress.value = res.project_progress || []
    
    // 初始化图表
    nextTick(() => {
      initCharts(res)
    })
  } catch (error) {
    console.error('获取统计数据失败', error)
  }
}

const initCharts = (data) => {
  // 任务趋势图
  if (trendChart.value) {
    trendChartInstance = echarts.init(trendChart.value)
    trendChartInstance.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['新建任务', '完成任务'] },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: data.task_trend?.dates || []
      },
      yAxis: { type: 'value' },
      series: [
        {
          name: '新建任务',
          type: 'line',
          smooth: true,
          data: data.task_trend?.created || [],
          itemStyle: { color: '#1890ff' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
              { offset: 1, color: 'rgba(24, 144, 255, 0.05)' }
            ])
          }
        },
        {
          name: '完成任务',
          type: 'line',
          smooth: true,
          data: data.task_trend?.completed || [],
          itemStyle: { color: '#52c41a' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(82, 196, 26, 0.3)' },
              { offset: 1, color: 'rgba(82, 196, 26, 0.05)' }
            ])
          }
        }
      ]
    })
  }
  
  // 任务状态分布图
  if (statusChart.value) {
    statusChartInstance = echarts.init(statusChart.value)
    const statusData = data.task_status_distribution || []
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
          data: statusData.map(item => ({
            name: getStatusLabel(item.status),
            value: item.count
          }))
        }
      ],
      color: ['#909399', '#e6a23c', '#1890ff', '#67c23a']
    })
  }
  
  // 部门分布图
  if (deptChart.value) {
    deptChartInstance = echarts.init(deptChart.value)
    const deptData = data.department_distribution || []
    deptChartInstance.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'value' },
      yAxis: {
        type: 'category',
        data: deptData.map(item => item.department).reverse()
      },
      series: [
        {
          type: 'bar',
          data: deptData.map(item => item.count).reverse(),
          itemStyle: {
            color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
              { offset: 0, color: '#1890ff' },
              { offset: 1, color: '#36cfc9' }
            ]),
            borderRadius: [0, 4, 4, 0]
          }
        }
      ]
    })
  }
}

const getStatusLabel = (status) => {
  const labelMap = {
    'todo': '待处理',
    'in_progress': '进行中',
    'review': '审核中',
    'done': '已完成'
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
})

const checkRejectedStatus = async () => {
  try {
    const res = await getApprovals({ scope: 'my', per_page: 1, status: 'rejected' })
    const rejectedPermissions = (res.approvals || []).filter(a =>
      a.title && a.title.includes('[权限申请]')
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
      title: '[权限申请] 申请查看数据中心',
      approval_type: 'other',
      description: '申请查看数据中心权限',
      is_urgent: false
    })
    ElMessage.success('申请已提交，请等待管理员审批')
    wasRejected.value = false
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '申请失败')
  } finally {
    requesting.value = false
  }
}

onMounted(() => {
  if (hasAccess.value) {
    fetchStatistics()
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
