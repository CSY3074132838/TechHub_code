<template>
  <!-- 【第二次迭代】考勤与工时管理页面 -->
  <div class="attendance-page">
    <div class="page-header">
      <h2>考勤工时</h2>
      <el-button type="primary" @click="showWorkTimeDialog = true">
        <el-icon><Plus /></el-icon>填报工时
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ attendanceStats.total_hours || 0 }}h</div>
          <div class="stat-label">本月工时</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value success">{{ attendanceStats.total_overtime || 0 }}h</div>
          <div class="stat-label">本月加班</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value warning">{{ attendanceStats.total_days || 0 }}</div>
          <div class="stat-label">出勤天数</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value danger">{{ attendanceStats.late_days || 0 }}</div>
          <div class="stat-label">迟到次数</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 假期余额 -->
      <el-col :xs="24" :md="8">
        <el-card>
          <template #header>
            <span>假期余额（{{ currentYear }}年）</span>
          </template>
          <div v-for="item in leaveBalances" :key="item.leave_type" class="balance-item">
            <div class="balance-info">
              <span class="balance-label">{{ leaveTypeLabel(item.leave_type) }}</span>
              <span class="balance-value">{{ item.remaining_days }} / {{ item.total_days }} 天</span>
            </div>
            <el-progress
              :percentage="Math.round((item.used_days / item.total_days) * 100)"
              :status="item.remaining_days === 0 ? 'exception' : ''"
            />
          </div>
          <el-empty v-if="leaveBalances.length === 0" description="暂无假期数据" />
        </el-card>
      </el-col>

      <!-- 工时记录 -->
      <el-col :xs="24" :md="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>工时记录</span>
              <el-select v-model="selectedMonth" size="small" style="width: 120px;" @change="fetchData">
                <el-option
                  v-for="m in monthOptions"
                  :key="m.value"
                  :label="m.label"
                  :value="m.value"
                />
              </el-select>
            </div>
          </template>
          <el-table :data="workTimeRecords" v-loading="loading" size="small">
            <el-table-column label="日期" width="110">
              <template #default="{ row }">
                {{ formatDate(row.work_date) }}
              </template>
            </el-table-column>
            <el-table-column label="项目" min-width="150">
              <template #default="{ row }">
                {{ row.project?.name || '未关联项目' }}
              </template>
            </el-table-column>
            <el-table-column label="工时" width="80">
              <template #default="{ row }">
                <span style="color: #1890ff; font-weight: 500;">{{ row.hours }}h</span>
              </template>
            </el-table-column>
            <el-table-column label="工作内容" prop="description" min-width="200" show-overflow-tooltip />
          </el-table>
          <div class="pagination">
            <el-pagination
              v-model:current-page="page"
              v-model:page-size="pageSize"
              :total="total"
              layout="total, prev, pager, next"
              @current-change="fetchWorkTimeRecords"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 项目工时分布 -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <span>项目工时分布（{{ selectedMonth }}）</span>
      </template>
      <el-row :gutter="20">
        <el-col :xs="24" :md="12">
          <div id="worktime-chart" style="height: 300px;">
            <!-- 这里可以接入 ECharts，先以表格展示 -->
            <el-table :data="workTimeStats.by_project" size="small" border>
              <el-table-column label="项目ID" prop="project_id" width="100" />
              <el-table-column label="工时" prop="hours" width="100" />
              <el-table-column label="记录数" prop="record_count" width="100" />
            </el-table>
          </div>
        </el-col>
        <el-col :xs="24" :md="12">
          <el-descriptions title="汇总" :column="1" border>
            <el-descriptions-item label="总工时">{{ workTimeStats.total_hours || 0 }} 小时</el-descriptions-item>
            <el-descriptions-item label="项目数">{{ workTimeStats.by_project?.length || 0 }} 个</el-descriptions-item>
            <el-descriptions-item label="平均每日">{{ avgDailyHours }} 小时</el-descriptions-item>
          </el-descriptions>
        </el-col>
      </el-row>
    </el-card>

    <!-- 填报工时对话框 -->
    <el-dialog v-model="showWorkTimeDialog" title="填报工时" width="500px">
      <el-form :model="workTimeForm" label-width="100px">
        <el-form-item label="工作日期" required>
          <el-date-picker v-model="workTimeForm.work_date" type="date" placeholder="选择日期" style="width: 100%" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="关联项目">
          <el-select v-model="workTimeForm.project_id" placeholder="选择项目" clearable style="width: 100%">
            <el-option v-for="p in projectOptions" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="工时" required>
          <el-input-number v-model="workTimeForm.hours" :min="0.5" :max="24" :step="0.5" style="width: 100%" />
        </el-form-item>
        <el-form-item label="工作内容">
          <el-input v-model="workTimeForm.description" type="textarea" :rows="3" placeholder="描述今天的工作内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showWorkTimeDialog = false">取消</el-button>
        <el-button type="primary" @click="saveWorkTime" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { getAttendanceStats, getLeaveBalances, getWorkTimeRecords, createWorkTimeRecord, getWorkTimeStats } from '@/api/attendance'
