<!-- ================================================
     【第三次迭代于然负责】(8) 审批流程展示页面
     展示所有审批流程，方便员工查看了解流程内容
     总经理可对这些流程进行修改
     ================================================ -->
<template>
  <div class="workflow-definitions-page">
    <div class="page-header">
      <div class="header-left">
        <h2>{{ $t('approvals.workflowPageTitle') }}</h2>
        <p class="header-desc">{{ $t('approvals.workflowDescription') }}</p>
      </div>
      <div class="header-right">
        <el-button v-if="isGeneralManager" type="primary" @click="toggleEditMode">
          <el-icon><Edit /></el-icon>
          {{ isEditMode ? $t('common.cancel') : $t('approvals.editWorkflow') }}
        </el-button>
      </div>
    </div>

    <!-- 图例说明 -->
    <el-card class="legend-card" shadow="never">
      <div class="legend-title">{{ $t('approvals.flowLegend') }}</div>
      <div class="legend-items">
        <div class="legend-item">
          <div class="legend-dot serial"></div>
          <span>{{ $t('approvals.legendSerial') }}</span>
        </div>
        <div class="legend-item">
          <div class="legend-dot parallel"></div>
          <span>{{ $t('approvals.legendParallel') }}</span>
        </div>
        <div class="legend-item">
          <div class="legend-dot condition"></div>
          <span>{{ $t('approvals.legendCondition') }}</span>
        </div>
        <div class="legend-item">
          <div class="legend-dot auto"></div>
          <span>{{ $t('approvals.legendAuto') }}</span>
        </div>
      </div>
    </el-card>

    <!-- 审批流程列表 -->
    <div class="workflow-list">
      <el-card
        v-for="(wf, key) in workflows"
        :key="key"
        class="workflow-card"
        shadow="hover"
      >
        <template #header>
          <div class="workflow-header">
            <div class="workflow-title-section">
              <el-icon class="workflow-icon" :size="20"><DocumentChecked /></el-icon>
              <div>
                <h3 class="workflow-name">{{ wf.name }}</h3>
                <p class="workflow-desc">{{ wf.description }}</p>
              </div>
            </div>
            <el-tag :type="getWorkflowTypeTag(key)" effect="plain" size="small">
              {{ getTypeLabel(key) }}
            </el-tag>
          </div>
        </template>

        <!-- 流程步骤展示 -->
        <div class="workflow-steps">
          <div
            v-for="(node, index) in wf.nodes"
            :key="index"
            class="step-item"
            :class="[`step-${node.type}`]"
          >
            <div class="step-marker">
              <div class="step-number">{{ index + 1 }}</div>
              <div v-if="index < wf.nodes.length - 1" class="step-arrow">
                <el-icon><ArrowDown /></el-icon>
              </div>
            </div>
            <div class="step-content">
              <div class="step-header">
                <span class="step-name">{{ node.name }}</span>
                <el-tag
                  :type="getNodeTypeTag(node.type)"
                  size="small"
                  effect="plain"
                >
                  {{ getNodeTypeLabel(node.type) }}
                </el-tag>
              </div>
              <div class="step-details">
                <div v-if="node.role" class="detail-item">
                  <el-icon><User /></el-icon>
                  <span class="detail-label">{{ $t('approvals.responsibleRole') }}:</span>
                  <span v-if="!isEditMode" class="detail-value">{{ node.role }}</span>
                  <el-input
                    v-else
                    v-model="node.role"
                    size="small"
                    style="width: 300px;"
                  />
                </div>
                <div v-if="node.condition" class="detail-item">
                  <el-icon><Warning /></el-icon>
                  <span class="detail-label">{{ $t('approvals.conditionRule') }}:</span>
                  <span v-if="!isEditMode" class="detail-value condition-value">{{ node.condition }}</span>
                  <el-input
                    v-else
                    v-model="node.condition"
                    size="small"
                    style="width: 300px;"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 保存按钮（编辑模式） -->
    <div v-if="isEditMode" class="edit-actions">
      <el-button type="primary" size="large" @click="saveAllWorkflows" :loading="saving">
        <el-icon><Check /></el-icon>
        {{ $t('approvals.saveWorkflow') }}
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/stores/user'
import { getWorkflowDefinitions, updateWorkflowDefinition } from '@/api/approvals'

