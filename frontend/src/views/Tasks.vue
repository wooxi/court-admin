<template>
  <div class="tasks-page">
    <div class="page-header">
      <div>
        <h1>📋 任务管理</h1>
        <p class="subtitle">任务分派实时展示（每 5 秒自动刷新）</p>
      </div>
      <div class="header-actions">
        <el-tag type="info" effect="plain">
          上次更新：{{ lastUpdatedText }}
        </el-tag>
        <el-switch v-model="autoRefresh" inline-prompt active-text="自动刷新" inactive-text="手动" />
        <el-button @click="loadTasks">
          <el-icon><Refresh /></el-icon>
          立即刷新
        </el-button>
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          创建任务
        </el-button>
      </div>
    </div>

    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部状态" clearable>
            <el-option label="待处理" value="pending" />
            <el-option label="进行中" value="processing" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </el-form-item>
        <el-form-item label="承接人">
          <el-select v-model="filters.assignee" placeholder="全部大臣" clearable>
            <el-option v-for="m in ministers" :key="m.id" :label="m.name" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadTasks">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <el-table :data="tasks" v-loading="loading" stripe>
        <el-table-column prop="task_id" label="任务 ID" width="190" fixed="left" />
        <el-table-column prop="title" label="任务标题" min-width="240" show-overflow-tooltip />

        <el-table-column label="分派人" width="120">
          <template #default="{ row }">
            <el-tag size="small" type="warning" effect="plain">{{ getDispatcherName(row.dispatcher_id) }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="承接人" width="120">
          <template #default="{ row }">
            <el-tag size="small" type="success" effect="plain">{{ getAssigneeName(row.assignee_id) }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="分派时间" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>

        <el-table-column label="操作" width="170" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewTaskDetail(row)">详情</el-button>
            <el-button
              v-if="row.status !== 'completed'"
              size="small"
              type="success"
              @click="markCompleted(row)"
            >完成</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && tasks.length === 0" description="暂无任务" />
    </el-card>

    <el-dialog v-model="showCreateDialog" title="创建任务" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="任务标题">
          <el-input v-model="form.title" placeholder="任务标题" />
        </el-form-item>
        <el-form-item label="任务描述">
          <el-input v-model="form.description" type="textarea" :rows="4" placeholder="任务描述" />
        </el-form-item>
        <el-form-item label="承办大臣">
          <el-select v-model="form.assignee_id" placeholder="选择大臣">
            <el-option v-for="minister in ministers" :key="minister.id" :label="minister.name" :value="minister.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="form.priority" placeholder="选择优先级">
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createTask">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

import api from '@/api'
import { normalizeText } from '@/utils/text'

const POLL_INTERVAL = 5000
const DEFAULT_DISPATCHER_ID = 1

const router = useRouter()
const loading = ref(false)
const tasks = ref([])
const ministers = ref([])
const filters = ref({ status: '', assignee: '' })
const showCreateDialog = ref(false)
const autoRefresh = ref(true)
const lastUpdatedAt = ref(null)
const isPolling = ref(false)
const form = ref({
  title: '',
  description: '',
  assignee_id: null,
  priority: 'medium',
})

let timer = null

const ministerMap = computed(() => {
  const map = {}
  ministers.value.forEach((m) => {
    map[m.id] = m.name
  })
  return map
})

const lastUpdatedText = computed(() => {
  if (!lastUpdatedAt.value) return '--'
  return formatDate(lastUpdatedAt.value)
})

const loadTasks = async ({ silent = false } = {}) => {
  if (!silent) loading.value = true

  try {
    const params = { limit: 200 }
    if (filters.value.status) params.status = filters.value.status
    if (filters.value.assignee) params.assignee_id = filters.value.assignee

    const data = await api.get('/tasks/', { params })
    tasks.value = normalizeText(data)
    lastUpdatedAt.value = new Date()
  } catch (error) {
    if (!silent) {
      ElMessage.error(error?.response?.data?.detail || '加载任务失败')
    }
    console.error(error)
  } finally {
    if (!silent) loading.value = false
  }
}

const loadMinisters = async () => {
  const data = await api.get('/ministers/')
  ministers.value = normalizeText(data)
}

const getAssigneeName = (id) => ministerMap.value[id] || `#${id}`
const getDispatcherName = (id) => ministerMap.value[id] || '司礼监'
const getStatusType = (status) => ({ pending: 'info', processing: 'warning', completed: 'success' }[status] || 'info')
const getStatusText = (status) => ({ pending: '待处理', processing: '进行中', completed: '已完成' }[status] || status)
const formatDate = (value) => (value ? new Date(value).toLocaleString('zh-CN') : '-')

const resetFilters = () => {
  filters.value = { status: '', assignee: '' }
  loadTasks().catch((e) => console.error(e))
}

const viewTaskDetail = (task) => {
  router.push({
    name: 'TaskDetail',
    params: { taskCode: task.task_id },
  })
}

const buildTaskId = () => {
  const now = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `TASK-${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}-${Date.now().toString().slice(-4)}`
}

const createTask = async () => {
  if (!form.value.title || !form.value.assignee_id) {
    ElMessage.warning('请填写标题和承办大臣')
    return
  }

  try {
    const payload = {
      ...form.value,
      task_id: buildTaskId(),
      dispatcher_id: DEFAULT_DISPATCHER_ID,
      description: form.value.description || '',
    }

    await api.post('/tasks/', payload)
    ElMessage.success('任务创建成功')
    showCreateDialog.value = false
    form.value = { title: '', description: '', assignee_id: null, priority: 'medium' }
    await loadTasks()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '创建任务失败')
  }
}

const markCompleted = async (task) => {
  try {
    await api.put(`/tasks/${task.id}`, { status: 'completed' })
    ElMessage.success('任务已标记完成')
    await loadTasks()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '更新任务失败')
  }
}

const pollTasks = async () => {
  if (isPolling.value) return
  isPolling.value = true
  try {
    await loadTasks({ silent: true })
  } finally {
    isPolling.value = false
  }
}

const startPolling = () => {
  stopPolling()
  if (!autoRefresh.value) return

  timer = setInterval(() => {
    pollTasks().catch((e) => console.error(e))
  }, POLL_INTERVAL)
}

const stopPolling = () => {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

watch(autoRefresh, () => {
  startPolling()
})

onMounted(async () => {
  try {
    await Promise.all([loadMinisters(), loadTasks()])
    startPolling()
  } catch (error) {
    ElMessage.error('加载任务页面失败')
    console.error(error)
  }
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.tasks-page {
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
  gap: 12px;
  flex-wrap: wrap;
}

.page-header h1 {
  font-size: 20px;
  font-weight: 700;
}

.subtitle {
  margin-top: 4px;
  color: var(--muted);
  font-size: 12px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.filter-card {
  margin-bottom: 16px;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
