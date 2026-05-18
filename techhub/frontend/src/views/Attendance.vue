<template>
  <!-- 【第二次迭代】考勤与工时管理页面 -->
  <div class="attendance-page">
    <div class="page-header">
      <h2>考勤工时</h2>
      <div class="header-actions">
        <el-button type="success" @click="handleCheckIn" :loading="checkingIn">
          <el-icon><CircleCheck /></el-icon>一键打卡
        </el-button>
        <el-button type="warning" @click="handleCheckOut" :loading="checkingOut">
          <el-icon><CircleClose /></el-icon>一键下班
        </el-button>
        <el-button type="primary" @click="showLeaveDialog = true">
          <el-icon><Document /></el-icon>请假申请
        </el-button>
        <el-button type="primary" @click="showWorkTimeDialog = true">
          <el-icon><Plus /></el-icon>填报工时
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <!-- 普通员工：本月工时 -->
      <el-col :xs="12" :sm="6" v-if="!isManager">
        <div class="stat-card">
          <div class="stat-value">{{ attendanceStats.total_hours || 0 }}h</div>
          <div class="stat-label">本月工时</div>
          <div class="stat-sub" :class="{ 'text-success': attendanceStats.completion_rate >= 100, 'text-warning': attendanceStats.completion_rate < 100 && attendanceStats.completion_rate >= 80, 'text-danger': attendanceStats.completion_rate < 80 }">
            达成率 {{ attendanceStats.completion_rate || 0 }}%
          </div>
        </div>
      </el-col>
      <!-- 高管：所有员工本月工时 -->
      <el-col :xs="12" :sm="6" v-if="isManager">
        <div class="stat-card">
          <div class="stat-value">{{ managerOverview.total_all_hours || 0 }}h</div>
          <div class="stat-label">所有员工本月工时</div>
          <div class="stat-sub">
            共 {{ managerOverview.employee_stats?.length || 0 }} 人
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value success">{{ attendanceStats.total_overtime || 0 }}h</div>
          <div class="stat-label">本月加班</div>
          <div class="stat-sub">
            日均 {{ attendanceStats.avg_daily_hours || 0 }}h
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value warning">{{ attendanceStats.work_days || 0 }}</div>
          <div class="stat-label">出勤天数</div>
          <div class="stat-sub">
            应出勤 {{ attendanceStats.standard_workdays || 0 }} 天
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value" :class="{ 'text-success': attendanceStats.remaining_hours <= 0, 'text-danger': attendanceStats.remaining_hours > 0 }">
            {{ attendanceStats.remaining_hours <= 0 ? '已达标' : (attendanceStats.remaining_hours || 0) + 'h' }}
          </div>
          <div class="stat-label">剩余应工时</div>
          <div class="stat-sub" v-if="attendanceStats.late_days > 0">
            迟到 {{ attendanceStats.late_days }} 次
          </div>
          <div class="stat-sub text-success" v-else>
            全勤无迟到
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 高管专属图表区域 -->
    <el-row :gutter="20" style="margin-top: 20px;" v-if="isManager">
      <el-col :xs="24" :md="12">
        <el-card>
          <template #header>
            <span>本月员工考勤汇总</span>
          </template>
          <el-table :data="managerOverview.employee_stats" size="small" v-loading="managerLoading" height="300">
            <el-table-column label="姓名" prop="real_name" width="100" />
            <el-table-column label="部门" prop="department" width="120" />
            <el-table-column label="打卡天数" prop="check_in_days" width="90" />
            <el-table-column label="迟到" prop="late_days" width="70">
              <template #default="{ row }">
                <span :class="{ 'text-danger': row.late_days > 0 }">{{ row.late_days }}</span>
              </template>
            </el-table-column>
            <el-table-column label="早退" prop="early_days" width="70" />
            <el-table-column label="工时" prop="total_work_hours" width="90" />
            <el-table-column label="请假" prop="leave_days" width="90" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card>
          <template #header>
            <span>工时使用分布</span>
          </template>
          <div ref="pieChartRef" style="height: 300px;"></div>
        </el-card>
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
              <div class="header-right">
                <el-date-picker
                  v-model="dateRange"
                  type="daterange"
                  range-separator="至"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  value-format="YYYY-MM-DD"
                  size="small"
                  style="width: 220px; margin-right: 10px;"
                  @change="fetchWorkTimeRecords"
                />
                <el-select v-model="selectedMonth" size="small" style="width: 120px;" @change="fetchData">
                  <el-option
                    v-for="m in monthOptions"
                    :key="m.value"
                    :label="m.label"
                    :value="m.value"
                  />
                </el-select>
              </div>
            </div>
          </template>
          <el-table :data="workTimeRecords" v-loading="loading" size="small">
            <el-table-column label="日期" width="100">
              <template #default="{ row }">
                {{ formatDate(row.work_date) }}
              </template>
            </el-table-column>
            <el-table-column label="提交人" width="100">
              <template #default="{ row }">
                {{ row.user?.real_name || '-' }}
              </template>
            </el-table-column>
            <el-table-column label="项目" min-width="130">
              <template #default="{ row }">
                {{ row.project?.name || '未关联项目' }}
              </template>
            </el-table-column>
            <el-table-column label="工时" width="70">
              <template #default="{ row }">
                <span style="color: #1890ff; font-weight: 500;">{{ row.hours }}h</span>
              </template>
            </el-table-column>
            <el-table-column label="工作内容" prop="description" min-width="180" show-overflow-tooltip />
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="editWorkTime(row)">编辑</el-button>
                <el-button link type="danger" size="small" @click="deleteWorkTime(row)">删除</el-button>
              </template>
            </el-table-column>
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

    <!-- 请假记录面板 -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>请假记录</span>
          <div class="header-right">
            <el-select v-model="leaveFilterType" placeholder="请假类型" clearable size="small" style="width: 120px; margin-right: 10px;" @change="fetchLeaveRecords">
              <el-option label="年假" value="annual" />
              <el-option label="病假" value="sick" />
              <el-option label="事假" value="personal" />
            </el-select>
            <el-select v-model="leaveFilterStatus" placeholder="审批状态" clearable size="small" style="width: 120px; margin-right: 10px;" @change="fetchLeaveRecords">
              <el-option label="待审批" value="pending" />
              <el-option label="已通过" value="approved" />
              <el-option label="已拒绝" value="rejected" />
            </el-select>
            <el-select v-model="selectedMonth" size="small" style="width: 120px;" @change="fetchLeaveRecords">
              <el-option
                v-for="m in monthOptions"
                :key="m.value"
                :label="m.label"
                :value="m.value"
              />
            </el-select>
          </div>
        </div>
      </template>
      <el-table :data="leaveRecords" v-loading="leaveLoading" size="small">
        <el-table-column label="请假类型" width="80">
          <template #default="{ row }">
            <el-tag :type="getLeaveTagType(row.leave_type)">{{ row.leave_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="提交人" width="100">
          <template #default="{ row }">
            {{ row.applicant?.real_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="开始日期" prop="start_date" width="110" />
        <el-table-column label="结束日期" prop="end_date" width="110" />
        <el-table-column label="天数" prop="days" width="70" />
        <el-table-column label="原因" prop="reason" min-width="160" show-overflow-tooltip />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 'pending'" link type="primary" size="small" @click="editLeave(row)">编辑</el-button>
            <el-button v-if="row.status === 'pending'" link type="danger" size="small" @click="deleteLeave(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination">
        <el-pagination
          v-model:current-page="leavePage"
          v-model:page-size="leavePageSize"
          :total="leaveTotal"
          layout="total, prev, pager, next"
          @current-change="fetchLeaveRecords"
        />
      </div>
    </el-card>

    <!-- 项目工时分布 -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <span>项目工时分布（{{ selectedMonth }}）</span>
      </template>
      <el-row :gutter="20">
        <el-col :xs="24" :md="12">
          <div id="worktime-chart" style="height: 300px;">
            <el-table :data="workTimeStats.by_project" size="small" border>
              <el-table-column label="项目名称" prop="project_name" min-width="150" />
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
    <el-dialog v-model="showWorkTimeDialog" :title="isEditWorkTime ? '编辑工时' : '填报工时'" width="500px">
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

    <!-- 请假申请对话框 -->
    <el-dialog v-model="showLeaveDialog" :title="isEditLeave ? '编辑请假申请' : '请假申请'" width="500px">
      <el-form :model="leaveForm" label-width="100px" :rules="leaveRules" ref="leaveFormRef">
        <el-form-item label="请假类型" prop="leave_type" required>
          <el-select v-model="leaveForm.leave_type" placeholder="选择请假类型" style="width: 100%">
            <el-option label="年假" value="annual" />
            <el-option label="病假" value="sick" />
            <el-option label="事假" value="personal" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始日期" prop="start_date" required>
          <el-date-picker v-model="leaveForm.start_date" type="date" placeholder="选择开始日期" style="width: 100%" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="结束日期" prop="end_date" required>
          <el-date-picker v-model="leaveForm.end_date" type="date" placeholder="选择结束日期" style="width: 100%" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="请假天数" prop="days" required>
          <el-input-number v-model="leaveForm.days" :min="0.5" :max="30" :step="0.5" style="width: 100%" />
        </el-form-item>
        <el-form-item label="请假原因" prop="reason">
          <el-input v-model="leaveForm.reason" type="textarea" :rows="3" placeholder="请输入请假原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showLeaveDialog = false">取消</el-button>
        <el-button type="primary" @click="saveLeave" :loading="leaveSaving">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import * as echarts from 'echarts'
import { useUserStore } from '@/stores/user'
import {
  getAttendanceStats, getLeaveBalances, getWorkTimeRecords,
  createWorkTimeRecord, updateWorkTimeRecord, deleteWorkTimeRecord,
  getWorkTimeStats, checkIn, checkOut,
  getLeaveRecords, createLeaveRecord, updateLeaveRecord, deleteLeaveRecord,
  getManagerOverview
} from '@/api/attendance'
import { getProjects } from '@/api/projects'

const userStore = useUserStore()
const isManager = computed(() => userStore.isAdmin)

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
const dateRange = ref([])

// 打卡状态
const checkingIn = ref(false)
const checkingOut = ref(false)

// 工时对话框
const showWorkTimeDialog = ref(false)
const saving = ref(false)
const isEditWorkTime = ref(false)
const editingWorkTimeId = ref(null)
const workTimeForm = ref({
  work_date: dayjs().format('YYYY-MM-DD'),
  project_id: null,
  hours: 8,
  description: ''
})

// 请假
const showLeaveDialog = ref(false)
const leaveSaving = ref(false)
const isEditLeave = ref(false)
const editingLeaveId = ref(null)
const leaveFormRef = ref(null)
const leaveForm = ref({
  leave_type: '',
  start_date: '',
  end_date: '',
  days: 1,
  reason: ''
})
const leaveRules = {
  leave_type: [{ required: true, message: '请选择请假类型', trigger: 'change' }],
  start_date: [{ required: true, message: '请选择开始日期', trigger: 'change' }],
  end_date: [{ required: true, message: '请选择结束日期', trigger: 'change' }],
  days: [{ required: true, message: '请输入请假天数', trigger: 'blur' }]
}

// 请假记录
const leaveRecords = ref([])
const leaveLoading = ref(false)
const leavePage = ref(1)
const leavePageSize = ref(10)
const leaveTotal = ref(0)
const leaveFilterType = ref('')
const leaveFilterStatus = ref('')

// 高管数据
const managerOverview = ref({ employee_stats: [], project_distribution: [] })
const managerLoading = ref(false)
const pieChartRef = ref(null)
let pieChart = null

const avgDailyHours = computed(() => {
  const total = workTimeStats.value.total_hours || 0
  return total > 0 ? (total / 22).toFixed(1) : '0.0'
})

const leaveTypeLabel = (type) => {
  const map = { annual: '年假', sick: '病假', personal: '事假', marriage: '婚假', maternity: '产假' }
  return map[type] || type
}

const getLeaveTagType = (type) => {
  const map = { annual: 'success', sick: 'danger', personal: 'warning' }
  return map[type] || ''
}

const getStatusTagType = (status) => {
  const map = { pending: 'warning', approved: 'success', rejected: 'danger' }
  return map[status] || ''
}

const getStatusLabel = (status) => {
  const map = { pending: '待审批', approved: '已通过', rejected: '已拒绝' }
  return map[status] || status
}

const formatDate = (dateStr) => {
  return dateStr ? dayjs(dateStr).format('MM-DD') : '-'
}

// 一键打卡
const handleCheckIn = async () => {
  checkingIn.value = true
  try {
    const res = await checkIn()
    ElMessage.success(res.message || '打卡成功')
    fetchAttendanceStats()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '打卡失败')
  } finally {
    checkingIn.value = false
  }
}

// 一键下班
const handleCheckOut = async () => {
  checkingOut.value = true
  try {
    const res = await checkOut()
    ElMessage.success(res.message || '下班打卡成功')
    fetchAttendanceStats()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '下班打卡失败')
  } finally {
    checkingOut.value = false
  }
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
    const params = {
      page: page.value,
      per_page: pageSize.value,
      month: selectedMonth.value
    }
    if (dateRange.value && dateRange.value.length === 2) {
      params.date_from = dateRange.value[0]
      params.date_to = dateRange.value[1]
    }
    const res = await getWorkTimeRecords(params)
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

// 工时编辑
const editWorkTime = (row) => {
  isEditWorkTime.value = true
  editingWorkTimeId.value = row.id
  workTimeForm.value = {
    work_date: row.work_date,
    project_id: row.project_id,
    hours: row.hours,
    description: row.description || ''
  }
  showWorkTimeDialog.value = true
}

// 工时删除
const deleteWorkTime = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除这条工时记录吗？', '确认删除', { type: 'warning' })
    await deleteWorkTimeRecord(row.id)
    ElMessage.success('删除成功')
    fetchWorkTimeRecords()
    fetchWorkTimeStats()
    fetchAttendanceStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '删除失败')
    }
  }
}

