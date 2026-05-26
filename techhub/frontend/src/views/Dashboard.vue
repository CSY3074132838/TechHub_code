<!-- 第三次迭代陈思言负责 -->
<template>
  <div class="dashboard-page">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card" @click="$router.push('/tasks')" style="cursor: pointer;">
          <div class="stat-header">
            <div class="stat-icon" style="background: #e6f7ff; color: #1890ff;">
              <el-icon size="24"><Document /></el-icon>
            </div>
            <div>
              <div class="stat-title">{{ $t('dashboard.todoTasks') }}</div>
              <div class="stat-value">{{ overview.my_pending_tasks || 0 }}</div>
            </div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card" @click="$router.push('/projects')" style="cursor: pointer;">
          <div class="stat-header">
            <div class="stat-icon" style="background: #f6ffed; color: #52c41a;">
              <el-icon size="24"><Folder /></el-icon>
            </div>
            <div>
              <div class="stat-title">{{ $t('dashboard.myProjects') }}</div>
              <div class="stat-value">{{ overview.my_projects || 0 }}</div>
            </div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card" @click="$router.push('/approvals')" style="cursor: pointer;">
          <div class="stat-header">
            <div class="stat-icon" style="background: #fff7e6; color: #faad14;">
              <el-icon size="24"><Timer /></el-icon>
            </div>
            <div>
              <div class="stat-title">{{ $t('dashboard.pendingApprovals') }}</div>
              <div class="stat-value">{{ overview.my_pending_approvals || 0 }}</div>
            </div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card" @click="$router.push('/tasks')" style="cursor: pointer;">
          <div class="stat-header">
            <div class="stat-icon" style="background: #f9f0ff; color: #722ed1;">
              <el-icon size="24"><CircleCheck /></el-icon>
            </div>
            <div>
              <div class="stat-title">{{ $t('dashboard.todayCompleted') }}</div>
              <div class="stat-value">{{ overview.today_completed || 0 }}</div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 【第二次迭代】行政财务概览卡片 -->
    <el-row :gutter="20" class="stat-row" style="margin-top: 20px;">
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card" @click="$router.push('/attendance')" style="cursor: pointer;">
          <div class="stat-header">
            <div class="stat-icon" style="background: #e6fffb; color: #13c2c2;">
              <el-icon size="24"><Clock /></el-icon>
            </div>
            <div>
              <div class="stat-title">{{ $t('dashboard.monthlyWorkHours') }}</div>
              <div class="stat-value">{{ attendanceStats.total_hours || 0 }}h</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card" @click="$router.push('/attendance')" style="cursor: pointer;">
          <div class="stat-header">
            <div class="stat-icon" style="background: #fff2f0; color: #ff4d4f;">
              <el-icon size="24"><AlarmClock /></el-icon>
            </div>
            <div>
              <div class="stat-title">{{ $t('dashboard.overtimeHours') }}</div>
              <div class="stat-value">{{ attendanceStats.total_overtime || 0 }}h</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card" @click="$router.push('/attendance')" style="cursor: pointer;">
          <div class="stat-header">
            <div class="stat-icon" style="background: #f0f5ff; color: #2f54eb;">
              <el-icon size="24"><Calendar /></el-icon>
            </div>
            <div>
              <div class="stat-title">{{ $t('dashboard.annualLeave') }}</div>
              <div class="stat-value">{{ annualLeaveBalance }}{{ $t('common.unitDay') }}</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6" v-if="userStore.isAdmin">
        <div class="stat-card" @click="$router.push('/expenses')" style="cursor: pointer;">
          <div class="stat-header">
            <div class="stat-icon" style="background: #fff7e6; color: #fa8c16;">
              <el-icon size="24"><Money /></el-icon>
            </div>
            <div>
              <div class="stat-title">{{ $t('dashboard.pendingExpenses') }}</div>
              <div class="stat-value">{{ pendingExpenseCount }}{{ $t('common.unitPiece') }}</div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 快捷操作和团队动态 -->
    <el-row :gutter="20" class="content-row">
      <el-col :xs="24" :lg="16">
        <el-card class="activity-card">
          <template #header>
            <div class="card-header">
              <span>{{ $t('common.teamActivity') }}</span>
              <el-button text @click="$router.push('/projects')">{{ $t('common.more') }}</el-button>
            </div>
          </template>
          
          <el-timeline>
            <el-timeline-item
              v-for="activity in activities"
              :key="activity.id"
              :type="getActivityType(activity.activity_type)"
              :timestamp="formatTime(activity.created_at)"
            >
              <div class="activity-item">
                <el-avatar :size="28" :src="activity.user?.avatar">
                  {{ activity.user?.real_name?.charAt(0) || 'U' }}
                </el-avatar>
                <div class="activity-content">
                  <span class="activity-user">{{ activity.user?.real_name }}</span>
                  <span class="activity-action">{{ activity.title }}</span>
                </div>
              </div>
            </el-timeline-item>
          </el-timeline>
          
          <el-empty v-if="activities.length === 0" :description="$t('common.noActivity')" />
        </el-card>
      </el-col>
      
      <el-col :xs="24" :lg="8">
        <el-card class="quick-actions">
          <template #header>
            <span>{{ $t('common.quickActions') }}</span>
          </template>
          
          <div class="action-list">
            <el-button type="primary" plain class="action-btn" @click="showCreateTask = true">
              <el-icon><Plus /></el-icon>
              {{ $t('dashboard.newTask') }}
            </el-button>
            <el-button type="success" plain class="action-btn" @click="showCreateProject = true">
              <el-icon><FolderAdd /></el-icon>
              {{ $t('dashboard.newProject') }}
            </el-button>
            <el-button type="warning" plain class="action-btn" @click="$router.push('/approvals')">
              <el-icon><DocumentChecked /></el-icon>
              {{ $t('dashboard.newApproval') }}
            </el-button>
          </div>
        </el-card>
        
        <el-card class="my-tasks" style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <span>{{ $t('common.myTodo') }}</span>
              <el-button text @click="$router.push('/tasks')">{{ $t('common.viewAll') }}</el-button>
            </div>
          </template>
          
          <div v-if="myTasks.length > 0" class="task-list">
            <div
              v-for="task in myTasks.slice(0, 5)"
              :key="task.id"
              class="task-item"
              @click="$router.push(`/projects/${task.project_id}`)"
            >
              <div class="task-title">{{ task.title }}</div>
              <div class="task-meta">
                <el-tag :type="getPriorityType(task.priority)" size="small">
                  {{ getPriorityLabel(task.priority) }}
                </el-tag>
                <span class="task-date">{{ formatDate(task.due_date) }}</span>
              </div>
            </div>
          </div>
          <el-empty v-else :description="$t('common.noTodo')" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 新建任务对话框 -->
    <el-dialog v-model="showCreateTask" :title="$t('dashboard.taskDialogTitle')" width="600px">
      <el-form :model="taskForm" label-width="80px">
        <el-form-item :label="$t('dashboard.taskTitle')">
          <el-input v-model="taskForm.title" :placeholder="$t('dashboard.taskTitlePlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('dashboard.project')">
          <el-select v-model="taskForm.project_id" :placeholder="$t('dashboard.selectProject')" style="width: 100%;">
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('common.priority')">
          <el-select v-model="taskForm.priority" style="width: 100%;">
            <el-option :label="$t('dashboard.urgent')" value="urgent" />
            <el-option :label="$t('dashboard.high')" value="high" />
            <el-option :label="$t('dashboard.medium')" value="medium" />
            <el-option :label="$t('dashboard.low')" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('dashboard.deadline')">
          <el-date-picker
            v-model="taskForm.due_date"
            type="datetime"
            :placeholder="$t('dashboard.selectDeadline')"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item :label="$t('dashboard.taskDesc')">
          <el-input
            v-model="taskForm.description"
            type="textarea"
            rows="3"
            :placeholder="$t('dashboard.taskDescPlaceholder')"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateTask = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="createTask" :loading="creating">{{ $t('common.create') }}</el-button>
      </template>
    </el-dialog>

    <!-- 新建项目对话框 -->
    <el-dialog v-model="showCreateProject" :title="$t('dashboard.projectDialogTitle')" width="600px">
      <el-form :model="projectForm" label-width="80px">
        <el-form-item :label="$t('dashboard.projectName')">
          <el-input v-model="projectForm.name" :placeholder="$t('dashboard.projectNamePlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('dashboard.projectDesc')">
          <el-input
            v-model="projectForm.description"
            type="textarea"
            rows="3"
            :placeholder="$t('dashboard.projectDescPlaceholder')"
          />
        </el-form-item>
        <el-form-item :label="$t('dashboard.startDate')">
          <el-date-picker
            v-model="projectForm.start_date"
            type="date"
            :placeholder="$t('dashboard.selectStartDate')"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item :label="$t('dashboard.endDate')">
          <el-date-picker
            v-model="projectForm.end_date"
            type="date"
            :placeholder="$t('dashboard.selectEndDate')"
            style="width: 100%;"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateProject = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="createProject" :loading="creatingProject">{{ $t('common.create') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { getOverview, getActivities, getTodos } from '@/api/dashboard'
import { createTask as apiCreateTask } from '@/api/tasks'
import { getProjects, createProject as apiCreateProject } from '@/api/projects'
// 【第二次迭代】财务行政工作台增强
import { getAttendanceStats, getLeaveBalances } from '@/api/attendance'
import { getExpenseStats } from '@/api/expenses'
import { useUserStore } from '@/stores/user'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const router = useRouter()
const userStore = useUserStore()

const overview = ref({})
const activities = ref([])
const myTasks = ref([])
const projects = ref([])
// 【第二次迭代】财务行政数据
const attendanceStats = ref({})
const leaveBalances = ref([])
const expenseStats = ref({})

const showCreateTask = ref(false)
const showCreateProject = ref(false)
const creating = ref(false)
const creatingProject = ref(false)

// 【第二次迭代】计算属性
const annualLeaveBalance = computed(() => {
  const annual = leaveBalances.value.find(b => b.leave_type === 'annual')
  return annual ? annual.remaining_days : 0
})

const pendingExpenseCount = computed(() => {
  const pending = expenseStats.value.by_status?.find(s => s.status === 'pending')
  return pending ? pending.count : 0
})

const taskForm = ref({
  title: '',
  project_id: '',
  priority: 'medium',
  due_date: '',
  description: ''
})

const projectForm = ref({
  name: '',
  description: '',
  start_date: '',
  end_date: ''
})

const fetchData = async () => {
  try {
    const [overviewRes, activitiesRes, todosRes, projectsRes] = await Promise.all([
      getOverview(),
      getActivities({ limit: 10 }),
      getTodos(),
      getProjects()
    ])
    
    overview.value = overviewRes
    activities.value = activitiesRes.activities || []
    myTasks.value = todosRes.tasks || []
    projects.value = projectsRes.projects || []
    
    // 【第二次迭代】获取财务行政数据
    try {
      const [attRes, leaveRes, expRes] = await Promise.all([
        getAttendanceStats({ month: dayjs().format('YYYY-MM') }),
        getLeaveBalances({ year: dayjs().year() }),
        getExpenseStats({ month: dayjs().format('YYYY-MM') })
      ])
      attendanceStats.value = attRes
      leaveBalances.value = leaveRes.balances || []
      expenseStats.value = expRes
    } catch (e) {
      console.error(t('dashboard.createFailed'), e)
    }
  } catch (error) {
    console.error(t('dashboard.createFailed'), error)
  }
}

const createTask = async () => {
  if (!taskForm.value.title || !taskForm.value.project_id) {
    ElMessage.warning(t('dashboard.pleaseFillInfo'))
    return
  }
  
  creating.value = true
  try {
    await apiCreateTask(taskForm.value)
    ElMessage.success(t('dashboard.createTaskSuccess'))
    showCreateTask.value = false
    fetchData()
    taskForm.value = { title: '', project_id: '', priority: 'medium', due_date: '', description: '' }
  } catch (error) {
    console.error(t('dashboard.createFailed'), error)
  } finally {
    creating.value = false
  }
}

const createProject = async () => {
  if (!projectForm.value.name) {
    ElMessage.warning(t('dashboard.pleaseFillInfo'))
    return
  }
  
  creatingProject.value = true
  try {
    await apiCreateProject(projectForm.value)
    ElMessage.success(t('dashboard.createProjectSuccess'))
    showCreateProject.value = false
    fetchData()
    projectForm.value = { name: '', description: '', start_date: '', end_date: '' }
  } catch (error) {
    console.error(t('dashboard.createFailed'), error)
  } finally {
    creatingProject.value = false
  }
}

const formatTime = (time) => {
  return dayjs(time).format('MM-DD HH:mm')
}

const formatDate = (date) => {
  if (!date) return t('dashboard.noDeadline')
  return dayjs(date).format('MM-DD')
}

const getActivityType = (type) => {
  const typeMap = {
    'task_created': 'primary',
    'task_completed': 'success',
    'project_created': 'warning',
    'comment_added': 'info'
  }
  return typeMap[type] || 'info'
}

const getPriorityType = (priority) => {
  const typeMap = {
    'urgent': 'danger',
    'high': 'warning',
    'medium': '',
    'low': 'info'
  }
  return typeMap[priority] || ''
}

const getPriorityLabel = (priority) => {
  const labelMap = {
    'urgent': t('dashboard.urgent'),
    'high': t('dashboard.high'),
    'medium': t('dashboard.medium'),
    'low': t('dashboard.low')
  }
  return labelMap[priority] || priority
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped lang="scss">
.dashboard-page {
  .stat-row {
    margin-bottom: 20px;
  }
  
  .content-row {
    .activity-card {
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      
      .activity-item {
        display: flex;
        align-items: center;
        gap: 12px;
        
        .activity-content {
          .activity-user {
            font-weight: 500;
            margin-right: 8px;
          }
          
          .activity-action {
            color: #666;
          }
        }
      }
    }
    
    .quick-actions {
      .action-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
        
        .action-btn {
          justify-content: flex-start;
          
          .el-icon {
            margin-right: 8px;
          }
        }
      }
    }
    
    .my-tasks {
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      
      .task-list {
        .task-item {
          padding: 12px 0;
          border-bottom: 1px solid #eee;
          cursor: pointer;
          
          &:last-child {
            border-bottom: none;
          }
          
          &:hover {
            background-color: #f5f7fa;
          }
          
          .task-title {
            font-size: 14px;
            margin-bottom: 8px;
          }
          
          .task-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            
            .task-date {
              font-size: 12px;
              color: #999;
            }
          }
        }
      }
    }
  }
}
</style>
