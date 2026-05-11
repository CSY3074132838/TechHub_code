<template>
  <!-- 【第二次迭代】财务概览看板 -->
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

    <!-- 趋势与类别分布 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :xs="24" :lg="14">
        <el-card>
          <template #header>
            <span>近6个月财务趋势</span>
          </template>
          <el-table :data="trend" size="small" border>
            <el-table-column label="月份" prop="month" width="120" />
            <el-table-column label="收入" width="130">
              <template #default="{ row }">
                <span style="color: #67c23a;">¥{{ row.income }}</span>
              </template>
            </el-table-column>
            <el-table-column label="支出" width="130">
              <template #default="{ row }">
                <span style="color: #f56c6c;">¥{{ row.expense }}</span>
              </template>
            </el-table-column>
            <el-table-column label="报销" width="130">
              <template #default="{ row }">
                <span style="color: #e6a23c;">¥{{ row.reimbursement }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="10">
        <el-card>
          <template #header>
            <span>本月报销类别分布</span>
          </template>
          <div v-for="item in categoryDistribution" :key="item.category" class="category-item">
            <div class="category-header">
              <span>{{ item.category }}</span>
              <span class="category-amount">¥{{ item.amount }} ({{ item.count }}笔)</span>
            </div>
            <el-progress :percentage="Math.round((item.amount / (overview.month_reimbursement || 1)) * 100)" />
          </div>
          <el-empty v-if="!categoryDistribution.length" description="暂无数据" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 待审批报销 -->
    <el-card style="margin-top: 20px;" v-if="pendingExpenseList.length">
      <template #header>
        <div class="card-header">
          <span>待审批报销</span>
          <el-button text type="primary" size="small" @click="$router.push('/expenses')">查看全部</el-button>
        </div>
      </template>
      <el-table :data="pendingExpenseList" size="small">
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
        <el-table-column label="提交时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="approveExpense(row)">通过</el-button>
            <el-button type="danger" link size="small" @click="rejectExpense(row)">驳回</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { getFinanceOverview } from '@/api/dashboard'
import { approveExpense as apiApprove, rejectExpense as apiReject } from '@/api/expenses'

const overview = ref({})
const trend = ref([])
const categoryDistribution = ref([])
const pendingExpenseList = ref([])
const loading = ref(false)

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getFinanceOverview()
    overview.value = res.overview || {}
    trend.value = res.trend || []
    categoryDistribution.value = res.category_distribution || []
    pendingExpenseList.value = res.pending_expense_list || []
  } catch (error) {
    console.error('获取财务概览失败', error)
    // 403/401 错误已由 request.js 统一拦截提示，此处无需重复弹窗
  } finally {
    loading.value = false
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

onMounted(() => {
  fetchData()
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
