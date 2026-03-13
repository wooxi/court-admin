<template>
  <div class="git-timeline">
    <div v-for="(flow, index) in flows" :key="flow.id" class="git-entry" :class="getEntryClass(flow)">
      <div class="git-node">
        <span class="git-dot"></span>
        <span v-if="index !== flows.length - 1" class="git-line"></span>
      </div>

      <div class="git-content">
        <div class="git-header">
          <span class="git-action">{{ flow.action || '流转' }}</span>
          <span class="git-time">{{ formatTime(flow.timestamp) }}</span>
        </div>

        <div class="git-actors">
          <span class="from">{{ flow.from_actor || '未知' }}</span>
          <span class="arrow">→</span>
          <span class="to">{{ flow.to_actor || '未知' }}</span>
        </div>

        <div v-if="flow.remark" class="git-remark">{{ flow.remark }}</div>

        <div v-if="flow.metadata && Object.keys(flow.metadata).length" class="git-meta">
          <pre>{{ prettyMeta(flow.metadata) }}</pre>
        </div>
      </div>
    </div>

    <el-empty v-if="flows.length === 0" description="暂无流转记录" />
  </div>
</template>

<script setup>
const props = defineProps({
  flows: {
    type: Array,
    default: () => [],
  },
})

const formatTime = (value) => (value ? new Date(value).toLocaleString('zh-CN') : '-')

const getEntryClass = (flow) => {
  const action = (flow?.action || '').toLowerCase()

  if (action.includes('完成')) return 'done'
  if (action.includes('分派') || action.includes('调度') || action.includes('转交')) return 'dispatch'
  if (action.includes('创建')) return 'create'
  return 'processing'
}

const prettyMeta = (metadata) => JSON.stringify(metadata, null, 2)
</script>

<style scoped>
.git-timeline {
  position: relative;
  padding: 8px 0;
}

.git-entry {
  display: flex;
  gap: 12px;
  min-height: 70px;
}

.git-node {
  width: 24px;
  position: relative;
  display: flex;
  justify-content: center;
}

.git-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-top: 8px;
  border: 2px solid var(--acc);
  background: #0f1219;
  z-index: 2;
}

.git-line {
  position: absolute;
  top: 20px;
  bottom: -2px;
  left: 11px;
  width: 2px;
  background: #303a57;
}

.git-content {
  flex: 1;
  border: 1px solid var(--line);
  background: var(--panel2);
  border-radius: 10px;
  padding: 10px 12px;
  margin-bottom: 12px;
}

.git-header {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
}

.git-action {
  font-weight: 700;
  color: var(--text);
}

.git-time {
  color: var(--muted);
  font-size: 12px;
  font-family: Menlo, Monaco, Consolas, monospace;
}

.git-actors {
  margin-top: 6px;
  font-size: 13px;
  color: var(--muted);
  display: flex;
  align-items: center;
  gap: 6px;
}

.git-actors .from {
  color: #8ab4ff;
}

.git-actors .to {
  color: #7fe4b4;
}

.git-remark {
  margin-top: 8px;
  border-left: 2px solid #4f5f87;
  padding-left: 8px;
  color: var(--text);
  line-height: 1.5;
}

.git-meta {
  margin-top: 8px;
}

.git-meta pre {
  margin: 0;
  font-size: 12px;
  border-radius: 8px;
  padding: 8px;
  background: #0a0d14;
  border: 1px solid #1e263c;
  color: #9fb1d9;
  white-space: pre-wrap;
  word-break: break-all;
}

.git-entry.done .git-dot {
  border-color: var(--ok);
  background: var(--ok);
}

.git-entry.dispatch .git-dot {
  border-color: var(--warn);
  background: var(--warn);
}

.git-entry.create .git-dot {
  border-color: #7f8cff;
  background: #7f8cff;
}
</style>
