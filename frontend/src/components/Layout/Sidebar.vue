<template>
  <aside class="sidebar" :class="{ collapsed: collapsed }">
    <!-- Logo 区域 -->
    <div class="sidebar-header">
      <div class="logo-text" v-show="!collapsed">
        <span class="logo-icon">🏛️</span>
        <span class="logo-title">朝廷政务</span>
      </div>
      <button class="collapse-btn" @click="$emit('toggle')">
        <el-icon><component :is="collapsed ? 'Expand' : 'Fold'" /></el-icon>
      </button>
    </div>
    
    <!-- 菜单列表 -->
    <nav class="sidebar-menu">
      <router-link
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        class="menu-item"
        :class="{ active: isActive(item.path) }"
        :title="collapsed ? item.title : ''"
      >
        <el-icon class="menu-icon"><component :is="item.icon" /></el-icon>
        <span class="menu-text" v-show="!collapsed">{{ item.title }}</span>
        <el-badge
          v-if="item.badge"
          :value="item.badge"
          :hidden="collapsed"
          class="menu-badge"
          type="danger"
        />
      </router-link>
    </nav>
    
    <!-- 底部信息 -->
    <div class="sidebar-footer" v-show="!collapsed">
      <div class="version-info">v2.0.0</div>
    </div>
  </aside>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import {
  DataAnalysis,
  User,
  Document,
  Connection,
  AlarmClock,
  TrendCharts,
  Setting,
  Fold,
  Expand
} from '@element-plus/icons-vue'
import api from '@/api'

const props = defineProps({
  collapsed: {
    type: Boolean,
    default: false
  }
})

defineEmits(['toggle'])

const route = useRoute()

// 任务角标（动态获取）
const taskBadge = ref('')

// 加载任务角标
const loadTaskBadge = async () => {
  try {
    // 获取 pending 和 processing 状态的任务数量
    // 后端 /api/tasks 的 limit 上限为 500，避免触发 422
    const tasks = await api.get('/tasks/', { params: { limit: 500 } })
    const pendingCount = tasks.filter(t => t.status === 'pending' || t.status === 'processing').length
    
    if (pendingCount > 0) {
      taskBadge.value = pendingCount > 99 ? '99+' : pendingCount
    } else {
      taskBadge.value = ''
    }
  } catch (error) {
    console.error('加载任务角标失败:', error)
    taskBadge.value = ''
  }
}

// 定时刷新角标（每 30 秒）
let refreshTimer = null
onMounted(() => {
  loadTaskBadge()
  refreshTimer = setInterval(loadTaskBadge, 30000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})

const menuItems = computed(() => [
  { path: '/', title: '📊 总览', icon: DataAnalysis, badge: '' },
  { path: '/ministers', title: '👥 大臣', icon: User, badge: '' },
  { path: '/tasks', title: '📋 任务', icon: Document, badge: taskBadge.value },
  { path: '/flows', title: '🔗 流转', icon: Connection, badge: '' },
  { path: '/scheduler', title: '⏰ 定时', icon: AlarmClock, badge: '' },
  { path: '/stats', title: '📈 报表', icon: TrendCharts, badge: '' },
  { path: '/config', title: '⚙️ 配置', icon: Setting, badge: '' }
])

const isActive = (path) => {
  if (path === '/tasks') {
    return route.path === '/tasks' || route.path.startsWith('/tasks/')
  }
  return route.path === path
}
</script>

<style scoped>
.sidebar {
  width: 240px;
  height: 100vh;
  background: var(--panel);
  border-right: 1px solid var(--line);
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  overflow: hidden;
}

.sidebar.collapsed {
  width: 64px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 16px;
  border-bottom: 1px solid var(--line);
}

.logo-text {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 700;
  color: var(--acc);
}

.logo-icon {
  font-size: 24px;
}

.collapse-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  border: 1px solid var(--line);
  background: transparent;
  color: var(--text);
  cursor: pointer;
  transition: all 0.2s;
}

.collapse-btn:hover {
  background: var(--panel2);
  border-color: var(--acc);
  color: var(--acc);
}

.sidebar-menu {
  flex: 1;
  padding: 12px 8px;
  overflow-y: auto;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  margin-bottom: 4px;
  border-radius: 8px;
  color: var(--text);
  text-decoration: none;
  transition: all 0.2s;
  cursor: pointer;
}

.menu-item:hover {
  background: var(--panel2);
  color: var(--acc);
}

.menu-item.active {
  background: linear-gradient(135deg, rgba(106, 158, 255, 0.15), rgba(106, 158, 255, 0.05));
  color: var(--acc);
  font-weight: 600;
  border-left: 3px solid var(--acc);
}

.menu-icon {
  font-size: 20px;
  flex-shrink: 0;
  color: var(--muted);
}

.menu-item:hover .menu-icon,
.menu-item.active .menu-icon {
  color: var(--acc);
}

.menu-text {
  flex: 1;
  font-size: 14px;
  white-space: nowrap;
}

.menu-badge {
  flex-shrink: 0;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--line);
  text-align: center;
}

.version-info {
  font-size: 12px;
  color: var(--muted);
}

/* 响应式 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    z-index: 1000;
    height: 100vh;
    transform: translateX(-100%);
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.3);
  }
  
  .sidebar:not(.collapsed) {
    transform: translateX(0);
  }
  
  /* 移动端遮罩层 */
  .sidebar-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 999;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.3s;
  }
  
  .sidebar:not(.collapsed) + .sidebar-overlay {
    opacity: 1;
    pointer-events: auto;
  }
}
</style>
