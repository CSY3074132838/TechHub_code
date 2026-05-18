<template>
  <div class="project-detail-page">
    <!-- 项目头部信息 -->
    <div class="project-header-bar">
      <div class="header-left">
        <el-button text @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon>返回
        </el-button>
        <div class="project-title">
          <div class="color-dot" :style="{ background: project.color }"></div>
          <h2>{{ project.name }}</h2>
          <el-tag v-if="project.client" type="primary" size="small" style="margin-left: 12px" @click="goToClient(project.client_id)">
            <el-icon><OfficeBuilding /></el-icon>
            {{ project.client.name }}
          </el-tag>
        </div>
      </div>
      <div class="header-right">
        <el-button @click="openEditDialog">
          <el-icon><Edit /></el-icon>编辑
        </el-button>
        <el-button type="primary" @click="showCreateTask = true">
          <el-icon><Plus /></el-icon>新建任务
        </el-button>
      </div>
    </div>

    <!-- 主内容区：左侧看板 + 右侧动态 -->
    <el-row :gutter="20">
      <!-- 左侧：看板 + 任务流程进度条 -->
      <el-col :xs="24" :lg="17">
        <!-- 任务流程可视化进度条 -->
        <el-card class="workflow-card" style="margin-bottom: 16px;">
          <div class="workflow-header">
            <span class="workflow-title">任务开发流程</span>
            <span class="workflow-subtitle">拖拽任务卡片可变更状态 · 审核中任务需项目负责人审批</span>
          </div>
          <div class="workflow-steps">
            <div 
              v-for="(step, idx) in workflowSteps" 
              :key="step.key"
              class="workflow-step"
              :class="{ active: currentWorkflowStep >= idx, current: currentWorkflowStep === idx }"
            >
              <div class="step-icon-wrapper">
                <el-icon size="20"><component :is="step.icon" /></el-icon>
              </div>
              <div class="step-info">
                <div class="step-name">{{ step.name }}</div>
                <div class="step-desc">{{ step.desc }}</div>
              </div>
              <div v-if="idx < workflowSteps.length - 1" class="step-arrow">
                <el-icon><ArrowRight /></el-icon>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 看板 -->
        <div class="kanban-board">
          <div
            v-for="column in columns"
            :key="column.key"
            class="kanban-column"
            @dragover.prevent
            @drop="handleDrop(column.key, $event)"
          >
            <div class="kanban-header">
              <span class="column-title">{{ column.title }}</span>
              <span class="column-count">{{ getTasksByStatus(column.key).length }}</span>
            </div>
            
            <div class="kanban-tasks">
              <div
                v-for="task in getTasksByStatus(column.key)"
                :key="task.id"
                class="kanban-card"
                :class="{ 'review-pending': task.status === 'review' }"
                draggable="true"
                @dragstart="handleDragStart(task, $event)"
                @click="openTaskDetail(task)"
              >
                <div class="card-title">{{ task.title }}</div>
                <div class="card-meta">
                  <div class="card-tags">
                    <el-tag :type="getPriorityType(task.priority)" size="small" effect="plain">
                      {{ getPriorityLabel(task.priority) }}
                    </el-tag>
                    <el-tag v-if="task.status === 'review'" type="warning" size="small" effect="dark">
                      待审核
                    </el-tag>
                  </div>
                  <el-avatar
                    v-if="task.assignee"
                    :size="24"
                    :src="task.assignee.avatar"
                    :title="task.assignee.real_name"
                  >
                    {{ task.assignee.real_name?.charAt(0) }}
                  </el-avatar>
                </div>
                <div v-if="task.due_date" class="card-due">
                  <el-icon><Calendar /></el-icon>
                  <span :class="{ overdue: isOverdue(task.due_date) }">
                    {{ formatDate(task.due_date) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 右侧：项目最近动态看板 -->
      <el-col :xs="24" :lg="7">
        <el-card class="activity-card">
          <template #header>
            <div class="activity-header">
              <span class="activity-title">
                <el-icon><Bell /></el-icon>
                项目最近动态
              </span>
              <el-button text size="small" @click="fetchActivities">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>
          <div class="activity-list" v-loading="activityLoading">
            <div v-if="activities.length === 0" class="activity-empty">
              <el-empty description="暂无动态" :image-size="60" />
            </div>
            <div
              v-for="activity in activities"
              :key="activity.id"
              class="activity-item"
            >
              <div class="activity-avatar">
                <el-avatar :size="32" :src="activity.user?.avatar">
                  {{ activity.user?.real_name?.charAt(0) || 'U' }}
                </el-avatar>
              </div>
              <div class="activity-content">
                <div class="activity-text">
                  <span class="user-name">{{ activity.user?.real_name || '未知用户' }}</span>
                  <span class="action">{{ formatActivityTitle(activity) }}</span>
                </div>
                <div class="activity-time">{{ formatDateTime(activity.created_at) }}</div>
              </div>
              <div class="activity-icon" :class="activity.activity_type">
                <el-icon size="14">
                  <component :is="getActivityIcon(activity.activity_type)" />
                </el-icon>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 项目成员 -->
        <el-card class="members-card" style="margin-top: 16px;">
          <template #header>
            <div class="members-header">
              <span>项目成员</span>
              <span class="members-count">{{ project.members?.length || 0 }}人</span>
            </div>
          </template>
          <div class="members-list">
            <div
              v-for="member in project.members"
              :key="member.id"
              class="member-item"
            >
              <el-avatar :size="36" :src="member.avatar">
                {{ member.real_name?.charAt(0) || 'U' }}
              </el-avatar>
              <div class="member-info">
                <div class="member-name">{{ member.real_name || member.username }}</div>
                <div class="member-role">
                  <el-tag v-if="member.id === project.leader_id" type="warning" size="small">负责人</el-tag>
                  <span v-else class="member-position">{{ member.position || '成员' }}</span>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 新建任务对话框 -->
    <el-dialog v-model="showCreateTask" title="新建任务" width="600px">
      <el-form :model="taskForm" label-width="80px">
        <el-form-item label="任务标题">
          <el-input v-model="taskForm.title" placeholder="请输入任务标题" />
        </el-form-item>
        <el-form-item label="负责人">
          <el-select v-model="taskForm.assignee_id" placeholder="选择负责人" style="width: 100%;">
            <el-option
              v-for="member in project.members"
              :key="member.id"
              :label="member.real_name"
              :value="member.id"
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

    <!-- 编辑项目对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑项目" width="600px">
      <el-form :model="editForm" label-width="100px" :rules="editRules" ref="editFormRef">
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="项目描述">
          <el-input
            v-model="editForm.description"
            type="textarea"
            rows="3"
            placeholder="请输入项目描述"
          />
        </el-form-item>
        <el-form-item label="项目颜色">
          <el-color-picker v-model="editForm.color" />
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker
            v-model="editForm.start_date"
            type="date"
            placeholder="选择开始日期"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker
            v-model="editForm.end_date"
            type="date"
            placeholder="选择结束日期"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="关联客户">
          <el-select
            v-model="editForm.client_id"
            clearable
            placeholder="选择关联客户（可选）"
            style="width: 100%;"
          >
            <el-option
              v-for="client in clientOptions"
              :key="client.id"
              :label="client.name"
              :value="client.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="项目负责人">
          <el-select v-model="editForm.leader_id" placeholder="选择项目负责人" style="width: 100%;">
            <el-option
              v-for="user in users"
              :key="user.id"
              :label="user.real_name"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="项目成员">
          <el-select
            v-model="editForm.member_ids"
            multiple
            placeholder="选择项目成员"
            style="width: 100%;"
          >
            <el-option
              v-for="user in users"
              :key="user.id"
              :label="user.real_name"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleUpdate" :loading="updating">保存</el-button>
      </template>
    </el-dialog>

    <!-- 任务详情对话框 -->
    <el-dialog v-model="showTaskDetail" title="任务详情" width="700px">
      <div v-if="currentTask" class="task-detail">
        <div class="detail-header">
          <h3>{{ currentTask.title }}</h3>
          <div class="header-actions">
            <el-tag :type="getStatusType(currentTask.status)">
              {{ getStatusLabel(currentTask.status) }}
            </el-tag>
            <el-button v-if="!taskEditMode" link type="primary" @click="startTaskEdit">
              <el-icon><Edit /></el-icon>编辑
            </el-button>
          </div>
        </div>
        
        <!-- 任务流程进度条（任务详情内） -->
        <div class="task-workflow">
          <el-steps :active="getTaskStepIndex(currentTask.status)" finish-status="success" simple>
            <el-step title="待处理" />
            <el-step title="进行中" />
            <el-step title="审核中" />
            <el-step title="已完成" />
          </el-steps>
        </div>
        
        <!-- 审核操作区：仅项目负责人可见 -->
        <div v-if="currentTask.status === 'review' && isProjectLeader" class="review-actions">
          <el-alert
            title="该任务正在等待审核"
            description="作为项目负责人，您可以审核此任务"
            type="warning"
            :closable="false"
            show-icon
            style="margin-bottom: 12px;"
          />
          <div class="review-buttons">
            <el-button type="danger" @click="handleReview('reject')">
              <el-icon><Close /></el-icon>驳回
            </el-button>
            <el-button type="success" @click="handleReview('approve')">
              <el-icon><Check /></el-icon>通过审核
            </el-button>
          </div>
        </div>
        
        <!-- 非负责人看到审核中提示 -->
        <div v-else-if="currentTask.status === 'review' && !isProjectLeader" class="review-waiting">
          <el-alert
            title="该任务正在审核中"
            description="等待项目负责人审核..."
            type="info"
            :closable="false"
            show-icon
          />
        </div>

        <!-- 提交审核按钮：任务负责人可见，且任务在进行中 -->
        <div v-if="currentTask.status === 'in_progress' && canSubmitReview" class="submit-review">
          <el-button type="primary" @click="handleSubmitReview">
            <el-icon><Upload /></el-icon>提交审核
          </el-button>
        </div>
        
        <!-- 展示模式 -->
        <div v-if="!taskEditMode" class="detail-info">
          <div class="info-item">
            <span class="label">负责人：</span>
            <span>{{ currentTask.assignee?.real_name || '未分配' }}</span>
          </div>
          <div class="info-item">
            <span class="label">优先级：</span>
            <el-tag :type="getPriorityType(currentTask.priority)" size="small">
              {{ getPriorityLabel(currentTask.priority) }}
            </el-tag>
          </div>
          <div class="info-item">
            <span class="label">截止日期：</span>
            <span>{{ currentTask.due_date ? formatDateTime(currentTask.due_date) : '无' }}</span>
          </div>
        </div>
        
        <!-- 编辑模式 -->
        <div v-else class="detail-info edit-mode">
          <el-form :model="taskEditForm" label-width="80px">
            <el-form-item label="负责人">
              <el-select v-model="taskEditForm.assignee_id" clearable placeholder="选择负责人" style="width: 100%;">
                <el-option
                  v-for="member in project.members"
                  :key="member.id"
                  :label="member.real_name"
                  :value="member.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="优先级">
              <el-select v-model="taskEditForm.priority" style="width: 100%;">
                <el-option label="紧急" value="urgent" />
                <el-option label="高" value="high" />
                <el-option label="中" value="medium" />
                <el-option label="低" value="low" />
              </el-select>
            </el-form-item>
            <el-form-item label="截止日期">
              <el-date-picker
                v-model="taskEditForm.due_date"
                type="datetime"
                placeholder="选择截止日期"
                style="width: 100%;"
              />
            </el-form-item>
          </el-form>
        </div>
        
        <div class="detail-desc">
          <h4>任务描述</h4>
          <p v-if="!taskEditMode">{{ currentTask.description || '暂无描述' }}</p>
          <el-input
            v-else
            v-model="taskEditForm.description"
            type="textarea"
            rows="4"
            placeholder="请输入任务描述"
          />
        </div>
        
        <!-- 评论区域 -->
        <div class="detail-comments">
          <h4>评论</h4>
          <div class="comment-list">
            <div
              v-for="comment in currentTask.comments"
              :key="comment.id"
              class="comment-item"
            >
              <el-avatar :size="32" :src="comment.author?.avatar">
                {{ comment.author?.real_name?.charAt(0) }}
              </el-avatar>
              <div class="comment-content">
                <div class="comment-header">
                  <span class="author">{{ comment.author?.real_name }}</span>
                  <span class="time">{{ formatDateTime(comment.created_at) }}</span>
                </div>
                <p class="text">{{ comment.content }}</p>
              </div>
            </div>
          </div>
          
          <div class="comment-input">
            <el-input
              v-model="newComment"
              type="textarea"
              rows="2"
              placeholder="添加评论..."
            />
            <el-button type="primary" @click="addComment" :loading="addingComment">
              发送
            </el-button>
          </div>
        </div>
      </div>
      <template #footer>
        <template v-if="taskEditMode">
          <el-button @click="cancelTaskEdit">取消</el-button>
          <el-button type="primary" @click="saveTaskEdit" :loading="taskSaving">保存</el-button>
        </template>
        <template v-else>
          <el-button @click="showTaskDetail = false">关闭</el-button>
          <el-button
            v-if="currentTask?.status !== 'done' && currentTask?.status !== 'review' && canEditTask"
            type="success"
            @click="completeTask"
          >
            完成任务
          </el-button>
        </template>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { useUserStore } from '@/stores/user'
import { getProject, getProjectTasks, updateProject, getProjectActivities } from '@/api/projects'
import { 
  createTask as apiCreateTask, updateTask, getTask, addComment as apiAddComment,
  submitTaskForReview, reviewTask 
} from '@/api/tasks'
import { getUsers } from '@/api/users'
import { getClientOptions } from '@/api/clients'

const route = useRoute()
const userStore = useUserStore()
const projectId = route.params.id

const project = ref({})
const board = ref({
  todo: [],
  in_progress: [],
  review: [],
  done: []
})

const columns = [
  { key: 'todo', title: '待处理' },
  { key: 'in_progress', title: '进行中' },
  { key: 'review', title: '审核中' },
  { key: 'done', title: '已完成' }
]

// 任务流程步骤
const workflowSteps = [
  { key: 'todo', name: '待处理', desc: '任务已创建', icon: 'Document' },
  { key: 'in_progress', name: '进行中', desc: '开发处理中', icon: 'Loading' },
  { key: 'review', name: '审核中', desc: '等待负责人审核', icon: 'View' },
  { key: 'done', name: '已完成', desc: '审核通过', icon: 'CircleCheck' }
]

const currentWorkflowStep = computed(() => {
  // 根据当前选中任务或整体项目进度计算
  if (!currentTask.value) return -1
  const stepMap = { todo: 0, in_progress: 1, review: 2, done: 3 }
  return stepMap[currentTask.value.status] || 0
})

// 权限计算
const isProjectLeader = computed(() => {
  const currentUserId = userStore.userInfo?.id
  return project.value.leader_id === currentUserId || 
         userStore.hasPermission('project_manage')
})

const canSubmitReview = computed(() => {
  if (!currentTask.value) return false
  // 项目成员均可提交审核
  const memberIds = project.value.members?.map(m => m.id) || []
  const isMember = memberIds.includes(userStore.userInfo?.id)
  const isAssignee = currentTask.value.assignee?.id === userStore.userInfo?.id
  const isCreator = currentTask.value.creator?.id === userStore.userInfo?.id
  return currentTask.value.status === 'in_progress' && (isMember || isAssignee || isCreator || isProjectLeader.value)
})

const canEditTask = computed(() => {
  if (!currentTask.value) return false
  const isAssignee = currentTask.value.assignee?.id === userStore.userInfo?.id
  const isCreator = currentTask.value.creator?.id === userStore.userInfo?.id
  return isAssignee || isCreator || isProjectLeader.value
})

// 动态数据
const activities = ref([])
const activityLoading = ref(false)

const showCreateTask = ref(false)
const showTaskDetail = ref(false)
const showEditDialog = ref(false)
const creating = ref(false)
const updating = ref(false)
const addingComment = ref(false)
const taskEditMode = ref(false)
const taskSaving = ref(false)
const currentTask = ref(null)
const newComment = ref('')
const editFormRef = ref(null)
const users = ref([])
const clientOptions = ref([])

const taskForm = ref({
  title: '',
  assignee_id: '',
  priority: 'medium',
  due_date: '',
  description: ''
})

const taskEditForm = ref({
  assignee_id: '',
  priority: 'medium',
  due_date: '',
  description: ''
})

const editForm = ref({
  name: '',
  description: '',
  color: '#1890ff',
  start_date: '',
  end_date: '',
  client_id: '',
  leader_id: '',
  member_ids: []
})

const editRules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }]
}

