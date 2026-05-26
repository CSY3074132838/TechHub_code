<template>
  <!-- 第三次迭代陈思言负责 -->
  <!-- 【第二次迭代】考勤与工时管理页面 -->
  <div class="attendance-page">
    <div class="page-header">
      <h2>{{ t('attendance.pageTitle') }}</h2>
      <div class="header-actions">
        <el-button type="success" @click="handleCheckIn" :loading="checkingIn">
          <el-icon><CircleCheck /></el-icon>{{ t('attendance.checkIn') }}
        </el-button>
        <el-button type="warning" @click="handleCheckOut" :loading="checkingOut">
          <el-icon><CircleClose /></el-icon>{{ t('attendance.checkOut') }}
        </el-button>
        <el-button type="primary" @click="showLeaveDialog = true">
          <el-icon><Document /></el-icon>{{ t('attendance.leaveApply') }}
        </el-button>
        <el-button type="primary" @click="showWorkTimeDialog = true">
          <el-icon><Plus /></el-icon>{{ t('attendance.workTimeReport') }}
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <!-- 普通员工：本月工时 -->
      <el-col :xs="12" :sm="6" v-if="!isManager">
        <div class="stat-card">
          <div class="stat-value">{{ attendanceStats.total_hours || 0 }}h</div>
          <div class="stat-label">{{ t('attendance.monthlyWorkHours') }}</div>
          <div class="stat-sub" :class="{ 'text-success': attendanceStats.completion_rate >= 100, 'text-warning': attendanceStats.completion_rate < 100 && attendanceStats.completion_rate >= 80, 'text-danger': attendanceStats.completion_rate < 80 }">
            {{ t('attendance.achievementRate') }} {{ attendanceStats.completion_rate || 0 }}%
          </div>
        </div>
      </el-col>
      <!-- 高管：所有员工本月工时 -->
      <el-col :xs="12" :sm="6" v-if="isManager">
        <div class="stat-card">
          <div class="stat-value">{{ managerOverview.total_all_hours || 0 }}h</div>
          <div class="stat-label">{{ t('attendance.allEmployeesWorkHours') }}</div>
          <div class="stat-sub">
            {{ t('attendance.totalPeople') }} {{ managerOverview.employee_stats?.length || 0 }} {{ t('common.unitPeople') }}
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value success">{{ attendanceStats.total_overtime || 0 }}h</div>
          <div class="stat-label">{{ t('attendance.monthlyOvertime') }}</div>
          <div class="stat-sub">
            {{ t('attendance.dailyAverage') }} {{ attendanceStats.avg_daily_hours || 0 }}h
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value warning">{{ attendanceStats.work_days || 0 }}</div>
          <div class="stat-label">{{ t('attendance.attendanceDays') }}</div>
          <div class="stat-sub">
            {{ t('attendance.shouldAttendance') }} {{ attendanceStats.standard_workdays || 0 }} {{ t('common.unitDay') }}
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value" :class="{ 'text-success': attendanceStats.remaining_hours <= 0, 'text-danger': attendanceStats.remaining_hours > 0 }">
            {{ attendanceStats.remaining_hours <= 0 ? t('attendance.achieved') : (attendanceStats.remaining_hours || 0) + 'h' }}
          </div>
          <div class="stat-label">{{ t('attendance.remainingWorkHours') }}</div>
          <div class="stat-sub" v-if="attendanceStats.late_days > 0">
            {{ t('attendance.late') }} {{ attendanceStats.late_days }} {{ t('attendance.times') }}
          </div>
          <div class="stat-sub text-success" v-else>
            {{ t('attendance.noLate') }}
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 高管专属图表区域 -->
    <el-row :gutter="20" style="margin-top: 20px;" v-if="isManager">
      <el-col :xs="24" :md="12">
        <el-card>
          <template #header>
            <span>{{ t('attendance.monthlyAttendanceSummary') }}</span>
          </template>
          <el-table :data="managerOverview.employee_stats" size="small" v-loading="managerLoading" height="300">
            <el-table-column :label="t('attendance.name')" prop="real_name" width="100" />
            <el-table-column :label="t('attendance.department')" prop="department" width="120" />
            <el-table-column :label="t('attendance.checkInDays')" prop="check_in_days" width="90" />
            <el-table-column :label="t('attendance.late')" prop="late_days" width="70">
              <template #default="{ row }">
                <span :class="{ 'text-danger': row.late_days > 0 }">{{ row.late_days }}</span>
              </template>
            </el-table-column>
            <el-table-column :label="t('attendance.earlyLeave')" prop="early_days" width="70" />
            <el-table-column :label="t('attendance.workHours')" prop="total_work_hours" width="90" />
            <el-table-column :label="t('attendance.leave')" prop="leave_days" width="90" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card>
          <template #header>
            <span>{{ t('attendance.workTimeDistribution') }}</span>
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
            <span>{{ t('attendance.leaveBalance') }}（{{ currentYear }}{{ t('attendance.year') }}）</span>
          </template>
          <div v-for="item in leaveBalances" :key="item.leave_type" class="balance-item">
            <div class="balance-info">
              <span class="balance-label">{{ leaveTypeLabel(item.leave_type) }}</span>
              <span class="balance-value">{{ item.remaining_days }} / {{ item.total_days }} {{ t('common.unitDay') }}</span>
            </div>
            <el-progress
              :percentage="Math.round((item.used_days / item.total_days) * 100)"
              :status="item.remaining_days === 0 ? 'exception' : ''"
            />
          </div>
          <el-empty v-if="leaveBalances.length === 0" :description="t('attendance.noLeaveData')" />
        </el-card>
      </el-col>

      <!-- 工时记录 -->
      <el-col :xs="24" :md="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>{{ t('attendance.workTimeRecords') }}</span>
              <div class="header-right">
                <el-date-picker
                  v-model="dateRange"
                  type="daterange"
                  :range-separator="t('attendance.to')"
                  :start-placeholder="t('attendance.startDate')"
                  :end-placeholder="t('attendance.endDate')"
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
            <el-table-column :label="t('common.date')" width="100">
              <template #default="{ row }">
                {{ formatDate(row.work_date) }}
              </template>
            </el-table-column>
            <el-table-column :label="t('attendance.submitter')" width="100">
              <template #default="{ row }">
                {{ row.user?.real_name || '-' }}
              </template>
            </el-table-column>
            <el-table-column :label="t('attendance.project')" min-width="130">
              <template #default="{ row }">
                {{ row.project?.name || t('attendance.noRelatedProject') }}
              </template>
            </el-table-column>
            <el-table-column :label="t('attendance.workHours')" width="70">
              <template #default="{ row }">
                <span style="color: #1890ff; font-weight: 500;">{{ row.hours }}h</span>
              </template>
            </el-table-column>
            <el-table-column :label="t('attendance.workContent')" prop="description" min-width="180" show-overflow-tooltip />
            <el-table-column :label="t('common.operation')" width="120" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="editWorkTime(row)">{{ t('common.edit') }}</el-button>
                <el-button link type="danger" size="small" @click="deleteWorkTime(row)">{{ t('common.delete') }}</el-button>
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
          <span>{{ t('attendance.leaveRecords') }}</span>
          <div class="header-right">
            <el-select v-model="leaveFilterType" :placeholder="t('attendance.leaveType')" clearable size="small" style="width: 120px; margin-right: 10px;" @change="fetchLeaveRecords">
              <el-option :label="t('attendance.annualLeave')" value="annual" />
              <el-option :label="t('attendance.sickLeave')" value="sick" />
              <el-option :label="t('attendance.personalLeave')" value="personal" />
            </el-select>
            <el-select v-model="leaveFilterStatus" :placeholder="t('attendance.approvalStatus')" clearable size="small" style="width: 120px; margin-right: 10px;" @change="fetchLeaveRecords">
              <el-option :label="t('attendance.pendingApproval')" value="pending" />
              <el-option :label="t('attendance.approved')" value="approved" />
              <el-option :label="t('attendance.rejected')" value="rejected" />
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
        <el-table-column :label="t('attendance.leaveType')" width="80">
          <template #default="{ row }">
            <el-tag :type="getLeaveTagType(row.leave_type)">{{ leaveTypeLabel(row.leave_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('attendance.submitter')" width="100">
          <template #default="{ row }">
            {{ row.applicant?.real_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column :label="t('attendance.startDateLabel')" prop="start_date" width="110" />
        <el-table-column :label="t('attendance.endDateLabel')" prop="end_date" width="110" />
        <el-table-column :label="t('attendance.days')" prop="days" width="70" />
        <el-table-column :label="t('attendance.reason')" prop="reason" min-width="160" show-overflow-tooltip />
        <el-table-column :label="t('attendance.approvalStatus')" width="90">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('common.operation')" width="120" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 'pending'" link type="primary" size="small" @click="editLeave(row)">{{ t('common.edit') }}</el-button>
            <el-button v-if="row.status === 'pending'" link type="danger" size="small" @click="deleteLeave(row)">{{ t('common.delete') }}</el-button>
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
        <span>{{ t('attendance.projectWorkTimeDistribution') }}（{{ selectedMonth }}）</span>
      </template>
      <el-row :gutter="20">
        <el-col :xs="24" :md="12">
          <div id="worktime-chart" style="height: 300px;">
            <el-table :data="workTimeStats.by_project" size="small" border>
              <el-table-column :label="t('attendance.projectName')" prop="project_name" min-width="150" />
              <el-table-column :label="t('attendance.workHours')" prop="hours" width="100" />
              <el-table-column :label="t('attendance.recordCount')" prop="record_count" width="100" />
            </el-table>
          </div>
        </el-col>
        <el-col :xs="24" :md="12">
          <el-descriptions :title="t('attendance.summary')" :column="1" border>
            <el-descriptions-item :label="t('attendance.totalWorkHours')">{{ workTimeStats.total_hours || 0 }} {{ t('common.unitHour') }}</el-descriptions-item>
            <el-descriptions-item :label="t('attendance.projectCount')">{{ workTimeStats.by_project?.length || 0 }} {{ t('common.unitItem') }}</el-descriptions-item>
            <el-descriptions-item :label="t('attendance.averageDaily')">{{ avgDailyHours }} {{ t('common.unitHour') }}</el-descriptions-item>
          </el-descriptions>
        </el-col>
      </el-row>
    </el-card>

    <!-- 填报工时对话框 -->
    <el-dialog v-model="showWorkTimeDialog" :title="isEditWorkTime ? t('attendance.editWorkTime') : t('attendance.reportWorkTime')" width="500px">
      <el-form :model="workTimeForm" label-width="100px">
        <el-form-item :label="t('attendance.workDate')" required>
          <el-date-picker v-model="workTimeForm.work_date" type="date" :placeholder="t('attendance.selectDate')" style="width: 100%" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item :label="t('attendance.relatedProject')">
          <el-select v-model="workTimeForm.project_id" :placeholder="t('attendance.selectProject')" clearable style="width: 100%">
            <el-option v-for="p in projectOptions" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('attendance.workHoursLabel')" required>
          <el-input-number v-model="workTimeForm.hours" :min="0.5" :max="24" :step="0.5" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="t('attendance.workContent')">
          <el-input v-model="workTimeForm.description" type="textarea" :rows="3" :placeholder="t('attendance.workContentPlaceholder')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showWorkTimeDialog = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="saveWorkTime" :loading="saving">{{ t('common.save') }}</el-button>
      </template>
    </el-dialog>

    <!-- 请假申请对话框 -->
    <el-dialog v-model="showLeaveDialog" :title="isEditLeave ? t('attendance.editLeave') : t('attendance.leaveApplication')" width="500px">
      <el-form :model="leaveForm" label-width="100px" :rules="leaveRules" ref="leaveFormRef">
        <el-form-item :label="t('attendance.leaveType')" prop="leave_type" required>
          <el-select v-model="leaveForm.leave_type" :placeholder="t('attendance.selectLeaveType')" style="width: 100%">
            <el-option :label="t('attendance.annualLeave')" value="annual" />
            <el-option :label="t('attendance.sickLeave')" value="sick" />
            <el-option :label="t('attendance.personalLeave')" value="personal" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('attendance.startDateLabel')" prop="start_date" required>
          <el-date-picker v-model="leaveForm.start_date" type="date" :placeholder="t('attendance.selectStartDate')" style="width: 100%" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item :label="t('attendance.endDateLabel')" prop="end_date" required>
          <el-date-picker v-model="leaveForm.end_date" type="date" :placeholder="t('attendance.selectEndDate')" style="width: 100%" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item :label="t('attendance.leaveDays')" prop="days" required>
          <el-input-number v-model="leaveForm.days" :min="0.5" :max="30" :step="0.5" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="t('attendance.leaveReason')" prop="reason">
          <el-input v-model="leaveForm.reason" type="textarea" :rows="3" :placeholder="t('attendance.leaveReasonPlaceholder')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showLeaveDialog = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="saveLeave" :loading="leaveSaving">{{ t('common.submit') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
// 第三次迭代陈思言负责
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
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

const { t } = useI18n()
const userStore = useUserStore()
const isManager = computed(() => userStore.isAdmin)

// 月份选项（近12个月）
// 第三次迭代陈思言负责
const generateMonthOptions = () => {
  const options = []
  for (let i = 0; i < 12; i++) {
    const d = dayjs().subtract(i, 'month')
    options.push({
      value: d.format('YYYY-MM'),
      label: d.format(t('attendance.monthOptionFormat'))
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
  leave_type: [{ required: true, message: t('attendance.pleaseSelectLeaveType'), trigger: 'change' }],
  start_date: [{ required: true, message: t('attendance.pleaseSelectStartDate'), trigger: 'change' }],
  end_date: [{ required: true, message: t('attendance.pleaseSelectEndDate'), trigger: 'change' }],
  days: [{ required: true, message: t('attendance.pleaseEnterLeaveDays'), trigger: 'blur' }]
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
  const map = { annual: t('attendance.annualLeave'), sick: t('attendance.sickLeave'), personal: t('attendance.personalLeave'), marriage: t('attendance.marriageLeave'), maternity: t('attendance.maternityLeave') }
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
  const map = { pending: t('attendance.pendingApproval'), approved: t('attendance.approved'), rejected: t('attendance.rejected') }
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
    ElMessage.success(res.message || t('attendance.checkInSuccess'))
    fetchAttendanceStats()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || t('attendance.checkInFailed'))
  } finally {
    checkingIn.value = false
  }
}

// 一键下班
const handleCheckOut = async () => {
  checkingOut.value = true
  try {
    const res = await checkOut()
    ElMessage.success(res.message || t('attendance.checkOutSuccess'))
    fetchAttendanceStats()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || t('attendance.checkOutFailed'))
  } finally {
    checkingOut.value = false
  }
}

const fetchAttendanceStats = async () => {
  try {
    const res = await getAttendanceStats({ month: selectedMonth.value })
    attendanceStats.value = res
  } catch (error) {
    console.error(t('attendance.fetchStatsFailed'), error)
  }
}

const fetchLeaveBalances = async () => {
  try {
    const res = await getLeaveBalances({ year: currentYear.value })
    leaveBalances.value = res.balances || []
  } catch (error) {
    console.error(t('attendance.fetchLeaveBalancesFailed'), error)
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
    console.error(t('attendance.fetchWorkTimeRecordsFailed'), error)
  } finally {
    loading.value = false
  }
}

const fetchWorkTimeStats = async () => {
  try {
    const res = await getWorkTimeStats({ month: selectedMonth.value })
    workTimeStats.value = res
  } catch (error) {
    console.error(t('attendance.fetchWorkTimeStatsFailed'), error)
  }
}

const fetchProjects = async () => {
  try {
    const res = await getProjects()
    projectOptions.value = res.projects || []
  } catch (error) {
    console.error(t('attendance.fetchProjectsFailed'), error)
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
    await ElMessageBox.confirm(t('attendance.deleteWorkTimeConfirm'), t('attendance.confirmDelete'), { type: 'warning' })
    await deleteWorkTimeRecord(row.id)
    ElMessage.success(t('common.delete') + t('common.success'))
    fetchWorkTimeRecords()
    fetchWorkTimeStats()
    fetchAttendanceStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || t('common.delete') + t('common.failed'))
    }
  }
}

const saveWorkTime = async () => {
  if (!workTimeForm.value.work_date || !workTimeForm.value.hours) {
    ElMessage.warning(t('attendance.pleaseFillDateHours'))
    return
  }
  saving.value = true
  try {
    if (isEditWorkTime.value && editingWorkTimeId.value) {
      await updateWorkTimeRecord(editingWorkTimeId.value, workTimeForm.value)
      ElMessage.success(t('attendance.workTimeUpdated'))
    } else {
      await createWorkTimeRecord(workTimeForm.value)
      ElMessage.success(t('attendance.workTimeSaved'))
    }
    showWorkTimeDialog.value = false
    workTimeForm.value = { work_date: dayjs().format('YYYY-MM-DD'), project_id: null, hours: 8, description: '' }
    isEditWorkTime.value = false
    editingWorkTimeId.value = null
    fetchWorkTimeRecords()
    fetchWorkTimeStats()
    fetchAttendanceStats()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || t('common.save') + t('common.failed'))
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
    console.error(t('attendance.fetchLeaveRecordsFailed'), error)
  } finally {
    leaveLoading.value = false
  }
}

// 请假编辑
const editLeave = (row) => {
  isEditLeave.value = true
  editingLeaveId.value = row.id
  leaveForm.value = {
    leave_type: row.leave_type === t('attendance.annualLeave') ? 'annual' : row.leave_type === t('attendance.sickLeave') ? 'sick' : 'personal',
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
    await ElMessageBox.confirm(t('attendance.deleteLeaveConfirm'), t('attendance.confirmDelete'), { type: 'warning' })
    await deleteLeaveRecord(row.id)
    ElMessage.success(t('common.delete') + t('common.success'))
    fetchLeaveRecords()
    fetchLeaveBalances()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || t('common.delete') + t('common.failed'))
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
      ElMessage.success(t('attendance.leaveUpdated'))
    } else {
      await createLeaveRecord(leaveForm.value)
      ElMessage.success(t('attendance.leaveSubmitted'))
    }
    showLeaveDialog.value = false
    leaveForm.value = { leave_type: '', start_date: '', end_date: '', days: 1, reason: '' }
    isEditLeave.value = false
    editingLeaveId.value = null
    fetchLeaveRecords()
    fetchLeaveBalances()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || t('common.submit') + t('common.failed'))
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
    console.error(t('attendance.fetchManagerOverviewFailed'), error)
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
