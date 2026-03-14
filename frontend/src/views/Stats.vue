<template>
  <div class="stats">
    <h1>📈 统计报表</h1>

    <el-card style="margin-bottom: 20px;">
      <template #header>
        <div class="card-header">
          <span>📊 Token 用量统计（近 7 天）</span>
          <el-button size="small" @click="loadAll">刷新</el-button>
        </div>
      </template>
      <div ref="tokenChart" style="height: 380px;"></div>
    </el-card>

    <el-card style="margin-bottom: 20px;">
      <template #header>
        <span>📋 任务处理统计（近 30 天）</span>
      </template>

      <el-table :data="taskStats" stripe>
        <el-table-column prop="name" label="大臣" width="110" />
        <el-table-column prop="department" label="部门" width="110" />
        <el-table-column prop="total" label="总数" width="90" />
        <el-table-column prop="completed" label="完成" width="90" />
        <el-table-column prop="processing" label="进行中" width="90" />
        <el-table-column prop="pending" label="待处理" width="90" />
        <el-table-column prop="completion_rate" label="完成率" min-width="180">
          <template #default="{ row }">
            <el-progress :percentage="row.completion_rate" :stroke-width="10" />
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card style="margin-bottom: 20px;">
      <template #header>
        <div class="card-header execution-header">
          <span>🧾 任务执行明细（仅启用后新增数据）</span>
          <div class="execution-actions">
            <el-select v-model="executionFilters.minister_id" placeholder="全部大臣" clearable style="width: 140px;">
              <el-option v-for="minister in ministers" :key="minister.id" :label="minister.name" :value="minister.id" />
            </el-select>
            <el-date-picker
              v-model="executionFilters.time_range"
              type="datetimerange"
              range-separator="至"
              start-placeholder="开始时间"
              end-placeholder="结束时间"
              style="width: 360px;"
            />
            <el-button type="primary" @click="searchExecutionDetails">查询</el-button>
            <el-button @click="resetExecutionFilters">重置</el-button>
          </div>
        </div>
      </template>

      <div class="execution-summary">
        <div class="summary-item">
          <div class="summary-label">人均单任务 Token</div>
          <div class="summary-value">{{ executionSummary.avg_tokens_per_task }}</div>
        </div>
        <div class="summary-item">
          <div class="summary-label">平均耗时</div>
          <div class="summary-value">{{ formatDuration(executionSummary.avg_duration_seconds) }}</div>
        </div>
        <div class="summary-item">
          <div class="summary-label">总耗时</div>
          <div class="summary-value">{{ formatDuration(executionSummary.total_duration_seconds) }}</div>
        </div>
        <div class="summary-item">
          <div class="summary-label">明细记录数</div>
          <div class="summary-value">{{ executionSummary.total_records }}</div>
        </div>
      </div>

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

    <el-card>
      <template #header>
        <span>⏱️ 平均处理时长排行（小时）</span>
      </template>
      <div ref="efficiencyChart" style="height: 320px;"></div>
    </el-card>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts/core'
import { BarChart } from 'echarts/charts'
import {
  GridComponent,
  LegendComponent,
  TitleComponent,
  TooltipComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

import api from '@/api'

echarts.use([BarChart, GridComponent, LegendComponent, TitleComponent, TooltipComponent, CanvasRenderer])

const tokenChart = ref(null)
const efficiencyChart = ref(null)
const taskStats = ref([])
const ministers = ref([])

const executionLoading = ref(false)
const executionDetails = ref([])
const executionFilters = ref({
  minister_id: null,
  time_range: [],
})
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

let tokenChartInstance = null
let efficiencyChartInstance = null

const renderTokenChart = (data) => {
  if (!tokenChart.value) return
  if (!tokenChartInstance) {
    tokenChartInstance = echarts.init(tokenChart.value)
  }

  tokenChartInstance.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['输入 Token', '输出 Token'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: data.by_minister.map((m) => m.name) },
    yAxis: { type: 'value', name: 'Token 数' },
    series: [
      {
        name: '输入 Token',
        type: 'bar',
        data: data.by_minister.map((m) => m.input_tokens),
        itemStyle: { color: '#409EFF' },
      },
      {
        name: '输出 Token',
        type: 'bar',
        data: data.by_minister.map((m) => m.output_tokens),
        itemStyle: { color: '#67C23A' },
      },
    ],
  })
}

const renderEfficiencyChart = (data) => {
  if (!efficiencyChart.value) return
  if (!efficiencyChartInstance) {
    efficiencyChartInstance = echarts.init(efficiencyChart.value)
  }

  const list = [...data.efficiency_ranking].reverse()

  efficiencyChartInstance.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'value', name: '小时' },
    yAxis: { type: 'category', data: list.map((m) => m.minister_name) },
    series: [
      {
        name: '平均处理时长',
        type: 'bar',
        data: list.map((m) => m.avg_hours),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#83bff6' },
            { offset: 0.5, color: '#188df0' },
            { offset: 1, color: '#188df0' },
          ]),
        },
      },
    ],
  })
}

const formatDateTime = (value) => {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN')
}

const formatDuration = (seconds) => {
  if (seconds === null || seconds === undefined) return '-'
  const sec = Number(seconds)
  if (Number.isNaN(sec)) return '-'

  if (sec < 60) return `${sec.toFixed(0)} 秒`
  if (sec < 3600) return `${(sec / 60).toFixed(1)} 分钟`
  return `${(sec / 3600).toFixed(2)} 小时`
}

const buildExecutionParams = (page = executionPagination.value.page) => {
  const params = {
    page,
    page_size: executionPagination.value.page_size,
  }

  if (executionFilters.value.minister_id) {
    params.minister_id = executionFilters.value.minister_id
  }

  if (executionFilters.value.time_range?.length === 2) {
    params.start_time = new Date(executionFilters.value.time_range[0]).toISOString()
    params.end_time = new Date(executionFilters.value.time_range[1]).toISOString()
  }

  return params
}

const loadExecutionDetails = async (page = 1, { silent = false } = {}) => {
  executionLoading.value = true
  try {
    const params = buildExecutionParams(page)
    const data = await api.get('/stats/task-executions', { params })

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

const searchExecutionDetails = async () => {
  executionPagination.value.page = 1
  await loadExecutionDetails(1)
}

const resetExecutionFilters = async () => {
  executionFilters.value = {
    minister_id: null,
    time_range: [],
  }
  executionPagination.value.page = 1
  executionPagination.value.page_size = 20
  await loadExecutionDetails(1)
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

const loadAll = async () => {
  try {
    const [tokenData, taskData, efficiencyData, ministerData] = await Promise.all([
      api.get('/stats/token', { params: { days: 7 } }),
      api.get('/stats/tasks', { params: { days: 30 } }),
      api.get('/stats/efficiency', { params: { days: 30 } }),
      api.get('/ministers/'),
    ])

    ministers.value = ministerData || []
    taskStats.value = taskData.by_minister || []
    renderTokenChart(tokenData)
    renderEfficiencyChart(efficiencyData)
    await loadExecutionDetails(executionPagination.value.page, { silent: true })
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '加载统计数据失败')
    console.error(error)
  }
}

const handleResize = () => {
  tokenChartInstance?.resize()
  efficiencyChartInstance?.resize()
}

onMounted(() => {
  loadAll()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  tokenChartInstance?.dispose()
  efficiencyChartInstance?.dispose()
  tokenChartInstance = null
  efficiencyChartInstance = null
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
  gap: 8px;
}

.execution-header {
  flex-wrap: wrap;
}

.execution-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.execution-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.summary-item {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px;
  background: #fafafa;
}

.summary-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.summary-value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