const { t } = useI18n()
const userStore = useUserStore()

const workflows = ref({})
const loading = ref(false)
const saving = ref(false)
const isEditMode = ref(false)

// 判断是否为总经理（super_admin）
const isGeneralManager = computed(() => {
  return userStore.userInfo?.roles?.some(r => r.name === 'super_admin')
})

const fetchWorkflows = async () => {
  loading.value = true
  try {
    const res = await getWorkflowDefinitions()
    workflows.value = res.definitions || {}
  } catch (error) {
    console.error(t('approvals.fetchDetailFailed'), error)
    ElMessage.error(t('approvals.fetchDetailFailed'))
  } finally {
    loading.value = false
  }
}

const toggleEditMode = () => {
  if (!isGeneralManager.value) {
    ElMessage.warning(t('approvals.noPermissionEditWorkflow'))
    return
  }
  isEditMode.value = !isEditMode.value
}

const saveAllWorkflows = async () => {
  saving.value = true
  try {
    const keys = Object.keys(workflows.value)
    for (const key of keys) {
      await updateWorkflowDefinition(key, {
        name: workflows.value[key].name,
        description: workflows.value[key].description,
        nodes: workflows.value[key].nodes
      })
    }
    ElMessage.success(t('approvals.updateWorkflowSuccess'))
    isEditMode.value = false
  } catch (error) {
    console.error(t('approvals.updateWorkflowFailed'), error)
    ElMessage.error(t('approvals.updateWorkflowFailed'))
  } finally {
    saving.value = false
  }
}

const getWorkflowTypeTag = (type) => {
  const map = {
    purchase: 'warning',
    expense: 'success',
    leave: 'primary',
    overtime: 'danger',
    permission: 'info',
    contract: 'warning',
    ticket: 'primary',
    other: 'info'
  }
  return map[type] || ''
}

const getTypeLabel = (type) => {
  const typeMap = {
    'leave': t('approvals.leave'),
    'expense': t('approvals.expense'),
    'purchase': t('approvals.purchase'),
    'overtime': t('approvals.overtime'),
    'permission': t('approvals.permission'),
    'contract': t('approvals.contract'),
    'ticket': t('approvals.ticket'),
    'other': t('approvals.other')
  }
  return typeMap[type] || type
}

const getNodeTypeTag = (nodeType) => {
  const map = {
    serial: 'primary',
    parallel: 'warning',
    condition: 'danger',
    auto: 'info'
  }
  return map[nodeType] || ''
}

const getNodeTypeLabel = (nodeType) => {
  const map = {
    serial: t('approvals.workflowTypeSerial'),
    parallel: t('approvals.workflowTypeParallel'),
    condition: t('approvals.workflowTypeCondition'),
    auto: t('approvals.workflowTypeAuto')
  }
  return map[nodeType] || nodeType
}

onMounted(() => {
  fetchWorkflows()
})
</script>

