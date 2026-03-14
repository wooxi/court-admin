import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/components/Layout/MainLayout.vue'

const routes = [
  {
    path: '/',
    component: MainLayout,
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: {
          module: 'court',
          moduleTitle: '朝廷政务',
          title: '📊 总览',
        },
      },
      {
        path: 'ministers',
        name: 'Ministers',
        component: () => import('@/views/Ministers.vue'),
        meta: {
          module: 'court',
          moduleTitle: '朝廷政务',
          title: '👥 大臣',
        },
      },
      {
        path: 'tasks',
        name: 'Tasks',
        component: () => import('@/views/Tasks.vue'),
        meta: {
          module: 'court',
          moduleTitle: '朝廷政务',
          title: '📋 任务',
        },
      },
      {
        path: 'tasks/:taskCode',
        name: 'TaskDetail',
        component: () => import('@/views/TaskDetail.vue'),
        meta: {
          module: 'court',
          moduleTitle: '朝廷政务',
          title: '📋 任务详情',
        },
      },
      {
        path: 'flows',
        name: 'Flows',
        component: () => import('@/views/Flows.vue'),
        meta: {
          module: 'court',
          moduleTitle: '朝廷政务',
          title: '🔗 流转',
        },
      },
      {
        path: 'scheduler',
        name: 'Scheduler',
        component: () => import('@/views/Scheduler.vue'),
        meta: {
          module: 'court',
          moduleTitle: '朝廷政务',
          title: '⏰ 定时任务',
        },
      },
      {
        path: 'cron',
        redirect: '/scheduler',
      },
      {
        path: 'stats',
        name: 'Stats',
        component: () => import('@/views/Stats.vue'),
        meta: {
          module: 'court',
          moduleTitle: '朝廷政务',
          title: '📈 报表',
        },
      },
      {
        path: 'config',
        name: 'Config',
        component: () => import('@/views/Config.vue'),
        meta: {
          module: 'court',
          moduleTitle: '朝廷政务',
          title: '⚙️ 配置',
        },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
