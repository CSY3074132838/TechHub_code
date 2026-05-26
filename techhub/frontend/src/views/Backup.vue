<template>
  <div class="backup-page">
    <!-- 第三次迭代陈思言负责 -->
    <h1 class="page-title">{{ t('backup.pageTitle') }}</h1>

    <el-card class="backup-card">
      <div class="backup-header">
        <el-button type="primary" @click="handleCreateBackup" :loading="creating">
          <el-icon><Plus /></el-icon>
          {{ t('backup.manualBackup') }}
        </el-button>
      </div>

      <el-table :data="backupList" style="width: 100%" v-loading="loading">
        <el-table-column :label="t('backup.time')" min-width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('backup.size')" min-width="120">
          <template #default="{ row }">
            {{ row.size }} MB
          </template>
        </el-table-column>
        <el-table-column :label="t('backup.operation')" min-width="300" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleDownload(row)">
              <el-icon><Download /></el-icon>
              {{ t('backup.download') }}
            </el-button>
            <el-button type="warning" size="small" @click="handleRestore(row)">
              <el-icon><RefreshLeft /></el-icon>
              {{ t('backup.restore') }}
            </el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">
              <el-icon><Delete /></el-icon>
              {{ t('backup.delete') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && backupList.length === 0" :description="t('backup.noBackups')" />
    </el-card>
  </div>
</template>

<script setup>
// 第三次迭代陈思言负责
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Download, RefreshLeft, Delete } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import {
  getBackupList,
  createBackup,
  downloadBackup,
  restoreBackup,
  deleteBackup
} from '@/api/backup.js'

const { t } = useI18n()

const backupList = ref([])
const loading = ref(false)
const creating = ref(false)

const fetchBackupList = async () => {
  loading.value = true
  try {
    const res = await getBackupList()
    backupList.value = res.backups || []
  } catch (error) {
    console.error('获取备份列表失败', error)
    ElMessage.error('获取备份列表失败')
  } finally {
    loading.value = false
  }
}

const handleCreateBackup = async () => {
  creating.value = true
  try {
    await createBackup()
    ElMessage.success(t('backup.createSuccess'))
    fetchBackupList()
  } catch (error) {
    ElMessage.error(t('backup.createFailed'))
  } finally {
    creating.value = false
  }
}

const handleDownload = async (row) => {
  try {
    const res = await downloadBackup(row.filename)
    const blob = new Blob([res.data], { type: 'application/octet-stream' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', row.filename)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('下载成功')
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

const handleRestore = async (row) => {
  try {
    await ElMessageBox.confirm(t('backup.confirmRestore'), t('backup.restore'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning'
    })
    await restoreBackup(row.filename)
    ElMessage.success(t('backup.restoreSuccess'))
    fetchBackupList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('backup.restoreFailed'))
    }
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(t('backup.confirmDelete'), t('backup.delete'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning'
    })
    await deleteBackup(row.filename)
    ElMessage.success(t('backup.deleteSuccess'))
    fetchBackupList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('backup.deleteFailed'))
    }
  }
}

const formatTime = (time) => {
  if (!time) return '-'
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

onMounted(() => {
  fetchBackupList()
})
</script>

<style scoped>
.backup-page {
  padding: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 20px;
}

.backup-card {
  margin-bottom: 20px;
}

.backup-header {
  margin-bottom: 16px;
  display: flex;
  justify-content: flex-start;
}
</style>
