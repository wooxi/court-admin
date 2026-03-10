<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-header">
          <div class="stat-label">大臣数量</div>
          <div class="stat-icon primary">
            <el-icon :size="24"><User /></el-icon>
          </div>
        </div>
        <div class="stat-value">{{ stats.ministers }}</div>
        <div class="stat-trend up">
          <el-icon><Top /></el-icon>
          <span>较上周 +2</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-header">
          <div class="stat-label">任务总数</div>
          <div class="stat-icon success">
            <el-icon :size="24"><Document /></el-icon>
          </div>
        </div>
        <div class="stat-value">{{ stats.tasks }}</div>
        <div class="stat-trend up">
          <el-icon><Top /></el-icon>
          <span>较上周 +15</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-header">
          <div class="stat-label">Token 用量</div>
          <div class="stat-icon warning">
            <el-icon :size="24"><TrendCharts /></el-icon>
          </div>
        </div>
        <div class="stat-value">{{ stats.tokens }}</div>
        <div class="stat-trend down">
          <el-icon><Bottom /></el-icon>
          <span>较上周 -5%</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-header">
          <div class="stat-label">完成率</div>
          <div class="stat-icon danger">
            <el-icon :size="24"><CircleCheck /></el-icon>
          </div>
        </div>
        <div class="stat-value">{{ stats.completionRate }}%</div>
        <div class="stat-trend up">
          <el-icon><Top /></el-icon>
          <span>较上周 +3.2%</span>
        </div>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="content-panel">
      <div class="panel-header">
        <div class="panel-title">⚡ 快捷操作</div>
      </div>
      <div style="display: flex; gap: 12px; flex-wrap: wrap;">
        <el-button type="primary" @click="$router.push('/tasks')">
          <el-icon><Plus /></el-icon>
          创建任务
        </el-button>
        <el-button type="success" @click="$router.push('/ministers')">
          <el-icon><User /></el-icon>
          大臣配置
        </el-button>
        <el-button type="warning" @click="$router.push('/stats')">
          <el-icon><TrendCharts /></el-icon>
          查看报表
        </el-button>
        <el-button type="info" @click="$router.push('/config')">
          <el-icon><Setting /></el-icon>
          系统配置
        </el-button>
      </div>
    </div>

    <!-- 最近任务 -->
    <div class="content-panel">
      <div class="panel-header">
        <div class="panel-title">📋 最近任务</div>
        <el-button type="primary" link @click="$router.push('/tasks')">
          查看全部 <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>
      <el-table :data="recentTasks" stripe style="width: 100%">
        <el-table-column prop="task_id" label="任务 ID" width="160" />
        <el-table-column prop="title" label="任务标题" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="assignee" label="承办大臣" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewTask(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  User, Document, TrendCharts, CircleCheck, Top, Bottom,
  Plus, ArrowRight, Setting
} from '@element-plus/icons-vue'

const router = useRouter()

const stats = ref({
  ministers: 7,
  tasks: 238,
  tokens: '446k',
  completionRate: 86.1
})

const recentTasks = ref([
  {
    task_id: 'TASK-20260310-001',
    title: '全面审查三省六部项目健康度',
    status: 'completed',
    assignee: '兵部',
    created_at: '2026-03-10 05:20'
  },
  {
    task_id: 'TASK-20260310-002',
    title: '调研工业数据大模型应用',
    status: 'processing',
    assignee: '户部',
    created_at: '2026-03-10 05:25'
  },
  {
    task_id: 'TASK-20260310-003',
    title: '撰写 OpenClaw 技术博客',
    status: 'pending',
    assignee: '礼部',
    created_at: '2026-03-10 05:30'
  }
])

const getStatusType = (status) => {
  const map = {
    pending: 'info',
    processing: 'warning',
    completed: 'success'
  }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = {
    pending: '待处理',
    processing: '进行中',
    completed: '已完成'
  }
  return map[status] || status
}

const viewTask = (task) => {
  router.push(`/tasks?id=${task.task_id}`)
}
</script>

<style scoped>
.dashboard {
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
</style>
