<template>
  <div class="projects-page">
    <div class="page-header">
      <h2>项目管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>新建项目
      </el-button>
    </div>

    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索项目名、成员、客户、负责人..."
        clearable
        :prefix-icon="SearchIcon"
        @keyup.enter="handleSearch"
        style="width: 400px;"
      />
      <el-button type="primary" @click="handleSearch">
        <el-icon><Search /></el-icon>搜索
      </el-button>
      <el-button @click="resetSearch">重置</el-button>
    </div>

    <!-- 项目列表 -->
    <el-row :gutter="20">
      <el-col
        v-for="project in projects"
        :key="project.id"
        :xs="24"
        :sm="12"
        :lg="8"
        :xl="6"
        class="project-col"
      >
        <el-card class="project-card" shadow="hover">
          <div class="project-header" @click="goToProject(project.id)">
            <div class="project-color" :style="{ background: project.color }"></div>
            <div class="project-info">
              <h3 class="project-name">{{ project.name }}</h3>
              <p class="project-desc">{{ project.description || '暂无描述' }}</p>
            </div>
          </div>
          
          <div class="project-meta">
            <div class="meta-item" v-if="project.leader">
              <el-icon><UserFilled /></el-icon>
              <span>负责人：{{ project.leader.real_name }}</span>
            </div>
            <div class="meta-item" v-if="project.client">
              <el-icon><OfficeBuilding /></el-icon>
              <span>客户：{{ project.client.name }}</span>
            </div>
            <div class="meta-item" v-if="project.start_date || project.end_date">
              <el-icon><Calendar /></el-icon>
              <span>{{ formatDateRange(project.start_date, project.end_date) }}</span>
            </div>
          </div>
          
          <div class="project-stats">
            <div class="stat-item">
              <span class="stat-label">任务</span>
              <span class="stat-value">{{ project.stats?.total || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">已完成</span>
              <span class="stat-value success">{{ project.stats?.done || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">进度</span>
              <span class="stat-value primary">{{ project.stats?.progress || 0 }}%</span>
            </div>
          </div>
          
          <div class="project-footer">
            <div class="project-members">
              <el-avatar
                v-for="member in project.members?.slice(0, 3)"
                :key="member.id"
                :size="28"
                :src="member.avatar"
                :title="member.real_name"
              >
                {{ member.real_name?.charAt(0) }}
              </el-avatar>
              <el-avatar v-if="project.members?.length > 3" :size="28">
                +{{ project.members.length - 3 }}
              </el-avatar>
            </div>
            <div class="project-actions">
              <el-button 
                text 
                size="small" 
                type="danger" 
                @click.stop="handleDelete(project)"
                v-if="canDelete(project)"
              >
                <el-icon><Delete /></el-icon>删除
              </el-button>
            </div>
          </div>
          <el-progress
            :percentage="project.stats?.progress || 0"
            :show-text="false"
            :stroke-width="4"
            :color="project.color"
            style="margin-top: 8px;"
          />
        </el-card>
      </el-col>
    </el-row>

    <el-empty v-if="projects.length === 0" description="暂无项目" />

    <!-- 新建项目对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建项目" width="600px">
      <el-form :model="form" label-width="100px" :rules="rules" ref="formRef">
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="项目描述">
          <el-input
            v-model="form.description"
            type="textarea"
            rows="3"
            placeholder="请输入项目描述"
          />
        </el-form-item>
        <el-form-item label="项目负责人">
          <el-select v-model="form.leader_id" placeholder="选择项目负责人" style="width: 100%;">
            <el-option
              v-for="user in users"
              :key="user.id"
              :label="user.real_name"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="项目颜色">
          <el-color-picker v-model="form.color" />
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker
            v-model="form.start_date"
            type="date"
            placeholder="选择开始日期"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker
            v-model="form.end_date"
            type="date"
            placeholder="选择结束日期"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="关联客户">
          <el-select
            v-model="form.client_id"
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
        <el-form-item label="项目成员">
          <el-select
            v-model="form.member_ids"
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
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getProjects, createProject, deleteProject } from '@/api/projects'
import { getUsers } from '@/api/users'
import { getClientOptions } from '@/api/clients'
import { useUserStore } from '@/stores/user'
import { Search as SearchIcon, Calendar } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

const projects = ref([])
const users = ref([])
const clientOptions = ref([])
const showCreateDialog = ref(false)
const creating = ref(false)
const formRef = ref(null)
const searchQuery = ref('')

const form = ref({
  name: '',
  description: '',
  color: '#1890ff',
  start_date: '',
  end_date: '',
  client_id: '',
  leader_id: '',
  member_ids: []
})

const rules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }]
}

