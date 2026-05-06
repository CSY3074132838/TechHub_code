<template>
  <!-- 【第二次迭代】组织架构管理页面 -->
  <div class="departments-page">
    <div class="page-header">
      <h2>组织架构</h2>
      <el-button type="primary" @click="openDialog()" v-if="userStore.hasPermission('user_manage')">
        <el-icon><Plus /></el-icon>添加部门
      </el-button>
    </div>

    <el-row :gutter="20">
      <!-- 左侧部门树 -->
      <el-col :xs="24" :md="8">
        <el-card>
          <template #header>
            <span>部门列表</span>
          </template>
          <el-tree
            :data="departmentTree"
            :props="{ label: 'name', children: 'children' }"
            node-key="id"
            default-expand-all
            highlight-current
            @node-click="handleNodeClick"
            v-loading="treeLoading"
          >
            <template #default="{ node, data }">
              <div class="dept-tree-node">
                <span>{{ node.label }}</span>
                <el-tag size="small" type="info">{{ data.total_member_count }}人</el-tag>
              </div>
            </template>
          </el-tree>
        </el-card>
      </el-col>

      <!-- 右侧部门详情与成员 -->
      <el-col :xs="24" :md="16">
        <!-- 部门概览卡片 -->
        <el-row :gutter="20" class="stats-row">
          <el-col :xs="12" :sm="8">
            <div class="stat-card">
              <div class="stat-value">{{ stats.total_departments || 0 }}</div>
              <div class="stat-label">部门总数</div>
            </div>
          </el-col>
          <el-col :xs="12" :sm="8">
            <div class="stat-card">
              <div class="stat-value success">{{ stats.total_members_with_dept || 0 }}</div>
              <div class="stat-label">已分配部门</div>
            </div>
          </el-col>
          <el-col :xs="12" :sm="8">
            <div class="stat-card">
              <div class="stat-value warning">{{ currentDept?.total_member_count || 0 }}</div>
              <div class="stat-label">当前部门人数</div>
            </div>
          </el-col>
        </el-row>

        <!-- 当前部门信息 -->
        <el-card v-if="currentDept" style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <span>{{ currentDept.name }}</span>
              <div v-if="userStore.hasPermission('user_manage')">
                <el-button text size="small" @click="openDialog(currentDept)">编辑</el-button>
                <el-button text type="danger" size="small" @click="removeDept(currentDept)">删除</el-button>
              </div>
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="部门编码">{{ currentDept.code }}</el-descriptions-item>
            <el-descriptions-item label="部门负责人">
              {{ currentDept.manager?.real_name || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="直属人数">{{ currentDept.member_count }}人</el-descriptions-item>
            <el-descriptions-item label="总人数（含子部门）">{{ currentDept.total_member_count }}人</el-descriptions-item>
            <el-descriptions-item label="描述" :span="2">{{ currentDept.description || '-' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 成员列表 -->
        <el-card style="margin-top: 20px;" v-if="currentDept">
          <template #header>
            <span>部门成员</span>
          </template>
          <el-table :data="members" v-loading="memberLoading" size="small">
            <el-table-column label="姓名" min-width="120">
              <template #default="{ row }">
                <div style="display: flex; align-items: center; gap: 8px;">
                  <el-avatar :size="28" :src="row.avatar">{{ row.real_name?.charAt(0) || 'U' }}</el-avatar>
                  <span>{{ row.real_name || row.username }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="职位" prop="position" width="120" />
            <el-table-column label="邮箱" prop="email" min-width="180" />
            <el-table-column label="电话" prop="phone" width="120" />
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
                  {{ row.is_active ? '正常' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination" v-if="memberTotal > memberPageSize">
            <el-pagination
              v-model:current-page="memberPage"
              v-model:page-size="memberPageSize"
              :total="memberTotal"
              layout="prev, pager, next"
              @current-change="fetchMembers"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 添加/编辑部门对话框 -->
    <el-dialog v-model="showDialog" :title="isEdit ? '编辑部门' : '添加部门'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="部门名称" required>
          <el-input v-model="form.name" placeholder="请输入部门名称" />
        </el-form-item>
        <el-form-item label="部门编码" required>
          <el-input v-model="form.code" placeholder="如：DEV-001" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="上级部门">
          <el-tree-select
            v-model="form.parent_id"
            :data="departmentTree"
            :props="{ label: 'name', value: 'id', children: 'children' }"
            placeholder="选择上级部门"
            check-strictly
            clearable
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="部门负责人">
          <el-select v-model="form.manager_id" placeholder="选择负责人" clearable style="width: 100%">
            <el-option
              v-for="user in managerOptions"
              :key="user.id"
              :label="user.real_name"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="排序号">
          <el-input-number v-model="form.sort_order" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="部门描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="saveDept" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { getDepartments, createDepartment, updateDepartment, deleteDepartment, getDepartmentMembers, getDepartmentStats } from '@/api/departments'
import { getManagers } from '@/api/users'

const userStore = useUserStore()
const departmentTree = ref([])
const treeLoading = ref(false)
const currentDept = ref(null)
const members = ref([])
const memberLoading = ref(false)
const memberPage = ref(1)
const memberPageSize = ref(10)
const memberTotal = ref(0)
const stats = ref({})
const managerOptions = ref([])

const showDialog = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const form = ref({
  id: '',
  name: '',
  code: '',
  parent_id: null,
  manager_id: null,
  sort_order: 0,
  description: ''
})

const fetchDepartments = async () => {
  treeLoading.value = true
  try {
    const res = await getDepartments()
    departmentTree.value = res.departments || []
  } catch (error) {
    console.error('获取部门失败', error)
  } finally {
    treeLoading.value = false
  }
}

const fetchStats = async () => {
  try {
    const res = await getDepartmentStats()
    stats.value = res
  } catch (error) {
    console.error('获取统计失败', error)
  }
}

const fetchMembers = async () => {
  if (!currentDept.value) return
  memberLoading.value = true
  try {
    const res = await getDepartmentMembers(currentDept.value.id, {
      page: memberPage.value,
      per_page: memberPageSize.value,
      include_sub: false
    })
    members.value = res.members || []
    memberTotal.value = res.total || 0
  } catch (error) {
    console.error('获取成员失败', error)
  } finally {
    memberLoading.value = false
  }
}

const handleNodeClick = (data) => {
  currentDept.value = data
  memberPage.value = 1
  fetchMembers()
}

const openDialog = (dept = null) => {
  isEdit.value = !!dept
  if (dept) {
    form.value = {
      id: dept.id,
      name: dept.name,
      code: dept.code,
      parent_id: dept.parent_id,
      manager_id: dept.manager_id,
      sort_order: dept.sort_order || 0,
      description: dept.description || ''
    }
  } else {
    form.value = { id: '', name: '', code: '', parent_id: null, manager_id: null, sort_order: 0, description: '' }
  }
  showDialog.value = true
}

const saveDept = async () => {
  if (!form.value.name || !form.value.code) {
    ElMessage.warning('请填写部门名称和编码')
    return
  }
  saving.value = true
  try {
    if (isEdit.value) {
      await updateDepartment(form.value.id, {
        name: form.value.name,
        description: form.value.description,
        parent_id: form.value.parent_id,
        manager_id: form.value.manager_id,
        sort_order: form.value.sort_order
      })
      ElMessage.success('部门更新成功')
    } else {
      await createDepartment({
        name: form.value.name,
        code: form.value.code,
        description: form.value.description,
        parent_id: form.value.parent_id,
        manager_id: form.value.manager_id,
        sort_order: form.value.sort_order
      })
      ElMessage.success('部门创建成功')
    }
    showDialog.value = false
    fetchDepartments()
    fetchStats()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

const removeDept = async (dept) => {
  try {
    await ElMessageBox.confirm(`确定要删除部门 "${dept.name}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteDepartment(dept.id)
    ElMessage.success('部门已删除')
    currentDept.value = null
    members.value = []
    fetchDepartments()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '删除失败')
    }
  }
}

const fetchManagers = async () => {
  try {
    const res = await getManagers()
    managerOptions.value = res.managers || []
  } catch (error) {
    console.error('获取负责人列表失败', error)
  }
}

onMounted(() => {
  fetchDepartments()
  fetchStats()
  fetchManagers()
})
</script>

<style scoped lang="scss">
.departments-page {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    h2 { margin: 0; }
  }

  .stats-row {
    margin-bottom: 0;
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
      }
      .stat-label {
        font-size: 14px;
        color: #666;
      }
    }
  }

  .dept-tree-node {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    padding-right: 8px;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .pagination {
    margin-top: 16px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
