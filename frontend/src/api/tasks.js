import api from '@/api'

export const fetchTasks = (params = {}) => api.get('/tasks/', { params })

export const fetchTaskByCode = (taskCode) => api.get(`/tasks/by-code/${encodeURIComponent(taskCode)}`)

export const fetchTaskFlows = (taskPk) => api.get(`/flows/task/${taskPk}`)

export const createTask = (payload) => api.post('/tasks/', payload)

export const updateTask = (taskPk, payload) => api.put(`/tasks/${taskPk}`, payload)

export const fetchMinisters = (params = {}) => api.get('/ministers/', { params })
