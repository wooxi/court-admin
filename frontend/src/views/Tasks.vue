<template>
  <div class="tasks-page">
    <div class="page-header">
      <div>
        <h1>📋 任务管理</h1>
        <p class="subtitle">任务台账实时更新，右侧可查看执行明细</p>
      </div>
      <div class="header-actions">
        <el-tag type="info" effect="plain">上次更新：{{ lastUpdatedText }}</el-tag>
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

    <el-card class="filter-card" shadow="never">
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

    <el-card shadow="never">
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

        <el-table-column label="总 Token" width="120">
          <template #default="{ row }">
            {{ formatTokenValue(row.execution_detail?.total_tokens) }}
          </template>
        </el-table-column>

        <el-table-column label="耗时" width="120">
          <template #default="{ row }">
            {{ formatDuration(row.execution_detail?.duration_seconds) }}
          </template>
        </el-table-column>

        <el-table-column label="分派时间" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>

        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" plain @click="openDetailDrawer(row)">详情</el-button>
            <el-button size="small" @click="goTaskDetailPage(row)">详情页</el-button>
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

    <el-drawer
      v-model="drawer.visible"
      direction="rtl"
      size="46%"
      destroy-on-close
      class="task-detail-drawer"
    >
      <template #header>
        <div class="drawer-header" v-if="drawer.task">
          <div>
            <div class="drawer-title">🧭 {{ drawer.task.title }}</div>
            <div class="drawer-subtitle">{{ drawer.task.task_id }}</div>
          </div>
          <div class="drawer-actions">
            <el-tag :type="getStatusType(drawer.task.status)">{{ getStatusText(drawer.task.status) }}</el-tag>
            <el-button size="small" @click="refreshDrawer">刷新</el-button>
            <el-button size="small" @click="goTaskDetailPage(drawer.task)">详情页</el-button>
          </div>
        </div>
      </template>

      <div v-loading="drawer.loading" class="drawer-content">
        <el-empty v-if="!drawer.task" description="请选择任务" />

        <template v-else>
          <el-card shadow="never" class="drawer-section">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="分派人">{{ getDispatcherName(drawer.task.dispatcher_id) }}</el-descriptions-item>
              <el-descriptions-item label="承接人">{{ getAssigneeName(drawer.task.assignee_id) }}</el-descriptions-item>
              <el-descriptions-item label="分派时间">{{ formatDate(drawer.task.created_at) }}</el-descriptions-item>
              <el-descriptions-item label="完成时间">{{ formatDate(drawer.task.completed_at) }}</el-descriptions-item>
            </el-descriptions>
          </el-card>

          <el-card shadow="never" class="drawer-section">
            <template #header>
              <div class="card-header">
                <span>🧮 Token 明细</span>
                <span class="header-tip">统一口径：task_execution_details</span>
              </div>
            </template>
            <div class="token-grid">
              <div class="token-item">
                <div class="token-label">Prompt Token</div>
                <div class="token-value">{{ formatTokenValue(drawer.task.execution_detail?.input_tokens) }}</div>
              </div>
              <div class="token-item">
                <div class="token-label">Output Token</div>
                <div class="token-value">{{ formatTokenValue(drawer.task.execution_detail?.output_tokens) }}</div>
              </div>
              <div class="token-item total">
                <div class="token-label">Total Token</div>
                <div class="token-value">{{ formatTokenValue(drawer.task.execution_detail?.total_tokens) }}</div>
              </div>
              <div class="token-item">
                <div class="token-label">总耗时</div>
                <div class="token-value">{{ formatDuration(drawer.task.execution_detail?.duration_seconds) }}</div>
              </div>
            </div>
          </el-card>

          <el-card shadow="never" class="drawer-section">
            <template #header>
              <span>🧾 执行时间轴</span>
            </template>
            <TaskTimeline :flows="drawer.flows" />
          </el-card>

          <el-card shadow="never" class="drawer-section">
            <template #header>
              <div class="card-header">
                <span>⏱️ 分步骤耗时 / Token</span>
                <span class="header-tip">按相邻流转时间推算步骤耗时</span>
              </div>
            </template>

            <el-table :data="drawerSteps" size="small" stripe>
              <el-table-column prop="step" label="步骤" min-width="180" show-overflow-tooltip />
              <el-table-column prop="at" label="执行时间" min-width="160" />
              <el-table-column prop="durationText" label="步骤耗时" width="110" />
              <el-table-column prop="promptTokens" label="Prompt" width="90" />
              <el-table-column prop="outputTokens" label="Output" width="90" />
              <el-table-column prop="totalTokens" label="Total" width="90" />
              <el-table-column prop="remark" label="备注" min-width="180" show-overflow-tooltip />
            </el-table>
          </el-card>
        </template>
      </div>
    </el-drawer>

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
        <el-button type="primary" @click="createNewTask">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

