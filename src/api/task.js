/**
 * 通用任务管理 API
 * 接口 25-26
 */

const USE_MOCK = false  // 生产模式

// ===================== Mock 数据 =====================
const MOCK_TASK_LIST = [
  {
    id: 1,
    name: '1688 商品批量采集',
    type: 'collect',
    status: 'completed',
    progress: 100,
    total: 50,
    completed: 50,
    failed: 0,
    creator: { id: 1, username: 'admin', nickname: '管理员' },
    created_at: '2026-04-10T09:30:00Z',
    updated_at: '2026-04-10T09:45:00Z',
    completed_at: '2026-04-10T09:45:00Z',
  },
  {
    id: 2,
    name: '库存同步 - Amazon US',
    type: 'sync',
    status: 'running',
    progress: 65,
    total: 200,
    completed: 130,
    failed: 2,
    creator: { id: 1, username: 'admin', nickname: '管理员' },
    created_at: '2026-04-10T10:00:00Z',
    updated_at: '2026-04-10T10:15:00Z',
    completed_at: null,
  },
  {
    id: 3,
    name: '批量更新 SKU 价格',
    type: 'sku_update',
    status: 'pending',
    progress: 0,
    total: 30,
    completed: 0,
    failed: 0,
    creator: { id: 1, username: 'admin', nickname: '管理员' },
    created_at: '2026-04-10T11:00:00Z',
    updated_at: '2026-04-10T11:00:00Z',
    completed_at: null,
  },
  {
    id: 4,
    name: '1688 商品采集（断点续传）',
    type: 'collect',
    status: 'failed',
    progress: 40,
    total: 100,
    completed: 38,
    failed: 2,
    error_msg: '网络超时，请重试',
    creator: { id: 2, username: 'editor', nickname: '编辑员' },
    created_at: '2026-04-09T15:30:00Z',
    updated_at: '2026-04-09T16:00:00Z',
    completed_at: null,
  },
]

const mockTaskList = (params) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      const { type, status, page = 1, page_size = 10 } = params || {}
      let filtered = [...MOCK_TASK_LIST]
      if (type) filtered = filtered.filter((t) => t.type === type)
      if (status) filtered = filtered.filter((t) => t.status === status)
      const total = filtered.length
      const start = (page - 1) * page_size
      const items = filtered.slice(start, start + page_size)
      resolve({ code: 200, message: 'success', data: { items, total, page, page_size } })
    }, 400)
  })
}

const mockTaskDetail = (id) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      const task = MOCK_TASK_LIST.find((t) => t.id === Number(id))
      resolve(task ? { code: 200, message: 'success', data: task } : { code: 404, message: '任务不存在' })
    }, 300)
  })
}

const mockTaskUpdate = (id, data) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ code: 200, message: '更新成功', data: { id, ...data } })
    }, 400)
  })
}

const mockTaskDelete = (id) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ code: 200, message: '删除成功' })
    }, 300)
  })
}

const mockTaskCreate = (data) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        code: 200,
        message: '任务创建成功',
        data: { id: Date.now(), ...data, status: 'pending', progress: 0, created_at: new Date().toISOString() },
      })
    }, 500)
  })
}

// ===================== 真实接口 =====================
import axios from 'axios'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 15000,
})

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

request.interceptors.response.use((response) => response.data, (error) => Promise.reject(error))

// ===================== API 函数 =====================

/**
 * 任务列表
 * GET /api/tasks/
 * @param {Object} params - { type?, status?, page, page_size }
 */
export const getTaskList = (params) =>
  USE_MOCK ? mockTaskList(params) : request.get('/api/tasks/', { params })

/**
 * 任务详情
 * GET /api/tasks/{id}/
 */
export const getTaskDetail = (id) =>
  USE_MOCK ? mockTaskDetail(id) : request.get(`/api/tasks/${id}/`)

/**
 * 创建任务
 * POST /api/tasks/
 * @param {Object} data - { name, type, config }
 */
export const createTask = (data) =>
  USE_MOCK ? mockTaskCreate(data) : request.post('/api/tasks/', data)

/**
 * 更新任务
 * PUT /api/tasks/{id}/
 * @param {number} id
 * @param {Object} data
 */
export const updateTask = (id, data) =>
  USE_MOCK ? mockTaskUpdate(id, data) : request.put(`/api/tasks/${id}/`, data)

/**
 * 部分更新任务
 * PATCH /api/tasks/{id}/
 * @param {number} id
 * @param {Object} data
 */
export const patchTask = (id, data) =>
  USE_MOCK ? mockTaskUpdate(id, data) : request.patch(`/api/tasks/${id}/`, data)

/**
 * 删除任务
 * DELETE /api/tasks/{id}/
 * @param {number} id
 */
export const deleteTask = (id) =>
  USE_MOCK ? mockTaskDelete(id) : request.delete(`/api/tasks/${id}/`)

export default { getTaskList, getTaskDetail, createTask, updateTask, patchTask, deleteTask }
