<template>
  <header class="layout-header">
    <div class="header-left">
      <div class="app-logo">🏛️ 朝廷政务管理系统</div>
      <div class="breadcrumb">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
          <el-breadcrumb-item>{{ currentRouteTitle }}</el-breadcrumb-item>
        </el-breadcrumb>
      </div>
    </div>
    <div class="header-right">
      <span class="status-chip ok">✅ 系统正常</span>
      <span class="status-chip">{{ taskCount }} 任务</span>
      <button class="icon-btn" @click="refresh" title="刷新">
        <el-icon><Refresh /></el-icon>
      </button>
      <el-avatar :size="32">
        <el-icon><User /></el-icon>
      </el-avatar>
    </div>
  </header>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import api from '@/api'

const route = useRoute()
const taskCount = ref(0)

const routeTitleMap = {
  '/': '📊 总览',
  '/ministers': '👥 大臣',
  '/tasks': '📋 任务',
  '/flows': '🔗 流转',
  '/scheduler': '⏰ 定时任务',
  '/cron': '⏰ 定时任务',
  '/stats': '📈 报表',
  '/config': '⚙️ 配置',
}

const currentRouteTitle = computed(() => routeTitleMap[route.path] || '页面')

const loadTaskCount = async () => {
  try {
    const tasks = await api.get('/tasks/', { params: { limit: 1 } })
    // 后端当前未返回总数，这里退化为已拉取数；由 dashboard 提供更准确总量
    taskCount.value = Array.isArray(tasks) ? tasks.length : 0
  } catch {
    taskCount.value = 0
  }
}

const refresh = () => {
  window.dispatchEvent(new CustomEvent('global-refresh'))
  loadTaskCount()
}

onMounted(() => {
  loadTaskCount()
})
</script>

<style scoped>
.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--panel);
  border-bottom: 1px solid var(--line);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.app-logo {
  font-size: 18px;
  font-weight: 800;
  background: linear-gradient(135deg, #6a9eff, #a07aff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.breadcrumb {
  font-size: 13px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-chip {
  font-size: 11px;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--panel2);
  border: 1px solid var(--line);
  color: var(--muted);
}

.status-chip.ok {
  border-color: #2ecc8a44;
  color: var(--ok);
}

.icon-btn {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  border: 1px solid var(--line);
  background: transparent;
  color: var(--text);
  cursor: pointer;
}

.icon-btn:hover {
  background: var(--panel2);
  border-color: var(--acc);
}

@media (max-width: 768px) {
  .layout-header {
    padding: 10px;
  }
  .breadcrumb {
    display: none;
  }
  .app-logo {
    font-size: 14px;
  }
}
</style>