const fetchProject = async () => {
  try {
    const res = await getProject(projectId)
    project.value = res.project
  } catch (error) {
    console.error('获取项目失败', error)
  }
}

const fetchUsers = async () => {
  try {
    const res = await getUsers({ per_page: 100 })
    users.value = res.users
  } catch (error) {
    console.error('获取用户失败', error)
  }
}

const fetchClientOptions = async () => {
  try {
    const res = await getClientOptions()
    clientOptions.value = res.clients
  } catch (error) {
    console.error('获取客户选项失败', error)
  }
}

const fetchActivities = async () => {
  activityLoading.value = true
  try {
    const res = await getProjectActivities(projectId, { per_page: 50 })
    activities.value = res.activities || []
  } catch (error) {
    console.error('获取动态失败', error)
  } finally {
    activityLoading.value = false
  }
}

const openEditDialog = () => {
  editForm.value = {
    name: project.value.name || '',
    description: project.value.description || '',
    color: project.value.color || '#1890ff',
    start_date: project.value.start_date || '',
    end_date: project.value.end_date || '',
    client_id: project.value.client_id || '',
    leader_id: project.value.leader_id || '',
    member_ids: project.value.members?.map(m => m.id) || []
  }
  showEditDialog.value = true
}

const handleUpdate = async () => {
  const valid = await editFormRef.value?.validate().catch(() => false)
  if (!valid) return

  updating.value = true
  try {
    await updateProject(projectId, { ...editForm.value })
    ElMessage.success('项目更新成功')
    showEditDialog.value = false
    fetchProject()
  } catch (error) {
    console.error('更新项目失败', error)
    ElMessage.error(error.response?.data?.message || '操作失败')
  } finally {
    updating.value = false
  }
}