<style scoped lang="scss">
.workflow-definitions-page {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 24px;

    .header-left {
      h2 {
        margin: 0 0 8px;
        font-size: 22px;
        color: #303133;
      }

      .header-desc {
        margin: 0;
        color: #909399;
        font-size: 14px;
      }
    }

    .header-right {
      display: flex;
      gap: 12px;
    }
  }

  .legend-card {
    margin-bottom: 20px;
    background: #f5f7fa;
    border: none;

    :deep(.el-card__body) {
      padding: 16px 20px;
    }

    .legend-title {
      font-size: 14px;
      font-weight: 600;
      color: #606266;
      margin-bottom: 12px;
    }

    .legend-items {
      display: flex;
      flex-wrap: wrap;
      gap: 20px;

      .legend-item {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 13px;
        color: #606266;

        .legend-dot {
          width: 12px;
          height: 12px;
          border-radius: 50%;

          &.serial {
            background: #409eff;
          }

          &.parallel {
            background: #e6a23c;
          }

          &.condition {
            background: #f56c6c;
          }

          &.auto {
            background: #909399;
          }
        }
      }
    }
  }

  .workflow-list {
    display: flex;
    flex-direction: column;
    gap: 20px;

    .workflow-card {
      :deep(.el-card__header) {
        padding: 16px 20px;
        background: #fafafa;
      }

      .workflow-header {
        display: flex;
        justify-content: space-between;
        align-items: center;

        .workflow-title-section {
          display: flex;
          align-items: center;
          gap: 12px;

          .workflow-icon {
            color: #409eff;
            background: #ecf5ff;
            padding: 10px;
            border-radius: 8px;
          }

          .workflow-name {
            margin: 0 0 4px;
            font-size: 16px;
            color: #303133;
          }

          .workflow-desc {
            margin: 0;
            font-size: 13px;
            color: #909399;
          }
        }
      }

      .workflow-steps {
        padding: 8px 0;

        .step-item {
          display: flex;
          gap: 16px;
          padding: 12px 0;

          .step-marker {
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 36px;
            flex-shrink: 0;

            .step-number {
              width: 32px;
              height: 32px;
              border-radius: 50%;
              display: flex;
              align-items: center;
              justify-content: center;
              font-size: 14px;
              font-weight: 600;
              color: #fff;
              background: #409eff;
              z-index: 1;
            }

            .step-arrow {
              flex: 1;
              display: flex;
              align-items: center;
              justify-content: center;
              color: #c0c4cc;
              padding: 4px 0;

              .el-icon {
                font-size: 16px;
              }
            }
          }

          .step-content {
            flex: 1;
            padding-bottom: 8px;

            .step-header {
              display: flex;
              align-items: center;
              gap: 10px;
              margin-bottom: 8px;

              .step-name {
                font-weight: 600;
                font-size: 15px;
                color: #303133;
              }
            }

            .step-details {
              display: flex;
              flex-direction: column;
              gap: 6px;

              .detail-item {
                display: flex;
                align-items: center;
                gap: 6px;
                font-size: 13px;

                .el-icon {
                  color: #909399;
                  font-size: 14px;
                }

                .detail-label {
                  color: #606266;
                  font-weight: 500;
                  min-width: 70px;
                }

                .detail-value {
                  color: #409eff;
                  background: #ecf5ff;
                  padding: 2px 10px;
                  border-radius: 4px;

                  &.condition-value {
                    color: #e6a23c;
                    background: #fdf6ec;
                  }
                }
              }
            }
          }

          // 不同节点类型的颜色区分
          &.step-serial {
            .step-number {
              background: #409eff;
            }
          }

          &.step-parallel {
            .step-number {
              background: #e6a23c;
            }
          }

          &.step-condition {
            .step-number {
              background: #f56c6c;
            }
          }

          &.step-auto {
            .step-number {
              background: #909399;
            }
          }

          &:last-child {
            .step-arrow {
              display: none;
            }
          }
        }
      }
    }
  }

  .edit-actions {
    position: fixed;
    bottom: 30px;
    right: 30px;
    z-index: 100;

    .el-button {
      box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
    }
  }
}

@media (max-width: 768px) {
  .workflow-definitions-page {
    .page-header {
      flex-direction: column;
      gap: 12px;
    }

    .legend-card {
      .legend-items {
        flex-direction: column;
        gap: 10px;
      }
    }

    .workflow-list {
      .workflow-card {
        .workflow-header {
          flex-direction: column;
          align-items: flex-start;
          gap: 10px;
        }

        .workflow-steps {
          .step-item {
            .step-content {
              .step-header {
                flex-wrap: wrap;
              }

              .step-details {
                .detail-item {
                  flex-wrap: wrap;
                }
              }
            }
          }
        }
      }
    }
  }
}
</style>
