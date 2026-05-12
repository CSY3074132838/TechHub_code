<template>
  <!-- 【第三次迭代】财务概览看板 — 加入图表可视化 -->
  <div class="finance-page">
    <div class="page-header">
      <h2>财务看板</h2>
      <el-button type="primary" @click="$router.push('/payments')">
        <el-icon><DocumentCopy /></el-icon>收付款明细
      </el-button>
    </div>

    <!-- 概览卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="8" :lg="4">
        <div class="stat-card">
          <div class="stat-icon" style="background: #e6f7ff; color: #1890ff;">
            <el-icon size="24"><TrendCharts /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">¥{{ overview.month_income || 0 }}</div>
            <div class="stat-label">本月收入</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="8" :lg="4">
        <div class="stat-card">
          <div class="stat-icon" style="background: #fff1f0; color: #f5222d;">
            <el-icon size="24"><Money /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">¥{{ overview.month_expense || 0 }}</div>
            <div class="stat-label">本月支出</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="8" :lg="4">
        <div class="stat-card">
          <div class="stat-icon" style="background: #f6ffed; color: #52c41a;">
            <el-icon size="24"><Wallet /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">¥{{ overview.month_reimbursement || 0 }}</div>
            <div class="stat-label">本月报销</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="8" :lg="4">
        <div class="stat-card">
          <div class="stat-icon" style="background: #fff7e6; color: #faad14;">
            <el-icon size="24"><DocumentChecked /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ overview.pending_expenses || 0 }}</div>
            <div class="stat-label">待审批报销</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="8" :lg="4">
        <div class="stat-card">
          <div class="stat-icon" style="background: #f9f0ff; color: #722ed1;">
            <el-icon size="24"><Document /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">¥{{ overview.total_contract_amount || 0 }}</div>
            <div class="stat-label">合同总额</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="8" :lg="4">
        <div class="stat-card">
          <div class="stat-icon" style="background: #e6fffb; color: #13c2c2;">
            <el-icon size="24"><CircleCheck /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">¥{{ overview.receivable || 0 }}</div>
            <div class="stat-label">应收账款</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 —— 2x2 等宽网格布局 -->
    <el-row :gutter="20" class="charts-row">
      <el-col :xs="24" :lg="12">
        <el-card class="dashboard-card">
          <template #header>
            <span>近6个月财务趋势</span>
          </template>
          <div ref="trendChart" class="chart-container"></div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card class="dashboard-card">
          <template #header>
            <span>本月收支构成</span>
          </template>
          <div ref="incomeExpenseChart" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="charts-row">
      <el-col :xs="24" :lg="12">
        <el-card class="dashboard-card">
          <template #header>
            <span>本月报销类别分布</span>
          </template>
          <div ref="categoryChart" class="chart-container"></div>
          <el-empty v-if="!categoryDistribution.length" description="暂无数据" />
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card class="dashboard-card">
          <template #header>
            <span>近6个月财务数据明细</span>
          </template>
          <div class="table-container">
            <el-table :data="trendWithBalance" size="small" border stripe>
              <el-table-column label="月份" prop="month" width="100" align="center" />
              <el-table-column label="收入" width="110" align="right">
                <template #default="{ row }">
                  <span style="color: #52c41a; font-weight: 600;">¥{{ row.income }}</span>
                </template>
              </el-table-column>
              <el-table-column label="支出" width="110" align="right">
                <template #default="{ row }">
                  <span style="color: #f5222d; font-weight: 600;">¥{{ row.expense }}</span>
                </template>
              </el-table-column>
              <el-table-column label="报销" width="110" align="right">
                <template #default="{ row }">
                  <span style="color: #faad14; font-weight: 600;">¥{{ row.reimbursement }}</span>
                </template>
              </el-table-column>
              <el-table-column label="结余" align="right">
                <template #default="{ row }">
                  <span :style="{ color: row.balance >= 0 ? '#52c41a' : '#f5222d', fontWeight: 600 }">
                    ¥{{ row.balance }}
                  </span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 待审批报销 —— 精简列表，全宽展示 -->
    <el-row :gutter="20" class="charts-row" v-if="pendingExpenseList.length">
      <el-col :xs="24">
        <el-card class="dashboard-card">
          <template #header>
            <div class="card-header">
              <span>待审批报销</span>
              <el-button text type="primary" size="small" @click="$router.push('/expenses')">查看全部</el-button>
            </div>
          </template>
          <el-table :data="pendingExpenseList.slice(0, 5)" size="small">
            <el-table-column label="报销人" width="120">
              <template #default="{ row }">
                <div style="display: flex; align-items: center; gap: 8px;">
                  <el-avatar :size="24">{{ row.user?.real_name?.charAt(0) || 'U' }}</el-avatar>
                  <span>{{ row.user?.real_name }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="标题" prop="title" min-width="200" show-overflow-tooltip />
            <el-table-column label="金额" width="120">
              <template #default="{ row }">
                <span style="color: #f56c6c; font-weight: 600;">¥{{ row.amount }}</span>
              </template>
            </el-table-column>
            <el-table-column label="类别" width="100">
              <template #default="{ row }">
                <el-tag size="small">{{ row.category }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="approveExpense(row)">通过</el-button>
                <el-button type="danger" link size="small" @click="rejectExpense(row)">驳回</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import * as echarts from 'echarts'
import { getFinanceOverview } from '@/api/dashboard'
import { approveExpense as apiApprove, rejectExpense as apiReject } from '@/api/expenses'

const overview = ref({})
const trend = ref([])
const categoryDistribution = ref([])
const pendingExpenseList = ref([])
const loading = ref(false)

// 带结余的财务趋势数据
const trendWithBalance = computed(() => {
  return trend.value.map(item => ({
    ...item,
    income: item.income || 0,
    expense: item.expense || 0,
    reimbursement: item.reimbursement || 0,
    balance: (item.income || 0) - (item.expense || 0) - (item.reimbursement || 0)
  }))
})

// 图表 DOM 引用
const trendChart = ref(null)
const incomeExpenseChart = ref(null)
const categoryChart = ref(null)

// 图表实例
let trendChartInstance = null
let incomeExpenseChartInstance = null
let categoryChartInstance = null

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getFinanceOverview()
    overview.value = res.overview || {}
    trend.value = res.trend || []
    categoryDistribution.value = res.category_distribution || []
    pendingExpenseList.value = res.pending_expense_list || []
    // 数据获取完成后，在 DOM 更新后初始化图表
    nextTick(() => {
      initCharts()
    })
  } catch (error) {
    console.error('获取财务概览失败', error)
  } finally {
    loading.value = false
  }
}