const fetchBoard = async () => {
  try {
    const res = await getProjectTasks(projectId)
    board.value = res.board
  } catch (error) {
    console.error('获取看板失败', error)
  }
}

const getTasksByStatus = (status) => {
  return board.value[status] || []
}

const createTask = async () => {
  if (!taskForm.value.title) {
    ElMessage.warning('请输入任务标题')
    return
  }
  
  creating.value = true
  try {
    await apiCreateTask({
      ...taskForm.value,
      project_id: projectId
    })
    ElMessage.success('任务创建成功')
    showCreateTask.value = false
    fetchBoard()
    fetchActivities()
    taskForm.value = {
      title: '',
      assignee_id: '',
      priority: 'medium',
      due_date: '',
      description: ''
    }
  } catch (error) {
    console.error('创建任务失败', error)
  } finally {
    creating.value = false
  }
}

const openTaskDetail = async (task) => {
  try {
    const res = await getTask(task.id)
    currentTask.value = res.task
    showTaskDetail.value = true
  } catch (error) {
    console.error('获取任务详情失败', error)
  }
}

const addComment = async () => {
  if (!newComment.value.trim()) return
  
  addingComment.value = true
  try {
    await apiAddComment(currentTask.value.id, newComment.value)
    ElMessage.success('评论添加成功')
    newComment.value = ''
    const res = await getTask(currentTask.value.id)
    currentTask.value = res.task
    fetchActivities()
  } catch (error) {
    console.error('添加评论失败', error)
  } finally {
    addingComment.value = false
  }
}

