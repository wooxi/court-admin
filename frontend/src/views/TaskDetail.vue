<template>
  <div class="task-detail-page" v-loading="loading">
    <div class="page-header">
      <div>
        <h1>🧭 任务详情</h1>
        <p class="subtitle">{{ task?.task_id || route.params.taskCode }}</p>
      </div>

      <div class="header-actions">
        <el-tag type="info" effect="plain">上次更新：{{ lastUpdatedText }}</el-tag>
        <el-switch v-model="autoRefresh" inline-prompt active-text="自动刷新" inactive-text="手动" />
        <el-button @click="loadTaskDetail">
          <el-icon><Refresh /></el-icon>
          立即刷新
        </el-button>
        <el-button @click="router.push('/tasks')">返回任务列表</el-button>
      </div>
    </div>

    <el-card v-if="task" class="summary-card" shadow="never">
      <el-descriptions :column="3" border>
        <el-descriptions-item label="任务标题" :span="3">{{ task.title }}</el-descriptions-item>
        <el-descriptions-item label="任务状态">
          <el-tag :type="getStatusType(task.status)">{{ getStatusText(task.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="分派人">{{ getMinisterName(task.dispatcher_id, '司礼监') }}</el-descriptions-item>
        <el-descriptions-item label="承接人">{{ getMinisterName(task.assignee_id) }}</el-descriptions-item>
        <el-descriptions-item label="分派时间">{{ formatDate(task.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="完成时间">{{ formatDate(task.completed_at) }}</el-descriptions-item>
        <el-descriptions-item label="优先级">{{ getPriorityText(task.priority) }}</el-descriptions-item>
        <el-descriptions-item label="总 Token">{{ formatTokenValue(task.execution_detail?.total_tokens) }}</el-descriptions-item>
        <el-descriptions-item label="输入/输出 Token">
          {{ formatTokenSplit(task.execution_detail?.input_tokens, task.execution_detail?.output_tokens) }}
        </el-descriptions-item>
        <el-descriptions-item label="执行耗时">{{ formatDuration(task.execution_detail?.duration_seconds) }}</el-descriptions-item>
        <el-descriptions-item label="明细来源">{{ task.execution_detail?.source || '--' }}</el-descriptions-item>
        <el-descriptions-item label="任务描述" :span="3">{{ task.description || '--' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-row :gutter="16" class="content-row">
      <el-col :xs="24" :lg="16">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>📍 流转时间线（实时）</span>
              <el-tag type="success" effect="plain">每 5 秒刷新</el-tag>
            </div>
          </template>

          <TaskTimeline :flows="flows" />
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="8">
        <el-card shadow="never" class="log-card">
          <template #header>
            <div class="card-header">
              <span>📝 执行日志</span>
              <span class="count">{{ executionLogs.length }} 条</span>
            </div>
          </template>

          <div v-if="executionLogs.length" class="log-list">
            <div v-for="log in executionLogs" :key="log.id" class="log-item">
              <div class="log-time">{{ formatDate(log.timestamp) }}</div>
              <div class="log-title">{{ log.title }}</div>
              <pre class="log-message">{{ log.message }}</pre>
            </div>
          </div>
          <el-empty v-else description="暂无执行日志" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'

import api from '@/api'
import TaskTimeline from '@/components/task/TaskTimeline.vue'
import { normalizeText } from '@/utils/text'

const POLL_INTERVAL = 5000

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const task = ref(null)
const flows = ref([])
const ministers = ref([])
const autoRefresh = ref(true)
const lastUpdatedAt = ref(null)
const isPolling = ref(false)

let timer = null

const ministerMap = computed(() => {
  const map = {}
  ministers.value.forEach((item) => {
    map[item.id] = item.name
  })
  return map
})

const lastUpdatedText = computed(() => {
  if (!lastUpdatedAt.value) return '--'
  return formatDate(lastUpdatedAt.value)
})

const executionLogs = computed(() => {
  const logs = []

  flows.value.forEach((flow) => {
    const title = `${flow.from_actor || '未知'} → ${flow.to_actor || '未知'} · ${flow.action || '流转'}`

    if (flow.remark) {
      logs.push({
        id: `${flow.id}-remark`,
        timestamp: flow.timestamp,
        title,
        message: flow.remark,
      })
    }

    const metadata = flow.metadata || {}
    if (!Object.keys(metadata).length) return

    if (Array.isArray(metadata.logs)) {
      metadata.logs.forEach((message, idx) => {
        logs.push({
          id: `${flow.id}-logs-${idx}`,
          timestamp: flow.timestamp,
          title: `${title} · logs[${idx + 1}]`,
          message: typeof message === 'string' ? message : JSON.stringify(message, null, 2),
        })
      })
      return
    }

    if (metadata.log) {
      logs.push({
        id: `${flow.id}-log`,
        timestamp: flow.timestamp,
        title: `${title} · log`,
        message: typeof metadata.log === 'string' ? metadata.log : JSON.stringify(metadata.log, null, 2),
      })
      return
    }

    logs.push({
      id: `${flow.id}-metadata`,
      timestamp: flow.timestamp,
      title: `${title} · metadata`,
      message: JSON.stringify(metadata, null, 2),
    })
  })

  return logs
})

const formatDate = (value) => (value ? new Date(value).toLocaleString('zh-CN') : '--')
const getStatusType = (status) => ({ pending: 'info', processing: 'warning', completed: 'success' }[status] || 'info')
const getStatusText = (status) => ({ pending: '待处理', processing: '进行中', completed: '已完成' }[status] || status)
const getPriorityText = (priority) => ({ high: '高', medium: '中', low: '低' }[priority] || priority || '--')

const formatTokenValue = (value) => {
  if (value === null || value === undefined) return '--'
  return Number(value).toLocaleString('zh-CN')
}

const formatTokenSplit = (input, output) => {
  const inputText = formatTokenValue(input)
  const outputText = formatTokenValue(output)
  if (inputText === '--' && outputText === '--') return '--'
  return `${inputText} / ${outputText}`
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

const getMinisterName = (id, fallback = '-') => ministerMap.value[id] || fallback

const loadMinisters = async () => {
  const data = await api.get('/ministers/')
  ministers.value = normalizeText(data)
}

const loadTaskDetail = async ({ silent = false } = {}) => {
  if (!route.params.taskCode) return
  if (!silent) loading.value = true

  try {
    const taskInfo = await api.get(`/tasks/by-code/${encodeURIComponent(route.params.taskCode)}`)
    task.value = normalizeText(taskInfo)

    const flowData = await api.get(`/flows/task/${task.value.id}`)
    flows.value = normalizeText(flowData)

    lastUpdatedAt.value = new Date()
  } catch (error) {
    if (!silent) {
      ElMessage.error(error?.response?.data?.detail || '加载任务详情失败')
    }
    console.error(error)
  } finally {
    if (!silent) loading.value = false
  }
}

const pollTaskDetail = async () => {
  if (isPolling.value) return
  isPolling.value = true
  try {
    await loadTaskDetail({ silent: true })
  } finally {
    isPolling.value = false
  }
}

const startPolling = () => {
  stopPolling()
  if (!autoRefresh.value) return

  timer = setInterval(() => {
    pollTaskDetail().catch((e) => console.error(e))
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
  () => route.params.taskCode,
  () => {
    loadTaskDetail().catch((e) => console.error(e))
  }
)

onMounted(async () => {
  await Promise.all([loadMinisters(), loadTaskDetail()])
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.task-detail-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
}

.page-header h1 {
  font-size: 22px;
  margin: 0;
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

.summary-card {
  border-color: var(--line);
}

.content-row {
  align-items: stretch;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.log-card {
  height: 100%;
}

.count {
  color: var(--muted);
  font-size: 12px;
}

.log-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 560px;
  overflow-y: auto;
  padding-right: 4px;
}

.log-item {
  border: 1px solid var(--line);
  background: var(--panel2);
  border-radius: 8px;
  padding: 10px;
}

.log-time {
  font-size: 11px;
  color: var(--muted);
  margin-bottom: 4px;
}

.log-title {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 6px;
  color: var(--text);
}

.log-message {
  margin: 0;
  font-size: 12px;
  color: #9fb1d9;
  white-space: pre-wrap;
  word-break: break-all;
  line-height: 1.5;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