const saveWorkTime = async () => {
  if (!workTimeForm.value.work_date || !workTimeForm.value.hours) {
    ElMessage.warning('请填写日期和工时')
    return
  }
  saving.value = true
  try {
    if (isEditWorkTime.value && editingWorkTimeId.value) {
      await updateWorkTimeRecord(editingWorkTimeId.value, workTimeForm.value)
      ElMessage.success('工时记录已更新')
    } else {
      await createWorkTimeRecord(workTimeForm.value)
      ElMessage.success('工时记录已保存')
    }
    showWorkTimeDialog.value = false
    workTimeForm.value = { work_date: dayjs().format('YYYY-MM-DD'), project_id: null, hours: 8, description: '' }
    isEditWorkTime.value = false
    editingWorkTimeId.value = null
    fetchWorkTimeRecords()
    fetchWorkTimeStats()
    fetchAttendanceStats()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

// 请假记录
const fetchLeaveRecords = async () => {
  leaveLoading.value = true
  try {
    const params = {
      page: leavePage.value,
      per_page: leavePageSize.value,
      month: selectedMonth.value
    }
    if (leaveFilterType.value) params.leave_type = leaveFilterType.value
    if (leaveFilterStatus.value) params.status = leaveFilterStatus.value
    const res = await getLeaveRecords(params)
    leaveRecords.value = res.records || []
    leaveTotal.value = res.total || 0
  } catch (error) {
    console.error('获取请假记录失败', error)
  } finally {
    leaveLoading.value = false
  }
}

// 请假编辑
const editLeave = (row) => {
  isEditLeave.value = true
  editingLeaveId.value = row.id
  leaveForm.value = {
    leave_type: row.leave_type === '年假' ? 'annual' : row.leave_type === '病假' ? 'sick' : 'personal',
    start_date: row.start_date,
    end_date: row.end_date,
    days: parseFloat(row.days),
    reason: row.reason
  }
  showLeaveDialog.value = true
}

// 请假删除
const deleteLeave = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除这条请假申请吗？', '确认删除', { type: 'warning' })
    await deleteLeaveRecord(row.id)
    ElMessage.success('删除成功')
    fetchLeaveRecords()
    fetchLeaveBalances()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '删除失败')
    }
  }
}

