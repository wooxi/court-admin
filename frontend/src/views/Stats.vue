<template>
  <div class="stats">
    <h1>📈 统计报表（整合重构版）</h1>

    <el-card class="filter-card" style="margin-bottom: 16px;">
      <div class="card-header filters-header">
        <div class="filters-left">
          <span class="filter-label">统计窗口</span>
          <el-radio-group v-model="periodDays" size="small">
            <el-radio-button :label="7">近 7 天</el-radio-button>
            <el-radio-button :label="30">近 30 天</el-radio-button>
          </el-radio-group>

          <span class="filter-label">大臣筛选</span>
          <el-select v-model="selectedMinisterId" placeholder="全部大臣" clearable style="width: 150px;">
            <el-option
              v-for="minister in ministers"
              :key="minister.id"
              :label="minister.name"
              :value="minister.id"
            />
          </el-select>
        </div>

        <div class="filters-right">
          <el-tag v-if="linkedDate" type="warning" closable @close="clearLinkedDate">
            图表联动日期：{{ linkedDate }}
          </el-tag>
          <el-button size="small" @click="refreshAll">刷新</el-button>
        </div>
      </div>
    </el-card>

    <el-row :gutter="12" class="overview-row">
      <el-col
        v-for="item in metricCards"
        :key="item.key"
        :xs="24"
        :sm="12"
        :md="8"
        :lg="8"
        :xl="4"
      >
        <el-card class="overview-card" shadow="hover">
          <div class="summary-label">{{ item.label }}</div>
          <div class="summary-value">{{ item.value }}</div>
          <div class="summary-desc">{{ item.desc }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-bottom: 16px;">
      <template #header>
        <div class="card-header">
          <span>📉 执行趋势（Token / 平均耗时）</span>
          <span class="header-tip">点击图中某天可联动下方明细表</span>
        </div>
      </template>
      <div ref="trendChart" style="height: 360px;"></div>
    </el-card>

    <el-card style="margin-bottom: 16px;">
      <template #header>
        <span>📋 任务状态（{{ periodLabel }}）</span>
      </template>

      <el-table :data="taskStatsView" stripe>
        <el-table-column prop="name" label="大臣" width="110" />
        <el-table-column prop="department" label="部门" width="110" />
        <el-table-column prop="total" label="总数" width="90" />
        <el-table-column prop="completed" label="完成" width="90" />
        <el-table-column prop="processing" label="进行中" width="90" />
        <el-table-column prop="pending" label="待处理" width="90" />
        <el-table-column prop="completion_rate" label="完成率" min-width="180">
          <template #default="{ row }">
            <el-progress :percentage="Number(row.completion_rate || 0)" :stroke-width="10" />
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card>
      <template #header>
        <div class="card-header execution-header">
          <span>🧾 任务执行明细（仅启用后新增数据）</span>
          <span class="header-tip">当前范围：{{ executionScopeLabel }}</span>
        </div>
      </template>

      <el-table :data="executionDetails" stripe v-loading="executionLoading">
        <el-table-column prop="task_id" label="任务 ID" min-width="180" />
        <el-table-column prop="minister_name" label="大臣" width="110" />
        <el-table-column prop="minister_department" label="部门" width="110" />
        <el-table-column prop="input_tokens" label="输入 Token" width="110" />
        <el-table-column prop="output_tokens" label="输出 Token" width="110" />
        <el-table-column prop="total_tokens" label="总 Token" width="110" />
        <el-table-column prop="duration_seconds" label="耗时" width="130">
          <template #default="{ row }">{{ formatDuration(row.duration_seconds) }}</template>
        </el-table-column>
        <el-table-column prop="completed_at" label="完成时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.completed_at) }}</template>
        </el-table-column>
        <el-table-column prop="session_key" label="会话 Key" min-width="180" show-overflow-tooltip />
        <el-table-column prop="source" label="来源" min-width="140" />
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          background
          layout="total, sizes, prev, pager, next"
          :current-page="executionPagination.page"
          :page-size="executionPagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="executionPagination.total"
          @size-change="handleExecutionPageSizeChange"
          @current-change="handleExecutionPageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

import api from '@/api'

echarts.use([LineChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer])

const trendChart = ref(null)
const ministers = ref([])

const periodDays = ref(7)
const selectedMinisterId = ref(null)
const linkedDate = ref('')

const taskStatsData = ref({
  total: {
    total: 0,
    completed: 0,
    processing: 0,
    pending: 0,
    completion_rate: 0,
  },
  by_minister: [],
})
const trendRows = ref([])

const executionLoading = ref(false)
const executionDetails = ref([])
const executionSummary = ref({
  total_records: 0,
  total_tokens: 0,
  avg_tokens_per_task: 0,
  avg_duration_seconds: 0,
  total_duration_seconds: 0,
})
const executionPagination = ref({
  page: 1,
  page_size: 20,
  total: 0,
})

let trendChartInstance = null

const selectedMinister = computed(() => {
  if (!selectedMinisterId.value) return null
  return ministers.value.find((item) => item.id === selectedMinisterId.value) || null
})

const periodLabel = computed(() => `近 ${periodDays.value} 天`)

const executionScopeLabel = computed(() => {
  const ministerText = selectedMinister.value ? `，${selectedMinister.value.name}` : ''
  if (linkedDate.value) {
    return `${linkedDate.value}（图表联动）${ministerText}`
  }
  return `${periodLabel.value}${ministerText}`
})

const taskSummary = computed(() => {
  if (!selectedMinisterId.value) {
    return taskStatsData.value.total || {
      total: 0,
      completed: 0,
      processing: 0,
      pending: 0,
      completion_rate: 0,
    }
  }

  const row = (taskStatsData.value.by_minister || []).find((item) => item.id === selectedMinisterId.value)
  return row || {
    total: 0,
    completed: 0,
    processing: 0,
    pending: 0,
    completion_rate: 0,
  }
})

const taskStatsView = computed(() => {
  const rows = taskStatsData.value.by_minister || []
  if (selectedMinisterId.value) {
    return rows.filter((row) => row.id === selectedMinisterId.value)
  }
  return rows
})

const metricCards = computed(() => [
  {
    key: 'completed',
    label: '完成任务数',
    value: formatNumber(taskSummary.value.completed),
    desc: `口径：${executionScopeLabel.value}`,
  },
  {
    key: 'completion_rate',
    label: '任务完成率',
    value: `${Number(taskSummary.value.completion_rate || 0).toFixed(2)}%`,
    desc: '来源：/api/stats/tasks',
  },
  {
    key: 'avg_tokens',
    label: '平均单任务 Token',
    value: formatNumber(executionSummary.value.avg_tokens_per_task),
    desc: '来源：/api/stats/task-executions',
  },
  {
    key: 'avg_duration',
    label: '平均耗时',
    value: formatDuration(executionSummary.value.avg_duration_seconds),
    desc: '来源：/api/stats/task-executions',
  },
  {
    key: 'total_tokens',
    label: '总 Token',
    value: formatNumber(executionSummary.value.total_tokens),
    desc: '来源：/api/stats/task-executions',
  },
  {
    key: 'total_duration',
    label: '总耗时',
    value: formatDuration(executionSummary.value.total_duration_seconds),
    desc: '来源：/api/stats/task-executions',
  },
])

const formatDateTime = (value) => {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN')
}

const formatNumber = (value) => {
  const num = Number(value || 0)
  if (Number.isNaN(num)) return '0'

  if (Number.isInteger(num)) {
    return num.toLocaleString('zh-CN')
  }

  return num.toLocaleString('zh-CN', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })
}

