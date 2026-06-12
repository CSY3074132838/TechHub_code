<!-- 【第三次迭代陈思言负责】 -->
<!--
  (5) 个人中心与用户管理同步，支持显示多个身份（多部门多角色）
  (6) 实现中英文网页语言切换
-->
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
            <!-- 多身份角色标签 -->
            <div v-if="userInfo?.identities && userInfo.identities.length > 0" class="role-tags">
              <div v-for="(identity, idx) in userInfo.identities" :key="identity.id" class="identity-tag-row">
                <el-tag :type="identity.is_primary ? 'success' : 'info'" size="small" style="margin-right: 4px; min-width: 60px; text-align: center;">
                  {{ identity.department?.name || '-' }}
                </el-tag>
                <el-tag
                  v-for="role in identity.roles"
                  :key="role.id"
                  size="small"
                  style="margin-right: 4px;"
                >
                  {{ role.description }}
                </el-tag>
                <el-tag :type="identity.is_primary ? 'success' : 'warning'" size="small" effect="plain">
                  {{ identity.is_primary ? $t('users.primaryIdentity') : $t('users.secondaryIdentity') + ' ' + idx }}
                </el-tag>
              </div>
            </div>
            <div v-else class="role-tags">
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
              <span class="label">{{ $t('profile.username') }}</span>
              <span class="value">{{ userInfo?.username }}</span>
            </div>
            <div class="info-item">
              <span class="label">{{ $t('profile.employeeNo') }}</span>
              <span class="value">{{ userInfo?.employee_no || '-' }}</span>
            </div>
            <!-- 多身份展示 -->
            <div v-if="userInfo?.identities && userInfo.identities.length > 0" class="info-item identities-info">
              <span class="label">{{ $t('profile.identities') || '身份' }}</span>
              <div class="value identity-list">
                <div v-for="(identity, idx) in userInfo.identities" :key="identity.id" class="identity-row">
                  <el-tag :type="identity.is_primary ? 'success' : 'info'" size="small" style="margin-right: 4px; min-width: 60px; text-align: center;">
                    {{ identity.department?.name || '-' }}
                  </el-tag>
                  <span style="color: #606266; margin-right: 4px; display: inline-block; min-width: 80px;">{{ identity.position || '-' }}</span>
                  <el-tag :type="identity.is_primary ? 'success' : 'warning'" size="small" effect="plain">
                    {{ identity.is_primary ? $t('users.primaryIdentity') : $t('users.secondaryIdentity') + ' ' + idx }}
                  </el-tag>
                </div>
              </div>
            </div>
            <template v-else>
              <div class="info-item">
                <span class="label">{{ $t('profile.department') }}</span>
                <span class="value">{{ userInfo?.department || '-' }}</span>
              </div>
              <div class="info-item">
                <span class="label">{{ $t('profile.position') }}</span>
                <span class="value">{{ userInfo?.position || '-' }}</span>
              </div>
            </template>
            <div class="info-item">
              <span class="label">{{ $t('profile.phone') }}</span>
              <span class="value">{{ userInfo?.phone || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">{{ $t('profile.entryDate') }}</span>
              <span class="value">{{ userInfo?.entry_date || '-' }}</span>
            </div>
          </div>
        </el-card>
        
        <!-- 权限列表 -->
        <el-card class="permissions-card" style="margin-top: 20px;">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span>{{ $t('profile.myPermissions') }}</span>
              <el-button type="primary" size="small" @click="openApplyDialog">
                {{ $t('profile.applyPermission') }}
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
          <el-empty v-if="permissions.length === 0" :description="$t('profile.noPermission')" />
        </el-card>
      </el-col>
      
      <!-- 右侧编辑表单 -->
      <el-col :xs="24" :md="16" class="profile-col">
        <!-- 【第二次迭代】档案详情 Tab 页 -->
        <el-card class="archive-card">
          <template #header>
            <span>{{ $t('profile.myProfile') }}</span>
          </template>
          <el-tabs v-model="activeTab">
            <el-tab-pane :label="$t('profile.basicInfo')" name="basic">
              <el-form :model="form" label-width="100px">
                <el-form-item :label="$t('profile.realName')">
                  <el-input v-model="form.real_name" :placeholder="$t('profile.realNamePlaceholder')" />
                </el-form-item>
                <el-form-item :label="$t('profile.phone')">
                  <el-input v-model="form.phone" :placeholder="$t('profile.phonePlaceholder')" />
                </el-form-item>
                <el-form-item :label="$t('profile.address')">
                  <el-input v-model="form.address" type="textarea" :rows="2" :placeholder="$t('profile.addressPlaceholder')" />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="saveProfile" :loading="saving">{{ $t('profile.save') }}</el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>
            
            <!-- 【第二次迭代】档案详情（只读，修改需审批） -->
            <el-tab-pane :label="$t('profile.profileDetail')" name="detail">
              <el-descriptions :column="2" border>
                <el-descriptions-item :label="$t('profile.employeeStatus')">{{ employeeStatusLabel(userInfo?.employee_status) }}</el-descriptions-item>
                <el-descriptions-item :label="$t('profile.employeeNo')">{{ userInfo?.employee_no || '-' }}</el-descriptions-item>
                <el-descriptions-item :label="$t('profile.entryDate')">{{ userInfo?.entry_date || '-' }}</el-descriptions-item>
                <el-descriptions-item :label="$t('profile.formalDate')">{{ userInfo?.probation_end_date || '-' }}</el-descriptions-item>
                <el-descriptions-item :label="$t('profile.gender')">{{ userInfo?.gender || '-' }}</el-descriptions-item>
                <el-descriptions-item :label="$t('profile.birthday')">{{ userInfo?.birthday || '-' }}</el-descriptions-item>
                <el-descriptions-item :label="$t('profile.birthplace')">{{ userInfo?.native_place || '-' }}</el-descriptions-item>
                <el-descriptions-item :label="$t('profile.idCard')">{{ maskIdCard(userInfo?.id_card) }}</el-descriptions-item>
                <el-descriptions-item :label="$t('profile.education')">{{ userInfo?.education || '-' }}</el-descriptions-item>
                <el-descriptions-item :label="$t('profile.school')">{{ userInfo?.school || '-' }}</el-descriptions-item>
                <el-descriptions-item :label="$t('profile.major')">{{ userInfo?.major || '-' }}</el-descriptions-item>
                <el-descriptions-item :label="$t('profile.emergencyContact')">{{ userInfo?.emergency_contact || '-' }}</el-descriptions-item>
                <el-descriptions-item :label="$t('profile.emergencyPhone')">{{ maskPhone(userInfo?.emergency_phone) }}</el-descriptions-item>
                <el-descriptions-item :label="$t('profile.directManager')">
                  {{ userInfo?.manager?.real_name || '-' }}
                </el-descriptions-item>
              </el-descriptions>
              <el-alert
                :title="$t('profile.contactHR')"
                type="info"
                :closable="false"
                style="margin-top: 16px;"
              />
            </el-tab-pane>
            
            <!-- 【第二次迭代】我的考勤 -->
            <el-tab-pane :label="$t('profile.myAttendance')" name="attendance">
              <el-empty v-if="attendanceRecords.length === 0" :description="$t('profile.noAttendanceRecords')" />
              <el-timeline v-else>
                <el-timeline-item
                  v-for="record in attendanceRecords"
                  :key="record.id"
                  :type="record.status === 'normal' ? 'primary' : 'warning'"
                  :timestamp="formatDate(record.work_date)"
                >
                  <p>{{ $t('profile.workTimePrefix') }}{{ record.work_hours }}h {{ record.overtime_hours > 0 ? `(${$t('profile.overtime')} ${record.overtime_hours}h)` : '' }}</p>
                  <p v-if="record.remark">{{ $t('profile.remarkPrefix') }}{{ record.remark }}</p>
                </el-timeline-item>
              </el-timeline>
            </el-tab-pane>
          </el-tabs>
        </el-card>
        
        <el-card class="password-card">
          <template #header>
            <span>{{ $t('profile.changePassword') }}</span>
          </template>
          
          <el-form :model="pwdForm" label-width="100px" :rules="pwdRules" ref="pwdFormRef">
            <el-form-item :label="$t('profile.oldPassword')" prop="old_password">
              <el-input v-model="pwdForm.old_password" type="password" :placeholder="$t('profile.oldPasswordPlaceholder')" />
            </el-form-item>
            <el-form-item :label="$t('profile.newPassword')" prop="new_password">
              <el-input v-model="pwdForm.new_password" type="password" :placeholder="$t('profile.newPasswordPlaceholder')" />
            </el-form-item>
            <el-form-item :label="$t('profile.confirmPassword')" prop="confirm_password">
              <el-input v-model="pwdForm.confirm_password" type="password" :placeholder="$t('profile.confirmPasswordPlaceholder')" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="changePassword" :loading="pwdLoading">{{ $t('profile.changePasswordButton') }}</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <!-- 申请权限对话框 -->
    <el-dialog v-model="showApplyDialog" :title="$t('profile.applyPermissionDialog')" width="500px" :close-on-click-modal="false">
      <el-form :model="applyForm" label-width="100px">
        <el-form-item :label="$t('profile.applyPermissionLabel')">
          <el-select v-model="applyForm.permission" :placeholder="$t('profile.selectPermission')" style="width: 100%">
            <el-option v-for="perm in availablePermissions" :key="perm.code" :label="perm.label" :value="perm.code" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('profile.applyReason')">
          <el-input v-model="applyForm.reason" type="textarea" :rows="3" :placeholder="$t('profile.applyReasonPlaceholder')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showApplyDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="submitApply" :loading="applyLoading">{{ $t('profile.submitApply') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
// 第三次迭代陈思言负责
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/stores/user'
import { updateUser, getPermissions, getMyDetail } from '@/api/users'
import { changePassword as apiChangePassword } from '@/api/auth'
import { createApproval } from '@/api/approvals'
import { getAttendanceRecords } from '@/api/attendance'
import dayjs from 'dayjs'

const { t } = useI18n()
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
    console.error(t('profile.fetchDetailFailed'), error)
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
    ElMessage.success(t('profile.profileUpdateSuccess'))
    await userStore.fetchUserInfo()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || t('profile.updateFailed'))
  } finally {
    saving.value = false
  }
}

