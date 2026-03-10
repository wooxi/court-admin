<template>
  <div id="app">
    <div class="app-container">
      <!-- 头部导航 -->
      <header class="app-header">
        <div class="header-left">
          <div>
            <div class="app-logo">🏛️ 朝廷政务管理系统</div>
            <div class="app-subtitle">Court Administration System</div>
          </div>
        </div>
        <div class="header-right">
          <span class="status-chip ok">✅ 系统正常</span>
          <span class="status-chip">{{ taskCount }} 任务</span>
          <button class="icon-btn" @click="refresh" title="刷新">
            <el-icon><Refresh /></el-icon>
          </button>
          <el-avatar :size="32" icon="User" style="cursor: pointer" />
        </div>
      </header>

      <!-- 标签页导航 -->
      <nav class="tab-nav">
        <div
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-item"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          <el-icon>{{ tab.icon }}</el-icon>
          {{ tab.label }}
          <span v-if="tab.badge" class="tab-badge">{{ tab.badge }}</span>
        </div>
      </nav>

      <!-- 主内容区 -->
      <main class="content-panel fade-in">
        <component :is="currentComponent" />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Refresh, DataAnalysis, User, Document, Connection, TrendCharts, Setting } from '@element-plus/icons-vue'
import Dashboard from './views/Dashboard.vue'
import Ministers from './views/Ministers.vue'
import Tasks from './views/Tasks.vue'
import Flows from './views/Flows.vue'
import Stats from './views/Stats.vue'
import Config from './views/Config.vue'

const activeTab = ref('dashboard')
const taskCount = ref(0)

const tabs = [
  { key: 'dashboard', label: '📊 总览', icon: DataAnalysis, badge: '' },
  { key: 'ministers', label: '👥 大臣', icon: User, badge: '7' },
  { key: 'tasks', label: '📋 任务', icon: Document, badge: '3' },
  { key: 'flows', label: '🔗 流转', icon: Connection, badge: '' },
  { key: 'stats', label: '📈 报表', icon: TrendCharts, badge: '' },
  { key: 'config', label: '⚙️ 配置', icon: Setting, badge: '' }
]

const componentMap = {
  dashboard: Dashboard,
  ministers: Ministers,
  tasks: Tasks,
  flows: Flows,
  stats: Stats,
  config: Config
}

const currentComponent = computed(() => componentMap[activeTab.value])

const refresh = () => {
  // TODO: 实现刷新逻辑
  console.log('刷新数据')
}

onMounted(() => {
  // 模拟任务数量
  taskCount.value = 238
})
</script>

<style scoped>
#app {
  min-height: 100vh;
  background: var(--bg);
}
</style>
