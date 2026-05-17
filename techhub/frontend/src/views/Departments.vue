<template>
  <!-- 【UI重构】组织架构管理页面 - 支持部门/角色/职位三分类 -->
  <div class="departments-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>组织架构</h2>
        <span class="header-subtitle">管理公司部门、成员及组织信息</span>
      </div>
      <el-button type="primary" @click="openAddDialog()" v-if="userStore.hasPermission('user_manage')">
        <el-icon><Plus /></el-icon>
        {{ addButtonText }}
      </el-button>
    </div>

    <!-- 分类切换标签 -->
    <div class="category-tabs">
      <div
        v-for="tab in categoryTabs"
        :key="tab.key"
        class="tab-item"
        :class="{ active: activeCategory === tab.key }"
        @click="switchCategory(tab.key)"
      >
        <el-icon size="16"><component :is="tab.icon" /></el-icon>
        <span>{{ tab.label }}</span>
      </div>
    </div>

    <el-row :gutter="20">
      <!-- 左侧：组织树/角色列表/职位列表 -->
      <el-col :xs="24" :md="9" class="left-column">
        <!-- 列表卡片 -->
        <el-card class="tree-card" :body-style="{ padding: '0' }">
          <div class="card-title">{{ leftCardTitle }}</div>
          <div class="tree-search">
            <el-input
              v-model="treeSearch"
              :placeholder="searchPlaceholder"
              clearable
              :prefix-icon="SearchIcon"
              size="small"
            />
            <el-button size="small" class="refresh-btn" @click="refreshData">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>
          <div class="tree-wrapper">
            <!-- 部门树 -->
            <el-tree
              v-if="activeCategory === 'department'"
              :data="filteredDepartmentTree"
              :props="{ label: 'name', children: 'children' }"
              node-key="id"
              default-expand-all
              highlight-current
              :current-node-key="currentDept?.id"
              @node-click="handleNodeClick"
              v-loading="treeLoading"
            >
              <template #default="{ node, data }">
                <div class="dept-tree-node" :class="{ active: currentDept?.id === data.id }">
                  <div class="node-left">
                    <el-icon class="node-icon"><OfficeBuilding /></el-icon>
                    <span class="node-label">{{ node.label }}</span>
                  </div>
                  <span class="node-count">{{ data.total_member_count }}人</span>
                </div>
              </template>
            </el-tree>

            <!-- 角色列表 -->
            <div v-else-if="activeCategory === 'role'" class="simple-list" v-loading="treeLoading">
              <div
                v-for="role in filteredRoleList"
                :key="role.id"
                class="list-item"
                :class="{ active: currentRole?.id === role.id }"
                @click="handleRoleClick(role)"
              >
                <div class="node-left">
                  <el-icon class="node-icon"><UserFilled /></el-icon>
                  <div class="item-info">
                    <span class="node-label">{{ role.description || role.name }}</span>
                    <span class="item-sub">{{ role.name }}</span>
                  </div>
                </div>
                <span class="node-count">{{ role.user_count }}人</span>
              </div>
            </div>

            <!-- 职位列表 -->
            <div v-else-if="activeCategory === 'position'" class="simple-list" v-loading="treeLoading">
              <div
                v-for="pos in filteredPositionList"
                :key="pos.id"
                class="list-item"
                :class="{ active: currentPosition?.id === pos.id }"
                @click="handlePositionClick(pos)"
              >
                <div class="node-left">
                  <el-icon class="node-icon"><Postcard /></el-icon>
                  <span class="node-label">{{ pos.name }}</span>
                </div>
                <span class="node-count">{{ pos.user_count }}人</span>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 分布饼图 -->
        <el-card class="chart-card" style="margin-top: 16px;">
          <div class="card-title">{{ chartTitle }}</div>
          <div ref="pieChart" class="pie-chart-container"></div>
        </el-card>
      </el-col>

      <!-- 右侧：统计 + 详情 + 成员 -->
      <el-col :xs="24" :md="15" class="right-column">
        <!-- 统计卡片 -->
        <el-row :gutter="16" class="stats-row">
          <el-col :xs="12" :sm="6" v-for="(stat, idx) in currentStats" :key="idx">
            <div class="stat-card">
              <div class="stat-icon-wrapper" :style="stat.iconStyle">
                <el-icon size="20"><component :is="stat.icon" /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value" :style="{ color: stat.color }">{{ stat.value }}</div>
                <div class="stat-label">{{ stat.label }}</div>
                <div class="stat-trend">{{ stat.trend }}</div>
              </div>
            </div>
          </el-col>
        </el-row>

        <!-- ========== 部门详情面板 ========== -->
        <template v-if="activeCategory === 'department' && currentDept">
          <el-card class="detail-card">
            <div class="detail-header">
              <div class="detail-title">部门详情</div>
              <div class="detail-actions" v-if="userStore.hasPermission('user_manage')">
                <el-button text size="small" @click="openEditDialog(currentDept)">编辑</el-button>
                <el-button text type="danger" size="small" @click="removeDept(currentDept)">删除</el-button>
              </div>
            </div>
            <div class="detail-body">
              <div class="detail-left">
                <div class="dept-name-row">
                  <div class="dept-icon-large" style="background: #e6f7ff; color: #1890ff;">
                    <el-icon size="24"><OfficeBuilding /></el-icon>
                  </div>
                  <div class="dept-name-info">
                    <span class="dept-name">{{ currentDept.name }}</span>
                  </div>
                </div>
                <el-row :gutter="40" class="detail-grid">
                  <el-col :span="8">
                    <div class="grid-item">
                      <div class="grid-label">部门编码</div>
                      <div class="grid-value">{{ currentDept.code }}</div>
                    </div>
                  </el-col>
                  <el-col :span="8">
                    <div class="grid-item">
                      <div class="grid-label">直属人数</div>
                      <div class="grid-value">{{ currentDept.member_count }}人</div>
                    </div>
                  </el-col>
                  <el-col :span="8">
                    <div class="grid-item">
                      <div class="grid-label">总人数（含子部门）</div>
                      <div class="grid-value">{{ currentDept.total_member_count }}人</div>
                    </div>
                  </el-col>
                  <el-col :span="8">
                    <div class="grid-item">
                      <div class="grid-label">部门负责人</div>
                      <div class="grid-value">{{ currentDept.manager?.real_name || '-' }}</div>
                    </div>
                  </el-col>
                  <el-col :span="16">
                    <div class="grid-item">
                      <div class="grid-label">描述</div>
                      <div class="grid-value">{{ currentDept.description || '-' }}</div>
                    </div>
                  </el-col>
                </el-row>
              </div>
            </div>
          </el-card>

          <!-- 部门成员表格 -->
          <el-card class="member-card">
            <div class="member-header">
              <div class="member-title">部门成员</div>
              <el-button type="primary" size="small" @click="openAddMemberDialog" v-if="userStore.hasPermission('user_manage')">
                <el-icon><Plus /></el-icon>添加成员
              </el-button>
            </div>
            <el-table :data="members" v-loading="memberLoading" size="small" class="member-table">
              <el-table-column label="姓名" min-width="140">
                <template #default="{ row }">
                  <div class="user-cell">
                    <el-avatar :size="32" :src="row.avatar">{{ row.real_name?.charAt(0) || 'U' }}</el-avatar>
                    <span class="user-name">{{ row.real_name || row.username }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="职位" prop="position" width="140" />
              <el-table-column label="邮箱" prop="email" min-width="180" />
              <el-table-column label="电话" width="130">
                <template #default="{ row }">{{ maskPhone(row.phone) }}</template>
              </el-table-column>
              <el-table-column label="状态" width="90">
                <template #default="{ row }">
                  <div class="status-dot">
                    <span class="dot" :class="row.is_active ? 'active' : 'inactive'"></span>
                    <span>{{ row.is_active ? '在职' : '离职' }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80" fixed="right" v-if="userStore.hasPermission('user_manage')">
                <template #default="{ row }">
                  <el-dropdown trigger="click" @command="(cmd) => handleMemberCommand(cmd, row)">
                    <el-button type="primary" link><el-icon><MoreFilled /></el-icon></el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item command="transfer">转移</el-dropdown-item>
                        <el-dropdown-item command="remove" style="color: #f56c6c;">移除</el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </template>
              </el-table-column>
            </el-table>
            <div class="member-footer">
              <span class="total-text">共 {{ memberTotal }} 人</span>
              <el-pagination
                v-model:current-page="memberPage"
                v-model:page-size="memberPageSize"
                :total="memberTotal"
                layout="prev, pager, next, sizes"
                :page-sizes="[10, 20, 50]"
                @current-change="fetchMembers"
                @size-change="fetchMembers"
                small
              />
            </div>
          </el-card>
        </template>

        <!-- ========== 角色详情面板 ========== -->
        <template v-if="activeCategory === 'role' && currentRole">
          <el-card class="detail-card">
            <div class="detail-header">
              <div class="detail-title">角色详情</div>
              <div class="detail-actions" v-if="userStore.hasPermission('user_manage')">
                <el-button text size="small" @click="openEditDialog(currentRole)">编辑</el-button>
                <el-button text type="danger" size="small" @click="removeRole(currentRole)">删除</el-button>
              </div>
            </div>
            <div class="detail-body">
              <div class="detail-left">
                <div class="dept-name-row">
                  <div class="dept-icon-large" style="background: #f6ffed; color: #52c41a;">
                    <el-icon size="24"><UserFilled /></el-icon>
                  </div>
                  <div class="dept-name-info">
                    <span class="dept-name">{{ currentRole.description || currentRole.name }}</span>
                    <el-tag size="small" type="success">{{ currentRole.name }}</el-tag>
                  </div>
                </div>
                <el-row :gutter="40" class="detail-grid">
                  <el-col :span="8">
                    <div class="grid-item">
                      <div class="grid-label">角色编码</div>
                      <div class="grid-value">{{ currentRole.name }}</div>
                    </div>
                  </el-col>
                  <el-col :span="8">
                    <div class="grid-item">
                      <div class="grid-label">等级</div>
                      <div class="grid-value">Level {{ currentRole.level }}</div>
                    </div>
                  </el-col>
                  <el-col :span="8">
                    <div class="grid-item">
                      <div class="grid-label">成员人数</div>
                      <div class="grid-value">{{ currentRole.user_count }}人</div>
                    </div>
                  </el-col>
                  <el-col :span="8">
                    <div class="grid-item">
                      <div class="grid-label">数据范围</div>
                      <div class="grid-value">{{ currentRole.data_scope || 'self' }}</div>
                    </div>
                  </el-col>
                  <el-col :span="16">
                    <div class="grid-item">
                      <div class="grid-label">描述</div>
                      <div class="grid-value">{{ currentRole.description || '-' }}</div>
                    </div>
                  </el-col>
                </el-row>
              </div>
            </div>
          </el-card>

          <!-- 角色成员表格 -->
          <el-card class="member-card">
            <div class="member-header">
              <div class="member-title">角色成员</div>
              <el-button type="primary" size="small" @click="openAddRoleMemberDialog" v-if="userStore.hasPermission('user_manage')">
                <el-icon><Plus /></el-icon>添加成员
              </el-button>
            </div>
            <el-table :data="roleMembers" v-loading="roleMemberLoading" size="small" class="member-table">
              <el-table-column label="姓名" min-width="140">
                <template #default="{ row }">
                  <div class="user-cell">
                    <el-avatar :size="32" :src="row.avatar">{{ row.real_name?.charAt(0) || 'U' }}</el-avatar>
                    <span class="user-name">{{ row.real_name || row.username }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="职位" prop="position" width="140" />
              <el-table-column label="邮箱" prop="email" min-width="180" />
              <el-table-column label="电话" width="130">
                <template #default="{ row }">{{ maskPhone(row.phone) }}</template>
              </el-table-column>
              <el-table-column label="状态" width="90">
                <template #default="{ row }">
                  <div class="status-dot">
                    <span class="dot" :class="row.is_active ? 'active' : 'inactive'"></span>
                    <span>{{ row.is_active ? '在职' : '离职' }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80" fixed="right" v-if="userStore.hasPermission('user_manage')">
                <template #default="{ row }">
                  <el-button type="danger" link size="small" @click="handleRemoveRoleMember(row)">移除</el-button>
                </template>
              </el-table-column>
            </el-table>
            <div class="member-footer">
              <span class="total-text">共 {{ roleMemberTotal }} 人</span>
              <el-pagination
                v-model:current-page="roleMemberPage"
                v-model:page-size="roleMemberPageSize"
                :total="roleMemberTotal"
                layout="prev, pager, next, sizes"
                :page-sizes="[10, 20, 50]"
                @current-change="fetchRoleMembers"
                @size-change="fetchRoleMembers"
                small
              />
            </div>
          </el-card>
        </template>

        <!-- ========== 职位详情面板 ========== -->
        <template v-if="activeCategory === 'position' && currentPosition">
          <el-card class="detail-card">
            <div class="detail-header">
              <div class="detail-title">职位详情</div>
              <div class="detail-actions" v-if="userStore.hasPermission('user_manage')">
                <el-button text size="small" @click="openEditDialog(currentPosition)">编辑</el-button>
                <el-button text type="danger" size="small" @click="removePosition(currentPosition)">删除</el-button>
              </div>
            </div>
            <div class="detail-body">
              <div class="detail-left">
                <div class="dept-name-row">
                  <div class="dept-icon-large" style="background: #fff7e6; color: #fa8c16;">
                    <el-icon size="24"><Postcard /></el-icon>
                  </div>
                  <div class="dept-name-info">
                    <span class="dept-name">{{ currentPosition.name }}</span>
                  </div>
                </div>
                <el-row :gutter="40" class="detail-grid">
                  <el-col :span="12">
                    <div class="grid-item">
                      <div class="grid-label">职位名称</div>
                      <div class="grid-value">{{ currentPosition.name }}</div>
                    </div>
                  </el-col>
                  <el-col :span="12">
                    <div class="grid-item">
                      <div class="grid-label">在职人数</div>
                      <div class="grid-value">{{ currentPosition.user_count }}人</div>
                    </div>
                  </el-col>
                </el-row>
              </div>
            </div>
          </el-card>

          <!-- 职位成员表格 -->
          <el-card class="member-card">
            <div class="member-header">
              <div class="member-title">职位成员</div>
              <el-button type="primary" size="small" @click="openAddPositionMemberDialog" v-if="userStore.hasPermission('user_manage')">
                <el-icon><Plus /></el-icon>添加成员
              </el-button>
            </div>
            <el-table :data="positionMembers" v-loading="positionMemberLoading" size="small" class="member-table">
              <el-table-column label="姓名" min-width="140">
                <template #default="{ row }">
                  <div class="user-cell">
                    <el-avatar :size="32" :src="row.avatar">{{ row.real_name?.charAt(0) || 'U' }}</el-avatar>
                    <span class="user-name">{{ row.real_name || row.username }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="部门" prop="department" width="140" />
              <el-table-column label="邮箱" prop="email" min-width="180" />
              <el-table-column label="电话" width="130">
                <template #default="{ row }">{{ maskPhone(row.phone) }}</template>
              </el-table-column>
              <el-table-column label="状态" width="90">
                <template #default="{ row }">
                  <div class="status-dot">
                    <span class="dot" :class="row.is_active ? 'active' : 'inactive'"></span>
                    <span>{{ row.is_active ? '在职' : '离职' }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80" fixed="right" v-if="userStore.hasPermission('user_manage')">
                <template #default="{ row }">
                  <el-dropdown trigger="click" @command="(cmd) => handlePositionMemberCommand(cmd, row)">
                    <el-button type="primary" link><el-icon><MoreFilled /></el-icon></el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item command="transfer">转移</el-dropdown-item>
                        <el-dropdown-item command="remove" style="color: #f56c6c;">移除</el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </template>
              </el-table-column>
            </el-table>
            <div class="member-footer">
              <span class="total-text">共 {{ positionMemberTotal }} 人</span>
              <el-pagination
                v-model:current-page="positionMemberPage"
                v-model:page-size="positionMemberPageSize"
                :total="positionMemberTotal"
                layout="prev, pager, next, sizes"
                :page-sizes="[10, 20, 50]"
                @current-change="fetchPositionMembers"
                @size-change="fetchPositionMembers"
                small
              />
            </div>
          </el-card>
        </template>

        <!-- 未选择提示 -->
        <el-empty v-if="!hasCurrentItem" description="请从左侧选择一项查看详情" style="margin-top: 40px;" />
      </el-col>
    </el-row>

    <!-- ========== 对话框 ========== -->

    <!-- 部门添加/编辑对话框 -->
    <el-dialog v-model="showDeptDialog" :title="isEdit ? '编辑部门' : '添加部门'" width="500px">
      <el-form :model="deptForm" label-width="100px">
        <el-form-item label="部门名称" required>
          <el-input v-model="deptForm.name" placeholder="请输入部门名称" />
        </el-form-item>
        <el-form-item label="部门编码" required>
          <el-input v-model="deptForm.code" placeholder="如：DEV-001" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="上级部门">
          <el-tree-select v-model="deptForm.parent_id" :data="departmentTree"
            :props="{ label: 'name', value: 'id', children: 'children' }"
            placeholder="选择上级部门" check-strictly clearable style="width: 100%" />
        </el-form-item>
        <el-form-item label="部门负责人">
          <el-select v-model="deptForm.manager_id" placeholder="选择负责人" clearable style="width: 100%">
            <el-option v-for="user in managerOptions" :key="user.id" :label="user.real_name" :value="user.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序号">
          <el-input-number v-model="deptForm.sort_order" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="deptForm.description" type="textarea" :rows="2" placeholder="部门描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDeptDialog = false">取消</el-button>
        <el-button type="primary" @click="saveDept" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 角色添加/编辑对话框 -->
    <el-dialog v-model="showRoleDialog" :title="isEdit ? '编辑角色' : '添加角色'" width="500px">
      <el-form :model="roleForm" label-width="100px">
        <el-form-item label="角色名称" required>
          <el-input v-model="roleForm.name" placeholder="如：project_manager" />
        </el-form-item>
        <el-form-item label="显示名称" required>
          <el-input v-model="roleForm.description" placeholder="如：项目经理" />
        </el-form-item>
        <el-form-item label="等级">
          <el-input-number v-model="roleForm.level" :min="1" :max="10" style="width: 100%" />
        </el-form-item>
        <el-form-item label="数据范围">
          <el-select v-model="roleForm.data_scope" style="width: 100%">
            <el-option label="全部" value="all" />
            <el-option label="本部门" value="dept" />
            <el-option label="本部门及子部门" value="dept_and_below" />
            <el-option label="仅自己" value="self" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="roleForm.description" type="textarea" :rows="2" placeholder="角色描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRoleDialog = false">取消</el-button>
        <el-button type="primary" @click="saveRole" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 职位添加/编辑对话框 -->
    <el-dialog v-model="showPositionDialog" :title="isEdit ? '编辑职位' : '添加职位'" width="400px">
      <el-form :model="positionForm" label-width="80px">
        <el-form-item label="职位名称" required>
          <el-input v-model="positionForm.name" placeholder="请输入职位名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPositionDialog = false">取消</el-button>
        <el-button type="primary" @click="savePosition" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 添加成员到部门对话框 -->
    <el-dialog v-model="showAddMemberDialog" title="添加成员到部门" width="600px">
      <div v-loading="addMemberLoading">
        <el-empty v-if="!noDeptUsers.length" description="暂无可分配的用户（所有用户已分配部门）" />
        <el-table v-else :data="noDeptUsers" size="small" max-height="400">
          <el-table-column label="姓名" min-width="120">
            <template #default="{ row }">
              <div style="display: flex; align-items: center; gap: 8px;">
                <el-avatar :size="28">{{ row.real_name?.charAt(0) || 'U' }}</el-avatar>
                <span>{{ row.real_name || row.username }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="职位" prop="position" width="120" />
          <el-table-column label="邮箱" prop="email" min-width="180" />
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click="handleAddMember(row)">添加</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>

    <!-- 添加成员到角色对话框 -->
    <el-dialog v-model="showAddRoleMemberDialog" title="添加成员到角色" width="600px">
      <div v-loading="addMemberLoading">
        <el-empty v-if="!noRoleUsers.length" description="暂无可分配的用户" />
        <el-table v-else :data="noRoleUsers" size="small" max-height="400">
          <el-table-column label="姓名" min-width="120">
            <template #default="{ row }">
              <div style="display: flex; align-items: center; gap: 8px;">
                <el-avatar :size="28">{{ row.real_name?.charAt(0) || 'U' }}</el-avatar>
                <span>{{ row.real_name || row.username }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="职位" prop="position" width="120" />
          <el-table-column label="邮箱" prop="email" min-width="180" />
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click="handleAddRoleMember(row)">添加</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>

    <!-- 添加成员到职位对话框 -->
    <el-dialog v-model="showAddPositionMemberDialog" title="添加成员到职位" width="600px">
      <div v-loading="addMemberLoading">
        <el-empty v-if="!noPositionUsers.length" description="暂无可分配的用户" />
        <el-table v-else :data="noPositionUsers" size="small" max-height="400">
          <el-table-column label="姓名" min-width="120">
            <template #default="{ row }">
              <div style="display: flex; align-items: center; gap: 8px;">
                <el-avatar :size="28">{{ row.real_name?.charAt(0) || 'U' }}</el-avatar>
                <span>{{ row.real_name || row.username }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="部门" prop="department" width="120" />
          <el-table-column label="邮箱" prop="email" min-width="180" />
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click="handleAddPositionMember(row)">添加</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>

    <!-- 转移成员对话框 -->
    <el-dialog v-model="showTransferDialog" title="转移成员" width="400px">
      <div v-if="transferringUser">
        <p style="margin-bottom: 16px;">
          将 <strong>{{ transferringUser.real_name || transferringUser.username }}</strong>
          {{ transferSourceText }}
        </p>
        <el-tree-select
          v-if="activeCategory === 'department'"
          v-model="transferTargetId"
          :data="departmentTree"
          :props="{ label: 'name', value: 'id', children: 'children' }"
          placeholder="选择目标部门"
          check-strictly
          style="width: 100%"
        />
        <el-select v-else-if="activeCategory === 'position'" v-model="transferTargetName" placeholder="选择目标职位" style="width: 100%">
          <el-option v-for="pos in positionList" :key="pos.id" :label="pos.name" :value="pos.name" />
        </el-select>
      </div>
      <template #footer>
        <el-button @click="showTransferDialog = false">取消</el-button>
        <el-button type="primary" @click="handleTransfer">确认转移</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import {
  getDepartments, createDepartment, updateDepartment, deleteDepartment,
  getDepartmentMembers, getDepartmentStats,
  addDepartmentMember, removeDepartmentMember, transferDepartmentMember
} from '@/api/departments'
import {
  getRoles, createRole, updateRole, deleteRole,
  getRoleMembers, getRoleStats, addRoleMember, removeRoleMember
} from '@/api/roles'
import {
  getPositions, createPosition, updatePosition, deletePosition,
  getPositionMembers, getPositionStats, addPositionMember, removePositionMember,
  transferPositionMember, getUsersWithoutPosition
} from '@/api/positions'
import { getManagers, getUsers } from '@/api/users'
import * as echarts from 'echarts'
import {
  Search as SearchIcon, OfficeBuilding, UserFilled, User, Refresh,
  Plus, MoreFilled, Postcard
} from '@element-plus/icons-vue'

const userStore = useUserStore()

// ==================== 分类切换 ====================
const activeCategory = ref('department')
const categoryTabs = [
  { key: 'department', label: '部门', icon: 'OfficeBuilding' },
  { key: 'role', label: '角色', icon: 'UserFilled' },
  { key: 'position', label: '职位', icon: 'Postcard' }
]

const switchCategory = (key) => {
  activeCategory.value = key
  treeSearch.value = ''
  refreshData()
}

const addButtonText = computed(() => {
  const map = { department: '添加部门', role: '添加角色', position: '添加职位' }
  return map[activeCategory.value]
})

const leftCardTitle = computed(() => {
  const map = { department: '组织树', role: '角色列表', position: '职位列表' }
  return map[activeCategory.value]
})

const searchPlaceholder = computed(() => {
  const map = { department: '搜索部门名称', role: '搜索角色名称', position: '搜索职位名称' }
  return map[activeCategory.value]
})

const chartTitle = computed(() => {
  const map = { department: '部门成员分布', role: '角色成员分布', position: '职位成员分布' }
  return map[activeCategory.value]
})

const hasCurrentItem = computed(() => {
  if (activeCategory.value === 'department') return !!currentDept.value
  if (activeCategory.value === 'role') return !!currentRole.value
  if (activeCategory.value === 'position') return !!currentPosition.value
  return false
})

// ==================== 部门数据 ====================
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

// ==================== 角色数据 ====================
const roleList = ref([])
const currentRole = ref(null)
const roleMembers = ref([])
const roleMemberLoading = ref(false)
const roleMemberPage = ref(1)
const roleMemberPageSize = ref(10)
const roleMemberTotal = ref(0)
const roleStats = ref({})

// ==================== 职位数据 ====================
const positionList = ref([])
const currentPosition = ref(null)
const positionMembers = ref([])
const positionMemberLoading = ref(false)
const positionMemberPage = ref(1)
const positionMemberPageSize = ref(10)
const positionMemberTotal = ref(0)
const positionStats = ref({})

// ==================== 通用 ====================
const treeSearch = ref('')
const pieChart = ref(null)
let pieChartInstance = null

// ==================== 搜索过滤 ====================
const filteredDepartmentTree = computed(() => {
  if (!treeSearch.value || activeCategory.value !== 'department') return departmentTree.value
  const filter = (nodes) => {
    return nodes.filter(node => {
      const match = node.name.toLowerCase().includes(treeSearch.value.toLowerCase())
      const children = node.children ? filter(node.children) : []
      if (children.length) { node.children = children; return true }
      return match
    })
  }
  return filter(JSON.parse(JSON.stringify(departmentTree.value)))
})

const filteredRoleList = computed(() => {
  if (!treeSearch.value || activeCategory.value !== 'role') return roleList.value
  return roleList.value.filter(r =>
    (r.description || r.name).toLowerCase().includes(treeSearch.value.toLowerCase())
  )
})

const filteredPositionList = computed(() => {
  if (!treeSearch.value || activeCategory.value !== 'position') return positionList.value
  return positionList.value.filter(p =>
    p.name.toLowerCase().includes(treeSearch.value.toLowerCase())
  )
})

// ==================== 统计数据 ====================
const currentStats = computed(() => {
  if (activeCategory.value === 'department') {
    return [
      { value: stats.value.total_departments || 0, label: '部门总数', trend: '较上月 +2', icon: 'OfficeBuilding', iconStyle: 'background: #e6f7ff; color: #1890ff;', color: '#1890ff' },
      { value: stats.value.total_members_with_dept || 0, label: '已分配部门', trend: '较上月 +5', icon: 'UserFilled', iconStyle: 'background: #f6ffed; color: #52c41a;', color: '#52c41a' },
      { value: currentDept.value?.total_member_count || 0, label: '当前部门人数', trend: '较上月 +0', icon: 'User', iconStyle: 'background: #fff7e6; color: #fa8c16;', color: '#fa8c16' },
      { value: stats.value.total_members_with_dept || 0, label: '公司总人数', trend: '较上月 +3', icon: 'UserFilled', iconStyle: 'background: #f9f0ff; color: #722ed1;', color: '#722ed1' }
    ]
  } else if (activeCategory.value === 'role') {
    return [
      { value: roleStats.value.total_roles || 0, label: '角色总数', trend: '较上月 +1', icon: 'UserFilled', iconStyle: 'background: #e6f7ff; color: #1890ff;', color: '#1890ff' },
      { value: roleStats.value.total_users_with_role || 0, label: '已分配角色', trend: '较上月 +3', icon: 'UserFilled', iconStyle: 'background: #f6ffed; color: #52c41a;', color: '#52c41a' },
      { value: currentRole.value?.user_count || 0, label: '当前角色人数', trend: '较上月 +0', icon: 'User', iconStyle: 'background: #fff7e6; color: #fa8c16;', color: '#fa8c16' },
      { value: roleStats.value.total_users_with_role || 0, label: '公司总人数', trend: '较上月 +3', icon: 'UserFilled', iconStyle: 'background: #f9f0ff; color: #722ed1;', color: '#722ed1' }
    ]
  } else {
    return [
      { value: positionStats.value.total_positions || 0, label: '职位总数', trend: '较上月 +1', icon: 'Postcard', iconStyle: 'background: #e6f7ff; color: #1890ff;', color: '#1890ff' },
      { value: positionStats.value.total_users_with_position || 0, label: '已分配职位', trend: '较上月 +2', icon: 'UserFilled', iconStyle: 'background: #f6ffed; color: #52c41a;', color: '#52c41a' },
      { value: currentPosition.value?.user_count || 0, label: '当前职位人数', trend: '较上月 +0', icon: 'User', iconStyle: 'background: #fff7e6; color: #fa8c16;', color: '#fa8c16' },
      { value: positionStats.value.total_users_with_position || 0, label: '公司总人数', trend: '较上月 +3', icon: 'UserFilled', iconStyle: 'background: #f9f0ff; color: #722ed1;', color: '#722ed1' }
    ]
  }
})

// ==================== 数据获取 ====================
const fetchDepartments = async () => {
  treeLoading.value = true
  try {
    const res = await getDepartments()
    departmentTree.value = res.departments || []
  } catch (error) { console.error('获取部门失败', error) }
  finally { treeLoading.value = false }
}

const fetchRoles = async () => {
  treeLoading.value = true
  try {
    const res = await getRoles()
    roleList.value = res.roles || []
  } catch (error) { console.error('获取角色失败', error) }
  finally { treeLoading.value = false }
}

const fetchPositions = async () => {
  treeLoading.value = true
  try {
    const res = await getPositions()
    positionList.value = res.positions || []
  } catch (error) { console.error('获取职位失败', error) }
  finally { treeLoading.value = false }
}

const fetchStats = async () => {
  try {
    if (activeCategory.value === 'department') {
      const res = await getDepartmentStats()
      stats.value = res
    } else if (activeCategory.value === 'role') {
      const res = await getRoleStats()
      roleStats.value = res
    } else {
      const res = await getPositionStats()
      positionStats.value = res
    }
  } catch (error) { console.error('获取统计失败', error) }
}

const fetchMembers = async () => {
  if (!currentDept.value) return
  memberLoading.value = true
  try {
    const res = await getDepartmentMembers(currentDept.value.id, {
      page: memberPage.value, per_page: memberPageSize.value, include_sub: false
    })
    members.value = res.members || []
    memberTotal.value = res.total || 0
  } catch (error) { console.error('获取成员失败', error) }
  finally { memberLoading.value = false }
}

const fetchRoleMembers = async () => {
  if (!currentRole.value) return
  roleMemberLoading.value = true
  try {
    const res = await getRoleMembers(currentRole.value.id, {
      page: roleMemberPage.value, per_page: roleMemberPageSize.value
    })
    roleMembers.value = res.members || []
    roleMemberTotal.value = res.total || 0
  } catch (error) { console.error('获取角色成员失败', error) }
  finally { roleMemberLoading.value = false }
}

const fetchPositionMembers = async () => {
  if (!currentPosition.value) return
  positionMemberLoading.value = true
  try {
    const res = await getPositionMembers(currentPosition.value.name, {
      page: positionMemberPage.value, per_page: positionMemberPageSize.value
    })
    positionMembers.value = res.members || []
    positionMemberTotal.value = res.total || 0
  } catch (error) { console.error('获取职位成员失败', error) }
  finally { positionMemberLoading.value = false }
}

const refreshData = () => {
  if (activeCategory.value === 'department') {
    fetchDepartments()
    fetchStats()
    if (currentDept.value) fetchMembers()
  } else if (activeCategory.value === 'role') {
    fetchRoles()
    fetchStats()
    if (currentRole.value) fetchRoleMembers()
  } else {
    fetchPositions()
    fetchStats()
    if (currentPosition.value) fetchPositionMembers()
  }
}

// ==================== 点击事件 ====================
const handleNodeClick = (data) => {
  currentDept.value = data
  memberPage.value = 1
  fetchMembers()
}

const handleRoleClick = (role) => {
  currentRole.value = role
  roleMemberPage.value = 1
  fetchRoleMembers()
}

const handlePositionClick = (pos) => {
  currentPosition.value = pos
  positionMemberPage.value = 1
  fetchPositionMembers()
}

// ==================== 对话框状态 ====================
const showDeptDialog = ref(false)
const showRoleDialog = ref(false)
const showPositionDialog = ref(false)
const isEdit = ref(false)
const saving = ref(false)

const deptForm = ref({ id: '', name: '', code: '', parent_id: null, manager_id: null, sort_order: 0, description: '' })
const roleForm = ref({ id: '', name: '', description: '', level: 4, data_scope: 'self', permissions: [] })
const positionForm = ref({ oldName: '', name: '' })

const openAddDialog = () => {
  isEdit.value = false
  if (activeCategory.value === 'department') {
    deptForm.value = { id: '', name: '', code: '', parent_id: null, manager_id: null, sort_order: 0, description: '' }
    showDeptDialog.value = true
  } else if (activeCategory.value === 'role') {
    roleForm.value = { id: '', name: '', description: '', level: 4, data_scope: 'self', permissions: [] }
    showRoleDialog.value = true
  } else {
    positionForm.value = { oldName: '', name: '' }
    showPositionDialog.value = true
  }
}

const openEditDialog = (item) => {
  isEdit.value = true
  if (activeCategory.value === 'department') {
    deptForm.value = {
      id: item.id, name: item.name, code: item.code, parent_id: item.parent_id,
      manager_id: item.manager_id, sort_order: item.sort_order || 0, description: item.description || ''
    }
    showDeptDialog.value = true
  } else if (activeCategory.value === 'role') {
    roleForm.value = {
      id: item.id, name: item.name, description: item.description || '',
      level: item.level, data_scope: item.data_scope || 'self', permissions: item.permissions || []
    }
    showRoleDialog.value = true
  } else {
    positionForm.value = { oldName: item.name, name: item.name }
    showPositionDialog.value = true
  }
}

// ==================== 保存操作 ====================
const saveDept = async () => {
  if (!deptForm.value.name || !deptForm.value.code) {
    ElMessage.warning('请填写部门名称和编码')
    return
  }
  saving.value = true
  try {
    if (isEdit.value) {
      await updateDepartment(deptForm.value.id, {
        name: deptForm.value.name, description: deptForm.value.description,
        parent_id: deptForm.value.parent_id, manager_id: deptForm.value.manager_id,
        sort_order: deptForm.value.sort_order
      })
      ElMessage.success('部门更新成功')
    } else {
      await createDepartment({
        name: deptForm.value.name, code: deptForm.value.code,
        description: deptForm.value.description, parent_id: deptForm.value.parent_id,
        manager_id: deptForm.value.manager_id, sort_order: deptForm.value.sort_order
      })
      ElMessage.success('部门创建成功')
    }
    showDeptDialog.value = false
    fetchDepartments()
    fetchStats()
  } catch (error) { ElMessage.error(error.response?.data?.message || '保存失败') }
  finally { saving.value = false }
}

const saveRole = async () => {
  if (!roleForm.value.name) {
    ElMessage.warning('请填写角色名称')
    return
  }
  saving.value = true
  try {
    if (isEdit.value) {
      await updateRole(roleForm.value.id, {
        name: roleForm.value.name, description: roleForm.value.description,
        level: roleForm.value.level, data_scope: roleForm.value.data_scope,
        permissions: roleForm.value.permissions
      })
      ElMessage.success('角色更新成功')
    } else {
      await createRole({
        name: roleForm.value.name, description: roleForm.value.description,
        level: roleForm.value.level, data_scope: roleForm.value.data_scope,
        permissions: roleForm.value.permissions
      })
      ElMessage.success('角色创建成功')
    }
    showRoleDialog.value = false
    fetchRoles()
    fetchStats()
  } catch (error) { ElMessage.error(error.response?.data?.message || '保存失败') }
  finally { saving.value = false }
}

const savePosition = async () => {
  if (!positionForm.value.name) {
    ElMessage.warning('请填写职位名称')
    return
  }
  saving.value = true
  try {
    if (isEdit.value) {
      await updatePosition(positionForm.value.oldName, { name: positionForm.value.name })
      ElMessage.success('职位更新成功')
      if (currentPosition.value?.name === positionForm.value.oldName) {
        currentPosition.value = { ...currentPosition.value, name: positionForm.value.name }
      }
    } else {
      await createPosition({ name: positionForm.value.name })
      ElMessage.success('职位创建成功')
    }
    showPositionDialog.value = false
    fetchPositions()
    fetchStats()
  } catch (error) { ElMessage.error(error.response?.data?.message || '保存失败') }
  finally { saving.value = false }
}

// ==================== 删除操作 ====================
const removeDept = async (dept) => {
  try {
    await ElMessageBox.confirm(`确定要删除部门 "${dept.name}" 吗？`, '提示', { type: 'warning' })
    await deleteDepartment(dept.id)
    ElMessage.success('部门已删除')
    currentDept.value = null
    fetchDepartments()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error(error.response?.data?.message || '删除失败')
  }
}

const removeRole = async (role) => {
  try {
    await ElMessageBox.confirm(`确定要删除角色 "${role.description || role.name}" 吗？`, '提示', { type: 'warning' })
    await deleteRole(role.id)
    ElMessage.success('角色已删除')
    currentRole.value = null
    fetchRoles()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error(error.response?.data?.message || '删除失败')
  }
}

const removePosition = async (pos) => {
  try {
    await ElMessageBox.confirm(`确定要删除职位 "${pos.name}" 吗？该职位下所有用户将被清空职位信息。`, '提示', { type: 'warning' })
    await deletePosition(pos.name)
    ElMessage.success('职位已删除')
    currentPosition.value = null
    fetchPositions()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error(error.response?.data?.message || '删除失败')
  }
}

// ==================== 成员管理 ====================
const showAddMemberDialog = ref(false)
const showAddRoleMemberDialog = ref(false)
const showAddPositionMemberDialog = ref(false)
const addMemberLoading = ref(false)
const noDeptUsers = ref([])
const noRoleUsers = ref([])
const noPositionUsers = ref([])

const openAddMemberDialog = async () => {
  showAddMemberDialog.value = true
  addMemberLoading.value = true
  try {
    const res = await getUsers({ per_page: 1000 })
    noDeptUsers.value = (res.users || []).filter(u => !u.department_id)
  } catch (error) { console.error('获取用户失败', error) }
  finally { addMemberLoading.value = false }
}

const openAddRoleMemberDialog = async () => {
  showAddRoleMemberDialog.value = true
  addMemberLoading.value = true
  try {
    const res = await getUsers({ per_page: 1000 })
    noRoleUsers.value = (res.users || []).filter(u => !u.roles?.some(r => r.id === currentRole.value?.id))
  } catch (error) { console.error('获取用户失败', error) }
  finally { addMemberLoading.value = false }
}

const openAddPositionMemberDialog = async () => {
  showAddPositionMemberDialog.value = true
  addMemberLoading.value = true
  try {
    const res = await getUsersWithoutPosition()
    noPositionUsers.value = res.users || []
  } catch (error) { console.error('获取用户失败', error) }
  finally { addMemberLoading.value = false }
}

const handleAddMember = async (user) => {
  try {
    await addDepartmentMember(currentDept.value.id, user.id)
    ElMessage.success(`已将 ${user.real_name || user.username} 添加到部门`)
    fetchMembers()
    fetchDepartments()
    fetchStats()
    noDeptUsers.value = noDeptUsers.value.filter(u => u.id !== user.id)
  } catch (error) { ElMessage.error(error.response?.data?.message || '添加失败') }
}

const handleAddRoleMember = async (user) => {
  try {
    await addRoleMember(currentRole.value.id, user.id)
    ElMessage.success(`已将 ${user.real_name || user.username} 添加到角色`)
    fetchRoleMembers()
    fetchRoles()
    fetchStats()
    noRoleUsers.value = noRoleUsers.value.filter(u => u.id !== user.id)
  } catch (error) { ElMessage.error(error.response?.data?.message || '添加失败') }
}

const handleAddPositionMember = async (user) => {
  try {
    await addPositionMember(currentPosition.value.name, user.id)
    ElMessage.success(`已将 ${user.real_name || user.username} 设置为 ${currentPosition.value.name}`)
    fetchPositionMembers()
    fetchPositions()
    fetchStats()
    noPositionUsers.value = noPositionUsers.value.filter(u => u.id !== user.id)
  } catch (error) { ElMessage.error(error.response?.data?.message || '添加失败') }
}

const handleMemberCommand = (command, row) => {
  if (command === 'transfer') openTransferDialog(row)
  else if (command === 'remove') handleRemoveMember(row)
}

const handleRemoveMember = async (row) => {
  try {
    await ElMessageBox.confirm(`确定将 "${row.real_name || row.username}" 从 ${currentDept.value.name} 移除吗？`, '提示', { type: 'warning' })
    await removeDepartmentMember(currentDept.value.id, row.id)
    ElMessage.success('已移除')
    fetchMembers()
    fetchDepartments()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error(error.response?.data?.message || '移除失败')
  }
}

const handleRemoveRoleMember = async (row) => {
  try {
    await ElMessageBox.confirm(`确定将 "${row.real_name || row.username}" 从 ${currentRole.value.description || currentRole.value.name} 移除吗？`, '提示', { type: 'warning' })
    await removeRoleMember(currentRole.value.id, row.id)
    ElMessage.success('已移除')
    fetchRoleMembers()
    fetchRoles()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error(error.response?.data?.message || '移除失败')
  }
}

const handlePositionMemberCommand = (command, row) => {
  if (command === 'transfer') openTransferDialog(row)
  else if (command === 'remove') handleRemovePositionMember(row)
}

const handleRemovePositionMember = async (row) => {
  try {
    await ElMessageBox.confirm(`确定将 "${row.real_name || row.username}" 从 ${currentPosition.value.name} 移除吗？`, '提示', { type: 'warning' })
    await removePositionMember(currentPosition.value.name, row.id)
    ElMessage.success('已移除')
    fetchPositionMembers()
    fetchPositions()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error(error.response?.data?.message || '移除失败')
  }
}

// ==================== 转移成员 ====================
const showTransferDialog = ref(false)
const transferTargetId = ref(null)
const transferTargetName = ref('')
const transferringUser = ref(null)

const transferSourceText = computed(() => {
  if (activeCategory.value === 'department') return `从 ${currentDept.value?.name} 转移到：`
  if (activeCategory.value === 'position') return `从 ${currentPosition.value?.name} 转移到：`
  return ''
})

const openTransferDialog = (row) => {
  transferringUser.value = row
  transferTargetId.value = null
  transferTargetName.value = ''
  showTransferDialog.value = true
}

const handleTransfer = async () => {
  if (activeCategory.value === 'department') {
    if (!transferTargetId.value) { ElMessage.warning('请选择目标部门'); return }
    try {
      await transferDepartmentMember(currentDept.value.id, transferringUser.value.id, transferTargetId.value)
      ElMessage.success('转移成功')
      showTransferDialog.value = false
      fetchMembers()
      fetchDepartments()
      fetchStats()
    } catch (error) { ElMessage.error(error.response?.data?.message || '转移失败') }
  } else if (activeCategory.value === 'position') {
    if (!transferTargetName.value) { ElMessage.warning('请选择目标职位'); return }
    try {
      await transferPositionMember(currentPosition.value.name, transferringUser.value.id, transferTargetName.value)
      ElMessage.success('转移成功')
      showTransferDialog.value = false
      fetchPositionMembers()
      fetchPositions()
      fetchStats()
    } catch (error) { ElMessage.error(error.response?.data?.message || '转移失败') }
  }
}

// ==================== 工具函数 ====================
const maskPhone = (phone) => {
  if (!phone) return '-'
  if (phone.length === 11) return phone.slice(0, 3) + ' **** ' + phone.slice(7)
  return phone
}

// ==================== 饼图 ====================
const initPieChart = () => {
  if (!pieChart.value) return
  if (pieChartInstance) pieChartInstance.dispose()
  pieChartInstance = echarts.init(pieChart.value)

  let chartData = []
  let total = 0

  if (activeCategory.value === 'department') {
    chartData = (stats.value.by_department || []).filter(d => d.count > 0).map(d => ({ name: d.name, value: d.count }))
  } else if (activeCategory.value === 'role') {
    chartData = (roleStats.value.by_role || []).filter(d => d.count > 0).map(d => ({ name: d.name, value: d.count }))
  } else {
    chartData = (positionStats.value.by_position || []).filter(d => d.count > 0).map(d => ({ name: d.name, value: d.count }))
  }

  total = chartData.reduce((sum, d) => sum + d.value, 0)
  const colors = ['#1890ff', '#52c41a', '#722ed1', '#fa8c16', '#13c2c2', '#fadb14', '#999999']

  pieChartInstance.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}人 ({d}%)' },
    legend: {
      orient: 'vertical', right: '5%', top: 'center', itemGap: 12,
      textStyle: { fontSize: 12 },
      formatter: (name) => {
        const item = chartData.find(d => d.name === name)
        const percent = total > 0 ? ((item?.value || 0) / total * 100).toFixed(1) : 0
        return `${name}    ${item?.value || 0}人    ${percent}%`
      }
    },
    series: [{
      type: 'pie', radius: ['55%', '80%'], center: ['32%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: false, position: 'center' },
      emphasis: { label: { show: false } },
      labelLine: { show: false },
      data: chartData.length > 0 ? chartData : [{ name: '暂无数据', value: 0 }],
      color: colors
    }],
    graphic: [
      { type: 'text', left: '24%', top: '42%', style: { text: String(total), fontSize: 28, fontWeight: 'bold', fill: '#333', textAlign: 'center' } },
      { type: 'text', left: '26%', top: '55%', style: { text: '总人数', fontSize: 12, fill: '#999', textAlign: 'center' } }
    ]
  })
}

watch(() => [stats.value, roleStats.value, positionStats.value, activeCategory.value], () => {
  nextTick(() => initPieChart())
}, { deep: true })

window.addEventListener('resize', () => { pieChartInstance?.resize() })

// ==================== 初始化 ====================
const findFirstDept = (nodes) => {
  for (const node of nodes) {
    if (!node.children || node.children.length === 0) return node
    const found = findFirstDept(node.children)
    if (found) return found
  }
  return nodes[0] || null
}

onMounted(async () => {
  await fetchDepartments()
  await fetchStats()
  if (departmentTree.value.length > 0) {
    const firstDept = findFirstDept(departmentTree.value)
    if (firstDept) { currentDept.value = firstDept; fetchMembers() }
  }
})
</script>

<style scoped lang="scss">
.departments-page {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    .header-left {
      display: flex;
      align-items: baseline;
      gap: 12px;

      h2 { margin: 0; font-size: 20px; font-weight: 500; }
      .header-subtitle { font-size: 13px; color: #999; }
    }
  }

  // 分类切换标签
  .category-tabs {
    display: flex;
    gap: 8px;
    margin-bottom: 16px;

    .tab-item {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 8px 20px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 14px;
      color: #666;
      background: #f5f5f5;
      transition: all 0.2s;

      &:hover { background: #e6f7ff; color: #1890ff; }

      &.active {
        background: #1890ff;
        color: #fff;
      }
    }
  }

  .left-column {
    .tree-card {
      .card-title {
        padding: 16px 16px 0;
        font-size: 15px;
        font-weight: 500;
        color: #333;
      }

      .tree-search {
        display: flex;
        gap: 8px;
        padding: 12px 16px;

        .refresh-btn { padding: 0 10px; }
      }

      .tree-wrapper {
        padding: 0 8px 12px;
        max-height: 420px;
        overflow-y: auto;
      }
    }

    .chart-card {
      .card-title {
        font-size: 15px;
        font-weight: 500;
        color: #333;
        margin-bottom: 8px;
      }

      .pie-chart-container {
        height: 260px;
        width: 100%;
      }
    }
  }

  .dept-tree-node {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    padding: 6px 8px;
    border-radius: 4px;
    transition: all 0.2s;

    &.active { background: #e6f7ff; color: #1890ff; }

    .node-left {
      display: flex;
      align-items: center;
      gap: 6px;

      .node-icon { font-size: 14px; color: #999; }
      .node-label { font-size: 13px; }
    }

    .node-count { font-size: 12px; color: #999; }
  }

  // 简单列表样式（角色/职位）
  .simple-list {
    .list-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 12px;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s;
      margin-bottom: 4px;

      &:hover { background: #f5f5f5; }

      &.active { background: #e6f7ff; color: #1890ff; }

      .node-left {
        display: flex;
        align-items: center;
        gap: 8px;

        .node-icon { font-size: 16px; color: inherit; }
        .node-label { font-size: 14px; font-weight: 500; }
        .item-sub { font-size: 12px; color: #999; display: block; }
        .item-info { display: flex; flex-direction: column; }
      }

      .node-count { font-size: 12px; color: #999; }
    }
  }

  .stats-row {
    margin-bottom: 16px;

    .stat-card {
      background: #fff;
      border-radius: 8px;
      padding: 16px;
      display: flex;
      align-items: center;
      gap: 12px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);

      .stat-icon-wrapper {
        width: 44px;
        height: 44px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
      }

      .stat-info {
        flex: 1;

        .stat-value {
          font-size: 24px;
          font-weight: 600;
          line-height: 1.2;
        }

        .stat-label { font-size: 12px; color: #666; margin-top: 2px; }
        .stat-trend { font-size: 11px; color: #999; margin-top: 2px; }
      }
    }
  }

  .detail-card {
    margin-bottom: 16px;

    :deep(.el-card__body) { padding: 16px 20px; }

    .detail-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;

      .detail-title { font-size: 15px; font-weight: 500; color: #333; }
      .detail-actions { display: flex; gap: 8px; }
    }

    .detail-body {
      display: flex;
      justify-content: space-between;

      .detail-left {
        flex: 1;

        .dept-name-row {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 20px;

          .dept-icon-large {
            width: 48px;
            height: 48px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
          }

          .dept-name-info {
            display: flex;
            align-items: center;
            gap: 8px;

            .dept-name { font-size: 18px; font-weight: 600; color: #333; }
          }
        }

        .detail-grid {
          .grid-item {
            margin-bottom: 16px;

            .grid-label { font-size: 12px; color: #999; margin-bottom: 4px; }
            .grid-value { font-size: 13px; color: #333; font-weight: 500; }
          }
        }
      }
    }
  }

  .member-card {
    :deep(.el-card__body) { padding: 16px 20px; }

    .member-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;

      .member-title { font-size: 15px; font-weight: 500; color: #333; }
    }

    .member-table {
      .user-cell {
        display: flex;
        align-items: center;
        gap: 10px;

        .user-name { font-size: 13px; color: #333; }
      }

      .status-dot {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 13px;

        .dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;

          &.active { background: #52c41a; }
          &.inactive { background: #999; }
        }
      }
    }

    .member-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 16px;
      padding-top: 12px;
      border-top: 1px solid #f0f0f0;

      .total-text { font-size: 13px; color: #666; }
    }
  }
}
</style>
