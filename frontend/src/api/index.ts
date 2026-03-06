import axios from 'axios'
import { message } from 'ant-design-vue'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  res => res.data,
  err => {
    console.error('API Error:', err)
    if (err.response?.status === 401) {
      localStorage.removeItem('access_token')
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

export default api

export const authApi = {
  login: (username: string, password: string) => api.post('/auth/login', { username, password }),
  getMe: () => api.get('/auth/me'),
  getUsers: (params?: any) => api.get('/auth/users', { params }),
  createUser: (data: any) => api.post('/auth/users', data),
  updateUser: (id: number, data: any) => api.put(`/auth/users/${id}`, data),
  deleteUser: (id: number) => api.delete(`/auth/users/${id}`),
}

export const dashboardApi = {
  getKpi: (params?: any) => api.get('/cockpit/kpi', { params }),
  getProduction: (params?: any) => api.get('/cockpit/production', { params }),
  getSales: (params?: any) => api.get('/cockpit/sales', { params }),
  getRegionConfig: () => api.get('/cockpit/region-config'),
  saveRegionConfig: (data: any) => api.put('/cockpit/region-config', data),
}

export const queryApi = {
  getProduction: (params?: any) => api.get('/query/production', { params }),
  getProductionReport: (params?: any) => api.get('/query/production-report', { params }),
  getProductionEquipment: (params?: any) => api.get('/query/production-equipment', { params }),
  getProductionEquipmentDetail: (params?: any) => api.get('/query/production-equipment-detail', { params }),
  getProductionStopReasons: (params?: any) => api.get('/query/production-stop-reasons', { params }),
  getInventory: (params?: any) => api.get('/query/inventory', { params }),
  getSales: (params?: any) => api.get('/query/sales', { params }),
  getInventoryDaily: (params?: any) => api.get('/query/inventory-daily', { params }),
}

export const balanceApi = {
  getAlerts: (params?: any) => api.get('/balance/alerts', { params }),
  getSuggestions: (params?: any) => api.get('/balance/suggestions', { params }),
  runOptimize: (data?: any) => api.post('/balance/optimize', data),
}

export const dataApi = {
  upload: (file: File, templateType: string) => {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('template_type', templateType)
    return api.post('/data/upload', fd)
  },
  getTemplates: () => api.get('/data/templates'),
  getUploadRecords: (params?: any) => api.get('/data/upload-records', { params }),
}

export const agentApi = {
  chat: (question: string, context?: any) => api.post('/agent/chat', { question, context }),
  chatStream: (question: string, context?: any) => {
    const token = localStorage.getItem('access_token')
    return fetch('/api/agent/chat-stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ question, context }),
    })
  },
  getConfig: () => api.get('/agent/config'),
  saveConfig: (data: any) => api.put('/agent/config', data),
  updateApiKey: (apiKey: string) => api.patch('/agent/config/api-key', { api_key: apiKey }),
  getAuditLogs: (limit = 30) => api.get('/agent/config/audit', { params: { limit } }),
}
