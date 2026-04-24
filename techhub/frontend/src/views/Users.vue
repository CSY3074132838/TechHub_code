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

    <!-- 角色管理卡片 -->
    <el-card class="roles-card" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>角色管理</span>
          <el-button type="primary" size="small" @click="showRoleDialog = true">
            <el-icon><Plus /></el-icon>新增角色
          </el-button>
        </div>
      </template>
      
      <el-table :data="roles" size="small" border>
        <el-table-column label="角色名称" prop="description" min-width="150" />
        <el-table-column label="标识" prop="name" width="150" />
        <el-table-column label="等级" prop="level" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="权限" min-width="300">
          <template #default="{ row }">
            <el-tag
              v-for="perm in row.permissions"
              :key="perm"
              size="small"
              type="info"
              style="margin-right: 4px;"
            >
              {{ perm }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button text size="small" @click="editRole(row)">编辑</el-button>
            <el-button text type="danger" size="small" @click="removeRole(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
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

    <!-- 添加/编辑角色对话框 -->
    <el-dialog
      v-model="showRoleDialog"
      :title="isEditRole ? '编辑角色' : '新增角色'"
      width="500px"
    >
      <el-form :model="roleForm" label-width="100px">
        <el-form-item label="角色标识">
          <el-input v-model="roleForm.name" placeholder="如：project_manager" :disabled="isEditRole" />
        </el-form-item>
        <el-form-item label="角色名称">
          <el-input v-model="roleForm.description" placeholder="如：项目经理" />
        </el-form-item>
        <el-form-item label="等级">
          <el-input-number v-model="roleForm.level" :min="1" :max="10" />
        </el-form-item>
        <el-form-item label="权限">
          <el-select v-model="roleForm.permissions" multiple placeholder="选择权限" style="width: 100%;">
            <el-option label="全部权限" value="all" />
            <el-option label="仪表盘查看" value="dashboard_view" />
            <el-option label="团队管理" value="team_manage" />
            <el-option label="紧急审批" value="approval_urgent" />
            <el-option label="项目管理" value="project_manage" />
            <el-option label="任务分配" value="task_assign" />
            <el-option label="团队查看" value="team_view" />
            <el-option label="任务查看" value="task_view" />
            <el-option label="任务执行" value="task_execute" />
            <el-option label="审批提交" value="approval_submit" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRoleDialog = false">取消</el-button>
        <el-button type="primary" @click="saveRole" :loading="savingRole">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUsers, updateUser, getUserStats, getRoles, createRole, updateRole, deleteRole } from '@/api/users'

const users = ref([])
const roles = ref([])
const stats = ref({})
const loading = ref(false)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

const showCreateDialog = ref(false)
const showRoleDialog = ref(false)
const isEdit = ref(false)
const isEditRole = ref(false)
const saving = ref(false)
const savingRole = ref(false)

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

const roleForm = ref({
  id: '',
  name: '',
  description: '',
  level: 4,
  permissions: []
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
    stats.value = res
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
  if (!isEdit.value && (!form.value.username || !form.value.email)) {
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

const editRole = (role) => {
  isEditRole.value = true
  roleForm.value = {
    id: role.id,
    name: role.name,
    description: role.description,
    level: role.level,
    permissions: role.permissions || []
  }
  showRoleDialog.value = true
}

const removeRole = async (role) => {
  try {
    await ElMessageBox.confirm(`确定要删除角色 "${role.description}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteRole(role.id)
    ElMessage.success('角色已删除')
    fetchRoles()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '删除失败')
    }
  }
}

const saveRole = async () => {
  if (!roleForm.value.name || !roleForm.value.description) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  savingRole.value = true
  try {
    if (isEditRole.value) {
      await updateRole(roleForm.value.id, {
        name: roleForm.value.name,
        description: roleForm.value.description,
        level: roleForm.value.level,
        permissions: roleForm.value.permissions
      })
      ElMessage.success('角色更新成功')
    } else {
      await createRole({
        name: roleForm.value.name,
        description: roleForm.value.description,
        level: roleForm.value.level,
        permissions: roleForm.value.permissions
      })
      ElMessage.success('角色创建成功')
    }
    showRoleDialog.value = false
    roleForm.value = { id: '', name: '', description: '', level: 4, permissions: [] }
    fetchRoles()
  } catch (error) {
    console.error('保存角色失败', error)
    ElMessage.error(error.response?.data?.message || '保存失败')
  } finally {
    savingRole.value = false
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
