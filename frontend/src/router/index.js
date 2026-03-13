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
        component: () => import('@/views/Dashboard.vue')
      },
      {
        path: 'ministers',
        name: 'Ministers',
        component: () => import('@/views/Ministers.vue')
      },
      {
        path: 'tasks',
        name: 'Tasks',
        component: () => import('@/views/Tasks.vue')
      },
      {
        path: 'tasks/:taskCode',
        name: 'TaskDetail',
        component: () => import('@/views/TaskDetail.vue')
      },
      {
        path: 'flows',
        name: 'Flows',
        component: () => import('@/views/Flows.vue')
      },
      {
        path: 'scheduler',
        name: 'Scheduler',
        component: () => import('@/views/Scheduler.vue')
      },
      {
        path: 'cron',
        redirect: '/scheduler'
      },
      {
        path: 'stats',
        name: 'Stats',
        component: () => import('@/views/Stats.vue')
      },
      {
        path: 'config',
        name: 'Config',
        component: () => import('@/views/Config.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
