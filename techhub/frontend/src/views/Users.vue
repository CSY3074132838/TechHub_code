<template>
  <div class="users-page">
    <div class="page-header">
      <h2>用户管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>添加用户
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="8">
        <div class="stat-card">
          <div class="stat-value">{{ stats.total || 0 }}</div>
          <div class="stat-label">总用户</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="8">
        <div class="stat-card">
          <div class="stat-value success">{{ stats.active || 0 }}</div>
          <div class="stat-label">活跃用户</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="8">
        <div class="stat-card">
          <div class="stat-value warning">{{ (stats.total || 0) - (stats.active || 0) }}</div>
          <div class="stat-label">非活跃用户</div>
        </div>
      </el-col>
    </el-row>

    <!-- 用户列表 -->
    <el-card class="users-list">
      <el-table :data="users" v-loading="loading" stripe>
        <el-table-column label="用户" min-width="200">
          <template #default="{ row }">
            <div class="user-cell">
              <el-avatar :size="40" :src="row.avatar">
                {{ row.real_name?.charAt(0) || row.username?.charAt(0) }}
              </el-avatar>
              <div class="user-info">
                <div class="name">{{ row.real_name || row.username }}</div>
                <div class="email">{{ row.email }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="部门" width="120">
          <template #default="{ row }">
            {{ row.department || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="职位" width="120">
          <template #default="{ row }">
            {{ row.position || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="角色" width="150">
          <template #default="{ row }">
            <el-tag
              v-for="role in row.roles"
              :key="role.id"
              size="small"
              style="margin-right: 4px;"
            >
              {{ role.description }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button text size="small" @click="editUser(row)">编辑</el-button>
            <el-button
              :type="row.is_active ? 'danger' : 'success'"
              text
              size="small"
              @click="toggleStatus(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
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
          @size-change="fetchUsers"
          @current-change="fetchUsers"
        />
      </div>
    </el-card>

    <!-- 添加/编辑用户对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="isEdit ? '编辑用户' : '添加用户'"
      width="600px"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="请输入用户名" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" placeholder="请输入邮箱" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="密码" v-if="!isEdit">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" />
        </el-form-item>
        <el-form-item label="真实姓名">
          <el-input v-model="form.real_name" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item label="部门">
          <el-input v-model="form.department" placeholder="请输入部门" />
        </el-form-item>
        <el-form-item label="职位">
          <el-input v-model="form.position" placeholder="请输入职位" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role_ids" multiple placeholder="选择角色" style="width: 100%;">
            <el-option
              v-for="role in roles"
              :key="role.id"
              :label="role.description"
              :value="role.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveUser" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUsers, updateUser, getUserStats, getRoles } from '@/api/users'

const users = ref([])
const roles = ref([])
const stats = ref({})
const loading = ref(false)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

const showCreateDialog = ref(false)
const isEdit = ref(false)
const saving = ref(false)

const form = ref({
  id: '',
  username: '',
  email: '',
  password: '',
  real_name: '',
  department: '',
  position: '',
  role_ids: []
})

const fetchUsers = async () => {
  loading.value = true
  try {
    const res = await getUsers({ page: page.value, per_page: pageSize.value })
    users.value = res.users
    total.value = res.total
  } catch (error) {
    console.error('获取用户失败', error)
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const res = await getUserStats()
    stats.value = res.data
  } catch (error) {
    console.error('获取统计失败', error)
  }
}

const fetchRoles = async () => {
  try {
    const res = await getRoles()
    roles.value = res.roles
  } catch (error) {
    console.error('获取角色失败', error)
  }
}

const editUser = (row) => {
  isEdit.value = true
  form.value = {
    id: row.id,
    username: row.username,
    email: row.email,
    password: '',
    real_name: row.real_name,
    department: row.department,
    position: row.position,
    role_ids: row.roles.map(r => r.id)
  }
  showCreateDialog.value = true
}

const saveUser = async () => {
  if (!form.value.username || !form.value.email) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  saving.value = true
  try {
    if (isEdit.value) {
      await updateUser(form.value.id, {
        real_name: form.value.real_name,
        department: form.value.department,
        position: form.value.position,
        roles: form.value.role_ids
      })
      ElMessage.success('用户更新成功')
    }
    showCreateDialog.value = false
    fetchUsers()
  } catch (error) {
    console.error('保存用户失败', error)
  } finally {
    saving.value = false
  }
}

const toggleStatus = async (row) => {
  const action = row.is_active ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(`确定要${action}该用户吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await updateUser(row.id, { is_active: !row.is_active })
    ElMessage.success(`${action}成功`)
    fetchUsers()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(`${action}用户失败`, error)
    }
  }
}

onMounted(() => {
  fetchUsers()
  fetchStats()
  fetchRoles()
})
</script>

<style scoped lang="scss">
.users-page {
  .stats-row {
    margin-bottom: 20px;
    
    .stat-card {
      background: #fff;
      border-radius: 8px;
      padding: 20px;
      text-align: center;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
      
      .stat-value {
        font-size: 28px;
        font-weight: 600;
        color: #1890ff;
        margin-bottom: 8px;
        
        &.success {
          color: #67c23a;
        }
        
        &.warning {
          color: #e6a23c;
        }
      }
      
      .stat-label {
        font-size: 14px;
        color: #666;
      }
    }
  }
  
  .users-list {
    .user-cell {
      display: flex;
      align-items: center;
      gap: 12px;
      
      .user-info {
        .name {
          font-weight: 500;
        }
        
        .email {
          font-size: 12px;
          color: #999;
        }
      }
    }
    
    .pagination {
      margin-top: 20px;
      display: flex;
      justify-content: flex-end;
    }
  }
}
</style>
