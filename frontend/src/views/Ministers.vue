<template>
  <div class="ministers-page">
    <div class="page-header">
      <h1>👥 大臣配置</h1>
      <div class="header-actions">
        <el-button @click="loadFromOpenClaw" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新配置
        </el-button>
        <el-button type="success" @click="saveToOpenClaw" :loading="saving">
          <el-icon><Check /></el-icon>
          保存生效
        </el-button>
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          新增大臣
        </el-button>
      </div>
    </div>

    <div class="minister-grid" v-loading="loading">
      <MinisterCard
        v-for="minister in ministers"
        :key="minister.id"
        :minister="getMinisterWithStatus(minister)"
        :current-task="currentTasks[minister.id] || null"
        @view-task="viewTask"
      />
    </div>

    <el-empty v-if="!loading && ministers.length === 0" description="暂无大臣" />

    <el-dialog v-model="showEditDialog" :title="form.id ? '编辑大臣' : '新增大臣'" width="520px">
      <el-form :model="form" label-width="110px">
        <el-form-item label="大臣名称">
          <el-input v-model="form.name" placeholder="如：兵部" />
        </el-form-item>

        <el-form-item label="部门">
          <el-input v-model="form.department" placeholder="如：兵部" />
        </el-form-item>

        <el-form-item label="模型">
          <el-select v-model="form.model_id" placeholder="选择模型" :loading="loadingModels" filterable>
            <el-option
              v-for="model in availableModels"
              :key="model.full_id"
              :label="`${model.name} (${model.provider})`"
              :value="model.full_id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="工作区">
          <el-input v-model="form.workspace" placeholder="/root/clawd/xxx" />
        </el-form-item>

        <el-form-item label="启用">
          <el-switch v-model="form.enabled" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="saveMinister">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Check } from '@element-plus/icons-vue'

import api from '@/api'
import MinisterCard from '@/components/MinisterCard.vue'

const loading = ref(false)
const loadingModels = ref(false)
const saving = ref(false)
const ministers = ref([])
const availableModels = ref([])
const currentTasks = ref({})

const showEditDialog = ref(false)
const form = ref({
  id: null,
  name: '',
  department: '',
  model_id: '',
  workspace: '/root/clawd',
  enabled: true,
})

const ministerStatus = {
  司礼监: { status: 'active', emoji: '🏛️', lastActive: '刚刚' },
  兵部: { status: 'busy', emoji: '⚔️', lastActive: '2 分钟前' },
  户部: { status: 'idle', emoji: '💰', lastActive: '10 分钟前' },
  礼部: { status: 'active', emoji: '🎨', lastActive: '刚刚' },
  工部: { status: 'busy', emoji: '🔧', lastActive: '1 分钟前' },
  吏部: { status: 'idle', emoji: '📋', lastActive: '30 分钟前' },
  刑部: { status: 'idle', emoji: '⚖️', lastActive: '1 小时前' },
}

const getMinisterWithStatus = (minister) => {
  const status = ministerStatus[minister.name] || { status: 'idle', emoji: '👤', lastActive: '未知' }
  // 模型信息优先展示 OpenClaw 配置源（model_primary），避免被数据库旧值覆盖。
  const model = minister.model_primary || minister.model_id || ''
  return { ...minister, ...status, model }
}

const mergeMinistersWithConfig = (dbMinisters = [], configMinisters = []) => {
  const configById = new Map(configMinisters.map((item) => [item.id, item]))

  const merged = dbMinisters.map((minister) => {
    const configItem = configById.get(minister.id)
    if (!configItem) return minister

    return {
      ...minister,
      name: configItem.name || minister.name,
      model_id: configItem.model_primary || minister.model_id,
      model_primary: configItem.model_primary || minister.model_id,
      workspace: configItem.workspace || minister.workspace,
      enabled: typeof configItem.enabled === 'boolean' ? configItem.enabled : minister.enabled,
      config_source: 'openclaw',
    }
  })

  // 兜底：配置里有但数据库尚未入库的大臣，也要展示出来。
  configMinisters.forEach((configItem) => {
    if (merged.some((minister) => minister.id === configItem.id)) return

    merged.push({
      id: configItem.id,
      name: configItem.name || configItem.agent_id || `大臣-${configItem.id}`,
      department: configItem.name || configItem.agent_id || '',
      model_id: configItem.model_primary || '',
      model_primary: configItem.model_primary || '',
      workspace: configItem.workspace || '/root/clawd',
      enabled: typeof configItem.enabled === 'boolean' ? configItem.enabled : true,
      config_source: 'openclaw',
    })
  })

  return merged.sort((a, b) => a.id - b.id)
}