const startTaskEdit = () => {
  taskEditForm.value = {
    assignee_id: currentTask.value.assignee?.id || '',
    priority: currentTask.value.priority || 'medium',
    due_date: currentTask.value.due_date || '',
    description: currentTask.value.description || ''
  }
  taskEditMode.value = true
}

const cancelTaskEdit = () => {
  taskEditMode.value = false
}

const saveTaskEdit = async () => {
  taskSaving.value = true
  try {
    await updateTask(currentTask.value.id, { ...taskEditForm.value })
    ElMessage.success('任务更新成功')
    taskEditMode.value = false
    const res = await getTask(currentTask.value.id)
    currentTask.value = res.task
    fetchBoard()
    fetchActivities()
  } catch (error) {
    console.error('更新任务失败', error)
    ElMessage.error(error.response?.data?.message || '操作失败')
  } finally {
    taskSaving.value = false
  }
}

const completeTask = async () => {
  try {
    await updateTask(currentTask.value.id, { status: 'done' })
    ElMessage.success('任务已完成')
    showTaskDetail.value = false
    fetchBoard()
    fetchActivities()
  } catch (error) {
    console.error('完成任务失败', error)
  }
}

// 提交审核
const handleSubmitReview = async () => {
  try {
    await submitTaskForReview(currentTask.value.id)
    ElMessage.success('任务已提交审核')
    const res = await getTask(currentTask.value.id)
    currentTask.value = res.task
    fetchBoard()
    fetchActivities()
  } catch (error) {
    console.error('提交审核失败', error)
    ElMessage.error(error.response?.data?.message || '提交审核失败')
  }
}