const formatDuration = (seconds) => {
  if (seconds === null || seconds === undefined) return '-'
  const sec = Number(seconds)
  if (Number.isNaN(sec)) return '-'

  if (sec < 60) return `${sec.toFixed(0)} 秒`
  if (sec < 3600) return `${(sec / 60).toFixed(1)} 分钟`
  return `${(sec / 3600).toFixed(2)} 小时`
}

const getWindowRange = () => {
  if (linkedDate.value) {
    const start = new Date(`${linkedDate.value}T00:00:00`)
    const end = new Date(`${linkedDate.value}T23:59:59.999`)
    return { start, end }
  }

  const end = new Date()
  end.setHours(23, 59, 59, 999)

  const start = new Date(end)
  start.setDate(end.getDate() - (periodDays.value - 1))
  start.setHours(0, 0, 0, 0)

  return { start, end }
}

const buildTrendParams = () => {
  const params = { days: periodDays.value }
  if (selectedMinisterId.value) {
    params.minister_id = selectedMinisterId.value
  }
  return params
}

const buildExecutionParams = (page = executionPagination.value.page) => {
  const params = {
    page,
    page_size: executionPagination.value.page_size,
  }

  if (selectedMinisterId.value) {
    params.minister_id = selectedMinisterId.value
  }

  const { start, end } = getWindowRange()
  params.start_time = start.toISOString()
  params.end_time = end.toISOString()

  return params
}