const initCharts = () => {
  try {
  // 1. 近6个月财务趋势 — 柱状图+折线图
  if (trendChart.value && trend.value.length) {
    trendChartInstance = echarts.init(trendChart.value)
    const months = trend.value.map(item => item.month)
    const incomes = trend.value.map(item => item.income || 0)
    const expenses = trend.value.map(item => item.expense || 0)
    const reimbursements = trend.value.map(item => item.reimbursement || 0)

    trendChartInstance.setOption({
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' }
      },
      legend: {
        data: ['收入', '支出', '报销'],
        bottom: 0
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '10%',
        top: '10%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: months,
        axisLine: { lineStyle: { color: '#ddd' } },
        axisLabel: { color: '#666' }
      },
      yAxis: {
        type: 'value',
        axisLine: { show: false },
        splitLine: { lineStyle: { color: '#f0f0f0' } },
        axisLabel: { color: '#666' }
      },
      series: [
        {
          name: '收入',
          type: 'bar',
          data: incomes,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#52c41a' },
              { offset: 1, color: '#95de64' }
            ]),
            borderRadius: [4, 4, 0, 0]
          },
          barWidth: '25%'
        },
        {
          name: '支出',
          type: 'bar',
          data: expenses,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#f5222d' },
              { offset: 1, color: '#ff7875' }
            ]),
            borderRadius: [4, 4, 0, 0]
          },
          barWidth: '25%'
        },
        {
          name: '报销',
          type: 'line',
          data: reimbursements,
          smooth: true,
          itemStyle: { color: '#faad14' },
          lineStyle: { width: 3 },
          symbol: 'circle',
          symbolSize: 8
        }
      ]
    })
  }

  // 2. 本月收支构成 — 环形图
  if (incomeExpenseChart.value) {
    incomeExpenseChartInstance = echarts.init(incomeExpenseChart.value)
    const income = overview.value.month_income || 0
    const expense = overview.value.month_expense || 0
    const reimbursement = overview.value.month_reimbursement || 0

    incomeExpenseChartInstance.setOption({
      tooltip: {
        trigger: 'item',
        formatter: '{b}: ¥{c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        right: '5%',
        top: 'center',
        itemGap: 16
      },
      series: [
        {
          type: 'pie',
          radius: ['45%', '75%'],
          center: ['35%', '50%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 8,
            borderColor: '#fff',
            borderWidth: 3
          },
          label: {
            show: false
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 14,
              fontWeight: 'bold'
            },
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.2)'
            }
          },
          labelLine: {
            show: false
          },
          data: [
            { value: income, name: '本月收入', itemStyle: { color: '#52c41a' } },
            { value: expense, name: '本月支出', itemStyle: { color: '#f5222d' } },
            { value: reimbursement, name: '本月报销', itemStyle: { color: '#faad14' } }
          ]
        }
      ]
    })
  }

  // 3. 本月报销类别分布 — 饼图
  if (categoryChart.value && categoryDistribution.value.length) {
    categoryChartInstance = echarts.init(categoryChart.value)
    const totalAmount = categoryDistribution.value.reduce((sum, item) => sum + (item.amount || 0), 0)

    categoryChartInstance.setOption({
      tooltip: {
        trigger: 'item',
        formatter: (params) => {
          return `${params.name}<br/>金额: ¥${params.value}<br/>占比: ${params.percent}%<br/>笔数: ${params.data.count}笔`
        }
      },
      legend: {
        orient: 'vertical',
        right: '5%',
        top: 'center',
        itemGap: 12
      },
      series: [
        {
          type: 'pie',
          radius: '70%',
          center: ['35%', '50%'],
          data: categoryDistribution.value.map(item => ({
            name: item.category,
            value: item.amount,
            count: item.count,
            itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 }
          })),
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.2)'
            }
          },
          label: {
            show: true,
            formatter: '{b}\n{d}%'
          },
          labelLine: {
            show: true,
            length: 15,
            length2: 10
          }
        }
      ],
      color: ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#13c2c2', '#eb2f96']
    })
  }
  } catch (error) {
    console.error('图表初始化失败', error)
  }
}

