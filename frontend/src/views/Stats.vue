<template>
  <div class="stats-page">
    <div class="page-header">
      <div>
        <h1>📈 统计报表</h1>
        <p class="subtitle">统一口径：token / 耗时来自 task_execution_details，状态来自 tasks</p>
      </div>
      <el-button :loading="loading" @click="loadAll(false)">刷新报表</el-button>
    </div>

    <el-card class="filter-card" shadow="never">
      <div class="filter-wrap">
        <div class="filter-item">
          <span class="label">统计窗口</span>
          <el-radio-group v-model="periodDays" size="small">
            <el-radio-button :value="7">近 7 天</el-radio-button>
            <el-radio-button :value="30">近 30 天</el-radio-button>
            <el-radio-button :value="90">近 90 天</el-radio-button>
          </el-radio-group>
        </div>

        <div class="filter-item">
          <span class="label">部门筛选</span>
          <el-select v-model="selectedDepartment" placeholder="六部全量" clearable style="width: 180px">
            <el-option
              v-for="dept in departmentOptions"
              :key="dept"
              :label="dept"
              :value="dept"
            />
          </el-select>
        </div>
      </div>
    </el-card>

    <el-row :gutter="12" class="kpi-row">
      <el-col v-for="item in kpiCards" :key="item.key" :xs="12" :sm="12" :md="8" :lg="6" :xl="4">
        <el-card class="kpi-card" shadow="hover">
          <div class="kpi-label">{{ item.label }}</div>
          <div class="kpi-value">{{ item.value }}</div>
          <div class="kpi-desc">{{ item.desc }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="chart-card">
      <template #header>
        <div class="card-header">
          <span>📉 每日 Token 总消耗 vs 平均耗时</span>
          <span class="tip">{{ scopeLabel }}</span>
        </div>
      </template>
      <div ref="trendChartRef" class="chart-box"></div>
    </el-card>

    <el-row :gutter="12" class="chart-row">
      <el-col :xs="24" :lg="8">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>🥧 六部任务量占比</span>
              <span class="tip">按执行明细任务量</span>
            </div>
          </template>
          <div ref="deptPieRef" class="chart-box small"></div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="16">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>📊 各部门任务状态分布（堆叠）</span>
              <span class="tip">待处理 / 进行中 / 已完成</span>
            </div>
          </template>
          <div ref="statusStackRef" class="chart-box small"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="detail-card">
      <template #header>
        <div class="card-header">
          <span>🧾 部门状态明细</span>
          <span class="tip">{{ scopeLabel }}</span>
        </div>
      </template>
      <el-table :data="deptStatusRows" stripe>
        <el-table-column prop="department" label="部门" min-width="140" />
        <el-table-column prop="pending" label="待处理" width="100" />
        <el-table-column prop="processing" label="进行中" width="100" />
        <el-table-column prop="completed" label="已完成" width="100" />
        <el-table-column prop="total" label="总计" width="100" />
        <el-table-column label="完成率" min-width="180">
          <template #default="{ row }">
            <el-progress :percentage="row.rate" :stroke-width="10" />
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts/core'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

import { fetchExecutionReport, fetchTaskStatusStats } from '@/api/stats'
import { fetchMinisters } from '@/api/tasks'

echarts.use([LineChart, PieChart, BarChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer])

const loading = ref(false)
const periodDays = ref(30)
const selectedDepartment = ref('')
const ministers = ref([])

const reportData = ref(emptyReport())
const deptStatusRows = ref([])

const trendChartRef = ref(null)
const deptPieRef = ref(null)
const statusStackRef = ref(null)

let trendChart = null
let deptPieChart = null
let statusStackChart = null

function emptyReport() {
  return {
    period: { days: 0 },
    kpi: {
      total_tasks: 0,
      completed_tasks: 0,
      completion_rate: 0,
      execution_records: 0,
      total_tokens: 0,
      avg_tokens_per_task: 0,
      total_duration_seconds: 0,
      avg_duration_seconds: 0,
    },
    daily_trend: [],
    dept_distribution: [],
    status_distribution: [],
  }
}

const departmentOptions = computed(() => {
  const set = new Set(ministers.value.map((item) => item.department).filter(Boolean))
  return [...set]
})

const selectedAssigneeIds = computed(() => {
  if (!selectedDepartment.value) return []
  return ministers.value
    .filter((item) => item.department === selectedDepartment.value)
    .map((item) => item.id)
})

const scopeLabel = computed(() => {
  const deptText = selectedDepartment.value ? ` · ${selectedDepartment.value}` : ' · 六部全量'
  return `近 ${periodDays.value} 天${deptText}`
})

const kpiCards = computed(() => {
  const kpi = reportData.value.kpi || {}
  return [
    {
      key: 'total_tasks',
      label: '任务总量',
      value: formatNumber(kpi.total_tasks),
      desc: scopeLabel.value,
    },
    {
      key: 'completed_tasks',
      label: '已完成',
      value: formatNumber(kpi.completed_tasks),
      desc: `完成率 ${Number(kpi.completion_rate || 0).toFixed(2)}%`,
    },
    {
      key: 'execution_records',
      label: '执行记录',
      value: formatNumber(kpi.execution_records),
      desc: '来源：聚合报表 API',
    },
    {
      key: 'total_tokens',
      label: '总 Token',
      value: formatNumber(kpi.total_tokens),
      desc: '口径：task_execution_details',
    },
    {
      key: 'avg_tokens_per_task',
      label: '平均单任务 Token',
      value: formatNumber(kpi.avg_tokens_per_task),
      desc: '聚合字段',
    },
    {
      key: 'avg_duration_seconds',
      label: '平均耗时',
      value: formatDuration(kpi.avg_duration_seconds),
      desc: `总耗时 ${formatDuration(kpi.total_duration_seconds)}`,
    },
  ]
})

const formatNumber = (value) => {
  const num = Number(value || 0)
  if (!Number.isFinite(num)) return '0'
  if (Number.isInteger(num)) return num.toLocaleString('zh-CN')
  return num.toLocaleString('zh-CN', { maximumFractionDigits: 2 })
}

const formatDuration = (seconds) => {
  const sec = Number(seconds || 0)
  if (!Number.isFinite(sec) || sec <= 0) return '0 秒'
  if (sec < 60) return `${sec.toFixed(0)} 秒`
  if (sec < 3600) return `${(sec / 60).toFixed(1)} 分钟`
  return `${(sec / 3600).toFixed(2)} 小时`
}

const normalizeStatus = (status) => {
  if (!status) return 'pending'
  const value = String(status).toLowerCase()
  if (value.includes('completed') || value.includes('success') || value.includes('done')) return 'completed'
  if (value.includes('processing') || value.includes('running')) return 'processing'
  return 'pending'
}

const mergeReports = (payloads = []) => {
  if (!payloads.length) return emptyReport()

  const merged = emptyReport()
  const dayMap = new Map()
  const deptMap = new Map()
  const statusMap = new Map()

  for (const report of payloads) {
    const kpi = report.kpi || {}
    merged.kpi.total_tasks += Number(kpi.total_tasks || 0)
    merged.kpi.completed_tasks += Number(kpi.completed_tasks || 0)
    merged.kpi.execution_records += Number(kpi.execution_records || 0)
    merged.kpi.total_tokens += Number(kpi.total_tokens || 0)
    merged.kpi.total_duration_seconds += Number(kpi.total_duration_seconds || 0)

    for (const row of report.daily_trend || []) {
      const key = row.date
      if (!dayMap.has(key)) {
        dayMap.set(key, {
          date: key,
          task_count: 0,
          total_tokens: 0,
          total_duration_seconds: 0,
        })
      }
      const target = dayMap.get(key)
      target.task_count += Number(row.task_count || 0)
      target.total_tokens += Number(row.total_tokens || 0)
      target.total_duration_seconds += Number(row.total_duration_seconds || 0)
    }

    for (const row of report.dept_distribution || []) {
      const key = row.department || '未分组'
      if (!deptMap.has(key)) {
        deptMap.set(key, {
          department: key,
          task_count: 0,
          total_tokens: 0,
          total_duration_seconds: 0,
        })
      }
      const target = deptMap.get(key)
      target.task_count += Number(row.task_count || 0)
      target.total_tokens += Number(row.total_tokens || 0)
      target.total_duration_seconds += Number(row.total_duration_seconds || 0)
    }

    for (const row of report.status_distribution || []) {
      const key = normalizeStatus(row.status)
      statusMap.set(key, (statusMap.get(key) || 0) + Number(row.count || 0))
    }
  }

  merged.kpi.completion_rate =
    merged.kpi.total_tasks > 0 ? Number(((merged.kpi.completed_tasks / merged.kpi.total_tasks) * 100).toFixed(2)) : 0
  merged.kpi.avg_tokens_per_task =
    merged.kpi.execution_records > 0
      ? Number((merged.kpi.total_tokens / merged.kpi.execution_records).toFixed(2))
      : 0
  merged.kpi.avg_duration_seconds =
    merged.kpi.execution_records > 0
      ? Number((merged.kpi.total_duration_seconds / merged.kpi.execution_records).toFixed(2))
      : 0

  merged.daily_trend = [...dayMap.values()]
    .sort((a, b) => String(a.date).localeCompare(String(b.date)))
    .map((row) => ({
      ...row,
      avg_duration_seconds: row.task_count > 0 ? Number((row.total_duration_seconds / row.task_count).toFixed(2)) : 0,
      avg_tokens_per_task: row.task_count > 0 ? Number((row.total_tokens / row.task_count).toFixed(2)) : 0,
    }))

  merged.dept_distribution = [...deptMap.values()].sort((a, b) => b.task_count - a.task_count)
  merged.status_distribution = ['pending', 'processing', 'completed'].map((status) => ({
    status,
    count: statusMap.get(status) || 0,
  }))

  merged.period.days = periodDays.value
  return merged
}

const loadReportData = async () => {
  const assigneeIds = selectedAssigneeIds.value

  if (!selectedDepartment.value || assigneeIds.length === 0) {
    reportData.value = await fetchExecutionReport({ days: periodDays.value })
    return
  }

  if (assigneeIds.length === 1) {
    reportData.value = await fetchExecutionReport({ days: periodDays.value, assignee_id: assigneeIds[0] })
    return
  }

  const reportRows = await Promise.all(
    assigneeIds.map((assigneeId) => fetchExecutionReport({ days: periodDays.value, assignee_id: assigneeId }))
  )
  reportData.value = mergeReports(reportRows)
}

const loadDeptStatus = async () => {
  const payload = await fetchTaskStatusStats({ days: periodDays.value })
  const rows = payload.by_minister || []

  const map = new Map()
  rows.forEach((item) => {
    const department = item.department || '未分组'
    if (!map.has(department)) {
      map.set(department, {
        department,
        pending: 0,
        processing: 0,
        completed: 0,
        total: 0,
        rate: 0,
      })
    }
    const target = map.get(department)
    target.pending += Number(item.pending || 0)
    target.processing += Number(item.processing || 0)
    target.completed += Number(item.completed || 0)
    target.total += Number(item.total || 0)
  })

  const merged = [...map.values()].map((item) => ({
    ...item,
    rate: item.total > 0 ? Number(((item.completed / item.total) * 100).toFixed(2)) : 0,
  }))

  deptStatusRows.value = selectedDepartment.value
    ? merged.filter((item) => item.department === selectedDepartment.value)
    : merged
}

const renderTrendChart = () => {
  if (!trendChartRef.value) return
  if (!trendChart) trendChart = echarts.init(trendChartRef.value)

  const rows = reportData.value.daily_trend || []

  trendChart.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (items = []) => {
        if (!items.length) return ''
        const tokenPoint = items.find((item) => item.seriesName === 'Token 总消耗')
        const durationPoint = items.find((item) => item.seriesName === '平均耗时（分钟）')
        return [
          `<div>${items[0].axisValue}</div>`,
          `<div>${tokenPoint?.marker || ''} Token 总消耗：${formatNumber(tokenPoint?.value || 0)}</div>`,
          `<div>${durationPoint?.marker || ''} 平均耗时：${Number(durationPoint?.value || 0).toFixed(2)} 分钟</div>`,
        ].join('')
      },
    },
    legend: { data: ['Token 总消耗', '平均耗时（分钟）'] },
    grid: { left: '3%', right: '4%', bottom: '8%', containLabel: true },
    xAxis: {
      type: 'category',
      data: rows.map((row) => row.date),
      axisLabel: { formatter: (value) => value.slice(5) },
    },
    yAxis: [
      { type: 'value', name: 'Token' },
      { type: 'value', name: '分钟' },
    ],
    series: [
      {
        name: 'Token 总消耗',
        type: 'line',
        smooth: true,
        yAxisIndex: 0,
        itemStyle: { color: '#6a9eff' },
        lineStyle: { width: 3 },
        data: rows.map((row) => Number(row.total_tokens || 0)),
      },
      {
        name: '平均耗时（分钟）',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        itemStyle: { color: '#2ecc8a' },
        lineStyle: { width: 3 },
        data: rows.map((row) => Number((Number(row.avg_duration_seconds || 0) / 60).toFixed(2))),
      },
    ],
  })
}