const pwdFormRef = ref(null)
const pwdForm = ref({ old_password: '', new_password: '', confirm_password: '' })
const pwdLoading = ref(false)

const pwdRules = {
  old_password: [{ required: true, message: t('profile.oldPasswordRequired'), trigger: 'blur' }],
  new_password: [
    { required: true, message: t('profile.newPasswordRequired'), trigger: 'blur' },
    { min: 6, message: t('profile.passwordMinLength'), trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: t('profile.confirmPasswordRequired'), trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== pwdForm.value.new_password) {
          callback(new Error(t('profile.passwordMismatch')))
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
    console.error(t('profile.fetchPermissionsFailed'), error)
  }
}

const submitApply = async () => {
  if (!applyForm.value.permission) {
    ElMessage.warning(t('profile.pleaseSelectPermission'))
    return
  }
  
  applyLoading.value = true
  try {
    const perm = allPermissions.value.find(p => p.code === applyForm.value.permission)
    await createApproval({
      title: `${t('profile.permissionApplyPrefix')}${perm?.label || applyForm.value.permission}`,
      approval_type: 'permission',
      description: applyForm.value.reason || `${t('profile.userApplyPrefix')} ${perm?.label || applyForm.value.permission} ${t('profile.permissionSuffix')}`,
      is_urgent: false
    })
    ElMessage.success(t('profile.permissionApplySubmitted'))
    showApplyDialog.value = false
    applyForm.value = { permission: '', reason: '' }
  } catch (error) {
    ElMessage.error(error.response?.data?.message || t('profile.applySubmitFailed'))
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
    ElMessage.success(t('profile.passwordChangeSuccess'))
    userStore.logout()
    window.location.href = '/login'
  } catch (error) {
    ElMessage.error(error.response?.data?.message || t('profile.changePasswordFailed'))
  } finally {
    pwdLoading.value = false
  }
}

// 【第二次迭代】员工状态显示转换
const employeeStatusLabel = (status) => {
  const map = { probation: t('users.probation'), active: t('users.formal'), pending_leave: t('users.pendingResign'), left: t('users.resigned'), suspended: t('users.suspended') }
  return map[status] || status || t('users.probation')
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
    console.error(t('profile.fetchAttendanceFailed'), error)
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
        .identity-tag-row {
          display: flex;
          align-items: center;
          justify-content: center;
          flex-wrap: wrap;
          gap: 4px;
          width: 100%;
          margin-bottom: 6px;
          &:last-child { margin-bottom: 0; }
        }
      }
    }
    .profile-info {
      .info-item {
        display: flex;
        justify-content: space-between;
        padding: 12px 0;
        border-bottom: 1px solid #f0f0f0;
        &:last-child { border-bottom: none; }
        .label { color: #666; font-size: 14px; flex-shrink: 0; }
        .value { color: #333; font-weight: 500; }
        &.identities-info {
          flex-direction: column;
          gap: 8px;
          .label { margin-bottom: 4px; }
          .identity-list {
            display: flex;
            flex-direction: column;
            gap: 6px;
            .identity-row {
              display: flex;
              align-items: center;
              flex-wrap: wrap;
              gap: 4px;
              padding: 4px 0;
              border-bottom: 1px dashed #e4e7ed;
              &:last-child { border-bottom: none; }
            }
          }
        }
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
