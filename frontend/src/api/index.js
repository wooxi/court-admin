import axios from 'axios'

import { normalizeText } from '@/utils/text'

let configAdminToken = localStorage.getItem('court_admin_config_token') || ''

export const setConfigAdminToken = (token) => {
  configAdminToken = token || ''
  if (token) {
    localStorage.setItem('court_admin_config_token', token)
  } else {
    localStorage.removeItem('court_admin_config_token')
  }
}

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

api.interceptors.request.use(
  (config) => {
    if (config.url?.startsWith('/config') && configAdminToken) {
      config.headers = config.headers || {}
      config.headers['X-Admin-Token'] = configAdminToken
    }
    return config
  },
  (error) => Promise.reject(error)
)

api.interceptors.response.use(
  (response) => normalizeText(response.data),
  (error) => {
    console.error('API 错误:', error)
    return Promise.reject(error)
  }
)

export default api
