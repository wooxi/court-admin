<template>
  <div class="tasks">
    <div class="page-header">
      <h1>📋 任务管理</h1>
      <el-button type="primary" @click="showAddDialog = true">
        <el-icon><Plus /></el-icon>
        创建任务
      </el-button>
    </div>

    <!-- 筛选栏 -->
    <el-card style="margin-bottom: 20px;">
      <el-form :inline="true">
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部状态" clearable>
            <el-option label="待处理" value="pending" />
            <el-option label="进行中" value="processing" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="filters.priority" placeholder="全部优先级" clearable>
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadTasks">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 任务列表 -->
    <el-table :data="tasks" stripe style="width: 100%">
      <el-table-column prop="task_id" label="任务 ID" width="180" />
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="priority" label="优先级" width="80">
        <template #default="{ row }">
          <el-tag :type="getPriorityType(row.priority)" size="small">
            {{ getPriorityText(row.priority) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button size="small" @click="viewTask(row)">查看</el-button>
          <el-button size="small" @click="viewFlow(row)">流转</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建任务对话框 -->
    <el-dialog v-model="showAddDialog" title="创建任务" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="任务标题">
          <el-input v-model="form.title" placeholder="任务标题" />
        </el-form-item>
        <el-form-item label="任务描述">
          <el-input v-model="form.description" type="textarea" rows="4" placeholder="任务描述" />
        </el-form-item>
        <el-form-item label="承办大臣">
          <el-select v-model="form.assignee_id" placeholder="选择大臣">
            <el-option
              v-for="minister in ministers"
              :key="minister.id"
              :label="minister.name"
              :value="minister.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="form.priority" placeholder="选择优先级">
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="createTask">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'

const router = useRouter()
const tasks = ref([])
const ministers = ref([])
const filters = ref({
  status: '',
  priority: ''
})
const showAddDialog = ref(false)
const form = ref({
  title: '',
  description: '',
  assignee_id: null,
  priority: 'medium'
})

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

const getPriorityType = (priority) => {
  const map = {
    high: 'danger',
    medium: 'warning',
    low: 'info'
  }
  return map[priority] || 'info'
}

const getPriorityText = (priority) => {
  const map = {
    high: '高',
    medium: '中',
    low: '低'
  }
  return map[priority] || priority
}

const loadTasks = async () => {
  try {
    const params = {}
    if (filters.value.status) params.status = filters.value.status
    if (filters.value.priority) params.priority = filters.value.priority
    const data = await api.get('/tasks/', { params })
    tasks.value = data
  } catch (error) {
    console.error('加载任务列表失败:', error)
  }
}

const loadMinisters = async () => {
  try {
    const data = await api.get('/ministers/')
    ministers.value = data
  } catch (error) {
    console.error('加载大臣列表失败:', error)
  }
}

const viewTask = (task) => {
  console.log('查看任务:', task)
  // TODO: 实现任务详情
}

const viewFlow = (task) => {
  router.push(`/flows?task_id=${task.id}`)
}

const createTask = async () => {
  try {
    const taskData = {
      ...form.value,
      task_id: `TASK-${Date.now()}`
    }
    await api.post('/tasks/', taskData)
    showAddDialog.value = false
    await loadTasks()
  } catch (error) {
    console.error('创建任务失败:', error)
  }
}

onMounted(() => {
  loadTasks()
  loadMinisters()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
</style>
