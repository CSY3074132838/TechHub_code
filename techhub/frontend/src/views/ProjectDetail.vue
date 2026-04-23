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
        </div>
      </div>
      <div class="header-right">
        <el-button @click="showEditDialog = true">
          <el-icon><Edit /></el-icon>编辑
        </el-button>
        <el-button type="primary" @click="showCreateTask = true">
          <el-icon><Plus /></el-icon>新建任务
        </el-button>
      </div>
    </div>

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
            draggable="true"
            @dragstart="handleDragStart(task, $event)"
            @click="openTaskDetail(task)"
          >
            <div class="card-title">{{ task.title }}</div>
            <div class="card-meta">
              <div class="card-tags">
                <el-tag
                  :type="getPriorityType(task.priority)"
                  size="small"
                  effect="plain"
                >
                  {{ getPriorityLabel(task.priority) }}
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

    <!-- 任务详情对话框 -->
    <el-dialog v-model="showTaskDetail" title="任务详情" width="700px">
      <div v-if="currentTask" class="task-detail">
        <div class="detail-header">
          <h3>{{ currentTask.title }}</h3>
          <el-tag :type="getStatusType(currentTask.status)">
            {{ getStatusLabel(currentTask.status) }}
          </el-tag>
        </div>
        
        <div class="detail-info">
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
        
        <div class="detail-desc">
          <h4>任务描述</h4>
          <p>{{ currentTask.description || '暂无描述' }}</p>
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
        <el-button @click="showTaskDetail = false">关闭</el-button>
        <el-button
          v-if="currentTask?.status !== 'done'"
          type="success"
          @click="completeTask"
        >
          完成任务
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { getProject, getProjectTasks } from '@/api/projects'
import { createTask as apiCreateTask, updateTask, getTask, addComment as apiAddComment } from '@/api/tasks'

const route = useRoute()
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

const showCreateTask = ref(false)
const showTaskDetail = ref(false)
const showEditDialog = ref(false)
const creating = ref(false)
const addingComment = ref(false)
const currentTask = ref(null)
const newComment = ref('')

const taskForm = ref({
  title: '',
  assignee_id: '',
  priority: 'medium',
  due_date: '',
  description: ''
})

const fetchProject = async () => {
  try {
    const res = await getProject(projectId)
    project.value = res.project
  } catch (error) {
    console.error('获取项目失败', error)
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
    // 刷新任务详情
    const res = await getTask(currentTask.value.id)
    currentTask.value = res.task
  } catch (error) {
    console.error('添加评论失败', error)
  } finally {
    addingComment.value = false
  }
}

const completeTask = async () => {
  try {
    await updateTask(currentTask.value.id, { status: 'done' })
    ElMessage.success('任务已完成')
    showTaskDetail.value = false
    fetchBoard()
  } catch (error) {
    console.error('完成任务失败', error)
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
  
  // 乐观更新：先更新本地状态
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
  } catch (error) {
    console.error('更新任务状态失败', error)
    ElMessage.error('更新失败，正在刷新')
    fetchBoard() // 失败时回退
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

onMounted(() => {
  fetchProject()
  fetchBoard()
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
  
  .kanban-board {
    display: flex;
    gap: 16px;
    overflow-x: auto;
    padding-bottom: 16px;
    
    .kanban-column {
      min-width: 280px;
      max-width: 280px;
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
    
    &:hover {
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      transform: translateY(-2px);
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
