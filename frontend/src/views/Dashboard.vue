<template>
  <div class="dashboard-page">
    <div class="page-header">
      <div>
        <h1>📊 朝廷总览</h1>
        <p class="subtitle">一屏看清任务态势、执行效率与待办压力</p>
      </div>
      <el-button type="primary" @click="loadDashboard">
        <el-icon><Refresh /></el-icon>
        刷新数据
      </el-button>
    </div>

    <div class="kpi-grid">
      <el-card class="kpi-card" shadow="hover">
        <div class="kpi-top">
          <span>在编大臣</span>
          <el-icon class="kpi-icon"><User /></el-icon>
        </div>
        <div class="kpi-value">{{ kpi.ministers }}</div>
      </el-card>

      <el-card class="kpi-card" shadow="hover">
        <div class="kpi-top">
          <span>进行中任务</span>
          <el-icon class="kpi-icon"><Connection /></el-icon>
        </div>
        <div class="kpi-value warn">{{ kpi.processing }}</div>
      </el-card>

      <el-card class="kpi-card" shadow="hover">
        <div class="kpi-top">
          <span>已完成任务（30天）</span>
          <el-icon class="kpi-icon"><CircleCheck /></el-icon>
        </div>
        <div class="kpi-value ok">{{ kpi.completed }}</div>
      </el-card>

      <el-card class="kpi-card" shadow="hover">
        <div class="kpi-top">
          <span>完成率（30天）</span>
          <el-icon class="kpi-icon"><TrendCharts /></el-icon>
        </div>
        <div class="kpi-value">{{ kpi.completionRate }}%</div>
      </el-card>
    </div>

    <div class="main-grid">
      <el-card class="panel" shadow="never">
        <template #header>
          <div class="panel-header">
            <span>🔥 当前待办（未完成）</span>
            <el-button text @click="goTo('/tasks')">进入任务页</el-button>
          </div>
        </template>

        <el-empty v-if="openTasks.length === 0" description="当前无未完成任务" />

        <div v-else class="open-task-list">
          <div v-for="task in openTasks" :key="task.id" class="open-task-item">
            <div class="open-task-title">{{ task.title }}</div>
            <div class="open-task-meta">
              <el-tag :type="getStatusType(task.status)" size="small">{{ getStatusText(task.status) }}</el-tag>
              <span>{{ task.task_id }}</span>
              <span>{{ getAssignee(task.assignee_id) }}</span>
              <span>{{ formatDate(task.created_at) }}</span>
            </div>
          </div>
        </div>
      </el-card>

      <el-card class="panel" shadow="never">
        <template #header>
          <div class="panel-header">
            <span>🏛️ 各部执行概览（30天）</span>
            <el-button text @click="goTo('/stats')">查看报表</el-button>
          </div>
        </template>

        <el-table :data="deptStats" size="small" stripe>
          <el-table-column prop="name" label="大臣" min-width="100" />
          <el-table-column prop="total" label="总任务" width="90" />
          <el-table-column prop="processing" label="进行中" width="90" />
          <el-table-column prop="pending" label="待处理" width="90" />
          <el-table-column prop="completion_rate" label="完成率" min-width="130">
            <template #default="{ row }">{{ row.completion_rate }}%</template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <el-card class="panel" shadow="never">
      <template #header>
        <div class="panel-header">
          <span>🕒 最近任务（最新 8 条）</span>
          <div class="quick-actions">
            <el-button size="small" @click="goTo('/tasks')"><el-icon><Document /></el-icon>任务管理</el-button>
            <el-button size="small" @click="goTo('/flows')"><el-icon><Timer /></el-icon>流转追踪</el-button>
            <el-button size="small" @click="goTo('/config')"><el-icon><Setting /></el-icon>系统配置</el-button>
          </div>
        </div>
      </template>

      <el-table :data="recentTasks" stripe>
        <el-table-column prop="task_id" label="任务 ID" width="190" />
        <el-table-column prop="title" label="标题" min-width="240" />
        <el-table-column prop="assignee_name" label="承办" width="120" />
        <el-table-column prop="status" label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import api from '@/api'

const router = useRouter()

const ministers = ref([])
const tasks = ref([])
const taskStats = ref([])

const kpi = ref({
  ministers: 0,
  processing: 0,
  completed: 0,
  completionRate: 0,
})

const ministerMap = computed(() => {
  const map = {}
  ministers.value.forEach((m) => {
    map[m.id] = m.name
  })
  return map
})

const openTasks = computed(() => tasks.value.filter((t) => t.status !== 'completed'))

const recentTasks = computed(() =>
  tasks.value.slice(0, 8).map((task) => ({
    ...task,
    assignee_name: ministerMap.value[task.assignee_id] || `#${task.assignee_id}`,
  }))
)

const deptStats = computed(() => taskStats.value.slice(0, 10))

const getAssignee = (id) => ministerMap.value[id] || `#${id}`
const getStatusType = (status) => ({ pending: 'info', processing: 'warning', completed: 'success' }[status] || 'info')
const getStatusText = (status) => ({ pending: '待处理', processing: '进行中', completed: '已完成' }[status] || status)
const formatDate = (value) => (value ? new Date(value).toLocaleString('zh-CN') : '-')
const goTo = (path) => router.push(path)

const loadDashboard = async () => {
  const [ministerData, taskData, taskStatsData] = await Promise.all([
    api.get('/ministers/'),
    api.get('/tasks/', { params: { limit: 200 } }),
    api.get('/stats/tasks', { params: { days: 30 } }),
  ])

  ministers.value = ministerData
  tasks.value = taskData
  taskStats.value = taskStatsData.by_minister || []

  kpi.value = {
    ministers: ministerData.length,
    processing: taskData.filter((t) => t.status === 'processing').length,
    completed: taskStatsData.total?.completed || 0,
    completionRate: taskStatsData.total?.completion_rate || 0,
  }
}

onMounted(() => {
  loadDashboard().catch((e) => {
    console.error('加载总览失败', e)
  })
})
</script>

<style scoped>
.dashboard-page {
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
  font-size: 22px;
  margin: 0;
}

.subtitle {
  margin-top: 4px;
  color: var(--muted);
  font-size: 13px;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.kpi-card {
  border-color: var(--line);
  background: var(--panel);
}

.kpi-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: var(--muted);
  font-size: 12px;
}

.kpi-icon {
  color: var(--acc);
}

.kpi-value {
  margin-top: 8px;
  font-size: 28px;
  font-weight: 800;
  color: var(--text);
}

.kpi-value.ok {
  color: var(--ok);
}

.kpi-value.warn {
  color: var(--warn);
}

.main-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.panel {
  border-color: var(--line);
  background: var(--panel);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.open-task-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.open-task-item {
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 10px;
  background: var(--panel2);
}

.open-task-title {
  font-weight: 700;
  margin-bottom: 8px;
}

.open-task-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 12px;
  color: var(--muted);
}

.quick-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

@media (max-width: 980px) {
  .main-grid {
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
