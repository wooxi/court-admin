<template>
  <div class="flows">
    <div class="page-header">
      <h1>🔗 任务流转追踪</h1>
      <el-button @click="$router.push('/tasks')">返回任务列表</el-button>
    </div>

    <!-- 任务信息 -->
    <el-card v-if="task" style="margin-bottom: 20px;">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="任务 ID">{{ task.task_id }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(task.status)">
            {{ getStatusText(task.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="标题" :span="2">{{ task.title }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ task.created_at }}</el-descriptions-item>
        <el-descriptions-item label="完成时间">{{ task.completed_at || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 流转时间线 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>⏱️ 流转时间线</span>
        </div>
      </template>
      
      <el-timeline>
        <el-timeline-item
          v-for="flow in flows"
          :key="flow.id"
          :timestamp="formatTime(flow.timestamp)"
          placement="top"
        >
          <el-card>
            <div class="flow-item">
              <div class="flow-header">
                <el-tag type="primary">{{ flow.from_actor }}</el-tag>
                <el-icon><Right /></el-icon>
                <el-tag type="success">{{ flow.to_actor }}</el-tag>
                <el-tag :type="getActionType(flow.action)" style="margin-left: auto;">
                  {{ flow.action }}
                </el-tag>
              </div>
              <div class="flow-remark" v-if="flow.remark">
                <strong>备注：</strong>{{ flow.remark }}
              </div>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>

      <el-empty v-if="flows.length === 0" description="暂无流转记录" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api'

const route = useRoute()
const task = ref(null)
const flows = ref([])

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

const getActionType = (action) => {
  if (action.includes('创建')) return 'primary'
  if (action.includes('完成')) return 'success'
  if (action.includes('调度') || action.includes('分派')) return 'warning'
  return 'info'
}

const formatTime = (time) => {
  if (!time) return ''
  return new Date(time).toLocaleString('zh-CN')
}

const loadTaskFlows = async () => {
  try {
    const taskId = route.query.task_id
    if (!taskId) return
    
    // 获取流转记录
    const flowData = await api.get(`/flows/task/${taskId}`)
    flows.value = flowData
    
    // TODO: 获取任务详情
    task.value = {
      task_id: `TASK-${taskId}`,
      title: '任务标题',
      status: 'processing',
      created_at: '2026-03-10 05:20:00',
      completed_at: null
    }
  } catch (error) {
    console.error('加载流转记录失败:', error)
  }
}

onMounted(() => {
  loadTaskFlows()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.flow-item {
  padding: 10px 0;
}

.flow-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.flow-remark {
  background-color: #F5F7FA;
  padding: 10px;
  border-radius: 4px;
  color: #606266;
}
</style>