const renderDeptPie = () => {
  if (!deptPieRef.value) return
  if (!deptPieChart) deptPieChart = echarts.init(deptPieRef.value)

  const rows = (reportData.value.dept_distribution || []).filter((item) => Number(item.task_count || 0) > 0)
  deptPieChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, type: 'scroll' },
    series: [
      {
        name: '任务量占比',
        type: 'pie',
        radius: ['35%', '68%'],
        center: ['50%', '46%'],
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 1 },
        label: {
          formatter: ({ name, percent }) => `${name}\n${percent}%`,
        },
        data: rows.map((row) => ({
          name: row.department,
          value: Number(row.task_count || 0),
        })),
      },
    ],
  })
}

const renderStatusStack = () => {
  if (!statusStackRef.value) return
  if (!statusStackChart) statusStackChart = echarts.init(statusStackRef.value)

  const rows = deptStatusRows.value || []

  statusStackChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['待处理', '进行中', '已完成'] },
    grid: { left: '3%', right: '4%', bottom: '8%', containLabel: true },
    xAxis: {
      type: 'category',
      data: rows.map((row) => row.department),
    },
    yAxis: { type: 'value', name: '任务数' },
    series: [
      {
        name: '待处理',
        type: 'bar',
        stack: 'status',
        itemStyle: { color: '#909399' },
        data: rows.map((row) => row.pending),
      },
      {
        name: '进行中',
        type: 'bar',
        stack: 'status',
        itemStyle: { color: '#e6a23c' },
        data: rows.map((row) => row.processing),
      },
      {
        name: '已完成',
        type: 'bar',
        stack: 'status',
        itemStyle: { color: '#67c23a' },
        data: rows.map((row) => row.completed),
      },
    ],
  })
}

