<template>
  <div class="scheduler-page">
    <div class="page-header">
      <div>
        <h1>⏰ 定时任务总览</h1>
        <p class="subtitle">正式接口：jobs / detail / history</p>
      </div>
      <el-button type="primary" @click="loadJobs(false)">
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
    />

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
          <el-table-column prop="name" label="名称" min-width="150" show-overflow-tooltip />
          <el-table-column prop="source" label="来源" min-width="130" show-overflow-tooltip />
          <el-table-column prop="schedule" label="调度表达式" min-width="220" show-overflow-tooltip />
          <el-table-column label="状态" width="92">
            <template #default="{ row }">
              <el-tag :type="row.enabled ? 'success' : 'info'" size="small">{{ row.enabled ? '启用' : '停用' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="下次运行" min-width="170">
            <template #default="{ row }">
              {{ formatDate(row.next_run) }}
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <div class="right-panel">
        <el-card class="detail-card" v-loading="loadingDetail" shadow="never">
          <template #header>
            <div class="card-header">
              <span>🧾 任务详情</span>
              <el-button v-if="selectedJob" text @click="loadJobDetail()">刷新详情</el-button>
            </div>
          </template>

          <el-empty v-if="!selectedJob" description="请选择左侧任务查看详情" />

          <template v-else>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="任务 ID">{{ selectedJob.id }}</el-descriptions-item>
              <el-descriptions-item label="任务名称">{{ selectedJob.name }}</el-descriptions-item>
              <el-descriptions-item label="调度表达式">{{ detail?.schedule || selectedJob.schedule || '-' }}</el-descriptions-item>
              <el-descriptions-item label="最近执行时间">{{ formatDate(detail?.last_run || selectedJob.last_run) }}</el-descriptions-item>
              <el-descriptions-item label="最近状态">
                <el-tag :type="getStatusType(detail?.last_status || selectedJob.last_status)">
                  {{ getStatusText(detail?.last_status || selectedJob.last_status) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="最近摘要">
                <div class="log-summary">{{ detail?.last_result || selectedJob.last_result || '暂无摘要' }}</div>
              </el-descriptions-item>
            </el-descriptions>
          </template>
        </el-card>

        <el-card class="history-card" v-loading="loadingHistory" shadow="never">
          <template #header>
            <div class="card-header history-header">
              <span>🕘 执行历史（history）</span>
              <div class="header-actions">
                <el-select v-model="historyStatus" clearable size="small" style="width: 120px" placeholder="全部状态">
                  <el-option label="成功" value="success" />
                  <el-option label="失败" value="failed" />
                  <el-option label="执行中" value="running" />
                  <el-option label="等待中" value="pending" />
                </el-select>
                <el-select v-model="historyPagination.page_size" size="small" style="width: 110px">
                  <el-option :value="10" label="10 / 页" />
                  <el-option :value="20" label="20 / 页" />
                  <el-option :value="50" label="50 / 页" />
                </el-select>
              </div>
            </div>
          </template>

          <el-empty v-if="!selectedJob" description="请选择左侧任务查看执行历史" />

          <template v-else>
            <el-table :data="historyList" size="small" max-height="350">
              <el-table-column label="执行时间" min-width="170">
                <template #default="{ row }">{{ formatDate(row.started_at) }}</template>
              </el-table-column>
              <el-table-column label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusText(row.status) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="耗时" width="110">
                <template #default="{ row }">{{ formatDurationMs(row.duration_ms) }}</template>
              </el-table-column>
              <el-table-column label="Token" width="110">
                <template #default="{ row }">{{ formatTokenValue(extractToken(row)) }}</template>
              </el-table-column>
              <el-table-column prop="source" label="来源" min-width="130" show-overflow-tooltip />
              <el-table-column label="日志" width="90">
                <template #default="{ row }">
                  <el-button text type="primary" @click="openLogDialog(row)">查看</el-button>
                </template>
              </el-table-column>
            </el-table>

            <div class="pagination-wrap">
              <el-pagination
                background
                layout="total, prev, pager, next"
                :current-page="historyPagination.page"
                :page-size="historyPagination.page_size"
                :total="historyPagination.total"
                @current-change="handleHistoryPageChange"
              />
            </div>
          </template>
        </el-card>
      </div>
    </div>

    <el-dialog v-model="logDialog.visible" title="执行日志" width="760px">
      <div class="log-meta">
        <el-tag :type="getStatusType(logDialog.row?.status)">{{ getStatusText(logDialog.row?.status) }}</el-tag>
        <span>执行时间：{{ formatDate(logDialog.row?.started_at) }}</span>
        <span>耗时：{{ formatDurationMs(logDialog.row?.duration_ms) }}</span>
      </div>
      <pre class="log-content">{{ logDialog.content }}</pre>
      <template #footer>
        <el-button @click="logDialog.visible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'

import {
  fetchSchedulerJobDetail,
  fetchSchedulerJobs,
  fetchSchedulerRunHistory,
} from '@/api/scheduler'

const loadingJobs = ref(false)
const loadingDetail = ref(false)
const loadingHistory = ref(false)

const jobs = ref([])
const selectedJobId = ref('')
const detail = ref(null)
const historyList = ref([])
const historyStatus = ref('')

const pageError = ref('')
const historyPagination = ref({
  page: 1,
  page_size: 20,
  total: 0,
})

const logDialog = ref({
  visible: false,
  row: null,
  content: '',
})

const selectedJob = computed(() => jobs.value.find((item) => item.id === selectedJobId.value) || null)

const normalizeStatus = (status) => {
  if (!status) return 'unknown'
  const value = String(status).toLowerCase()
  if (['success', 'completed', 'done', 'ok', 'finished'].some((item) => value.includes(item))) return 'success'
  if (['failed', 'error', 'exception', 'timeout'].some((item) => value.includes(item))) return 'failed'
  if (['running', 'processing', 'executing'].some((item) => value.includes(item))) return 'running'
  if (['pending', 'waiting', 'queued'].some((item) => value.includes(item))) return 'pending'
  return value
}

const getStatusType = (status) => {
  const value = normalizeStatus(status)
  if (value === 'success') return 'success'
  if (value === 'failed') return 'danger'
  if (value === 'running') return 'warning'
  return 'info'
}

const getStatusText = (status) => {
  const value = normalizeStatus(status)
  if (value === 'success') return '成功'
  if (value === 'failed') return '失败'
  if (value === 'running') return '执行中'
  if (value === 'pending') return '等待中'
  if (value === 'unknown') return '未知'
  return String(status)
}

const formatDate = (value) => (value ? new Date(value).toLocaleString('zh-CN') : '-')

const formatDurationMs = (durationMs) => {
  const value = Number(durationMs)
  if (!Number.isFinite(value) || value <= 0) return '-'
  if (value < 1000) return `${Math.round(value)} ms`
  if (value < 60_000) return `${(value / 1000).toFixed(value < 10_000 ? 1 : 0)} s`
  if (value < 3_600_000) return `${(value / 60_000).toFixed(1)} 分`
  return `${(value / 3_600_000).toFixed(1)} 时`
}

const formatTokenValue = (value) => {
  if (value === null || value === undefined) return '--'
  const num = Number(value)
  if (!Number.isFinite(num)) return '--'
  return num.toLocaleString('zh-CN')
}

const extractToken = (row) => {
  const directKeys = ['total_tokens', 'token_total', 'tokens', 'totalTokens']
  for (const key of directKeys) {
    const value = row?.[key]
    if (typeof value === 'number' && Number.isFinite(value)) return value
    if (typeof value === 'string' && /^\d+$/.test(value.trim())) return Number(value)
  }

  const text = row?.result || ''
  if (typeof text === 'string') {
    const match = text.match(/(?:total[_\s-]?tokens?|token(?:总量|总消耗)?)[^\d]{0,12}(\d+)/i)
    if (match) return Number(match[1])
  }

  return null
}

const loadJobs = async (silent = true) => {
  if (!silent) loadingJobs.value = true
  pageError.value = ''

  try {
    const rows = await fetchSchedulerJobs()
    jobs.value = Array.isArray(rows) ? rows : []

    if (!jobs.value.length) {
      selectedJobId.value = ''
      detail.value = null
      historyList.value = []
      return
    }

    const current = jobs.value.find((item) => item.id === selectedJobId.value) || jobs.value[0]
    selectedJobId.value = current.id
    await Promise.all([loadJobDetail(), loadRunHistory()])
  } catch (error) {
    pageError.value = error?.response?.data?.detail || '加载定时任务失败'
    jobs.value = []
    detail.value = null
    historyList.value = []
  } finally {
    if (!silent) loadingJobs.value = false
  }
}

const loadJobDetail = async () => {
  if (!selectedJob.value) return
  loadingDetail.value = true
  try {
    detail.value = await fetchSchedulerJobDetail(selectedJob.value.id)
  } catch (error) {
    detail.value = selectedJob.value
    ElMessage.error(error?.response?.data?.detail || '加载任务详情失败')
  } finally {
    loadingDetail.value = false
  }
}

const loadRunHistory = async () => {
  if (!selectedJob.value) return

  loadingHistory.value = true
  try {
    const params = {
      task_id: selectedJob.value.id,
      page: historyPagination.value.page,
      page_size: historyPagination.value.page_size,
    }
    if (historyStatus.value) params.status = historyStatus.value

    const payload = await fetchSchedulerRunHistory(params)
    historyList.value = payload.items || []
    historyPagination.value.total = Number(payload.pagination?.total || 0)
  } catch (error) {
    historyList.value = []
    historyPagination.value.total = 0
    ElMessage.error(error?.response?.data?.detail || '加载执行历史失败')
  } finally {
    loadingHistory.value = false
  }
}

const handleSelectJob = async (job) => {
  if (!job?.id) return
  selectedJobId.value = job.id
  historyPagination.value.page = 1
  await Promise.all([loadJobDetail(), loadRunHistory()])
}

const handleHistoryPageChange = async (page) => {
  historyPagination.value.page = page
  await loadRunHistory()
}

const openLogDialog = (row) => {
  logDialog.value.visible = true
  logDialog.value.row = row
  logDialog.value.content = row?.result || '暂无日志内容'
}

watch(
  () => [historyStatus.value, historyPagination.value.page_size],
  async () => {
    if (!selectedJob.value) return
    historyPagination.value.page = 1
    await loadRunHistory()
  }
)

onMounted(() => {
  loadJobs(false).catch((error) => {
    console.error('加载定时任务失败', error)
  })
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
  grid-template-columns: minmax(360px, 43%) minmax(0, 57%);
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

.history-header {
  flex-wrap: wrap;
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

.log-summary {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}

.pagination-wrap {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
}

.log-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  color: #606266;
  font-size: 13px;
}

.log-content {
  margin: 0;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px;
  max-height: 420px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  background: #fafafa;
  color: #303133;
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