const fetchProjects = async () => {
  try {
    const params = {}
    if (searchQuery.value) {
      params.search = searchQuery.value
    }
    const res = await getProjects(params)
    projects.value = res.projects
  } catch (error) {
    console.error('获取项目失败', error)
  }
}

const handleSearch = () => {
  fetchProjects()
}

const resetSearch = () => {
  searchQuery.value = ''
  fetchProjects()
}

const fetchUsers = async () => {
  try {
    const res = await getUsers({ per_page: 100 })
    users.value = res.users
  } catch (error) {
    console.error('获取用户失败', error)
  }
}

const handleCreate = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  creating.value = true
  try {
    await createProject(form.value)
    ElMessage.success('项目创建成功')
    showCreateDialog.value = false
    fetchProjects()
    form.value = {
      name: '',
      description: '',
      color: '#1890ff',
      start_date: '',
      end_date: '',
      client_id: '',
      leader_id: '',
      member_ids: []
    }
  } catch (error) {
    console.error('创建项目失败', error)
    ElMessage.error(error.response?.data?.message || '创建失败')
  } finally {
    creating.value = false
  }
}

const goToProject = (id) => {
  router.push(`/projects/${id}`)
}

const formatDateRange = (start, end) => {
  if (!start && !end) return ''
  const s = start ? start.slice(5) : '?'  // MM-DD
  const e = end ? end.slice(5) : '?'
  return `${s} ~ ${e}`
}

const formatFullDate = (dateStr) => {
  if (!dateStr) return ''
  return dateStr  // YYYY-MM-DD
}

const canDelete = (project) => {
  return project.leader_id === userStore.userInfo?.id || userStore.hasPermission('project_manage')
}

const handleDelete = async (project) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除项目 "${project.name}" 吗？`,
      '确认删除',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
    await deleteProject(project.id)
    ElMessage.success('项目已删除')
    fetchProjects()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除项目失败', error)
      ElMessage.error(error.response?.data?.message || '删除失败')
    }
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

onMounted(() => {
  fetchProjects()
  fetchUsers()
  fetchClientOptions()
})
</script>

<style scoped lang="scss">
.projects-page {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }

  .search-bar {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
    padding: 16px;
    background: #fff;
    border-radius: 8px;
  }
  
  .project-col {
    margin-bottom: 20px;
  }
  
  .project-card {
    transition: all 0.3s;
    
    &:hover {
      transform: translateY(-4px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
    }
    
    .project-header {
      display: flex;
      gap: 12px;
      margin-bottom: 12px;
      cursor: pointer;
      
      .project-color {
        width: 48px;
        height: 48px;
        border-radius: 8px;
        flex-shrink: 0;
      }
      
      .project-info {
        flex: 1;
        min-width: 0;
        
        .project-name {
          font-size: 16px;
          font-weight: 500;
          margin-bottom: 4px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        
        .project-desc {
          font-size: 12px;
          color: #999;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
      }
    }

    .project-meta {
      display: flex;
      flex-direction: column;
      gap: 4px;
      margin-bottom: 12px;
      padding: 8px 0;
      border-top: 1px solid #f0f0f0;
      
      .meta-item {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 12px;
        color: #666;
      }
    }
    
    .project-stats {
      display: flex;
      justify-content: space-around;
      padding: 12px 0;
      border-top: 1px solid #eee;
      border-bottom: 1px solid #eee;
      margin-bottom: 12px;
      
      .stat-item {
        text-align: center;
        
        .stat-label {
          display: block;
          font-size: 12px;
          color: #999;
          margin-bottom: 4px;
        }
        
        .stat-value {
          font-size: 18px;
          font-weight: 500;
          
          &.success {
            color: #67c23a;
          }
          
          &.primary {
            color: #1890ff;
          }
        }
      }
    }
    
    .project-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .project-members {
        display: flex;
        
        .el-avatar {
          margin-right: -8px;
          border: 2px solid #fff;
        }
      }

      .project-actions {
        opacity: 0;
        transition: opacity 0.2s;
      }
    }

    &:hover .project-actions {
      opacity: 1;
    }
  }
}
</style>
