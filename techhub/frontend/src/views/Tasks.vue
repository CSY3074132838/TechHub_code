<template>
  <div class="tasks-page">
    <div class="page-header">
      <h2>我的任务</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>新建任务
      </el-button>
    </div>

    <!-- 筛选栏 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="全部状态" clearable @change="fetchTasks">
            <el-option label="待处理" value="todo" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="审核中" value="review" />
            <el-option label="已完成" value="done" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="filterForm.priority" placeholder="全部优先级" clearable @change="fetchTasks">
            <el-option label="紧急" value="urgent" />
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input
            v-model="filterForm.search"
            placeholder="搜索任务标题"
            clearable
            @keyup.enter="fetchTasks"
          />
        </el-form-item>
        <el-form-item>
          <el-button @click="resetFilter">重置</el-button>
          <el-button type="primary" @click="fetchTasks">搜索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 任务列表 -->
    <el-card class="tasks-list">
      <el-table :data="tasks" v-loading="loading" stripe>
        <el-table-column label="任务标题" min-width="250">
          <template #default="{ row }">
            <div class="task-title-cell">
              <el-tag :type="getPriorityType(row.priority)" size="small">
                {{ getPriorityLabel(row.priority) }}
              </el-tag>
              <span class="title" @click="viewTask(row)">{{ row.title }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="所属项目" width="150">
          <template #default="{ row }">
            {{ getProjectName(row.project_id) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="截止日期" width="120">
          <template #default="{ row }">
            <span :class="{ overdue: isOverdue(row.due_date) && row.status !== 'done' }">
              {{ row.due_date ? formatDate(row.due_date) : '无' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status !== 'done'"
              type="success"
              size="small"
              @click="completeTask(row)"
            >
              完成
            </el-button>
            <el-button text size="small" @click="viewTask(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchTasks"
          @current-change="fetchTasks"
        />
      </div>
    </el-card>

    <!-- 新建任务对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建任务" width="600px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="任务标题">
          <el-input v-model="form.title" placeholder="请输入任务标题" />
        </el-form-item>
        <el-form-item label="所属项目">
          <el-select v-model="form.project_id" placeholder="选择项目" style="width: 100%;">
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="form.priority" style="width: 100%;">
            <el-option label="紧急" value="urgent" />
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker
            v-model="form.due_date"
            type="datetime"
            placeholder="选择截止日期"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="任务描述">
          <el-input
            v-model="form.description"
            type="textarea"
            rows="3"
            placeholder="请输入任务描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createTask" :loading="creating">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { getTasks, createTask as apiCreateTask, updateTask } from '@/api/tasks'
import { getProjects } from '@/api/projects'

const router = useRouter()

const tasks = ref([])
const projects = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

const showCreateDialog = ref(false)
const creating = ref(false)

const filterForm = ref({
  status: '',
  priority: '',
  search: ''
})

const form = ref({
  title: '',
  project_id: '',
  priority: 'medium',
  due_date: '',
  description: ''
})

const fetchTasks = async () => {
  loading.value = true
  try {
    const params = {
      page: page.value,
      per_page: pageSize.value,
      ...filterForm.value
    }
    const res = await getTasks(params)
    tasks.value = res.tasks
    total.value = res.total
  } catch (error) {
    console.error('获取任务失败', error)
  } finally {
    loading.value = false
  }
}

const fetchProjects = async () => {
  try {
    const res = await getProjects({ per_page: 100 })
    projects.value = res.projects
  } catch (error) {
    console.error('获取项目失败', error)
  }
}

const getProjectName = (projectId) => {
  const project = projects.value.find(p => p.id === projectId)
  return project?.name || '未知项目'
}

const resetFilter = () => {
  filterForm.value = { status: '', priority: '', search: '' }
  fetchTasks()
}

const createTask = async () => {
  if (!form.value.title || !form.value.project_id) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  creating.value = true
  try {
    await apiCreateTask(form.value)
    ElMessage.success('任务创建成功')
    showCreateDialog.value = false
    fetchTasks()
    form.value = { title: '', project_id: '', priority: 'medium', due_date: '', description: '' }
  } catch (error) {
    console.error('创建任务失败', error)
  } finally {
    creating.value = false
  }
}

const completeTask = async (row) => {
  try {
    await updateTask(row.id, { status: 'done' })
    ElMessage.success('任务已完成')
    fetchTasks()
  } catch (error) {
    console.error('完成任务失败', error)
  }
}

const viewTask = (row) => {
  router.push(`/projects/${row.project_id}`)
}

const formatDate = (date) => {
  return dayjs(date).format('MM-DD')
}

const isOverdue = (date) => {
  return date && dayjs(date).isBefore(dayjs(), 'day')
}

const getPriorityType = (priority) => {
  const typeMap = { urgent: 'danger', high: 'warning', medium: '', low: 'info' }
  return typeMap[priority] || ''
}

const getPriorityLabel = (priority) => {
  const labelMap = { urgent: '紧急', high: '高', medium: '中', low: '低' }
  return labelMap[priority] || priority
}

const getStatusType = (status) => {
  const typeMap = { todo: 'info', in_progress: 'warning', review: 'primary', done: 'success' }
  return typeMap[status] || ''
}

const getStatusLabel = (status) => {
  const labelMap = { todo: '待处理', in_progress: '进行中', review: '审核中', done: '已完成' }
  return labelMap[status] || status
}

onMounted(() => {
  fetchTasks()
  fetchProjects()
})
</script>

<style scoped lang="scss">
.tasks-page {
  .filter-card {
    margin-bottom: 20px;
  }
  
  .tasks-list {
    .task-title-cell {
      display: flex;
      align-items: center;
      gap: 8px;
      
      .title {
        cursor: pointer;
        color: #1890ff;
        
        &:hover {
          text-decoration: underline;
        }
      }
    }
    
    .overdue {
      color: #f56c6c;
    }
    
    .pagination {
      margin-top: 20px;
      display: flex;
      justify-content: flex-end;
    }
  }
}
</style>