const saveLeave = async () => {
  const valid = await leaveFormRef.value?.validate().catch(() => false)
  if (!valid) return

  leaveSaving.value = true
  try {
    if (isEditLeave.value && editingLeaveId.value) {
      await updateLeaveRecord(editingLeaveId.value, leaveForm.value)
      ElMessage.success('请假申请已更新')
    } else {
      await createLeaveRecord(leaveForm.value)
      ElMessage.success('请假申请已提交')
    }
    showLeaveDialog.value = false
    leaveForm.value = { leave_type: '', start_date: '', end_date: '', days: 1, reason: '' }
    isEditLeave.value = false
    editingLeaveId.value = null
    fetchLeaveRecords()
    fetchLeaveBalances()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '提交失败')
  } finally {
    leaveSaving.value = false
  }
}

// 高管数据
const fetchManagerOverview = async () => {
  if (!isManager.value) return
  managerLoading.value = true
  try {
    const res = await getManagerOverview({ month: selectedMonth.value })
    managerOverview.value = res
    nextTick(() => {
      initPieChart()
    })
  } catch (error) {
    console.error('获取高管概览失败', error)
  } finally {
    managerLoading.value = false
  }
}

const initPieChart = () => {
  if (!pieChartRef.value) return
  if (pieChart) {
    pieChart.dispose()
  }
  pieChart = echarts.init(pieChartRef.value)
  const data = managerOverview.value.project_distribution || []
  const option = {
    tooltip: { trigger: 'item', formatter: '{b}: {c}h ({d}%)' },
    legend: { orient: 'vertical', left: 'left', textStyle: { fontSize: 12 } },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        label: { show: false, position: 'center' },
        emphasis: {
          label: { show: true, fontSize: 16, fontWeight: 'bold' }
        },
        labelLine: { show: false },
        data: data.map(item => ({ name: item.project_name, value: item.hours }))
      }
    ]
  }
  pieChart.setOption(option)
}

const fetchData = () => {
  fetchAttendanceStats()
  fetchWorkTimeRecords()
  fetchWorkTimeStats()
  fetchLeaveRecords()
  if (isManager.value) {
    fetchManagerOverview()
  }
}

onMounted(() => {
  fetchAttendanceStats()
  fetchLeaveBalances()
  fetchWorkTimeRecords()
  fetchWorkTimeStats()
  fetchProjects()
  fetchLeaveRecords()
  if (isManager.value) {
    fetchManagerOverview()
  }
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
    .header-actions {
      display: flex;
      gap: 8px;
    }
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
        margin-bottom: 4px;
      }
      .stat-sub {
        font-size: 12px;
        color: #999;
        margin-top: 4px;
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
    .header-right {
      display: flex;
      align-items: center;
    }
  }

  .pagination {
    margin-top: 16px;
    display: flex;
    justify-content: flex-end;
  }

  .text-success { color: #67c23a; }
  .text-warning { color: #e6a23c; }
  .text-danger { color: #f56c6c; }
}
</style>
