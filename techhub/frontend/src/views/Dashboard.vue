<template>
  <div class="dashboard-page">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card">
          <div class="stat-header">
            <div class="stat-icon" style="background: #e6f7ff; color: #1890ff;">
              <el-icon size="24"><Document /></el-icon>
            </div>
            <div>
              <div class="stat-title">待办任务</div>
              <div class="stat-value">{{ overview.my_pending_tasks || 0 }}</div>
            </div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card">
          <div class="stat-header">
            <div class="stat-icon" style="background: #f6ffed; color: #52c41a;">
              <el-icon size="24"><Folder /></el-icon>
            </div>
            <div>
              <div class="stat-title">我的项目</div>
              <div class="stat-value">{{ overview.my_projects || 0 }}</div>
            </div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card">
          <div class="stat-header">
            <div class="stat-icon" style="background: #fff7e6; color: #faad14;">
              <el-icon size="24"><Timer /></el-icon>
            </div>
            <div>
              <div class="stat-title">待处理审批</div>
              <div class="stat-value">{{ overview.my_pending_approvals || 0 }}</div>
            </div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card">
          <div class="stat-header">
            <div class="stat-icon" style="background: #f9f0ff; color: #722ed1;">
              <el-icon size="24"><CircleCheck /></el-icon>
            </div>
            <div>
              <div class="stat-title">今日完成</div>
              <div class="stat-value">{{ overview.today_completed || 0 }}</div>
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
              <span>团队动态</span>
              <el-button text @click="$router.push('/projects')">查看更多</el-button>
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
          
          <el-empty v-if="activities.length === 0" description="暂无动态" />
        </el-card>
      </el-col>
      
      <el-col :xs="24" :lg="8">
        <el-card class="quick-actions">
          <template #header>
            <span>快捷操作</span>
          </template>
          
          <div class="action-list">
            <el-button type="primary" plain class="action-btn" @click="showCreateTask = true">
              <el-icon><Plus /></el-icon>
              新建任务
            </el-button>
            <el-button type="success" plain class="action-btn" @click="showCreateProject = true">
              <el-icon><FolderAdd /></el-icon>
              新建项目
            </el-button>
            <el-button type="warning" plain class="action-btn" @click="$router.push('/approvals')">
              <el-icon><DocumentChecked /></el-icon>
              发起审批
            </el-button>
          </div>
        </el-card>
        
        <el-card class="my-tasks" style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <span>我的待办</span>
              <el-button text @click="$router.push('/tasks')">查看全部</el-button>
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
          <el-empty v-else description="暂无待办任务" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 新建任务对话框 -->
    <el-dialog v-model="showCreateTask" title="新建任务" width="600px">
      <el-form :model="taskForm" label-width="80px">
        <el-form-item label="任务标题">
          <el-input v-model="taskForm.title" placeholder="请输入任务标题" />
        </el-form-item>
        <el-form-item label="所属项目">
          <el-select v-model="taskForm.project_id" placeholder="选择项目" style="width: 100%;">
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="taskForm.priority" style="width: 100%;">
            <el-option label="紧急" value="urgent" />
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker
            v-model="taskForm.due_date"
            type="datetime"
            placeholder="选择截止日期"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="任务描述">
          <el-input
            v-model="taskForm.description"
            type="textarea"
            rows="3"
            placeholder="请输入任务描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateTask = false">取消</el-button>
        <el-button type="primary" @click="createTask" :loading="creating">创建</el-button>
      </template>
    </el-dialog>

    <!-- 新建项目对话框 -->
    <el-dialog v-model="showCreateProject" title="新建项目" width="600px">
      <el-form :model="projectForm" label-width="80px">
        <el-form-item label="项目名称">
          <el-input v-model="projectForm.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="项目描述">
          <el-input
            v-model="projectForm.description"
            type="textarea"
            rows="3"
            placeholder="请输入项目描述"
          />
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker
            v-model="projectForm.start_date"
            type="date"
            placeholder="选择开始日期"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker
            v-model="projectForm.end_date"
            type="date"
            placeholder="选择结束日期"
            style="width: 100%;"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateProject = false">取消</el-button>
        <el-button type="primary" @click="createProject" :loading="creatingProject">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { getOverview, getActivities } from '@/api/dashboard'
import { getMyTasks, createTask as apiCreateTask } from '@/api/tasks'
import { getProjects, createProject as apiCreateProject } from '@/api/projects'

const router = useRouter()

const overview = ref({})
const activities = ref([])
const myTasks = ref([])
const projects = ref([])

const showCreateTask = ref(false)
const showCreateProject = ref(false)
const creating = ref(false)
const creatingProject = ref(false)

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
    const [overviewRes, activitiesRes, tasksRes, projectsRes] = await Promise.all([
      getOverview(),
      getActivities({ limit: 10 }),
      getMyTasks(),
      getProjects()
    ])
    
    overview.value = overviewRes
    activities.value = activitiesRes.activities
    myTasks.value = tasksRes.tasks.filter(t => t.status !== 'done')
    projects.value = projectsRes.projects
  } catch (error) {
    console.error('获取数据失败', error)
  }
}

const createTask = async () => {
  if (!taskForm.value.title || !taskForm.value.project_id) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  creating.value = true
  try {
    await apiCreateTask(taskForm.value)
    ElMessage.success('任务创建成功')
    showCreateTask.value = false
    fetchData()
    taskForm.value = { title: '', project_id: '', priority: 'medium', due_date: '', description: '' }
  } catch (error) {
    console.error('创建任务失败', error)
  } finally {
    creating.value = false
  }
}

const createProject = async () => {
  if (!projectForm.value.name) {
    ElMessage.warning('请输入项目名称')
    return
  }
  
  creatingProject.value = true
  try {
    await apiCreateProject(projectForm.value)
    ElMessage.success('项目创建成功')
    showCreateProject.value = false
    fetchData()
    projectForm.value = { name: '', description: '', start_date: '', end_date: '' }
  } catch (error) {
    console.error('创建项目失败', error)
  } finally {
    creatingProject.value = false
  }
}

const formatTime = (time) => {
  return dayjs(time).format('MM-DD HH:mm')
}

const formatDate = (date) => {
  if (!date) return '无截止日期'
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
    'urgent': '紧急',
    'high': '高',
    'medium': '中',
    'low': '低'
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
