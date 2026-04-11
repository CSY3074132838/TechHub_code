<template>
  <div class="projects-page">
    <div class="page-header">
      <h2>项目管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>新建项目
      </el-button>
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
        <el-card class="project-card" shadow="hover" @click="goToProject(project.id)">
          <div class="project-header">
            <div class="project-color" :style="{ background: project.color }"></div>
            <div class="project-info">
              <h3 class="project-name">{{ project.name }}</h3>
              <p class="project-desc">{{ project.description || '暂无描述' }}</p>
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
            <el-progress
              :percentage="project.stats?.progress || 0"
              :show-text="false"
              :stroke-width="4"
              :color="project.color"
            />
          </div>
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
import { ElMessage } from 'element-plus'
import { getProjects, createProject } from '@/api/projects'
import { getUsers } from '@/api/users'

const router = useRouter()

const projects = ref([])
const users = ref([])
const showCreateDialog = ref(false)
const creating = ref(false)
const formRef = ref(null)

const form = ref({
  name: '',
  description: '',
  color: '#1890ff',
  start_date: '',
  end_date: '',
  member_ids: []
})

const rules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }]
}

const fetchProjects = async () => {
  try {
    const res = await getProjects()
    projects.value = res.projects
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
      member_ids: []
    }
  } catch (error) {
    console.error('创建项目失败', error)
  } finally {
    creating.value = false
  }
}

const goToProject = (id) => {
  router.push(`/projects/${id}`)
}

onMounted(() => {
  fetchProjects()
  fetchUsers()
})
</script>

<style scoped lang="scss">
.projects-page {
  .project-col {
    margin-bottom: 20px;
  }
  
  .project-card {
    cursor: pointer;
    transition: all 0.3s;
    
    &:hover {
      transform: translateY(-4px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
    }
    
    .project-header {
      display: flex;
      gap: 12px;
      margin-bottom: 16px;
      
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
      .project-members {
        display: flex;
        margin-bottom: 8px;
        
        .el-avatar {
          margin-right: -8px;
          border: 2px solid #fff;
        }
      }
    }
  }
}
</style>
