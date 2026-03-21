import api from '@/api'

export const fetchSchedulerJobs = () => api.get('/scheduler/jobs')

export const fetchSchedulerJobDetail = (jobId) => api.get(`/scheduler/jobs/${encodeURIComponent(jobId)}`)

export const fetchSchedulerRunHistory = (params = {}) => api.get('/scheduler/run-history', { params })
