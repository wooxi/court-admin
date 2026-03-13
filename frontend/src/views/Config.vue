<template>
  <div class="config">
    <h1>⚙️ OpenClaw 配置管理</h1>

    <el-card style="margin-bottom: 20px;">
      <template #header>
        <div class="card-header">
          <span>🔐 管理口令</span>
        </div>
      </template>

      <el-form :inline="true">
        <el-form-item label="X-Admin-Token">
          <el-input
            v-model="adminToken"
            placeholder="若后端启用 CONFIG_ADMIN_TOKEN，请填此值"
            style="width: 420px"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="applyAdminToken">保存到本地</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-bottom: 20px;">
      <template #header>
        <div class="card-header">
          <span>📄 配置概览</span>
          <div>
            <el-button type="warning" @click="createBackup">
              <el-icon><Download /></el-icon>
              备份配置
            </el-button>
            <el-button type="primary" @click="reloadConfig">
              <el-icon><Refresh /></el-icon>
              应用配置（重启网关）
            </el-button>
          </div>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="配置文件">/root/.openclaw/openclaw.json</el-descriptions-item>
        <el-descriptions-item label="版本">{{ config.version || '-' }}</el-descriptions-item>
        <el-descriptions-item label="最后更新">{{ config.updated_at || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag type="success">✅ 正常</el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card style="margin-bottom: 20px;">
      <template #header>
        <span>🤖 可用模型列表</span>
      </template>

      <el-collapse>
        <el-collapse-item v-for="provider in models.providers" :key="provider.name" :title="provider.name">
          <div class="provider-info">
            <p><strong>Base URL:</strong> {{ provider.baseUrl }}</p>
            <el-table :data="provider.models" stripe size="small">
              <el-table-column prop="id" label="模型 ID" />
              <el-table-column prop="full_id" label="完整 ID" />
              <el-table-column prop="contextWindow" label="上下文窗口" />
              <el-table-column prop="maxTokens" label="最大输出" />
            </el-table>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-card>

    <el-card style="margin-bottom: 20px;">
      <template #header>
        <span>👥 大臣配置</span>
      </template>

      <el-table :data="ministers" stripe>
        <el-table-column prop="id" label="ID" width="120" />
        <el-table-column prop="name" label="名称" width="120" />
        <el-table-column prop="model.primary" label="模型" min-width="260" />
        <el-table-column prop="workspace" label="工作区" min-width="220" />
        <el-table-column label="操作" width="140">
          <template #default="{ row }">
            <el-button size="small" @click="editMinister(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card>
      <template #header>
        <span>📦 备份历史</span>
      </template>

      <el-table :data="backups" stripe>
        <el-table-column prop="filename" label="文件名" min-width="260" />
        <el-table-column prop="size" label="大小" width="120">
          <template #default="{ row }">{{ (row.size / 1024).toFixed(2) }} KB</template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" min-width="220" />
        <el-table-column label="操作" width="220">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="restoreBackup(row)">恢复</el-button>
            <el-button size="small" type="danger" @click="deleteBackup(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showEditDialog" title="编辑大臣配置" width="640px">
      <el-alert
        title="⚠️ 修改会先自动备份 openclaw.json"
        type="warning"
        show-icon
        style="margin-bottom: 20px"
      />

      <el-form :model="editingMinister" label-width="120px">
        <el-form-item label="大臣 ID">
          <el-input v-model="editingMinister.id" disabled />
        </el-form-item>

        <el-form-item label="大臣名称">
          <el-input v-model="editingMinister.name" disabled />
        </el-form-item>

        <el-form-item label="选择模型">
          <el-select v-model="editingMinister.model.primary" placeholder="选择模型" filterable>
            <el-option
              v-for="model in allModels"
              :key="model.full_id"
              :label="`${model.name} (${model.full_id})`"
              :value="model.full_id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="工作区">
          <el-input v-model="editingMinister.workspace" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="saveMinisterConfig">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import api, { setConfigAdminToken } from '@/api'

const adminToken = ref(localStorage.getItem('court_admin_config_token') || '')

const config = ref({ version: '', updated_at: '' })
const models = ref({ providers: [] })
const ministers = ref([])
const backups = ref([])
const showEditDialog = ref(false)
const editingMinister = ref({})

const allModels = computed(() => models.value.providers.flatMap((p) => p.models))

const applyAdminToken = () => {
  setConfigAdminToken(adminToken.value)
  ElMessage.success('管理口令已保存（仅本浏览器）')
}

const loadConfig = async () => {
  const data = await api.get('/config/')
  config.value = { version: data.version, updated_at: data.updated_at }
}

const loadModels = async () => {
  models.value = await api.get('/models/available')
}

const loadMinisters = async () => {
  const data = await api.get('/config/ministers')
  ministers.value = data.ministers
}

const loadBackups = async () => {
  const data = await api.get('/config/backups')
  backups.value = data.backups
}

const createBackup = async () => {
  const result = await api.post('/config/backup')
  ElMessage.success(`备份成功：${result.backup_path}`)
  await loadBackups()
}

const reloadConfig = async () => {
  const result = await api.post('/config/reload', { perform: true, timeout_seconds: 30 })
  if (result.return_code === 0) {
    ElMessage.success('配置已应用（网关重启成功）')
  } else {
    ElMessage.warning(`重载返回码 ${result.return_code}，请检查日志`)
  }
}

const editMinister = (minister) => {
  editingMinister.value = JSON.parse(JSON.stringify(minister))
  editingMinister.value.model = editingMinister.value.model || { primary: '' }
  showEditDialog.value = true
}

const saveMinisterConfig = async () => {
  await api.put(`/config/ministers/${editingMinister.value.id}`, {
    config_key: 'openclaw',
    config_value: {
      model: editingMinister.value.model,
      workspace: editingMinister.value.workspace,
    },
  })
  ElMessage.success('保存成功')
  showEditDialog.value = false
  await Promise.all([loadConfig(), loadMinisters(), loadBackups()])
}

const restoreBackup = async (row) => {
  await ElMessageBox.confirm(`确认恢复备份 ${row.filename}？会覆盖当前配置。`, '确认恢复', {
    confirmButtonText: '恢复',
    cancelButtonText: '取消',
    type: 'warning',
  })

  await api.post('/config/restore', { filename: row.filename })
  ElMessage.success('恢复成功')
  await Promise.all([loadConfig(), loadBackups()])
}

const deleteBackup = async (row) => {
  await ElMessageBox.confirm(`确认删除备份 ${row.filename}？`, '确认删除', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning',
  })

  await api.delete(`/config/backups/${encodeURIComponent(row.filename)}`)
  ElMessage.success('删除成功')
  await loadBackups()
}

const loadAll = async () => {
  try {
    setConfigAdminToken(adminToken.value)
    await Promise.all([loadConfig(), loadModels(), loadMinisters(), loadBackups()])
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '加载配置页面失败')
    console.error(error)
  }
}

onMounted(() => {
  loadAll()
})
</script>

<style scoped>
.config h1 {
  margin-bottom: 20px;
  color: #303133;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.provider-info p {
  margin: 10px 0;
  color: #606266;
}
</style>