const loadMinisters = async ({ apply = true } = {}) => {
  const list = await api.get('/ministers/')
  if (apply) {
    ministers.value = list
  }
  return list
}

const loadFromOpenClaw = async () => {
  loading.value = true
  try {
    const data = await api.get('/ministers/openclaw/config')

    if (data.ok && Array.isArray(data.ministers)) {
      // 先触发后端同步，确保数据库与配置文件保持一致。
      const reloadResult = await api.post('/ministers/openclaw/reload')
      const dbMinisters = await loadMinisters({ apply: false })

      // 页面展示以 OpenClaw 配置接口为准，规避数据库旧缓存导致的错位。
      ministers.value = mergeMinistersWithConfig(dbMinisters, data.ministers)
      ElMessage.success(reloadResult.message || '配置已刷新')
      return
    }

    await loadMinisters()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '刷新配置失败')
  } finally {
    loading.value = false
  }
}

const saveToOpenClaw = async () => {
  saving.value = true
  try {
    // 准备同步数据
    const syncData = ministers.value.map((m) => ({
      id: m.id,
      model_primary: m.model_primary || m.model_id,
    }))

    const result = await api.put('/ministers/openclaw/sync', syncData)
    ElMessage.success(result.message || '配置已保存到 openclaw.json')
    await loadFromOpenClaw()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '保存配置失败')
  } finally {
    saving.value = false
  }
}

const loadModels = async () => {
  loadingModels.value = true
  try {
    const data = await api.get('/models/available')
    availableModels.value = data.providers.flatMap((p) => p.models)
  } finally {
    loadingModels.value = false
  }
}

const loadCurrentTasks = async () => {
  const taskList = await api.get('/tasks/', { params: { status: 'processing', limit: 200 } })
  const map = {}
  taskList.forEach((task) => {
    if (!map[task.assignee_id]) {
      map[task.assignee_id] = {
        task_id: task.task_id,
        title: task.title,
        now: task.description || '处理中',
        status: task.status,
      }
    }
  })
  currentTasks.value = map
}

const openCreateDialog = () => {
  form.value = {
    id: null,
    name: '',
    department: '',
    model_id: availableModels.value[0]?.full_id || '',
    workspace: '/root/clawd',
    enabled: true,
  }
  showEditDialog.value = true
}

const saveMinister = async () => {
  if (!form.value.name || !form.value.department || !form.value.model_id || !form.value.workspace) {
    ElMessage.warning('请填写完整信息')
    return
  }

  try {
    if (form.value.id) {
      await api.put(`/ministers/${form.value.id}`, form.value)
    } else {
      await api.post('/ministers/', form.value)
    }
    ElMessage.success('保存成功')
    showEditDialog.value = false
    await loadFromOpenClaw()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '保存失败')
  }
}

const viewTask = (task) => {
  ElMessage.info(`任务：${task.task_id} - ${task.title}`)
}

onMounted(async () => {
  try {
    // 页面加载时先从 openclaw.json 读取最新配置
    await loadFromOpenClaw()
    await Promise.all([loadModels(), loadCurrentTasks()])
  } catch (error) {
    ElMessage.error('加载大臣页面失败')
    console.error(error)
  }
})
</script>

<style scoped>
.ministers-page {
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  font-size: 20px;
  font-weight: 700;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.minister-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}
</style>
