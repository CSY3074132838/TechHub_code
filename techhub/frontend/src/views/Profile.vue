<template>
  <!-- 【第二次迭代】增强个人中心 - 员工自助与档案查看 -->
  <div class="profile-page">
    <el-row :gutter="20" class="profile-row">
      <!-- 左侧个人信息卡片 -->
      <el-col :xs="24" :md="8" class="profile-col">
        <el-card class="profile-card">
          <div class="profile-header">
            <el-avatar :size="80" :src="userInfo?.avatar">
              {{ userInfo?.real_name?.charAt(0) || userInfo?.username?.charAt(0) || 'U' }}
            </el-avatar>
            <h3>{{ userInfo?.real_name || userInfo?.username }}</h3>
            <p class="text-muted">{{ userInfo?.email }}</p>
            <div class="role-tags">
              <el-tag
                v-for="role in userInfo?.roles"
                :key="role.id"
                size="small"
                style="margin-right: 4px;"
              >
                {{ role.description }}
              </el-tag>
            </div>
            <!-- 【第二次迭代】员工状态标签 -->
            <div style="margin-top: 8px;">
              <el-tag :type="employeeStatusType(userInfo?.employee_status)" size="small">
                {{ employeeStatusLabel(userInfo?.employee_status) }}
              </el-tag>
            </div>
          </div>
          
          <el-divider />
          
          <div class="profile-info">
            <div class="info-item">
              <span class="label">用户名</span>
              <span class="value">{{ userInfo?.username }}</span>
            </div>
            <div class="info-item">
              <span class="label">工号</span>
              <span class="value">{{ userInfo?.employee_no || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">部门</span>
              <span class="value">{{ userInfo?.department || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">职位</span>
              <span class="value">{{ userInfo?.position || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">电话</span>
              <span class="value">{{ userInfo?.phone || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">入职日期</span>
              <span class="value">{{ userInfo?.entry_date || '-' }}</span>
            </div>
          </div>
        </el-card>
        
        <!-- 权限列表 -->
        <el-card class="permissions-card" style="margin-top: 20px;">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span>我的权限</span>
              <el-button type="primary" size="small" @click="openApplyDialog">
                申请权限
              </el-button>
            </div>
          </template>
          <el-tag
            v-for="perm in permissions"
            :key="perm"
            size="small"
            type="info"
            style="margin: 2px;"
          >
            {{ perm }}
          </el-tag>
          <el-empty v-if="permissions.length === 0" description="暂无权限" />
        </el-card>
      </el-col>
      
      <!-- 右侧编辑表单 -->
      <el-col :xs="24" :md="16" class="profile-col">
        <!-- 【第二次迭代】档案详情 Tab 页 -->
        <el-card class="archive-card">
          <template #header>
            <span>我的档案</span>
          </template>
          <el-tabs v-model="activeTab">
            <el-tab-pane label="基本信息" name="basic">
              <el-form :model="form" label-width="100px">
                <el-form-item label="真实姓名">
                  <el-input v-model="form.real_name" placeholder="请输入真实姓名" />
                </el-form-item>
                <el-form-item label="电话">
                  <el-input v-model="form.phone" placeholder="请输入电话" />
                </el-form-item>
                <el-form-item label="现居地址">
                  <el-input v-model="form.address" type="textarea" :rows="2" placeholder="请输入现居地址" />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="saveProfile" :loading="saving">保存</el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>
            
            <!-- 【第二次迭代】档案详情（只读，修改需审批） -->
            <el-tab-pane label="档案详情" name="detail">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="员工状态">{{ employeeStatusLabel(userInfo?.employee_status) }}</el-descriptions-item>
                <el-descriptions-item label="工号">{{ userInfo?.employee_no || '-' }}</el-descriptions-item>
                <el-descriptions-item label="入职日期">{{ userInfo?.entry_date || '-' }}</el-descriptions-item>
                <el-descriptions-item label="转正日期">{{ userInfo?.probation_end_date || '-' }}</el-descriptions-item>
                <el-descriptions-item label="性别">{{ userInfo?.gender || '-' }}</el-descriptions-item>
                <el-descriptions-item label="生日">{{ userInfo?.birthday || '-' }}</el-descriptions-item>
                <el-descriptions-item label="籍贯">{{ userInfo?.native_place || '-' }}</el-descriptions-item>
                <el-descriptions-item label="身份证号">{{ maskIdCard(userInfo?.id_card) }}</el-descriptions-item>
                <el-descriptions-item label="学历">{{ userInfo?.education || '-' }}</el-descriptions-item>
                <el-descriptions-item label="毕业院校">{{ userInfo?.school || '-' }}</el-descriptions-item>
                <el-descriptions-item label="专业">{{ userInfo?.major || '-' }}</el-descriptions-item>
                <el-descriptions-item label="紧急联系人">{{ userInfo?.emergency_contact || '-' }}</el-descriptions-item>
                <el-descriptions-item label="紧急电话">{{ maskPhone(userInfo?.emergency_phone) }}</el-descriptions-item>
                <el-descriptions-item label="直属上级">
                  {{ userInfo?.manager?.real_name || '-' }}
                </el-descriptions-item>
              </el-descriptions>
              <el-alert
                title="如需修改档案信息，请联系HR"
                type="info"
                :closable="false"
                style="margin-top: 16px;"
              />
            </el-tab-pane>
            
            <!-- 【第二次迭代】我的考勤 -->
            <el-tab-pane label="我的考勤" name="attendance">
              <el-empty v-if="attendanceRecords.length === 0" description="暂无考勤记录" />
              <el-timeline v-else>
                <el-timeline-item
                  v-for="record in attendanceRecords"
                  :key="record.id"
                  :type="record.status === 'normal' ? 'primary' : 'warning'"
                  :timestamp="formatDate(record.work_date)"
                >
                  <p>工时：{{ record.work_hours }}h {{ record.overtime_hours > 0 ? `(加班 ${record.overtime_hours}h)` : '' }}</p>
                  <p v-if="record.remark">备注：{{ record.remark }}</p>
                </el-timeline-item>
              </el-timeline>
            </el-tab-pane>
          </el-tabs>
        </el-card>
        
        <el-card class="password-card">
          <template #header>
            <span>修改密码</span>
          </template>
          
          <el-form :model="pwdForm" label-width="100px" :rules="pwdRules" ref="pwdFormRef">
            <el-form-item label="旧密码" prop="old_password">
              <el-input v-model="pwdForm.old_password" type="password" placeholder="请输入旧密码" />
            </el-form-item>
            <el-form-item label="新密码" prop="new_password">
              <el-input v-model="pwdForm.new_password" type="password" placeholder="请输入新密码" />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirm_password">
              <el-input v-model="pwdForm.confirm_password" type="password" placeholder="请再次输入新密码" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="changePassword" :loading="pwdLoading">修改密码</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <!-- 申请权限对话框 -->
    <el-dialog v-model="showApplyDialog" title="申请权限" width="500px" :close-on-click-modal="false">
      <el-form :model="applyForm" label-width="100px">
        <el-form-item label="申请权限">
          <el-select v-model="applyForm.permission" placeholder="请选择要申请的权限" style="width: 100%">
            <el-option v-for="perm in availablePermissions" :key="perm.code" :label="perm.label" :value="perm.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="申请理由">
          <el-input v-model="applyForm.reason" type="textarea" :rows="3" placeholder="请描述申请该权限的理由" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showApplyDialog = false">取消</el-button>
        <el-button type="primary" @click="submitApply" :loading="applyLoading">提交申请</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { updateUser, getPermissions, getMyDetail } from '@/api/users'
import { changePassword as apiChangePassword } from '@/api/auth'
import { createApproval } from '@/api/approvals'
import { getAttendanceRecords } from '@/api/attendance'
import dayjs from 'dayjs'

const userStore = useUserStore()
const userInfo = computed(() => userStore.userInfo)
const permissions = computed(() => userStore.permissions)
const activeTab = ref('basic')

// 【第二次迭代】获取完整档案
const fetchMyDetail = async () => {
  try {
    const res = await getMyDetail()
    if (res.user) {
      // 合并到 userStore 的 userInfo 中
      userStore.userInfo = { ...userStore.userInfo, ...res.user }
    }
  } catch (error) {
    console.error('获取档案详情失败', error)
  }
}

const form = ref({
  real_name: userInfo.value?.real_name || '',
  phone: userInfo.value?.phone || '',
  address: userInfo.value?.address || ''
})

const saving = ref(false)

const saveProfile = async () => {
  saving.value = true
  try {
    await updateUser(userInfo.value.id, {
      real_name: form.value.real_name,
      phone: form.value.phone,
      address: form.value.address
    })
    ElMessage.success('资料更新成功')
    await userStore.fetchUserInfo()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '更新失败')
  } finally {
    saving.value = false
  }
}

const pwdFormRef = ref(null)
const pwdForm = ref({ old_password: '', new_password: '', confirm_password: '' })
const pwdLoading = ref(false)

const pwdRules = {
  old_password: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== pwdForm.value.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 申请权限
const showApplyDialog = ref(false)
const allPermissions = ref([])
const applyForm = ref({ permission: '', reason: '' })
const applyLoading = ref(false)

const availablePermissions = computed(() => {
  const current = permissions.value || []
  return allPermissions.value.filter(p => !current.includes(p.code))
})

const openApplyDialog = async () => {
  showApplyDialog.value = true
  try {
    const res = await getPermissions()
    allPermissions.value = res.permissions || []
  } catch (error) {
    console.error('获取权限列表失败', error)
  }
}

const submitApply = async () => {
  if (!applyForm.value.permission) {
    ElMessage.warning('请选择要申请的权限')
    return
  }
  
  applyLoading.value = true
  try {
    const perm = allPermissions.value.find(p => p.code === applyForm.value.permission)
    await createApproval({
      title: `权限申请：${perm?.label || applyForm.value.permission}`,
      approval_type: 'permission',
      description: applyForm.value.reason || `用户申请 ${perm?.label || applyForm.value.permission} 权限`,
      is_urgent: false
    })
    ElMessage.success('权限申请已提交，等待审批')
    showApplyDialog.value = false
    applyForm.value = { permission: '', reason: '' }
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '申请提交失败')
  } finally {
    applyLoading.value = false
  }
}

const changePassword = async () => {
  const valid = await pwdFormRef.value.validate().catch(() => false)
  if (!valid) return
  
  pwdLoading.value = true
  try {
    await apiChangePassword({
      old_password: pwdForm.value.old_password,
      new_password: pwdForm.value.new_password
    })
    ElMessage.success('密码修改成功，请重新登录')
    userStore.logout()
    window.location.href = '/login'
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '修改失败')
  } finally {
    pwdLoading.value = false
  }
}

// 【第二次迭代】员工状态显示转换
const employeeStatusLabel = (status) => {
  const map = { probation: '试用期', active: '正式员工', pending_leave: '待离职', left: '已离职', suspended: '停薪留职' }
  return map[status] || status || '试用期'
}

const employeeStatusType = (status) => {
  const map = { probation: 'warning', active: 'success', pending_leave: 'danger', left: 'info', suspended: 'info' }
  return map[status] || ''
}

// 【第二次迭代】敏感信息脱敏
const maskIdCard = (idCard) => {
  if (!idCard) return '-'
  if (idCard.length === 18) {
    return idCard.slice(0, 6) + '********' + idCard.slice(14)
  }
  return idCard.slice(0, 3) + '****' + idCard.slice(-4)
}

const maskPhone = (phone) => {
  if (!phone) return '-'
  if (phone.length === 11) {
    return phone.slice(0, 3) + '****' + phone.slice(7)
  }
  return phone
}

// 【第二次迭代】考勤记录
const attendanceRecords = ref([])
const fetchAttendance = async () => {
  try {
    const res = await getAttendanceRecords({ per_page: 10 })
    attendanceRecords.value = res.records || []
  } catch (error) {
    console.error('获取考勤记录失败', error)
  }
}

const formatDate = (dateStr) => {
  return dateStr ? dayjs(dateStr).format('YYYY-MM-DD') : '-'
}

onMounted(() => {
  fetchMyDetail()
  fetchAttendance()
})
</script>

<style scoped lang="scss">
.profile-page {
  height: calc(100vh - 40px);

  .profile-row {
    height: 100%;
  }

  .profile-col {
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .profile-card {
    flex-shrink: 0;
    .profile-header {
      text-align: center;
      padding: 20px 0;
      h3 { margin: 12px 0 4px; font-size: 20px; }
      .text-muted { color: #999; font-size: 14px; margin-bottom: 12px; }
      .role-tags {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 4px;
      }
    }
    .profile-info {
      .info-item {
        display: flex;
        justify-content: space-between;
        padding: 12px 0;
        border-bottom: 1px solid #f0f0f0;
        &:last-child { border-bottom: none; }
        .label { color: #666; font-size: 14px; }
        .value { color: #333; font-weight: 500; }
      }
    }
  }

  .permissions-card {
    flex: 1;
    margin-top: 20px;
    overflow-y: auto;
    .el-tag { margin: 2px; }
  }

  .archive-card {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;

    :deep(.el-card__body) {
      flex: 1;
      overflow-y: auto;
    }
  }

  .password-card {
    flex-shrink: 0;
    margin-top: 20px;
  }
}
</style>