const renderTrendChart = () => {
  if (!trendChart.value) return

  if (!trendChartInstance) {
    trendChartInstance = echarts.init(trendChart.value)
  }

  const dates = trendRows.value.map((item) => item.date)

  trendChartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (items = []) => {
        if (!items.length) return ''
        const tokenPoint = items.find((item) => item.seriesName === 'Token 总量')
        const durationPoint = items.find((item) => item.seriesName === '平均耗时（小时）')
        const source = tokenPoint?.data?.raw || durationPoint?.data?.raw

        const taskCount = source ? source.task_count : 0
        const totalDurationSeconds = source ? source.total_duration_seconds : 0

        return [
          `<div>${items[0].axisValue}</div>`,
          `<div>${tokenPoint?.marker || ''} Token 总量：${formatNumber(tokenPoint?.value || 0)}</div>`,
          `<div>${durationPoint?.marker || ''} 平均耗时：${Number(durationPoint?.value || 0).toFixed(2)} 小时</div>`,
          `<div>任务数：${formatNumber(taskCount)}</div>`,
          `<div>总耗时：${formatDuration(totalDurationSeconds)}</div>`,
        ].join('')
      },
    },
    legend: { data: ['Token 总量', '平均耗时（小时）'] },
    grid: { left: '3%', right: '4%', bottom: '10%', containLabel: true },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        formatter: (value) => value.slice(5),
      },
    },
    yAxis: [
      {
        type: 'value',
        name: 'Token',
      },
      {
        type: 'value',
        name: '小时',
      },
    ],
    series: [
      {
        name: 'Token 总量',
        type: 'line',
        smooth: true,
        yAxisIndex: 0,
        itemStyle: { color: '#409EFF' },
        lineStyle: { width: 3 },
        data: trendRows.value.map((item) => ({
          value: item.total_tokens,
          raw: item,
        })),
        markLine: {
          symbol: 'none',
          label: { show: false },
          lineStyle: { color: '#E6A23C', type: 'dashed' },
          data: linkedDate.value ? [{ xAxis: linkedDate.value }] : [],
        },
      },
      {
        name: '平均耗时（小时）',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        itemStyle: { color: '#67C23A' },
        lineStyle: { width: 3 },
        data: trendRows.value.map((item) => ({
          value: Number((Number(item.avg_duration_seconds || 0) / 3600).toFixed(2)),
          raw: item,
        })),
      },
    ],
  })

  trendChartInstance.off('click')
  trendChartInstance.on('click', async (params) => {
    if (!params?.name) return
    linkedDate.value = params.name
    executionPagination.value.page = 1
    renderTrendChart()
    await loadExecutionDetails(1, { silent: true })
  })
}

