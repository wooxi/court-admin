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

const loadAll = async () => {
  try {
    const [tokenData, taskData, efficiencyData] = await Promise.all([
      api.get('/stats/token', { params: { days: 7 } }),
      api.get('/stats/tasks', { params: { days: 30 } }),
      api.get('/stats/efficiency', { params: { days: 30 } }),
    ])

    taskStats.value = taskData.by_minister || []
    renderTokenChart(tokenData)
    renderEfficiencyChart(efficiencyData)
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
}
</style>