import { getProjects } from '@/api/projects'

// 月份选项（近12个月）
const generateMonthOptions = () => {
  const options = []
  for (let i = 0; i < 12; i++) {
    const d = dayjs().subtract(i, 'month')
    options.push({
      value: d.format('YYYY-MM'),
      label: d.format('YYYY年M月')
    })
  }
  return options
}

const monthOptions = ref(generateMonthOptions())
const selectedMonth = ref(dayjs().format('YYYY-MM'))
const currentYear = ref(dayjs().year())

const loading = ref(false)
const attendanceStats = ref({})
const leaveBalances = ref([])
const workTimeRecords = ref([])
const workTimeStats = ref({ by_project: [] })
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const projectOptions = ref([])

const showWorkTimeDialog = ref(false)
const saving = ref(false)
const workTimeForm = ref({
  work_date: dayjs().format('YYYY-MM-DD'),
  project_id: null,
  hours: 8,
  description: ''
})

const avgDailyHours = computed(() => {
  const total = workTimeStats.value.total_hours || 0
  return total > 0 ? (total / 22).toFixed(1) : '0.0'
})

const leaveTypeLabel = (type) => {
  const map = { annual: '年假', sick: '病假', personal: '事假', marriage: '婚假', maternity: '产假' }
  return map[type] || type
}

const formatDate = (dateStr) => {
  return dateStr ? dayjs(dateStr).format('MM-DD') : '-'
}

const fetchAttendanceStats = async () => {
  try {
    const res = await getAttendanceStats({ month: selectedMonth.value })
    attendanceStats.value = res
  } catch (error) {
    console.error('获取考勤统计失败', error)
  }
}

const fetchLeaveBalances = async () => {
  try {
    const res = await getLeaveBalances({ year: currentYear.value })
    leaveBalances.value = res.balances || []
  } catch (error) {
    console.error('获取假期余额失败', error)
  }
}

const fetchWorkTimeRecords = async () => {
  loading.value = true
  try {
    const res = await getWorkTimeRecords({
      page: page.value,
      per_page: pageSize.value,
      month: selectedMonth.value
    })
    workTimeRecords.value = res.records || []
    total.value = res.total || 0
  } catch (error) {
    console.error('获取工时记录失败', error)
  } finally {
    loading.value = false
  }
}

const fetchWorkTimeStats = async () => {
  try {
    const res = await getWorkTimeStats({ month: selectedMonth.value })
    workTimeStats.value = res
  } catch (error) {
    console.error('获取工时统计失败', error)
  }
}

const fetchProjects = async () => {
  try {
    const res = await getProjects()
    projectOptions.value = res.projects || []
  } catch (error) {
    console.error('获取项目失败', error)
  }
}

const saveWorkTime = async () => {
  if (!workTimeForm.value.work_date || !workTimeForm.value.hours) {
    ElMessage.warning('请填写日期和工时')
    return
  }
  saving.value = true
  try {
    await createWorkTimeRecord(workTimeForm.value)
    ElMessage.success('工时记录已保存')
    showWorkTimeDialog.value = false
    workTimeForm.value = { work_date: dayjs().format('YYYY-MM-DD'), project_id: null, hours: 8, description: '' }
    fetchWorkTimeRecords()
    fetchWorkTimeStats()
    fetchAttendanceStats()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

const fetchData = () => {
  fetchAttendanceStats()
  fetchWorkTimeRecords()
  fetchWorkTimeStats()
}

onMounted(() => {
  fetchAttendanceStats()
  fetchLeaveBalances()
  fetchWorkTimeRecords()
  fetchWorkTimeStats()
  fetchProjects()
})
</script>

<style scoped lang="scss">
.attendance-page {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    h2 { margin: 0; }
  }

  .stats-row {
    margin-bottom: 0;
    .stat-card {
      background: #fff;
      border-radius: 8px;
      padding: 20px;
      text-align: center;
      box-shadow: 0 2px 12px rgba(0,0,0,0.05);
      .stat-value {
        font-size: 28px;
        font-weight: 600;
        color: #1890ff;
        margin-bottom: 8px;
        &.success { color: #67c23a; }
        &.warning { color: #e6a23c; }
        &.danger { color: #f56c6c; }
      }
      .stat-label {
        font-size: 14px;
        color: #666;
      }
    }
  }

  .balance-item {
    margin-bottom: 16px;
    .balance-info {
      display: flex;
      justify-content: space-between;
      margin-bottom: 4px;
      .balance-label { color: #333; font-size: 14px; }
      .balance-value { color: #666; font-size: 14px; }
    }
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .pagination {
    margin-top: 16px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