const loadTaskStats = async ({ silent = false } = {}) => {
  try {
    const data = await api.get('/stats/tasks', {
      params: {
        days: periodDays.value,
      },
    })

    taskStatsData.value = {
      total: data.total || {
        total: 0,
        completed: 0,
        processing: 0,
        pending: 0,
        completion_rate: 0,
      },
      by_minister: data.by_minister || [],
    }
  } catch (error) {
    if (!silent) {
      ElMessage.error(error?.response?.data?.detail || '加载任务状态统计失败')
    }
    console.error(error)
  }
}

const loadTrend = async ({ silent = false } = {}) => {
  try {
    const data = await api.get('/stats/task-executions/trend', {
      params: buildTrendParams(),
    })

    trendRows.value = data.trend || []
    renderTrendChart()
  } catch (error) {
    if (!silent) {
      ElMessage.error(error?.response?.data?.detail || '加载趋势图失败')
    }
    console.error(error)
  }
}

const loadExecutionDetails = async (page = 1, { silent = false } = {}) => {
  executionLoading.value = true
  try {
    const data = await api.get('/stats/task-executions', {
      params: buildExecutionParams(page),
    })

    executionDetails.value = data.items || []
    executionSummary.value = {
      total_records: data.summary?.total_records || 0,
      total_tokens: data.summary?.total_tokens || 0,
      avg_tokens_per_task: data.summary?.avg_tokens_per_task || 0,
      avg_duration_seconds: data.summary?.avg_duration_seconds || 0,
      total_duration_seconds: data.summary?.total_duration_seconds || 0,
    }

    executionPagination.value = {
      page: data.pagination?.page || page,
      page_size: data.pagination?.page_size || executionPagination.value.page_size,
      total: data.pagination?.total || 0,
    }
  } catch (error) {
    if (!silent) {
      ElMessage.error(error?.response?.data?.detail || '加载任务执行明细失败')
    }
    console.error(error)
  } finally {
    executionLoading.value = false
  }
}

const loadAll = async ({ silent = false } = {}) => {
  await Promise.all([
    loadTaskStats({ silent }),
    loadTrend({ silent }),
    loadExecutionDetails(executionPagination.value.page, { silent }),
  ])
}

const refreshAll = async () => {
  await loadAll({ silent: false })
}

const clearLinkedDate = async () => {
  linkedDate.value = ''
  executionPagination.value.page = 1
  renderTrendChart()
  await loadExecutionDetails(1, { silent: true })
}

const handleExecutionPageChange = async (page) => {
  executionPagination.value.page = page
  await loadExecutionDetails(page)
}

const handleExecutionPageSizeChange = async (size) => {
  executionPagination.value.page_size = size
  executionPagination.value.page = 1
  await loadExecutionDetails(1)
}

const handleResize = () => {
  trendChartInstance?.resize()
}

watch([periodDays, selectedMinisterId], async () => {
  linkedDate.value = ''
  executionPagination.value.page = 1
  await loadAll({ silent: true })
})

onMounted(async () => {
  try {
    ministers.value = await api.get('/ministers/')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '加载大臣列表失败')
    console.error(error)
  }

  await loadAll({ silent: false })
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  trendChartInstance?.dispose()
  trendChartInstance = null
})
</script>

<style scoped>
.stats h1 {
  margin-bottom: 20px;
  color: #303133;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.filters-header {
  flex-wrap: wrap;
}

.filters-left,
.filters-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.filter-label {
  font-size: 13px;
  color: #606266;
}

.header-tip {
  color: #909399;
  font-size: 12px;
}

.overview-row {
  margin-bottom: 16px;
}

.overview-card {
  margin-bottom: 12px;
  min-height: 114px;
}

.summary-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.summary-value {
  font-size: 22px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}

.summary-desc {
  margin-top: 8px;
  font-size: 12px;
  color: #a8abb2;
}

.execution-header {
  flex-wrap: wrap;
}

.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