import TaskTimeline from '@/components/task/TaskTimeline.vue'
import {
  createTask,
  fetchMinisters,
  fetchTaskByCode,
  fetchTaskFlows,
  fetchTasks,
  updateTask,
} from '@/api/tasks'

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

const drawer = ref({
  visible: false,
  loading: false,
  taskCode: '',
  task: null,
  flows: [],
})

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

const drawerSteps = computed(() => {
  const rows = [...(drawer.value.flows || [])].sort((a, b) => {
    const at = new Date(resolveFlowTime(a) || 0).getTime()
    const bt = new Date(resolveFlowTime(b) || 0).getTime()
    return at - bt
  })

  return rows.map((flow, index) => {
    const at = resolveFlowTime(flow)
    const nextFlow = rows[index + 1]
    const nextAt = resolveFlowTime(nextFlow) || drawer.value.task?.completed_at || null

    let stepDuration = null
    if (at && nextAt) {
      const diff = Math.floor((new Date(nextAt).getTime() - new Date(at).getTime()) / 1000)
      if (Number.isFinite(diff) && diff >= 0) stepDuration = diff
    }

    const tokenInfo = extractTokenSummary(flow.metadata)

    return {
      id: flow.id,
      step: `${flow.action || '流转'}（${flow.from_actor || '未知'} → ${flow.to_actor || '未知'}）`,
      at: formatDate(at),
      durationText: formatDuration(stepDuration),
      promptTokens: formatTokenCell(tokenInfo.prompt),
      outputTokens: formatTokenCell(tokenInfo.output),
      totalTokens: formatTokenCell(tokenInfo.total),
      remark: flow.remark || '-',
    }
  })
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

    tasks.value = await fetchTasks(params)
    lastUpdatedAt.value = new Date()
  } catch (error) {
    if (!silent) ElMessage.error(error?.response?.data?.detail || '加载任务失败')
    console.error(error)
  } finally {
    if (!silent) loading.value = false
  }
}

const loadMinisters = async () => {
  ministers.value = await fetchMinisters()
}

const getAssigneeName = (id) => ministerMap.value[id] || `#${id}`
const getDispatcherName = (id) => ministerMap.value[id] || '司礼监'
const getStatusType = (status) => ({ pending: 'info', processing: 'warning', completed: 'success' }[status] || 'info')
const getStatusText = (status) => ({ pending: '待处理', processing: '进行中', completed: '已完成' }[status] || status)
const formatDate = (value) => (value ? new Date(value).toLocaleString('zh-CN') : '--')
const resolveFlowTime = (flow) => flow?.timestamp || flow?.created_at || null

const formatTokenValue = (value) => {
  if (value === null || value === undefined) return '--'
  return Number(value).toLocaleString('zh-CN')
}

const formatTokenCell = (value) => {
  if (value === null || value === undefined) return '--'
  return Number(value).toLocaleString('zh-CN')
}

const formatDuration = (seconds) => {
  if (seconds === null || seconds === undefined) return '--'
  const total = Number(seconds)
  if (!Number.isFinite(total)) return '--'

  const h = Math.floor(total / 3600)
  const m = Math.floor((total % 3600) / 60)
  const s = total % 60

  if (h > 0) return `${h}小时${m}分${s}秒`
  if (m > 0) return `${m}分${s}秒`
  return `${s}秒`
}

