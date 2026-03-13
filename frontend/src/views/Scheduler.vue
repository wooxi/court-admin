<template>
  <div class="scheduler-page">
    <div class="page-header">
      <div>
        <h1>⏰ 定时任务总览</h1>
        <p class="subtitle">查看任务定义、最新状态与最近执行结果</p>
      </div>
      <el-button type="primary" @click="loadJobs">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <el-alert
      v-if="pageError"
      :title="pageError"
      type="error"
      show-icon
      :closable="false"
      class="error-alert"
    >
      <template #default>
        <el-button link type="danger" @click="loadJobs">重试</el-button>
      </template>
    </el-alert>

    <div class="scheduler-grid">
      <el-card class="jobs-card" v-loading="loadingJobs" shadow="never">
        <template #header>
          <div class="card-header">
            <span>📋 定时任务列表</span>
            <span class="count-text">共 {{ jobs.length }} 项</span>
          </div>
        </template>

        <el-empty v-if="!loadingJobs && jobs.length === 0" description="暂无定时任务" />

        <el-table
          v-else
          :data="jobs"
          row-key="id"
          highlight-current-row
          :current-row-key="selectedJobId"
          @row-click="handleSelectJob"
          max-height="560"
          size="small"
        >
          <el-table-column prop="name" label="名称" min-width="160" show-overflow-tooltip />
          <el-table-column prop="source" label="来源" min-width="120" show-overflow-tooltip />
          <el-table-column prop="schedule" label="调度表达式 / 触发条件" min-width="220" show-overflow-tooltip />
          <el-table-column label="启用状态" width="98">
            <template #default="{ row }">
              <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
                {{ row.enabled ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="下次运行" min-width="170">
            <template #default="{ row }">
              {{ formatDate(row.nextRunTime) }}
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <div class="right-panel">
        <el-card class="detail-card" v-loading="loadingDetail" shadow="never">
          <template #header>
            <div class="card-header">
              <span>🧾 任务详情</span>
              <el-button v-if="selectedJob" text @click="loadJobDetail(selectedJob)">刷新详情</el-button>
            </div>
          </template>

          <el-empty v-if="!selectedJob" description="请选择左侧任务查看详情" />

          <template v-else>
            <el-alert
              v-if="detailError"
              :title="detailError"
              type="warning"
              show-icon
              :closable="false"
              class="inner-alert"
            >
              <template #default>
                <el-button link type="warning" @click="loadJobDetail(selectedJob)">重试</el-button>
              </template>
            </el-alert>

            <el-descriptions :column="1" border>
              <el-descriptions-item label="任务名称">{{ selectedJob.name }}</el-descriptions-item>
              <el-descriptions-item label="最近一次运行时间">{{ formatDate(detail?.lastRunTime) }}</el-descriptions-item>
              <el-descriptions-item label="最近状态">
                <el-tag :type="getStatusType(detail?.lastStatus)">
                  {{ getStatusText(detail?.lastStatus) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="最近日志摘要">
                <div class="log-summary">{{ detail?.lastLogSummary || '暂无日志摘要' }}</div>
              </el-descriptions-item>
            </el-descriptions>
          </template>
        </el-card>

        <el-card class="history-card" v-loading="loadingHistory" shadow="never">
          <template #header>
            <div class="card-header">
              <span>🕘 执行历史（最近 N 次）</span>
              <div class="header-actions">
                <el-select v-model="historyLimit" size="small" style="width: 110px">
                  <el-option :value="10" label="最近 10 次" />
                  <el-option :value="20" label="最近 20 次" />
                  <el-option :value="50" label="最近 50 次" />
                </el-select>
                <el-button v-if="selectedJob" text @click="loadRunHistory(selectedJob)">刷新</el-button>
              </div>
            </div>
          </template>

          <el-empty v-if="!selectedJob" description="请选择左侧任务查看执行历史" />

          <template v-else>
            <el-alert
              v-if="historyError"
              :title="historyError"
              type="warning"
              show-icon
              :closable="false"
              class="inner-alert"
            >
              <template #default>
                <el-button link type="warning" @click="loadRunHistory(selectedJob)">重试</el-button>
              </template>
            </el-alert>

            <el-empty v-if="!loadingHistory && historyList.length === 0" description="暂无执行历史" />

            <el-table v-else :data="historyList" size="small" max-height="360">
              <el-table-column label="开始时间" min-width="160">
                <template #default="{ row }">{{ formatDate(row.startTime) }}</template>
              </el-table-column>
              <el-table-column label="结束时间" min-width="160">
                <template #default="{ row }">{{ formatDate(row.endTime) }}</template>
              </el-table-column>
              <el-table-column label="耗时" width="96">
                <template #default="{ row }">{{ formatDuration(row) }}</template>
              </el-table-column>
              <el-table-column label="状态" width="96">
                <template #default="{ row }">
                  <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusText(row.status) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="summary" label="结果摘要" min-width="220" show-overflow-tooltip>
                <template #default="{ row }">
                  {{ row.summary || '-' }}
                </template>
              </el-table-column>
            </el-table>
          </template>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Refresh } from '@element-plus/icons-vue'

import api from '@/api'

const loadingJobs = ref(false)
const loadingDetail = ref(false)
const loadingHistory = ref(false)

const jobs = ref([])
const selectedJobId = ref('')
const detail = ref(null)
const historyList = ref([])
const historyLimit = ref(10)

const pageError = ref('')
const detailError = ref('')
const historyError = ref('')

const selectedJob = computed(() => jobs.value.find((job) => job.id === selectedJobId.value) || null)

const isNotFound = (error) => error?.response?.status === 404
const formatError = (error) => error?.response?.data?.detail || error?.message || '请求失败'

const normalizeBoolean = (value) => {
  if (typeof value === 'boolean') return value
  if (typeof value === 'number') return value > 0
  if (typeof value === 'string') {
    const normalized = value.toLowerCase()
    if (['enabled', 'enable', 'active', 'on', 'true', 'running'].includes(normalized)) return true
    if (['disabled', 'disable', 'inactive', 'off', 'false', 'stopped'].includes(normalized)) return false
  }
  return false
}

const normalizeStatus = (status) => {
  if (!status) return 'unknown'
  const value = String(status).toLowerCase()
  if (['success', 'completed', 'done', 'ok', 'succeeded', 'finished'].some((v) => value.includes(v))) return 'success'
  if (['failed', 'error', 'exception', 'timeout'].some((v) => value.includes(v))) return 'failed'
  if (['running', 'processing', 'executing'].some((v) => value.includes(v))) return 'running'
  if (['pending', 'waiting', 'queued'].some((v) => value.includes(v))) return 'pending'
  if (['skipped', 'ignore'].some((v) => value.includes(v))) return 'skipped'
  return value
}

const getStatusType = (status) => {
  const normalized = normalizeStatus(status)
  if (normalized === 'success') return 'success'
  if (normalized === 'failed') return 'danger'
  if (normalized === 'running') return 'warning'
  if (normalized === 'pending') return 'info'
  return 'info'
}

const getStatusText = (status) => {
  const normalized = normalizeStatus(status)
  if (normalized === 'success') return '成功'
  if (normalized === 'failed') return '失败'
  if (normalized === 'running') return '执行中'
  if (normalized === 'pending') return '等待中'
  if (normalized === 'skipped') return '已跳过'
  if (normalized === 'unknown') return '未知'
  return String(status)
}

const resolveArray = (payload) => {
  if (Array.isArray(payload)) return payload
  if (Array.isArray(payload?.items)) return payload.items
  if (Array.isArray(payload?.jobs)) return payload.jobs
  if (Array.isArray(payload?.runs)) return payload.runs
  if (Array.isArray(payload?.history)) return payload.history
  if (Array.isArray(payload?.list)) return payload.list
  if (Array.isArray(payload?.data)) return payload.data
  return []
}

const resolveObject = (payload) => {
  if (!payload || Array.isArray(payload)) return null
  return payload.job || payload.item || payload.data || payload
}

const normalizeJob = (rawJob, index) => {
  const id = String(rawJob?.id ?? rawJob?.job_id ?? rawJob?.code ?? rawJob?.name ?? `job_${index}`)
  const name = rawJob?.name ?? rawJob?.job_name ?? rawJob?.title ?? `任务 ${index + 1}`
  const source = rawJob?.source ?? rawJob?.origin ?? rawJob?.module ?? rawJob?.owner ?? '-'
  const schedule =
    rawJob?.cron_expression ??
    rawJob?.cron ??
    rawJob?.schedule ??
    rawJob?.trigger ??
    rawJob?.trigger_condition ??
    rawJob?.trigger_desc ??
    '-'

  return {
    id,
    name,
    source,
    schedule,
    enabled: normalizeBoolean(rawJob?.enabled ?? rawJob?.is_enabled ?? rawJob?.active ?? rawJob?.status),
    nextRunTime: rawJob?.next_run_time ?? rawJob?.next_run ?? rawJob?.next_trigger_time ?? rawJob?.nextRunAt ?? null,
    lastRunTime: rawJob?.last_run_time ?? rawJob?.last_run ?? rawJob?.latest_run_time ?? null,
    lastStatus: rawJob?.last_status ?? rawJob?.latest_status ?? rawJob?.last_result ?? null,
    lastLogSummary:
      rawJob?.last_log_summary ?? rawJob?.log_summary ?? rawJob?.latest_log ?? rawJob?.last_message ?? '',
    embeddedRuns: resolveArray(rawJob?.recent_runs ?? rawJob?.runs ?? rawJob?.history),
    raw: rawJob,
  }
}

const normalizeDetail = (rawDetail, fallbackJob) => ({
  lastRunTime:
    rawDetail?.last_run_time ??
    rawDetail?.last_run ??
    rawDetail?.latest_run_time ??
    rawDetail?.latest_run?.start_time ??
    fallbackJob?.lastRunTime ??
    null,
  lastStatus:
    rawDetail?.last_status ??
    rawDetail?.latest_status ??
    rawDetail?.last_result ??
    rawDetail?.latest_run?.status ??
    fallbackJob?.lastStatus ??
    null,
  lastLogSummary:
    rawDetail?.last_log_summary ??
    rawDetail?.log_summary ??
    rawDetail?.latest_log ??
    rawDetail?.latest_run?.summary ??
    fallbackJob?.lastLogSummary ??
    '',
})

const normalizeRun = (rawRun) => {
  const startTime = rawRun?.start_time ?? rawRun?.started_at ?? rawRun?.startAt ?? null
  const endTime = rawRun?.end_time ?? rawRun?.ended_at ?? rawRun?.finished_at ?? rawRun?.endAt ?? null

  let durationMs = rawRun?.duration_ms ?? rawRun?.durationMs ?? null
  if (typeof durationMs !== 'number' && typeof rawRun?.duration === 'number') {
    durationMs = rawRun.duration > 1000 ? rawRun.duration : rawRun.duration * 1000
  }

  return {
    startTime,
    endTime,
    durationMs,
    durationText: rawRun?.duration_text ?? null,
    status: rawRun?.status ?? rawRun?.state ?? rawRun?.result_status ?? (rawRun?.success === false ? 'failed' : 'success'),
    summary: rawRun?.result_summary ?? rawRun?.summary ?? rawRun?.message ?? rawRun?.output ?? '',
  }
}

const formatDate = (value) => (value ? new Date(value).toLocaleString('zh-CN') : '-')

const formatDuration = (run) => {
  if (run?.durationText) return run.durationText

  let durationMs = typeof run?.durationMs === 'number' ? run.durationMs : null

  if (!durationMs && run?.startTime && run?.endTime) {
    const ms = new Date(run.endTime).getTime() - new Date(run.startTime).getTime()
    if (!Number.isNaN(ms) && ms > 0) durationMs = ms
  }

  if (!durationMs || durationMs <= 0) return '-'
  if (durationMs < 1000) return `${Math.round(durationMs)}ms`
  if (durationMs < 60_000) return `${(durationMs / 1000).toFixed(durationMs < 10_000 ? 1 : 0)}s`
  if (durationMs < 3_600_000) return `${(durationMs / 60_000).toFixed(1)}m`
  return `${(durationMs / 3_600_000).toFixed(1)}h`
}

const tryRequests = async (requestFns) => {
  for (const requestFn of requestFns) {
    try {
      return await requestFn()
    } catch (error) {
      if (isNotFound(error)) continue
      throw error
    }
  }
  return null
}

const loadJobs = async () => {
  loadingJobs.value = true
  pageError.value = ''

  try {
    const result = await tryRequests([
      () => api.get('/scheduler/jobs', { params: { limit: 200 } }),
      () => api.get('/scheduler/jobs/', { params: { limit: 200 } }),
      () => api.get('/scheduler', { params: { limit: 200 } }),
      () => api.get('/scheduler/overview'),
      () => api.get('/cron/jobs', { params: { limit: 200 } }),
    ])

    if (!result) {
      jobs.value = []
      selectedJobId.value = ''
      detail.value = null
      historyList.value = []
      pageError.value = '后端暂未提供定时任务接口（建议检查 /api/scheduler/*）。'
      return
    }

    const rawJobs = resolveArray(result)
    jobs.value = rawJobs.map(normalizeJob)

    if (jobs.value.length === 0) {
      selectedJobId.value = ''
      detail.value = null
      historyList.value = []
      return
    }

    const current = jobs.value.find((job) => job.id === selectedJobId.value) || jobs.value[0]
    await handleSelectJob(current)
  } catch (error) {
    jobs.value = []
    selectedJobId.value = ''
    detail.value = null
    historyList.value = []
    pageError.value = formatError(error)
  } finally {
    loadingJobs.value = false
  }
}

const loadJobDetail = async (job) => {
  if (!job) return

  detailError.value = ''
  loadingDetail.value = true
  detail.value = normalizeDetail(job.raw, job)

  try {
    const result = await tryRequests([
      () => api.get(`/scheduler/jobs/${encodeURIComponent(job.id)}`),
      () => api.get(`/scheduler/job/${encodeURIComponent(job.id)}`),
      () => api.get('/scheduler/job', { params: { job_id: job.id } }),
      () => api.get(`/cron/jobs/${encodeURIComponent(job.id)}`),
    ])

    if (!result) return

    const detailData = resolveObject(result)
    if (detailData) {
      detail.value = normalizeDetail({ ...job.raw, ...detailData }, job)
    }
  } catch (error) {
    detailError.value = formatError(error)
  } finally {
    loadingDetail.value = false
  }
}

const loadRunHistory = async (job) => {
  if (!job) return

  historyError.value = ''
  loadingHistory.value = true
  historyList.value = job.embeddedRuns.map(normalizeRun).slice(0, historyLimit.value)

  try {
    const result = await tryRequests([
      () => api.get(`/scheduler/jobs/${encodeURIComponent(job.id)}/runs`, { params: { limit: historyLimit.value } }),
      () => api.get(`/scheduler/jobs/${encodeURIComponent(job.id)}/history`, { params: { limit: historyLimit.value } }),
      () => api.get('/scheduler/history', { params: { job_id: job.id, limit: historyLimit.value } }),
      () => api.get(`/cron/jobs/${encodeURIComponent(job.id)}/runs`, { params: { limit: historyLimit.value } }),
    ])

    if (!result) return

    const rows = resolveArray(result)
    historyList.value = rows.map(normalizeRun).slice(0, historyLimit.value)
  } catch (error) {
    historyError.value = formatError(error)
  } finally {
    loadingHistory.value = false
  }
}

const handleSelectJob = async (job) => {
  if (!job?.id) return
  selectedJobId.value = job.id
  await Promise.all([loadJobDetail(job), loadRunHistory(job)])
}

const onGlobalRefresh = () => {
  loadJobs().catch((error) => {
    console.error('刷新定时任务失败', error)
  })
}

watch(historyLimit, () => {
  if (selectedJob.value) {
    loadRunHistory(selectedJob.value).catch((error) => {
      console.error('刷新执行历史失败', error)
    })
  }
})

onMounted(() => {
  loadJobs().catch((error) => {
    console.error('加载定时任务失败', error)
  })
  window.addEventListener('global-refresh', onGlobalRefresh)
})

onBeforeUnmount(() => {
  window.removeEventListener('global-refresh', onGlobalRefresh)
})
</script>

<style scoped>
.scheduler-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.page-header h1 {
  margin: 0;
  font-size: 22px;
}

.subtitle {
  margin-top: 4px;
  color: var(--muted);
  font-size: 13px;
}

.error-alert {
  margin-bottom: 4px;
}

.scheduler-grid {
  display: grid;
  grid-template-columns: minmax(360px, 44%) minmax(0, 56%);
  gap: 16px;
}

.right-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.count-text {
  color: var(--muted);
  font-size: 12px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.inner-alert {
  margin-bottom: 12px;
}

.log-summary {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}

:deep(.el-table__row) {
  cursor: pointer;
}

@media (max-width: 1200px) {
  .scheduler-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
