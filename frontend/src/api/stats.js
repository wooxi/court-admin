import api from '@/api'

export const fetchExecutionReport = (params = {}) => api.get('/stats/task-executions/report', { params })

export const fetchTaskStatusStats = (params = {}) => api.get('/stats/tasks', { params })
