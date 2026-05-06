<template>
  <div class="users-page">
    <div class="page-header">
      <h2>用户管理</h2>
      <div class="header-actions">
        <!-- 【第二次迭代】批量导入导出按钮 -->
        <el-button size="small" @click="handleExport" v-if="userStore.hasPermission('user_manage')">
          <el-icon><Download /></el-icon>导出
        </el-button>
        <el-button type="primary" @click="showCreateDialog = true" v-if="userStore.hasPermission('user_manage')">
          <el-icon><Plus /></el-icon>添加用户
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ stats.total || 0 }}</div>
          <div class="stat-label">总用户</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value success">{{ stats.active || 0 }}</div>
          <div class="stat-label">活跃用户</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value warning">{{ stats.new_this_month || 0 }}</div>
          <div class="stat-label">本月入职</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value info">{{ stats.inactive || 0 }}</div>
          <div class="stat-label">非活跃用户</div>
        </div>
      </el-col>
    </el-row>

    <!-- 【第二次迭代】高级筛选栏 -->
    <el-card class="filter-card" style="margin-bottom: 20px;">
      <el-row :gutter="12" align="middle">
        <el-col :xs="24" :sm="6">
          <el-input v-model="filter.search" placeholder="搜索：姓名/用户名/邮箱/手机/工号" clearable @change="handleFilterChange">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </el-col>
        <el-col :xs="12" :sm="4">
          <el-select v-model="filter.department_id" placeholder="选择部门" clearable @change="handleFilterChange" style="width: 100%">
            <el-option v-for="dept in flatDepartments" :key="dept.id" :label="dept.name" :value="dept.id" />
          </el-select>
        </el-col>
        <el-col :xs="12" :sm="4">
          <el-select v-model="filter.employee_status" placeholder="员工状态" clearable @change="handleFilterChange" style="width: 100%">
            <el-option label="试用期" value="probation" />
            <el-option label="正式员工" value="active" />
            <el-option label="待离职" value="pending_leave" />
            <el-option label="已离职" value="left" />
          </el-select>
        </el-col>
        <el-col :xs="12" :sm="4">
          <el-select v-model="filter.role_id" placeholder="角色" clearable @change="handleFilterChange" style="width: 100%">
            <el-option v-for="role in roles" :key="role.id" :label="role.description" :value="role.id" />
          </el-select>
        </el-col>
        <el-col :xs="12" :sm="4">
          <el-select v-model="filter.is_active" placeholder="账号状态" clearable @change="handleFilterChange" style="width: 100%">
            <el-option label="正常" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="2">
          <el-button text type="primary" @click="resetFilter">重置</el-button>
        </el-col>
      </el-row>
    </el-card>

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
                <!-- 【第二次迭代】显示工号 -->
                <div class="employee-no" v-if="row.employee_no">工号: {{ row.employee_no }}</div>
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
        <!-- 【第二次迭代】员工状态列 -->
        <el-table-column label="员工状态" width="100">
          <template #default="{ row }">
            <el-tag :type="employeeStatusType(row.employee_status)" size="small">
              {{ employeeStatusLabel(row.employee_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button text size="small" @click="viewDetail(row)">详情</el-button>
            <el-button text size="small" @click="editUser(row)">编辑</el-button>
            <el-button
              v-if="userStore.hasPermission('user_manage')"
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
          <el-button type="primary" size="small" @click="showRoleDialog = true" v-if="userStore.hasPermission('role_manage')">
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
            <el-button v-if="userStore.hasPermission('role_manage')" text type="danger" size="small" @click="removeRole(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 【第二次迭代】用户详情抽屉 -->
    <el-drawer v-model="showDetailDrawer" title="员工档案" size="600px" :destroy-on-close="true">
      <div v-if="detailUser" class="user-detail">
        <div class="detail-header">
          <el-avatar :size="64" :src="detailUser.avatar">
            {{ detailUser.real_name?.charAt(0) || detailUser.username?.charAt(0) }}
          </el-avatar>
          <div class="detail-header-info">
            <h3>{{ detailUser.real_name || detailUser.username }}</h3>
            <p>{{ detailUser.employee_no ? `工号：${detailUser.employee_no}` : '' }}</p>
            <div class="detail-tags">
              <el-tag v-for="role in detailUser.roles" :key="role.id" size="small">{{ role.description }}</el-tag>
              <el-tag :type="detailUser.is_active ? 'success' : 'info'" size="small">{{ detailUser.is_active ? '正常' : '禁用' }}</el-tag>
            </div>
          </div>
        </div>
        <el-divider />
        <el-descriptions :column="2" border>
          <el-descriptions-item label="用户名">{{ detailUser.username }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ detailUser.email }}</el-descriptions-item>
          <el-descriptions-item label="电话">{{ detailUser.phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="部门">{{ detailUser.department || '-' }}</el-descriptions-item>
          <el-descriptions-item label="职位">{{ detailUser.position || '-' }}</el-descriptions-item>
          <!-- 【第二次迭代】扩展档案字段 -->
          <el-descriptions-item label="员工状态">{{ employeeStatusLabel(detailUser.employee_status) }}</el-descriptions-item>
          <el-descriptions-item label="入职日期">{{ detailUser.entry_date || '-' }}</el-descriptions-item>
          <el-descriptions-item label="转正日期">{{ detailUser.probation_end_date || '-' }}</el-descriptions-item>
          <el-descriptions-item label="离职日期">{{ detailUser.leave_date || '-' }}</el-descriptions-item>
          <el-descriptions-item label="性别">{{ detailUser.gender || '-' }}</el-descriptions-item>
          <el-descriptions-item label="生日">{{ detailUser.birthday || '-' }}</el-descriptions-item>
          <el-descriptions-item label="籍贯">{{ detailUser.native_place || '-' }}</el-descriptions-item>
          <el-descriptions-item label="学历">{{ detailUser.education || '-' }}</el-descriptions-item>
          <el-descriptions-item label="毕业院校">{{ detailUser.school || '-' }}</el-descriptions-item>
          <el-descriptions-item label="专业">{{ detailUser.major || '-' }}</el-descriptions-item>
          <el-descriptions-item label="紧急联系人">{{ detailUser.emergency_contact || '-' }}</el-descriptions-item>
          <el-descriptions-item label="紧急电话">{{ detailUser.emergency_phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="现居地址" :span="2">{{ detailUser.address || '-' }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-drawer>

    <!-- 添加/编辑用户对话框 -->
    <el-dialog v-model="showCreateDialog" :title="isEdit ? '编辑用户' : '添加用户'" width="700px">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="基本信息" name="basic">
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
            <el-form-item label="工号">
              <el-input v-model="form.employee_no" placeholder="如：TECH-2025-001" />
            </el-form-item>
            <el-form-item label="部门">
              <el-input v-model="form.department" placeholder="请输入部门" />
            </el-form-item>
            <el-form-item label="职位">
              <el-input v-model="form.position" placeholder="请输入职位" />
            </el-form-item>
            <el-form-item label="电话">
              <el-input v-model="form.phone" placeholder="请输入电话" />
            </el-form-item>
            <el-form-item label="角色">
              <el-select v-model="form.role_ids" multiple placeholder="选择角色" style="width: 100%;">
                <el-option v-for="role in roles" :key="role.id" :label="role.description" :value="role.id" />
              </el-select>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        <!-- 【第二次迭代】员工档案详情 Tab -->
        <el-tab-pane label="档案详情" name="detail" v-if="isEdit">
          <el-form :model="detailForm" label-width="100px">
            <el-form-item label="员工状态">
              <el-select v-model="detailForm.employee_status" placeholder="选择状态" style="width: 100%">
                <el-option label="试用期" value="probation" />
                <el-option label="正式员工" value="active" />
                <el-option label="待离职" value="pending_leave" />
                <el-option label="已离职" value="left" />
                <el-option label="停薪留职" value="suspended" />
              </el-select>
            </el-form-item>
            <el-form-item label="入职日期">
              <el-date-picker v-model="detailForm.entry_date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
            <el-form-item label="转正日期">
              <el-date-picker v-model="detailForm.probation_end_date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
            <el-form-item label="身份证号">
              <el-input v-model="detailForm.id_card" placeholder="请输入身份证号" />
            </el-form-item>
            <el-form-item label="性别">
              <el-radio-group v-model="detailForm.gender">
                <el-radio label="男">男</el-radio>
                <el-radio label="女">女</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="学历">
              <el-select v-model="detailForm.education" placeholder="选择学历" clearable style="width: 100%">
                <el-option label="高中及以下" value="高中及以下" />
                <el-option label="大专" value="大专" />
                <el-option label="本科" value="本科" />
                <el-option label="硕士" value="硕士" />
                <el-option label="博士" value="博士" />
              </el-select>
            </el-form-item>
            <el-form-item label="毕业院校">
              <el-input v-model="detailForm.school" placeholder="请输入毕业院校" />
            </el-form-item>
            <el-form-item label="专业">
              <el-input v-model="detailForm.major" placeholder="请输入专业" />
            </el-form-item>
            <el-form-item label="紧急联系人">
              <el-input v-model="detailForm.emergency_contact" placeholder="请输入紧急联系人姓名" />
            </el-form-item>
            <el-form-item label="紧急电话">
              <el-input v-model="detailForm.emergency_phone" placeholder="请输入紧急联系人电话" />
            </el-form-item>
            <el-form-item label="现居地址">
              <el-input v-model="detailForm.address" type="textarea" :rows="2" placeholder="请输入现居地址" />
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveUser" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 添加/编辑角色对话框 -->
    <el-dialog v-model="showRoleDialog" :title="isEditRole ? '编辑角色' : '新增角色'" width="500px">
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
            <el-option v-for="perm in permissionOptions" :key="perm.code" :label="perm.label" :value="perm.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="数据范围">
          <el-select v-model="roleForm.data_scope" placeholder="选择数据范围" style="width: 100%;">
            <el-option label="全部数据" value="all" />
            <el-option label="本部门数据" value="dept" />
            <el-option label="本部门及子部门" value="dept_and_below" />
            <el-option label="仅自己的数据" value="self" />
            <el-option label="自定义" value="custom" />
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
import { useUserStore } from '@/stores/user'
import { getUsers, updateUser, getUserStats, getRoles, createRole, updateRole, deleteRole, getPermissions, exportUsers } from '@/api/users'
import { getDepartmentsFlat } from '@/api/departments'

const userStore = useUserStore()
const users = ref([])
const roles = ref([])
const stats = ref({})
const loading = ref(false)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 【第二次迭代】高级筛选
const filter = ref({
  search: '',
  department_id: '',
  employee_status: '',
  role_id: '',
  is_active: ''
})
const flatDepartments = ref([])

const showCreateDialog = ref(false)
const showDetailDrawer = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const activeTab = ref('basic')
const detailUser = ref(null)

const form = ref({
  id: '',
  username: '',
  email: '',
  password: '',
  real_name: '',
  employee_no: '',
  department: '',
  position: '',
  role_ids: []
})

// 【第二次迭代】档案详情表单
const detailForm = ref({
  employee_status: 'probation',
  entry_date: '',
  probation_end_date: '',
  id_card: '',
  gender: '',
  education: '',
  school: '',
  major: '',
  emergency_contact: '',
  emergency_phone: '',
  address: ''
})

const showRoleDialog = ref(false)
const isEditRole = ref(false)
const savingRole = ref(false)
const permissionOptions = ref([])

const roleForm = ref({
  id: '',
  name: '',
  description: '',
  level: 4,
  permissions: [],
  data_scope: 'self',
  data_scope_custom: []
})

const fetchUsers = async () => {
  loading.value = true
  try {
    const params = {
      page: page.value,
      per_page: pageSize.value,
      ...filter.value
    }
    const res = await getUsers(params)
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

// 【第二次迭代】获取部门列表
const fetchDepartments = async () => {
  try {
    const res = await getDepartmentsFlat()
    flatDepartments.value = res.departments || []
  } catch (error) {
    console.error('获取部门失败', error)
  }
}

const handleFilterChange = () => {
  page.value = 1
  fetchUsers()
}

const resetFilter = () => {
  filter.value = { search: '', department_id: '', employee_status: '', role_id: '', is_active: '' }
  handleFilterChange()
}

// 【第二次迭代】查看用户详情抽屉
const viewDetail = async (row) => {
  try {
    const res = await getUser(row.id, true)
    detailUser.value = res.user || row
    showDetailDrawer.value = true
  } catch (error) {
    detailUser.value = row
    showDetailDrawer.value = true
  }
}

const editUser = (row) => {
  isEdit.value = true
  activeTab.value = 'basic'
  form.value = {
    id: row.id,
    username: row.username,
    email: row.email,
    password: '',
    real_name: row.real_name,
    employee_no: row.employee_no || '',
    department: row.department,
    position: row.position,
    role_ids: row.roles.map(r => r.id)
  }
  // 【第二次迭代】填充档案详情
  detailForm.value = {
    employee_status: row.employee_status || 'probation',
    entry_date: row.entry_date || '',
    probation_end_date: row.probation_end_date || '',
    id_card: row.id_card || '',
    gender: row.gender || '',
    education: row.education || '',
    school: row.school || '',
    major: row.major || '',
    emergency_contact: row.emergency_contact || '',
    emergency_phone: row.emergency_phone || '',
    address: row.address || ''
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
      const payload = {
        real_name: form.value.real_name,
        department: form.value.department,
        position: form.value.position,
        phone: form.value.phone,
        employee_no: form.value.employee_no,
        roles: form.value.role_ids,
        // 【第二次迭代】合并档案详情字段
        ...detailForm.value
      }
      const res = await updateUser(form.value.id, payload)
      ElMessage.success(res.message || '用户更新成功')
      if (res.require_relogin) {
        ElMessage.warning('您的权限已变更，请重新登录')
      }
    }
    showCreateDialog.value = false
    fetchUsers()
    fetchStats()
  } catch (error) {
    console.error('保存用户失败', error)
    ElMessage.error(error.response?.data?.message || '保存失败')
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

// 【第二次迭代】导出用户
const handleExport = async () => {
  try {
    const res = await exportUsers('json')
    const dataStr = JSON.stringify(res.users || res, null, 2)
    const blob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `users_export_${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

const editRole = (role) => {
  isEditRole.value = true
  roleForm.value = {
    id: role.id,
    name: role.name,
    description: role.description,
    level: role.level,
    permissions: role.permissions || [],
    data_scope: role.data_scope || 'self',
    data_scope_custom: role.data_scope_custom || []
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
    roleForm.value = { id: '', name: '', description: '', level: 4, permissions: [], data_scope: 'self', data_scope_custom: [] }
    fetchRoles()
  } catch (error) {
    console.error('保存角色失败', error)
    ElMessage.error(error.response?.data?.message || '保存失败')
  } finally {
    savingRole.value = false
  }
}

const fetchPermissions = async () => {
  try {
    const res = await getPermissions()
    permissionOptions.value = res.permissions || []
  } catch (error) {
    console.error('获取权限列表失败', error)
  }
}

// 【第二次迭代】员工状态显示转换
const employeeStatusLabel = (status) => {
  const map = {
    probation: '试用期',
    active: '正式',
    pending_leave: '待离职',
    left: '已离职',
    suspended: '停薪留职'
  }
  return map[status] || status || '试用期'
}

const employeeStatusType = (status) => {
  const map = {
    probation: 'warning',
    active: 'success',
    pending_leave: 'danger',
    left: 'info',
    suspended: 'info'
  }
  return map[status] || ''
}

onMounted(() => {
  fetchUsers()
  fetchStats()
  fetchRoles()
  fetchPermissions()
  fetchDepartments()
})
</script>

<style scoped lang="scss">
.users-page {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    h2 { margin: 0; }
    .header-actions {
      display: flex;
      gap: 8px;
    }
  }

  .stats-row {
    margin-bottom: 20px;
    .stat-card {
      background: #fff;
      border-radius: 8px;
      padding: 20px;
      text-align: center;
      box-shadow: 0 2px 12px rgba(0,0,0,0.05);
      .stat-value {
        font-size: 28px;
        font-weight: 600;
        color: #1890ff;
        margin-bottom: 8px;
        &.success { color: #67c23a; }
        &.warning { color: #e6a23c; }
        &.info { color: #909399; }
      }
      .stat-label {
        font-size: 14px;
        color: #666;
      }
    }
  }

  .filter-card {
    :deep(.el-card__body) {
      padding: 16px 20px;
    }
  }

  .users-list {
    .user-cell {
      display: flex;
      align-items: center;
      gap: 12px;
      .user-info {
        .name { font-weight: 500; }
        .email { font-size: 12px; color: #999; }
        .employee-no { font-size: 11px; color: #1890ff; }
      }
    }
    .pagination {
      margin-top: 20px;
      display: flex;
      justify-content: flex-end;
    }
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  // 【第二次迭代】用户详情抽屉样式
  .user-detail {
    .detail-header {
      display: flex;
      align-items: center;
      gap: 16px;
      .detail-header-info {
        h3 { margin: 0 0 4px; font-size: 18px; }
        p { margin: 0; font-size: 13px; color: #666; }
        .detail-tags {
          margin-top: 8px;
          display: flex;
          gap: 4px;
          flex-wrap: wrap;
        }
      }
    }
  }
}
</style>