// 审核任务
const handleReview = async (action) => {
  try {
    await reviewTask(currentTask.value.id, action)
    ElMessage.success(action === 'approve' ? '审核通过' : '已驳回')
    const res = await getTask(currentTask.value.id)
    currentTask.value = res.task
    fetchBoard()
    fetchActivities()
  } catch (error) {
    console.error('审核失败', error)
    ElMessage.error(error.response?.data?.message || '审核失败')
  }
}

// 拖拽相关
let draggedTask = null

const handleDragStart = (task, event) => {
  draggedTask = task
  event.dataTransfer.effectAllowed = 'move'
}

const handleDrop = async (newStatus, event) => {
  event.preventDefault()
  if (!draggedTask || draggedTask.status === newStatus) return
  
  const oldStatus = draggedTask.status
  const taskId = draggedTask.id
  
  // 限制：只能拖拽到相邻状态，不能直接跳过
  const statusFlow = ['todo', 'in_progress', 'review', 'done']
  const oldIdx = statusFlow.indexOf(oldStatus)
  const newIdx = statusFlow.indexOf(newStatus)
  
  // 禁止从待处理直接跳到已完成，或反向跳
  if (Math.abs(newIdx - oldIdx) > 1 && newStatus !== 'done') {
    ElMessage.warning('请按流程顺序推进任务')
    draggedTask = null
    return
  }
  
  // 禁止从已完成往回拖
  if (oldStatus === 'done' && newIdx < oldIdx) {
    ElMessage.warning('已完成的任务不能回退')
    draggedTask = null
    return
  }
  
  // 审核中只能由负责人处理，普通成员不能拖拽
  if (oldStatus === 'review' && !isProjectLeader.value) {
    ElMessage.warning('审核中的任务只能由项目负责人操作')
    draggedTask = null
    return
  }
  
  // 乐观更新
  const taskIndex = board.value[oldStatus].findIndex(t => t.id === taskId)
  if (taskIndex > -1) {
    const task = board.value[oldStatus].splice(taskIndex, 1)[0]
    task.status = newStatus
    board.value[newStatus].push(task)
  }
  draggedTask = null
  
  try {
    await updateTask(taskId, { status: newStatus })
    ElMessage.success('任务状态已更新')
    fetchActivities()
  } catch (error) {
    console.error('更新任务状态失败', error)
    ElMessage.error('更新失败，正在刷新')
    fetchBoard()
  }
}