const approveExpense = async (row) => {
  try {
    await apiApprove(row.id)
    ElMessage.success('已通过')
    fetchData()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '操作失败')
  }
}

const rejectExpense = async (row) => {
  try {
    await apiReject(row.id)
    ElMessage.success('已驳回')
    fetchData()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '操作失败')
  }
}

const formatDateTime = (date) => {
  return date ? dayjs(date).format('MM-DD HH:mm') : '-'
}

// 窗口大小改变时重新渲染图表
const handleResize = () => {
  trendChartInstance?.resize()
  incomeExpenseChartInstance?.resize()
  categoryChartInstance?.resize()
}

onMounted(() => {
  fetchData()
  window.addEventListener('resize', handleResize)
})

// 组件卸载时移除监听并销毁图表实例
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  trendChartInstance?.dispose()
  incomeExpenseChartInstance?.dispose()
  categoryChartInstance?.dispose()
})
</script>

<style scoped lang="scss">
.finance-page {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    h2 { margin: 0; }
  }

  .stats-row {
    .stat-card {
      background: #fff;
      border-radius: 8px;
      padding: 20px;
      display: flex;
      align-items: center;
      gap: 16px;
      box-shadow: 0 2px 12px rgba(0,0,0,0.05);
      margin-bottom: 20px;
      .stat-icon {
        width: 48px;
        height: 48px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
      }
      .stat-info {
        .stat-value {
          font-size: 20px;
          font-weight: 600;
          color: #333;
        }
        .stat-label {
          font-size: 13px;
          color: #999;
          margin-top: 4px;
        }
      }
    }
  }

  .charts-row {
    margin-bottom: 20px;
    .el-col {
      margin-bottom: 0;
    }
  }

  .dashboard-card {
    height: 100%;
    transition: all 0.3s ease;
    &:hover {
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
    }
    :deep(.el-card__body) {
      padding: 16px;
    }
  }

  .chart-container {
    height: 300px;
  }

  .table-container {
    height: 300px;
    overflow-y: auto;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .category-item {
    margin-bottom: 16px;
    .category-header {
      display: flex;
      justify-content: space-between;
      margin-bottom: 4px;
      font-size: 14px;
      .category-amount { color: #666; }
    }
  }
}
</style>