const extractTokenSummary = (metadata) => {
  const source = typeof metadata === 'object' && metadata ? metadata : {}
  const prompt = findNumericValue(source, ['prompt_tokens', 'promptTokens', 'input_tokens', 'inputTokens'])
  const output = findNumericValue(source, ['output_tokens', 'outputTokens', 'completion_tokens', 'completionTokens'])
  let total = findNumericValue(source, ['total_tokens', 'totalTokens', 'tokens'])
  if (total === null && (prompt !== null || output !== null)) total = (prompt || 0) + (output || 0)
  return { prompt, output, total }
}

const findNumericValue = (payload, keys, depth = 0) => {
  if (!payload || typeof payload !== 'object' || depth > 5) return null

  for (const key of keys) {
    const value = payload[key]
    if (typeof value === 'number' && Number.isFinite(value)) return value
    if (typeof value === 'string' && /^\d+$/.test(value.trim())) return Number(value)
  }

  for (const value of Object.values(payload)) {
    if (value && typeof value === 'object') {
      const nested = findNumericValue(value, keys, depth + 1)
      if (nested !== null) return nested
    }
  }

  return null
}

const resetFilters = () => {
  filters.value = { status: '', assignee: '' }
  loadTasks().catch((e) => console.error(e))
}

const goTaskDetailPage = (task) => {
  const taskCode = task?.task_id || drawer.value.task?.task_id
  if (!taskCode) return

  router.push({
    name: 'TaskDetail',
    params: { taskCode },
  })
}

const loadDrawerData = async (taskCode, { silent = false } = {}) => {
  if (!taskCode) return

  drawer.value.taskCode = taskCode
  if (!silent) drawer.value.loading = true

  try {
    const taskData = await fetchTaskByCode(taskCode)
    const flowData = await fetchTaskFlows(taskData.id)
    drawer.value.task = taskData
    drawer.value.flows = flowData || []
  } catch (error) {
    if (!silent) ElMessage.error(error?.response?.data?.detail || '加载任务详情失败')
    console.error(error)
  } finally {
    if (!silent) drawer.value.loading = false
  }
}

const openDetailDrawer = async (task) => {
  drawer.value.visible = true
  await loadDrawerData(task.task_id)
}

const refreshDrawer = async () => {
  await loadDrawerData(drawer.value.taskCode)
}

const buildTaskId = () => {
  const now = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `TASK-${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}-${Date.now().toString().slice(-4)}`
}

const createNewTask = async () => {
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

    await createTask(payload)
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
    await updateTask(task.id, { status: 'completed' })
    ElMessage.success('任务已标记完成')
    await loadTasks()
    if (drawer.value.visible && drawer.value.taskCode === task.task_id) {
      await loadDrawerData(task.task_id, { silent: true })
    }
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '更新任务失败')
  }
}

const pollTasks = async () => {
  if (isPolling.value) return
  isPolling.value = true
  try {
    await loadTasks({ silent: true })
    if (drawer.value.visible && drawer.value.taskCode) {
      await loadDrawerData(drawer.value.taskCode, { silent: true })
    }
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

watch(
  () => drawer.value.visible,
  (visible) => {
    if (!visible) {
      drawer.value.task = null
      drawer.value.flows = []
      drawer.value.taskCode = ''
    }
  }
)

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

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
}

.drawer-title {
  font-size: 16px;
  font-weight: 700;
}

.drawer-subtitle {
  font-size: 12px;
  color: var(--muted);
  margin-top: 4px;
}

.drawer-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.drawer-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-bottom: 20px;
}

.drawer-section {
  border-color: var(--line);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.header-tip {
  color: var(--muted);
  font-size: 12px;
}

.token-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.token-item {
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 10px 12px;
  background: var(--panel2);
}

.token-item.total {
  border-color: rgba(106, 158, 255, 0.45);
}

.token-label {
  font-size: 12px;
  color: var(--muted);
}

.token-value {
  margin-top: 6px;
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
}

@media (max-width: 1200px) {
  :deep(.task-detail-drawer) {
    width: 78% !important;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  :deep(.task-detail-drawer) {
    width: 100% !important;
  }

  .token-grid {
    grid-template-columns: 1fr;
  }
}
</style>