const formatDate = (date) => {
  return dayjs(date).format('MM-DD')
}

const formatDateTime = (date) => {
  return dayjs(date).format('MM-DD HH:mm')
}

const isOverdue = (date) => {
  return dayjs(date).isBefore(dayjs(), 'day')
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

const getStatusType = (status) => {
  const typeMap = {
    'todo': 'info',
    'in_progress': 'warning',
    'review': 'primary',
    'done': 'success'
  }
  return typeMap[status] || ''
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

const getTaskStepIndex = (status) => {
  const map = { todo: 0, in_progress: 1, review: 2, done: 3 }
  return map[status] || 0
}

// 动态相关
const formatActivityTitle = (activity) => {
  const title = activity.title || ''
  // 移除用户名前缀，只保留动作
  return title.replace(/^.*?(创建了|完成了|更新了|评论了)/, '$1')
}

const getActivityIcon = (type) => {
  const iconMap = {
    'task_created': 'Document',
    'task_updated': 'Edit',
    'task_completed': 'CircleCheck',
    'comment_added': 'ChatDotRound',
    'project_created': 'FolderOpened'
  }
  return iconMap[type] || 'Notification'
}

onMounted(() => {
  fetchProject()
  fetchBoard()
  fetchUsers()
  fetchClientOptions()
  fetchActivities()
})
</script>

<style scoped lang="scss">
.project-detail-page {
  .project-header-bar {
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
      
      .project-title {
        display: flex;
        align-items: center;
        gap: 12px;
        
        .color-dot {
          width: 16px;
          height: 16px;
          border-radius: 4px;
        }
        
        h2 {
          margin: 0;
          font-size: 18px;
        }
      }
    }
    
    .header-right {
      display: flex;
      gap: 12px;
    }
  }

  // 任务流程可视化
  .workflow-card {
    :deep(.el-card__body) {
      padding: 16px 20px;
    }

    .workflow-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;

      .workflow-title {
        font-size: 15px;
        font-weight: 500;
        color: #333;
      }

      .workflow-subtitle {
        font-size: 12px;
        color: #999;
      }
    }

    .workflow-steps {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;

      .workflow-step {
        flex: 1;
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 12px 16px;
        border-radius: 8px;
        background: #f5f7fa;
        transition: all 0.3s;

        &.active {
          background: #e6f7ff;
          .step-icon-wrapper { background: #1890ff; color: #fff; }
          .step-name { color: #1890ff; }
        }

        &.current {
          box-shadow: 0 0 0 2px #1890ff;
          background: #e6f7ff;
        }

        .step-icon-wrapper {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          background: #e4e7ed;
          color: #909399;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          transition: all 0.3s;
        }

        .step-info {
          flex: 1;
          min-width: 0;

          .step-name {
            font-size: 14px;
            font-weight: 500;
            color: #333;
            margin-bottom: 2px;
          }

          .step-desc {
            font-size: 12px;
            color: #999;
          }
        }

        .step-arrow {
          color: #c0c4cc;
          margin-left: 4px;
        }
      }
    }
  }
  
  .kanban-board {
    display: flex;
    gap: 16px;
    overflow-x: auto;
    padding-bottom: 16px;
    
    .kanban-column {
      min-width: 260px;
      max-width: 260px;
      background: #f5f7fa;
      border-radius: 8px;
      padding: 12px;
      
      .kanban-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        padding: 0 4px;
        
        .column-title {
          font-weight: 500;
          font-size: 14px;
        }
        
        .column-count {
          background: #e4e7ed;
          padding: 2px 8px;
          border-radius: 10px;
          font-size: 12px;
        }
      }
      
      .kanban-tasks {
        min-height: 200px;
      }
    }
  }
  
  .kanban-card {
    background: #fff;
    border-radius: 6px;
    padding: 12px;
    margin-bottom: 8px;
    cursor: pointer;
    transition: all 0.2s;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    border-left: 3px solid transparent;
    
    &:hover {
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      transform: translateY(-2px);
    }

    &.review-pending {
      border-left-color: #e6a23c;
      background: #fdf6ec;
    }
    
    .card-title {
      font-size: 14px;
      margin-bottom: 8px;
      line-height: 1.4;
    }
    
    .card-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      
      .card-tags {
        display: flex;
        gap: 4px;
        flex-wrap: wrap;
      }
    }
    
    .card-due {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 12px;
      color: #999;
      
      .overdue {
        color: #f56c6c;
      }
    }
  }

  // 右侧动态看板
  .activity-card {
    :deep(.el-card__header) {
      padding: 12px 16px;
    }

    .activity-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .activity-title {
        font-size: 15px;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 8px;
      }
    }

    .activity-list {
      max-height: 500px;
      overflow-y: auto;

      .activity-empty {
        padding: 20px 0;
      }

      .activity-item {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 12px 0;
        border-bottom: 1px solid #f0f0f0;

        &:last-child {
          border-bottom: none;
        }

        .activity-avatar {
          flex-shrink: 0;
        }

        .activity-content {
          flex: 1;
          min-width: 0;

          .activity-text {
            font-size: 13px;
            line-height: 1.5;
            color: #333;

            .user-name {
              font-weight: 500;
              margin-right: 4px;
            }

            .action {
              color: #666;
            }
          }

          .activity-time {
            font-size: 12px;
            color: #999;
            margin-top: 4px;
          }
        }

        .activity-icon {
          width: 28px;
          height: 28px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          background: #f5f5f5;
          color: #999;

          &.task_created { background: #e6f7ff; color: #1890ff; }
          &.task_completed { background: #f6ffed; color: #52c41a; }
          &.task_updated { background: #fff7e6; color: #fa8c16; }
          &.comment_added { background: #f9f0ff; color: #722ed1; }
        }
      }
    }
  }

  // 成员卡片
  .members-card {
    :deep(.el-card__header) {
      padding: 12px 16px;
    }

    .members-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 15px;
      font-weight: 500;

      .members-count {
        font-size: 12px;
        color: #999;
        font-weight: normal;
      }
    }

    .members-list {
      .member-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 0;
        border-bottom: 1px solid #f5f5f5;

        &:last-child {
          border-bottom: none;
        }

        .member-info {
          flex: 1;

          .member-name {
            font-size: 13px;
            font-weight: 500;
            color: #333;
          }

          .member-role {
            margin-top: 2px;

            .member-position {
              font-size: 12px;
              color: #999;
            }
          }
        }
      }
    }
  }
  
  .task-detail {
    .detail-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      
      h3 {
        margin: 0;
        font-size: 18px;
      }
      
      .header-actions {
        display: flex;
        align-items: center;
        gap: 12px;
      }
    }

    .task-workflow {
      margin-bottom: 20px;
      padding: 16px;
      background: #f5f7fa;
      border-radius: 8px;
    }

    .review-actions {
      margin-bottom: 20px;
      padding: 16px;
      background: #fdf6ec;
      border-radius: 8px;
      border: 1px solid #f5dab1;

      .review-buttons {
        display: flex;
        justify-content: flex-end;
        gap: 12px;
      }
    }

    .review-waiting {
      margin-bottom: 20px;
    }

    .submit-review {
      margin-bottom: 20px;
      text-align: center;
    }
    
    .detail-info {
      display: flex;
      gap: 24px;
      margin-bottom: 20px;
      padding-bottom: 20px;
      border-bottom: 1px solid #eee;
      
      .info-item {
        .label {
          color: #666;
          margin-right: 8px;
        }
      }
    }
    
    .detail-desc {
      margin-bottom: 20px;
      
      h4 {
        font-size: 14px;
        margin-bottom: 8px;
      }
      
      p {
        color: #666;
        line-height: 1.6;
      }
    }
    
    .detail-comments {
      h4 {
        font-size: 14px;
        margin-bottom: 12px;
      }
      
      .comment-list {
        max-height: 300px;
        overflow-y: auto;
        margin-bottom: 16px;
        
        .comment-item {
          display: flex;
          gap: 12px;
          padding: 12px 0;
          border-bottom: 1px solid #eee;
          
          &:last-child {
            border-bottom: none;
          }
          
          .comment-content {
            flex: 1;
            
            .comment-header {
              display: flex;
              justify-content: space-between;
              margin-bottom: 4px;
              
              .author {
                font-weight: 500;
              }
              
              .time {
                font-size: 12px;
                color: #999;
              }
            }
            
            .text {
              color: #666;
              line-height: 1.5;
            }
          }
        }
      }
      
      .comment-input {
        display: flex;
        gap: 12px;
        
        .el-textarea {
          flex: 1;
        }
      }
    }
  }
}
</style>
