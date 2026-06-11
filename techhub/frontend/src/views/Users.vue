<!-- 第三次迭代陈思言负责 -->
<template>
  <div class="users-page">
    <div class="page-header">
      <h2>{{ $t('users.pageTitle') }}</h2>
      <div class="header-actions">
        <!-- 【第二次迭代】批量导入导出按钮 -->
        <el-button size="small" @click="handleExport" v-if="userStore.hasPermission('user_manage')">
          <el-icon><Download /></el-icon>{{ $t('users.export') }}
        </el-button>
        <el-button type="primary" @click="showCreateDialog = true" v-if="userStore.hasPermission('user_manage')">
          <el-icon><Plus /></el-icon>{{ $t('users.addUser') }}
        </el-button>
      </div>
    </div>

    <!-- 【第二次迭代】统计卡片 - 点击穿透筛选 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card clickable" @click="handleStatClick('total')" :title="$t('users.clickViewAll')">
          <div class="stat-value">{{ stats.total || 0 }}</div>
          <div class="stat-label">{{ $t('users.totalUsers') }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card clickable" @click="handleStatClick('active')" :title="$t('users.clickViewActive')">
          <div class="stat-value success">{{ stats.active || 0 }}</div>
          <div class="stat-label">{{ $t('users.activeUsers') }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card clickable" @click="handleStatClick('new_this_month')" :title="$t('users.clickViewNew')">
          <div class="stat-value warning">{{ stats.new_this_month || 0 }}</div>
          <div class="stat-label">{{ $t('users.newThisMonth') }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card clickable" @click="handleStatClick('inactive')" :title="$t('users.clickViewInactive')">
          <div class="stat-value info">{{ stats.inactive || 0 }}</div>
          <div class="stat-label">{{ $t('users.resignedUsers') }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 【第二次迭代】高级筛选栏 -->
    <el-card class="filter-card" style="margin-bottom: 20px;">
      <el-row :gutter="12" align="middle">
        <el-col :xs="24" :sm="6">
          <el-input v-model="filter.search" :placeholder="$t('users.searchPlaceholder')" clearable @change="handleFilterChange">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </el-col>
        <el-col :xs="12" :sm="4">
          <el-select v-model="filter.department_id" :placeholder="$t('users.selectDepartment')" clearable @change="handleFilterChange" style="width: 100%">
            <el-option v-for="dept in flatDepartments" :key="dept.id" :label="dept.name" :value="dept.id" />
          </el-select>
        </el-col>
        <el-col :xs="12" :sm="4">
          <el-select v-model="filter.employee_status" :placeholder="$t('users.employeeStatus')" clearable @change="handleFilterChange" style="width: 100%">
            <el-option :label="$t('users.probation')" value="probation" />
            <el-option :label="$t('users.formal')" value="active" />
            <el-option :label="$t('users.pendingResign')" value="pending_leave" />
            <el-option :label="$t('users.resigned')" value="left" />
          </el-select>
        </el-col>
        <el-col :xs="12" :sm="4">
          <el-select v-model="filter.role_id" :placeholder="$t('users.selectRole')" clearable @change="handleFilterChange" style="width: 100%">
            <el-option v-for="role in roles" :key="role.id" :label="role.description" :value="role.id" />
          </el-select>
        </el-col>
        <el-col :xs="12" :sm="4">
          <el-select v-model="filter.is_active" :placeholder="$t('users.accountStatus')" clearable @change="handleFilterChange" style="width: 100%">
            <el-option :label="$t('users.normal')" :value="true" />
            <el-option :label="$t('users.disabled')" :value="false" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="2">
          <el-button text type="primary" @click="resetFilter">{{ $t('common.reset') }}</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 用户列表 -->
    <el-card class="users-list">
      <el-table :data="users" v-loading="loading" stripe>
        <el-table-column :label="$t('users.user')" min-width="200">
          <template #default="{ row }">
            <div class="user-cell">
              <el-avatar :size="40" :src="row.avatar">
                {{ row.real_name?.charAt(0) || row.username?.charAt(0) }}
              </el-avatar>
              <div class="user-info">
                <div class="name">{{ row.real_name || row.username }}</div>
                <div class="email">{{ row.email }}</div>
                <!-- 【第二次迭代】显示工号 -->
                <div class="employee-no" v-if="row.employee_no">{{ $t('users.employeeNo') }}: {{ row.employee_no }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <!-- ================================================
             【第三次迭代于然负责】(5) 多身份展示
             一个员工可在多个部门拥有不同职位和角色
             ================================================ -->
        <!-- 多身份展示：部门 -->
        <el-table-column :label="$t('users.department')" width="140">
          <template #default="{ row }">
            <div v-if="row.identities && row.identities.length > 0">
              <div v-for="identity in row.identities" :key="identity.id" class="identity-line">
                <el-tag size="small" :type="identity.is_primary ? 'success' : 'info'" style="margin-bottom: 2px;">
                  {{ identity.department?.name || '-' }}
                </el-tag>
              </div>
            </div>
            <span v-else>{{ row.department || '-' }}</span>
          </template>
        </el-table-column>
        <!-- 多身份展示：职位 -->
        <el-table-column :label="$t('users.position')" width="140">
          <template #default="{ row }">
            <div v-if="row.identities && row.identities.length > 0">
              <div v-for="identity in row.identities" :key="identity.id" class="identity-line">
                <span style="font-size: 12px; color: #606266;">{{ identity.position || '-' }}</span>
              </div>
            </div>
            <span v-else style="color: #909399;">{{ row.position || '-' }}</span>
          </template>
        </el-table-column>
        <!-- 多身份展示：角色 -->
        <el-table-column :label="$t('users.role')" width="160">
          <template #default="{ row }">
            <div v-if="row.identities && row.identities.length > 0">
              <div v-for="identity in row.identities" :key="identity.id" class="identity-line" style="margin-bottom: 2px;">
                <el-tag
                  v-for="role in identity.roles"
                  :key="role.id"
                  size="small"
                  style="margin-right: 2px; margin-bottom: 2px;"
                >
                  {{ role.description }}
                </el-tag>
                <span v-if="!identity.roles || identity.roles.length === 0" style="font-size: 12px; color: #909399;">-</span>
              </div>
            </div>
            <div v-else>
              <el-tag
                v-for="role in row.roles"
                :key="role.id"
                size="small"
                style="margin-right: 4px;"
              >
                {{ role.description }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <!-- 【第二次迭代】员工状态列 -->
        <el-table-column :label="$t('users.employeeStatus')" width="100">
          <template #default="{ row }">
            <el-tag :type="employeeStatusType(row.employee_status)" size="small">
              {{ employeeStatusLabel(row.employee_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('users.accountStatus')" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? $t('users.normal') : $t('users.disabled') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.operation')" width="180" fixed="right">
          <template #default="{ row }">
            <el-button text size="small" @click="viewDetail(row)">{{ $t('users.detail') }}</el-button>
            <el-button text size="small" @click="editUser(row)">{{ $t('common.edit') }}</el-button>
            <el-button
              v-if="userStore.hasPermission('user_manage')"
              :type="row.is_active ? 'danger' : 'success'"
              text
              size="small"
              @click="toggleStatus(row)"
            >
              {{ row.is_active ? $t('users.disable') : $t('users.enable') }}
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
          <span>{{ $t('users.roleManagement') }}</span>
          <el-button type="primary" size="small" @click="showRoleDialog = true" v-if="userStore.hasPermission('role_manage')">
            <el-icon><Plus /></el-icon>{{ $t('users.newRole') }}
          </el-button>
        </div>
      </template>
      
      <el-table :data="roles" size="small" border>
        <el-table-column :label="$t('users.roleName')" prop="description" min-width="150" />
        <el-table-column :label="$t('users.roleCode')" prop="name" width="150" />
        <el-table-column :label="$t('users.level')" prop="level" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('users.permissions')" min-width="300">
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
        <el-table-column :label="$t('common.operation')" width="150">
          <template #default="{ row }">
            <el-button text size="small" @click="editRole(row)">{{ $t('common.edit') }}</el-button>
            <el-button v-if="userStore.hasPermission('role_manage')" text type="danger" size="small" @click="removeRole(row)">{{ $t('common.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- ================================================
         【第三次迭代于然负责】(5) 用户详情抽屉
         展示员工的多重身份信息（部门+职位+角色）
         ================================================ -->
    <!-- 【第二次迭代】用户详情抽屉 -->
    <el-drawer v-model="showDetailDrawer" :title="$t('users.employeeProfile')" size="600px" :destroy-on-close="true">
      <div v-if="detailUser" class="user-detail">
        <div class="detail-header">
          <el-avatar :size="64" :src="detailUser.avatar">
            {{ detailUser.real_name?.charAt(0) || detailUser.username?.charAt(0) }}
          </el-avatar>
          <div class="detail-header-info">
            <h3>{{ detailUser.real_name || detailUser.username }}</h3>
            <p>{{ detailUser.employee_no ? `${$t('users.employeeNo')}：${detailUser.employee_no}` : '' }}</p>
            <div class="detail-tags">
              <el-tag v-for="role in detailUser.roles" :key="role.id" size="small">{{ role.description }}</el-tag>
              <el-tag :type="detailUser.is_active ? 'success' : 'info'" size="small">{{ detailUser.is_active ? $t('users.normal') : $t('users.disabled') }}</el-tag>
            </div>
          </div>
        </div>
        <el-divider />
        <el-descriptions :column="2" border>
          <el-descriptions-item :label="$t('users.username')">{{ detailUser.username }}</el-descriptions-item>
          <el-descriptions-item :label="$t('users.email')">{{ detailUser.email }}</el-descriptions-item>
          <el-descriptions-item :label="$t('users.phone')">{{ detailUser.phone || '-' }}</el-descriptions-item>
          <!-- 多身份展示 -->
          <el-descriptions-item :label="$t('users.identities')" :span="2">
            <div v-if="detailUser.identities && detailUser.identities.length > 0" class="detail-identities">
              <div v-for="(identity, idx) in detailUser.identities" :key="identity.id" class="detail-identity-item">
                <el-tag :type="identity.is_primary ? 'success' : 'info'" size="small" style="margin-right: 8px; min-width: 60px; text-align: center;">
                  {{ identity.department?.name || '-' }}
                </el-tag>
                <span style="color: #606266; margin-right: 8px; display: inline-block; min-width: 80px;">{{ identity.position || '-' }}</span>
                <el-tag v-for="role in identity.roles" :key="role.id" size="small" style="margin-right: 4px;">{{ role.description }}</el-tag>
                <el-tag :type="identity.is_primary ? 'success' : 'warning'" size="small" effect="plain">
                  {{ identity.is_primary ? $t('users.primaryIdentity') : $t('users.secondaryIdentity') + ' ' + idx }}
                </el-tag>
              </div>
            </div>
            <div v-else>
              <span style="color: #909399;">{{ detailUser.department || '-' }} / {{ detailUser.position || '-' }}</span>
            </div>
          </el-descriptions-item>
          <!-- 【第二次迭代】扩展档案字段 -->
          <el-descriptions-item :label="$t('users.employeeStatus')">{{ employeeStatusLabel(detailUser.employee_status) }}</el-descriptions-item>
          <el-descriptions-item :label="$t('users.entryDate')">{{ detailUser.entry_date || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('users.formalDate')">{{ detailUser.probation_end_date || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('users.resignDate')">{{ detailUser.leave_date || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('users.gender')">{{ detailUser.gender || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('users.birthday')">{{ detailUser.birthday || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('users.birthplace')">{{ detailUser.native_place || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('users.education')">{{ detailUser.education || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('users.school')">{{ detailUser.school || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('users.major')">{{ detailUser.major || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('users.emergencyContact')">{{ detailUser.emergency_contact || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('users.emergencyPhone')">{{ detailUser.emergency_phone || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('users.address')" :span="2">{{ detailUser.address || '-' }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-drawer>

    <!-- 添加/编辑用户对话框 -->
    <el-dialog v-model="showCreateDialog" :title="isEdit ? $t('users.editUser') : $t('users.addUserDialog')" width="700px">
      <el-tabs v-model="activeTab">
        <el-tab-pane :label="$t('users.basicInfo')" name="basic">
          <el-form :model="form" label-width="100px">
            <el-form-item :label="$t('users.username')">
              <el-input v-model="form.username" :placeholder="$t('users.usernamePlaceholder')" :disabled="isEdit" />
            </el-form-item>
            <el-form-item :label="$t('users.email')">
              <el-input v-model="form.email" :placeholder="$t('users.emailPlaceholder')" :disabled="isEdit" />
            </el-form-item>
            <el-form-item :label="$t('users.password')" v-if="!isEdit">
              <el-input v-model="form.password" type="password" :placeholder="$t('users.passwordPlaceholder')" />
            </el-form-item>
            <el-form-item :label="$t('users.realName')">
              <el-input v-model="form.real_name" :placeholder="$t('users.realNamePlaceholder')" />
            </el-form-item>
            <el-form-item :label="$t('users.employeeNo')">
              <el-input v-model="form.employee_no" :placeholder="$t('users.employeeNoPlaceholder')" />
            </el-form-item>
            <el-form-item :label="$t('users.phone')">
              <el-input v-model="form.phone" :placeholder="$t('users.phonePlaceholder')" />
            </el-form-item>
          </el-form>
          <!-- 身份管理（编辑时显示） -->
          <!-- ================================================
               【第三次迭代于然负责】(5) 编辑页面多重身份编辑
               实现一个员工可拥有多个身份（不同部门+职位+角色）
               ================================================ -->
          <div v-if="isEdit" class="identities-section" style="margin-top: 8px;">
            <div class="identity-section-title" style="font-weight: 600; font-size: 14px; color: #303133; margin-bottom: 12px; padding-left: 100px;">{{ $t('users.identities') }}</div>
            <div v-for="(identity, index) in identityList" :key="identity._key || identity.id" class="identity-card">
              <div class="identity-header">
                <span class="identity-title">{{ $t('users.identity') }} {{ index + 1 }}</span>
                <el-tag v-if="identity.is_primary" type="success" size="small">{{ $t('users.primaryIdentity') }}</el-tag>
                <div class="identity-actions">
                  <el-button v-if="!identity.is_primary" link type="primary" size="small" @click="setPrimaryIdentityLocal(index)">{{ $t('users.setPrimary') }}</el-button>
                  <el-button link type="danger" size="small" @click="removeIdentity(index)">{{ $t('common.delete') }}</el-button>
                </div>
              </div>
              <el-form :model="identity" label-width="100px">
                <el-form-item :label="$t('users.department')" required>
                  <el-select v-model="identity.department_id" :placeholder="$t('users.selectDepartment')" style="width: 100%">
                    <el-option v-for="dept in flatDepartments" :key="dept.id" :label="dept.name" :value="dept.id" />
                  </el-select>
                </el-form-item>
                <el-form-item :label="$t('users.position')">
                  <el-select v-model="identity.position" :placeholder="$t('users.selectPosition')" clearable style="width: 100%">
                    <el-option v-for="pos in positionOptions" :key="pos" :label="pos" :value="pos" />
                  </el-select>
                </el-form-item>
                <el-form-item :label="$t('users.role')">
                  <el-select v-model="identity.role_ids" multiple :placeholder="$t('users.selectRole')" style="width: 100%">
                    <el-option v-for="role in roles" :key="role.id" :label="role.description" :value="role.id" />
                  </el-select>
                </el-form-item>
              </el-form>
            </div>
            <el-button type="primary" plain @click="addIdentity" style="width: 100%; margin-top: 12px;">
              <el-icon><Plus /></el-icon>{{ $t('users.addIdentity') }}
            </el-button>
          </div>
          <!-- 添加用户时的部门/职位/角色（非编辑时显示） -->
          <el-form v-if="!isEdit" :model="form" label-width="100px" style="margin-top: 8px;">
            <el-form-item :label="$t('users.department')">
              <el-select v-model="form.department" :placeholder="$t('users.selectDepartment')" clearable style="width: 100%">
                <el-option
                  v-for="dept in flatDepartments"
                  :key="dept.id"
                  :label="dept.name"
                  :value="dept.name"
                />
              </el-select>
            </el-form-item>
            <el-form-item :label="$t('users.position')">
              <el-select v-model="form.position" :placeholder="$t('users.selectPosition')" clearable style="width: 100%">
                <el-option
                  v-for="pos in positionOptions"
                  :key="pos"
                  :label="pos"
                  :value="pos"
                />
              </el-select>
            </el-form-item>
            <el-form-item :label="$t('users.role')">
              <el-select v-model="form.role_ids" multiple :placeholder="$t('users.selectRole')" style="width: 100%;">
                <el-option v-for="role in roles" :key="role.id" :label="role.description" :value="role.id" />
              </el-select>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        <!-- 【第二次迭代】员工档案详情 Tab -->
        <el-tab-pane :label="$t('users.profileDetail')" name="detail" v-if="isEdit">
          <el-form :model="detailForm" label-width="100px">
            <el-form-item :label="$t('users.employeeStatus')">
              <el-select v-model="detailForm.employee_status" :placeholder="$t('users.selectStatus')" style="width: 100%">
                <el-option :label="$t('users.probation')" value="probation" />
                <el-option :label="$t('users.formal')" value="active" />
                <el-option :label="$t('users.pendingResign')" value="pending_leave" />
                <el-option :label="$t('users.resigned')" value="left" />
                <el-option :label="$t('users.suspended')" value="suspended" />
              </el-select>
            </el-form-item>
            <el-form-item :label="$t('users.entryDate')">
              <el-date-picker v-model="detailForm.entry_date" type="date" :placeholder="$t('users.selectDate')" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
            <el-form-item :label="$t('users.formalDate')">
              <el-date-picker v-model="detailForm.probation_end_date" type="date" :placeholder="$t('users.selectDate')" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
            <el-form-item :label="$t('users.resignDate')">
              <el-date-picker v-model="detailForm.leave_date" type="date" :placeholder="$t('users.selectDate')" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
            <el-form-item :label="$t('users.idCard')">
              <el-input v-model="detailForm.id_card" :placeholder="$t('users.idCardPlaceholder')" />
            </el-form-item>
            <el-form-item :label="$t('users.gender')">
              <el-radio-group v-model="detailForm.gender">
                <el-radio :label="$t('users.male')">{{ $t('users.male') }}</el-radio>
                <el-radio :label="$t('users.female')">{{ $t('users.female') }}</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item :label="$t('users.birthday')">
              <el-date-picker v-model="detailForm.birthday" type="date" :placeholder="$t('users.selectDate')" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
            <el-form-item :label="$t('users.birthplace')">
              <el-input v-model="detailForm.native_place" :placeholder="$t('users.birthplacePlaceholder')" />
            </el-form-item>
            <el-form-item :label="$t('users.education')">
              <el-select v-model="detailForm.education" :placeholder="$t('users.selectEducation')" clearable style="width: 100%">
                <el-option :label="$t('users.highSchoolBelow')" value="高中及以下" />
                <el-option :label="$t('users.juniorCollege')" value="大专" />
                <el-option :label="$t('users.bachelor')" value="本科" />
                <el-option :label="$t('users.master')" value="硕士" />
                <el-option :label="$t('users.doctor')" value="博士" />
              </el-select>
            </el-form-item>
            <el-form-item :label="$t('users.school')">
              <el-input v-model="detailForm.school" :placeholder="$t('users.schoolPlaceholder')" />
            </el-form-item>
            <el-form-item :label="$t('users.major')">
              <el-input v-model="detailForm.major" :placeholder="$t('users.majorPlaceholder')" />
            </el-form-item>
            <el-form-item :label="$t('users.emergencyContact')">
              <el-input v-model="detailForm.emergency_contact" :placeholder="$t('users.emergencyContactPlaceholder')" />
            </el-form-item>
            <el-form-item :label="$t('users.emergencyPhone')">
              <el-input v-model="detailForm.emergency_phone" :placeholder="$t('users.emergencyPhonePlaceholder')" />
            </el-form-item>
            <el-form-item :label="$t('users.address')">
              <el-input v-model="detailForm.address" type="textarea" :rows="2" :placeholder="$t('users.addressPlaceholder')" />
            </el-form-item>
          </el-form>
        </el-tab-pane>

      </el-tabs>
      <template #footer>
        <el-button @click="showCreateDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="saveUser" :loading="saving">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>

    <!-- 添加/编辑角色对话框 -->
    <el-dialog v-model="showRoleDialog" :title="isEditRole ? $t('users.editRole') : $t('users.newRoleDialog')" width="500px">
      <el-form :model="roleForm" label-width="100px">
        <el-form-item :label="$t('users.roleCode')">
          <el-input v-model="roleForm.name" :placeholder="$t('users.roleCodePlaceholder')" :disabled="isEditRole" />
        </el-form-item>
        <el-form-item :label="$t('users.roleName')">
          <el-input v-model="roleForm.description" :placeholder="$t('users.roleNamePlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('users.level')">
          <el-input-number v-model="roleForm.level" :min="1" :max="10" />
        </el-form-item>
        <el-form-item :label="$t('users.permissions')">
          <el-select v-model="roleForm.permissions" multiple :placeholder="$t('users.selectPermissions')" style="width: 100%;">
            <el-option v-for="perm in permissionOptions" :key="perm.code" :label="perm.label" :value="perm.code" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('users.dataScope')">
          <el-select v-model="roleForm.data_scope" :placeholder="$t('users.selectDataScope')" style="width: 100%;">
            <el-option :label="$t('users.allData')" value="all" />
            <el-option :label="$t('users.deptData')" value="dept" />
            <el-option :label="$t('users.deptAndBelow')" value="dept_and_below" />
            <el-option :label="$t('users.onlySelf')" value="self" />
            <el-option :label="$t('users.custom')" value="custom" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRoleDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="saveRole" :loading="savingRole">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
// 第三次迭代陈思言负责
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { getUsers, getUser, updateUser, getUserStats, getRoles, createRole, updateRole, deleteRole, getPermissions, exportUsers } from '@/api/users'
import { getDepartmentsFlat } from '@/api/departments'
import { getUserIdentities, createUserIdentity, updateUserIdentity, deleteUserIdentity, setPrimaryIdentity as setPrimaryIdentityApi } from '@/api/userIdentities'
import dayjs from 'dayjs'

const { t } = useI18n()

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
  is_active: '',
  entry_month: ''  // 【第二次迭代】按入职月份筛选（统计卡片穿透）
})
const flatDepartments = ref([])

// 预定义职位选项
const positionOptions = [
  t('users.engineer'),
  t('users.seniorEngineer'),
  t('users.productManager'),
  t('users.designer'),
  t('users.testEngineer'),
  t('users.operationSpecialist'),
  t('users.techDirector'),
  t('users.projectManager'),
  t('users.deptManager'),
  t('users.adminSpecialist')
]

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

// 身份列表
const identityList = ref([])
let identityKeyCounter = 0

// 【第二次迭代】档案详情表单
const detailForm = ref({
  employee_status: 'probation',
  entry_date: '',
  probation_end_date: '',
  leave_date: '',
  id_card: '',
  gender: '',
  birthday: '',
  native_place: '',
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
    // 过滤掉空字符串参数，避免后端误判（如 is_active='' 会被解析为 False）
    const activeFilters = Object.fromEntries(
      Object.entries(filter.value).filter(([_, v]) => v !== '' && v !== null && v !== undefined)
    )
    const params = {
      page: page.value,
      per_page: pageSize.value,
      ...activeFilters
    }
    const res = await getUsers(params)
    users.value = res.users
    total.value = res.total
  } catch (error) {
    console.error(t('users.fetchFailed'), error)
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const res = await getUserStats()
    stats.value = res
  } catch (error) {
    console.error(t('users.fetchStatsFailed'), error)
  }
}

// ================================================
// 【第三次迭代于然负责】(1) 角色下拉框排序
// 按照：总经理 → 副总经理 → 数据分析员 → 运营总监 → 财务总监
// → 技术总监 → 部门负责人 → 项目经理 → 项目组长 → 普通成员
// ================================================
const ROLE_SORT_ORDER = [
  'super_admin',
  'deputy_general_manager',
  'data_analyst',
  'operations_director',
  'finance_director',
  'tech_director',
  'department_manager',
  'project_manager',
  'team_leader',
  'member'
]

const fetchRoles = async () => {
  try {
    const res = await getRoles()
    // 按自定义顺序排序
    roles.value = (res.roles || []).sort((a, b) => {
      const indexA = ROLE_SORT_ORDER.indexOf(a.name)
      const indexB = ROLE_SORT_ORDER.indexOf(b.name)
      if (indexA === -1 && indexB === -1) return 0
      if (indexA === -1) return 1
      if (indexB === -1) return -1
      return indexA - indexB
    })
  } catch (error) {
    console.error(t('users.fetchRolesFailed'), error)
  }
}

// 【第二次迭代】获取部门列表
const fetchDepartments = async () => {
  try {
    const res = await getDepartmentsFlat()
    flatDepartments.value = res.departments || []
  } catch (error) {
    console.error(t('users.fetchDeptsFailed'), error)
  }
}

const handleFilterChange = () => {
  page.value = 1
  fetchUsers()
}

const resetFilter = () => {
  filter.value = { search: '', department_id: '', employee_status: '', role_id: '', is_active: '', entry_month: '' }
  handleFilterChange()
}

// 【第二次迭代】统计卡片点击穿透筛选
const handleStatClick = (type) => {
  // 先清空所有筛选
  filter.value = { search: '', department_id: '', employee_status: '', role_id: '', is_active: '', entry_month: '' }
  
  switch (type) {
    case 'total':
      // 总用户：不附加任何筛选，直接显示全部
      break
    case 'active':
      // 在职用户：筛选 is_active = true
      filter.value.is_active = true
      break
    case 'inactive':
      // 离职用户：筛选 is_active = false
      filter.value.is_active = false
      break
    case 'new_this_month':
      // 本月入职：按入职月份筛选
      filter.value.entry_month = dayjs().format('YYYY-MM')
      break
  }
  
  page.value = 1
  fetchUsers()
  const msgMap = {
    total: t('users.filteredAll'),
    active: t('users.filteredActive'),
    inactive: t('users.filteredResigned'),
    new_this_month: t('users.filteredNew')
  }
  ElMessage.info(msgMap[type])
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
    leave_date: row.leave_date || '',
    id_card: row.id_card || '',
    gender: row.gender || '',
    birthday: row.birthday || '',
    native_place: row.native_place || '',
    education: row.education || '',
    school: row.school || '',
    major: row.major || '',
    emergency_contact: row.emergency_contact || '',
    emergency_phone: row.emergency_phone || '',
    address: row.address || ''
  }
  // 填充身份列表
  if (row.identities && row.identities.length > 0) {
    identityList.value = row.identities.map(i => ({
      ...i,
      _key: `existing_${i.id}`,
      role_ids: i.role_ids || []
    }))
  } else {
    // 如果没有身份，用当前部门/职位/角色创建一个默认身份
    identityList.value = [{
      _key: `default_${++identityKeyCounter}`,
      id: null,
      department_id: row.department_id || null,
      position: row.position || '',
      role_ids: row.roles ? row.roles.map(r => r.id) : [],
      is_primary: true
    }]
  }
  showCreateDialog.value = true
}

const addIdentity = () => {
  identityList.value.push({
    _key: `new_${++identityKeyCounter}`,
    id: null,
    department_id: null,
    position: '',
    role_ids: [],
    is_primary: identityList.value.length === 0
  })
}

const removeIdentity = (index) => {
  identityList.value.splice(index, 1)
  // 如果删除后没有主身份，将第一个设为主身份
  if (identityList.value.length > 0 && !identityList.value.some(i => i.is_primary)) {
    identityList.value[0].is_primary = true
  }
}

const setPrimaryIdentityLocal = (index) => {
  identityList.value.forEach((item, idx) => {
    item.is_primary = idx === index
  })
}

const saveUser = async () => {
  if (!isEdit.value && (!form.value.username || !form.value.email)) {
    ElMessage.warning(t('users.pleaseFillInfo'))
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
        // 身份列表
        identities: identityList.value.map(item => ({
          id: item.id,
          department_id: item.department_id,
          position: item.position,
          role_ids: item.role_ids,
          is_primary: item.is_primary
        })),
        // 【第二次迭代】合并档案详情字段
        ...detailForm.value
      }
      const res = await updateUser(form.value.id, payload)
      ElMessage.success(res.message || t('users.updateSuccess'))
      if (res.require_relogin) {
        ElMessage.warning(t('users.permissionChanged'))
      }
    }
    showCreateDialog.value = false
    fetchUsers()
    fetchStats()
  } catch (error) {
    console.error(t('users.saveFailed'), error)
    ElMessage.error(error.response?.data?.message || t('users.saveFailed'))
  } finally {
    saving.value = false
  }
}

const toggleStatus = async (row) => {
  const action = row.is_active ? t('users.disable') : t('users.enable')
  try {
    await ElMessageBox.confirm(`${t('users.operationConfirmPrefix')}${action}${t('users.operationConfirmSuffix')}`, t('common.tip'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning'
    })
    
    await updateUser(row.id, { is_active: !row.is_active })
    ElMessage.success(`${action}${t('common.success')}`)
    fetchUsers()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(`${action}${t('common.failed')}`, error)
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
    ElMessage.success(t('users.exportSuccess'))
  } catch (error) {
    ElMessage.error(t('users.exportFailed'))
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
    await ElMessageBox.confirm(`${t('users.deleteRoleConfirmPrefix')} "${role.description}" ${t('users.deleteConfirmSuffix')}`, t('common.tip'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning'
    })
    await deleteRole(role.id)
    ElMessage.success(t('users.roleDeleted'))
    fetchRoles()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || t('users.saveFailed'))
    }
  }
}

const saveRole = async () => {
  if (!roleForm.value.name || !roleForm.value.description) {
    ElMessage.warning(t('users.pleaseFillInfo'))
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
      ElMessage.success(t('users.roleUpdateSuccess'))
    } else {
      await createRole({
        name: roleForm.value.name,
        description: roleForm.value.description,
        level: roleForm.value.level,
        permissions: roleForm.value.permissions
      })
      ElMessage.success(t('users.roleCreateSuccess'))
    }
    showRoleDialog.value = false
    roleForm.value = { id: '', name: '', description: '', level: 4, permissions: [], data_scope: 'self', data_scope_custom: [] }
    fetchRoles()
  } catch (error) {
    console.error(t('users.saveRoleFailed'), error)
    ElMessage.error(error.response?.data?.message || t('users.saveFailed'))
  } finally {
    savingRole.value = false
  }
}

const fetchPermissions = async () => {
  try {
    const res = await getPermissions()
    permissionOptions.value = res.permissions || []
  } catch (error) {
    console.error(t('users.fetchPermsFailed'), error)
  }
}

// 【第二次迭代】员工状态显示转换
const employeeStatusLabel = (status) => {
  const map = {
    probation: t('users.probation'),
    active: t('users.formal'),
    pending_leave: t('users.pendingResign'),
    left: t('users.resigned'),
    suspended: t('users.suspended')
  }
  return map[status] || status || t('users.probation')
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
      transition: all 0.2s ease;
      .stat-value {
        font-size: 28px;
        font-weight: 600;
        color: #333;
        margin-bottom: 8px;
        &.success { color: #67c23a; }
        &.warning { color: #e6a23c; }
        &.info { color: #909399; }
      }
      .stat-label {
        font-size: 14px;
        color: #666;
      }
      // 【第二次迭代】统计卡片可点击样式
      &.clickable {
        cursor: pointer;
        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        }
        &:active {
          transform: translateY(0);
        }
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

  // 身份管理样式
  .identities-section {
    .identity-card {
      border: 1px solid #e4e7ed;
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 12px;
      background: #fafafa;

      .identity-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid #e4e7ed;

        .identity-title {
          font-weight: 600;
          font-size: 14px;
          color: #303133;
        }

        .identity-actions {
          margin-left: auto;
          display: flex;
          gap: 8px;
        }
      }
    }
  }
}
</style>
