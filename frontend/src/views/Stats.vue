<template>
  <div class="stats">
    <h1>📈 统计报表</h1>

    <!-- Token 用量统计 -->
    <el-card style="margin-bottom: 20px;">
      <template #header>
        <div class="card-header">
          <span>📊 Token 用量统计（近 7 天）</span>
          <el-button size="small" @click="exportStats">导出 CSV</el-button>
        </div>
      </template>
      
      <div ref="tokenChart" style="height: 400px;"></div>
    </el-card>

    <!-- 任务处理统计 -->
    <el-card style="margin-bottom: 20px;">
      <template #header>
        <span>📋 任务处理统计（近 30 天）</span>
      </template>
      
      <el-table :data="taskStats" stripe>
        <el-table-column prop="name" label="大臣" width="100" />
        <el-table-column prop="department" label="部门" width="100" />
        <el-table-column prop="total" label="总数" width="80" />
        <el-table-column prop="completed" label="完成" width="80" />
        <el-table-column prop="processing" label="进行中" width="80" />
        <el-table-column prop="pending" label="待处理" width="80" />
        <el-table-column prop="completion_rate" label="完成率" width="100">
          <template #default="{ row }">
            <el-progress :percentage="row.completion_rate" :stroke-width="10" />
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 效率排行 -->
    <el-card>
      <template #header>
        <span>⏱️ 平均处理时长排行</span>
      </template>
      
      <div ref="efficiencyChart" style="height: 300px;"></div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'
import api from '@/api'

const tokenChart = ref(null)
const efficiencyChart = ref(null)
const taskStats = ref([])

const loadTokenStats = async () => {
  try {
    const data = await api.get('/stats/token?days=7')
    
    // 渲染柱状图
    const chart = echarts.init(tokenChart.value)
    chart.setOption({
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' }
      },
      legend: {
        data: ['输入 Token', '输出 Token']
      },
      xAxis: {
        type: 'category',
        data: data.by_minister.map(m => m.name)
      },
      yAxis: {
        type: 'value',
        name: 'Token 数'
      },
      series: [
        {
          name: '输入 Token',
          type: 'bar',
          data: data.by_minister.map(m => m.input_tokens),
          itemStyle: { color: '#409EFF' }
        },
        {
          name: '输出 Token',
          type: 'bar',
          data: data.by_minister.map(m => m.output_tokens),
          itemStyle: { color: '#67C23A' }
        }
      ]
    })
  } catch (error) {
    console.error('加载 Token 统计失败:', error)
  }
}

const loadTaskStats = async () => {
  try {
    const data = await api.get('/stats/tasks?days=30')
    taskStats.value = data.by_minister
  } catch (error) {
    console.error('加载任务统计失败:', error)
  }
}

const loadEfficiencyStats = async () => {
  try {
    const data = await api.get('/stats/efficiency?days=30')
    
    // 渲染条形图
    const chart = echarts.init(efficiencyChart.value)
    chart.setOption({
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'value',
        name: '小时'
      },
      yAxis: {
        type: 'category',
        data: data.efficiency_ranking.map(m => m.minister_name).reverse()
      },
      series: [
        {
          name: '平均处理时长',
          type: 'bar',
          data: data.efficiency_ranking.map(m => m.avg_hours).reverse(),
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: '#83bff6' },
              { offset: 0.5, color: '#188df0' },
              { offset: 1, color: '#188df0' }
            ])
          }
        }
      ]
    })
  } catch (error) {
    console.error('加载效率统计失败:', error)
  }
}

const exportStats = () => {
  console.log('导出报表')
  // TODO: 实现导出功能
}

onMounted(() => {
  loadTokenStats()
  loadTaskStats()
  loadEfficiencyStats()
  
  // 响应式图表
  window.addEventListener('resize', () => {
    tokenChart.value && echarts.getInstanceByDom(tokenChart.value)?.resize()
    efficiencyChart.value && echarts.getInstanceByDom(efficiencyChart.value)?.resize()
  })
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
