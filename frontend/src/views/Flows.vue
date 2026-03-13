<template>
  <div class="flows">
    <div class="page-header">
      <h1>🔗 任务流转追踪</h1>
      <el-button @click="$router.push('/tasks')">返回任务列表</el-button>
    </div>

    <el-alert
      v-if="!taskCode"
      title="请从任务列表进入流转页"
      type="info"
      show-icon
      style="margin-bottom: 16px"
    />

    <el-card v-if="task" style="margin-bottom: 20px;">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="任务 ID">{{ task.task_id }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(task.status)">{{ getStatusText(task.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="标题" :span="2">{{ task.title }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(task.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="完成时间">{{ task.completed_at ? formatTime(task.completed_at) : '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>⏱️ 流转时间线</span>
          <el-button size="small" @click="loadTaskFlows">刷新</el-button>
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
              <el-collapse v-if="flow.metadata && Object.keys(flow.metadata).length">
                <el-collapse-item title="元数据" name="1">
                  <pre class="meta-block">{{ JSON.stringify(flow.metadata, null, 2) }}</pre>
                </el-collapse-item>
              </el-collapse>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>

      <el-empty v-if="!loading && flows.length === 0" description="暂无流转记录" />
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute } from 'vue-router'

import api from '@/api'

const route = useRoute()
const loading = ref(false)
const task = ref(null)
const flows = ref([])

const taskCode = computed(() => route.query.task_id)

const getStatusType = (status) => ({ pending: 'info', processing: 'warning', completed: 'success' }[status] || 'info')
const getStatusText = (status) => ({ pending: '待处理', processing: '进行中', completed: '已完成' }[status] || status)

const getActionType = (action) => {
  if ((action || '').includes('创建')) return 'primary'
  if ((action || '').includes('完成')) return 'success'
  if ((action || '').includes('调度') || (action || '').includes('分派')) return 'warning'
  return 'info'
}

const formatTime = (time) => (time ? new Date(time).toLocaleString('zh-CN') : '-')

const loadTaskFlows = async () => {
  if (!taskCode.value) return

  loading.value = true
  try {
    const taskInfo = await api.get(`/tasks/by-code/${encodeURIComponent(taskCode.value)}`)
    task.value = taskInfo
    flows.value = await api.get(`/flows/task/${taskInfo.id}`)
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '加载流转记录失败')
    console.error(error)
  } finally {
    loading.value = false
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
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  color: #606266;
  margin-top: 8px;
}

.meta-block {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
