<template>
  <div class="minister-card" :class="statusClass">
    <div class="minister-header">
      <div class="minister-emoji">{{ minister.emoji || '👤' }}</div>
      <div class="minister-info">
        <div class="minister-name">{{ minister.name }}</div>
        <div class="minister-role">{{ minister.department }}</div>
      </div>
      <div class="minister-status">
        <div class="status-dot" :class="minister.status"></div>
        <span class="status-text">{{ statusText }}</span>
      </div>
    </div>
    <div class="minister-body">
      <div v-if="currentTask" class="current-task" @click="$emit('view-task', currentTask)">
        <div class="task-id">{{ currentTask.task_id }}</div>
        <div class="task-title">{{ currentTask.title }}</div>
        <div class="task-now">{{ currentTask.now }}</div>
        <div class="task-meta">
          <el-tag size="small" :type="getStatusType(currentTask.status)">
            {{ getStatusText(currentTask.status) }}
          </el-tag>
        </div>
      </div>
      <div v-else class="idle-status">
        <el-icon><clock /></el-icon>
        <span>候命中...</span>
      </div>
    </div>
    <div class="minister-footer">
      <div class="model-info">
        <el-icon><cpu /></el-icon>
        <span>{{ minister.model }}</span>
      </div>
      <div class="last-active">
        <el-icon><timer /></el-icon>
        <span>{{ minister.lastActive || '无记录' }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Clock, Cpu, Timer } from '@element-plus/icons-vue'

// 支持 kebab-case 和 PascalCase
const props = defineProps({
  minister: {
    type: Object,
    required: true
  },
  currentTask: {
    type: Object,
    default: null
  }
})

defineEmits(['view-task'])

const statusClass = computed(() => {
  const map = {
    active: 'active-card',
    busy: 'busy-card',
    blocked: 'blocked-card',
    idle: 'idle-card'
  }
  return map[props.minister.status] || ''
})

const statusText = computed(() => {
  const map = {
    active: '执行中',
    busy: '忙碌',
    blocked: '阻塞',
    idle: '空闲'
  }
  return map[props.minister.status] || '未知'
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
</script>

<style scoped>
.minister-card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.2s;
}

.minister-card:hover {
  border-color: #2e3d6a;
}

.minister-card.active-card {
  border-color: var(--acc);
}

.minister-card.blocked-card {
  border-color: #ff527055;
}

.minister-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--panel2);
  border-bottom: 1px solid var(--line);
}

.minister-emoji {
  font-size: 24px;
}

.minister-info {
  flex: 1;
}

.minister-name {
  font-size: 14px;
  font-weight: 800;
}

.minister-role {
  font-size: 10px;
  color: var(--muted);
}

.minister-status {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-dot.active {
  background: var(--ok);
}

.status-dot.busy {
  background: var(--warn);
  animation: pulse 1.5s infinite;
}

.status-dot.blocked {
  background: var(--danger);
  animation: pulse 1s infinite;
}

.status-dot.idle {
  background: #2a3a5a;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-text {
  color: var(--muted);
}

.minister-body {
  padding: 14px 16px;
}

.current-task {
  display: flex;
  flex-direction: column;
  gap: 6px;
  cursor: pointer;
  padding: 6px;
  border-radius: 8px;
  border: 1px solid var(--line);
  transition: all 0.2s;
}

.current-task:hover {
  border-color: var(--acc);
}

.task-id {
  font-size: 10px;
  color: var(--acc);
  font-weight: 700;
  letter-spacing: 0.04em;
}

.task-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
  line-height: 1.3;
}

.task-now {
  font-size: 12px;
  color: var(--muted);
  line-height: 1.5;
  margin-top: 2px;
}

.task-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 6px;
}

.idle-status {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--muted);
  font-size: 13px;
  padding: 6px 0;
}

.minister-footer {
  padding: 8px 16px;
  border-top: 1px solid var(--line);
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--panel2);
  font-size: 10px;
  color: var(--muted);
}

.model-info,
.last-active {
  display: flex;
  align-items: center;
  gap: 4px;
}

.last-active {
  margin-left: auto;
}
</style>
