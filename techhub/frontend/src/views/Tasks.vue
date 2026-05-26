<!-- 第三次迭代陈思言负责 -->
<template>
  <div class="tasks-page">
    <div class="page-header">
      <h2>{{ $t('tasks.pageTitle') }}</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>{{ $t('tasks.newTask') }}
      </el-button>
    </div>

    <!-- 筛选栏 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm">
        <el-form-item :label="$t('tasks.status')">
          <el-select v-model="filterForm.status" :placeholder="$t('tasks.allStatus')" clearable @change="fetchTasks">
            <el-option :label="$t('tasks.todo')" value="todo" />
            <el-option :label="$t('tasks.inProgress')" value="in_progress" />
            <el-option :label="$t('tasks.inReview')" value="review" />
            <el-option :label="$t('tasks.done')" value="done" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('tasks.priority')">
          <el-select v-model="filterForm.priority" :placeholder="$t('tasks.allPriority')" clearable @change="fetchTasks">
            <el-option :label="$t('tasks.urgent')" value="urgent" />
            <el-option :label="$t('tasks.high')" value="high" />
            <el-option :label="$t('tasks.medium')" value="medium" />
            <el-option :label="$t('tasks.low')" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('common.search')">
          <el-input
            v-model="filterForm.search"
            :placeholder="$t('tasks.searchPlaceholder')"
            clearable
            @keyup.enter="fetchTasks"
          />
        </el-form-item>
        <el-form-item>
          <el-button @click="resetFilter">{{ $t('common.reset') }}</el-button>
          <el-button type="primary" @click="fetchTasks">{{ $t('common.search') }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 任务列表 -->
    <el-card class="tasks-list">
      <el-table :data="tasks" v-loading="loading" stripe>
        <el-table-column :label="$t('tasks.taskTitle')" min-width="250">
          <template #default="{ row }">
            <div class="task-title-cell">
              <el-tag :type="getPriorityType(row.priority)" size="small">
                {{ getPriorityLabel(row.priority) }}
              </el-tag>
              <span class="title" @click="viewTask(row)">{{ row.title }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column :label="$t('tasks.project')" width="150">
          <template #default="{ row }">
            {{ getProjectName(row.project_id) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('tasks.status')" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('tasks.deadline')" width="120">
          <template #default="{ row }">
            <span :class="{ overdue: isOverdue(row.due_date) && row.status !== 'done' }">
              {{ row.due_date ? formatDate(row.due_date) : $t('tasks.none') }}
            </span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.actions')" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status !== 'done'"
              type="success"
              size="small"
              @click="completeTask(row)"
            >
              {{ $t('tasks.complete') }}
            </el-button>
            <el-button text size="small" @click="viewTask(row)">{{ $t('common.view') }}</el-button>
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
    <el-dialog v-model="showCreateDialog" :title="$t('tasks.newTask')" width="600px">
      <el-form :model="form" label-width="80px">
        <el-form-item :label="$t('tasks.taskTitle')">
          <el-input v-model="form.title" :placeholder="$t('tasks.searchPlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('tasks.project')">
          <el-select v-model="form.project_id" :placeholder="$t('tasks.selectProject')" style="width: 100%;">
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('tasks.priority')">
          <el-select v-model="form.priority" style="width: 100%;">
            <el-option :label="$t('tasks.urgent')" value="urgent" />
            <el-option :label="$t('tasks.high')" value="high" />
            <el-option :label="$t('tasks.medium')" value="medium" />
            <el-option :label="$t('tasks.low')" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('tasks.deadline')">
          <el-date-picker
            v-model="form.due_date"
            type="datetime"
            :placeholder="$t('tasks.selectDeadline')"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item :label="$t('tasks.description')">
          <el-input
            v-model="form.description"
            type="textarea"
            rows="3"
            :placeholder="$t('tasks.descriptionPlaceholder')"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="createTask" :loading="creating">{{ $t('common.create') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { getTasks, createTask as apiCreateTask, updateTask } from '@/api/tasks'
import { getProjects } from '@/api/projects'

const router = useRouter()
const { t } = useI18n()

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
    console.error(t('tasks.fetchFailed'), error)
  } finally {
    loading.value = false
  }
}

const fetchProjects = async () => {
  try {
    const res = await getProjects({ per_page: 100 })
    projects.value = res.projects
  } catch (error) {
    console.error(t('tasks.fetchProjectsFailed'), error)
  }
}

const getProjectName = (projectId) => {
  const project = projects.value.find(p => p.id === projectId)
  return project?.name || t('tasks.unknownProject')
}

const resetFilter = () => {
  filterForm.value = { status: '', priority: '', search: '' }
  fetchTasks()
}

const createTask = async () => {
  if (!form.value.title || !form.value.project_id) {
    ElMessage.warning(t('tasks.fillRequired'))
    return
  }
  
  creating.value = true
  try {
    await apiCreateTask(form.value)
    ElMessage.success(t('tasks.createSuccess'))
    showCreateDialog.value = false
    fetchTasks()
    form.value = { title: '', project_id: '', priority: 'medium', due_date: '', description: '' }
  } catch (error) {
    console.error(t('tasks.createFailed'), error)
  } finally {
    creating.value = false
  }
}

const completeTask = async (row) => {
  try {
    await updateTask(row.id, { status: 'done' })
    ElMessage.success(t('tasks.completeSuccess'))
    fetchTasks()
  } catch (error) {
    console.error(t('tasks.completeFailed'), error)
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
  const labelMap = { urgent: t('tasks.urgent'), high: t('tasks.high'), medium: t('tasks.medium'), low: t('tasks.low') }
  return labelMap[priority] || priority
}

const getStatusType = (status) => {
  const typeMap = { todo: 'info', in_progress: 'warning', review: 'primary', done: 'success' }
  return typeMap[status] || ''
}

const getStatusLabel = (status) => {
  const labelMap = { todo: t('tasks.todo'), in_progress: t('tasks.inProgress'), review: t('tasks.inReview'), done: t('tasks.done') }
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
