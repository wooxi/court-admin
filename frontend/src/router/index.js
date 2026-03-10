import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue')
  },
  {
    path: '/ministers',
    name: 'Ministers',
    component: () => import('@/views/Ministers.vue')
  },
  {
    path: '/tasks',
    name: 'Tasks',
    component: () => import('@/views/Tasks.vue')
  },
  {
    path: '/flows',
    name: 'Flows',
    component: () => import('@/views/Flows.vue')
  },
  {
    path: '/stats',
    name: 'Stats',
    component: () => import('@/views/Stats.vue')
  },
  {
    path: '/config',
    name: 'Config',
    component: () => import('@/views/Config.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