const renderAllCharts = () => {
  renderTrendChart()
  renderDeptPie()
  renderStatusStack()
}

const loadAll = async (silent = true) => {
  if (!silent) loading.value = true
  try {
    await Promise.all([loadReportData(), loadDeptStatus()])
    renderAllCharts()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '加载报表失败')
    console.error(error)
  } finally {
    if (!silent) loading.value = false
  }
}

const handleResize = () => {
  trendChart?.resize()
  deptPieChart?.resize()
  statusStackChart?.resize()
}

watch([periodDays, selectedDepartment], async () => {
  await loadAll(true)
})

onMounted(async () => {
  try {
    ministers.value = await fetchMinisters()
    await loadAll(false)
    window.addEventListener('resize', handleResize)
  } catch (error) {
    ElMessage.error('加载统计页面失败')
    console.error(error)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  deptPieChart?.dispose()
  statusStackChart?.dispose()
  trendChart = null
  deptPieChart = null
  statusStackChart = null
})
</script>

<style scoped>
.stats-page {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.page-header h1 {
  font-size: 22px;
}

.subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: var(--muted);
}

.filter-wrap {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.label {
  color: var(--muted);
  font-size: 13px;
}

.kpi-row {
  margin-bottom: 4px;
}

.kpi-card {
  margin-bottom: 10px;
  min-height: 108px;
}

.kpi-label {
  color: var(--muted);
  font-size: 12px;
}

.kpi-value {
  margin-top: 8px;
  font-size: 24px;
  font-weight: 700;
}

.kpi-desc {
  margin-top: 8px;
  font-size: 12px;
  color: var(--muted);
}

.chart-row {
  margin-top: -2px;
}

.chart-card {
  border-color: var(--line);
}

.detail-card {
  margin-bottom: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.tip {
  color: var(--muted);
  font-size: 12px;
}

.chart-box {
  height: 340px;
}

.chart-box.small {
  height: 300px;
}

@media (max-width: 768px) {
  .page-header {
    align-items: flex-start;
  }

  .chart-box,
  .chart-box.small {
    height: 280px;
  }
}
</style>
