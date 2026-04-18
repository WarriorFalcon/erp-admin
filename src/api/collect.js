/**
 * 商品采集 API
 * 接口前缀：/api/v1/collect/
 * 接口文档：嘉瑞 Swagger 21个接口
 *
 * 当前接口状态：待确认（先用 mock；接口就绪后改 USE_MOCK = false）
 */
import request from '@/utils/request'

const USE_MOCK = false  // 生产模式

// ==================== Mock 数据（开发中用） ====================
const delay = (ms = 800) => new Promise(r => setTimeout(r, ms))

const mockCollect1688Single = (payload) =>
  delay().then(() => ({
    code: 0,
    message: '采集成功',
    data: {
      id: Date.now(),
      url: payload.url,
      title: '【示例】女士纯棉T恤 2024新款 宽松百搭',
      price: 49.5,
      original_price: 89.0,
      images: [
        'https://via.placeholder.com/400x400/667eea/ffffff?text=商品图1',
        'https://via.placeholder.com/400x400/764ba2/ffffff?text=商品图2',
      ],
      stock: 2000,
      sales: 3280,
      platform: '1688',
      status: 'collected',
    },
  }))

const mockCollect1688Batch = (payload) =>
  delay().then(() => ({
    code: 0,
    message: '批量采集任务已创建',
    data: {
      task_id: `task_${Date.now()}`,
      total: payload.urls?.length || 0,
      status: 'pending',
    },
  }))

const mockCreateTask = (payload) =>
  delay().then(() => ({
    code: 0,
    message: '任务创建成功',
    data: {
      id: `task_${Date.now()}`,
      name: payload.name,
      type: payload.type,
      status: 'pending',
      created_at: new Date().toISOString(),
    },
  }))

const mockTaskList = () =>
  delay(500).then(() => ({
    code: 0,
    data: [
      { id: 1, name: '1688批量采集-服装类', type: '1688_batch', status: 'running', progress: 45, total: 100, collected: 45, created_at: '2026-04-10T10:00:00Z' },
      { id: 2, name: 'TikTok采集-数码类', type: 'tiktok', status: 'pending', progress: 0, total: 50, collected: 0, created_at: '2026-04-10T09:30:00Z' },
      { id: 3, name: 'Amazon关键词采集', type: 'amazon', status: 'completed', progress: 100, total: 80, collected: 80, created_at: '2026-04-09T15:00:00Z' },
    ],
    total: 3,
  }))

const mockInventorySync = () =>
  delay(1200).then(() => ({
    code: 0,
    message: '库存同步完成',
    data: {
      synced: 1234,
      failed: 3,
      duration: '5.2s',
    },
  }))

const mockInventoryLog = () =>
  delay().then(() => ({
    code: 0,
    data: [
      { id: 1, action: 'trigger', status: 'success', synced: 1234, failed: 3, created_at: '2026-04-10T18:00:00Z' },
      { id: 2, action: 'trigger', status: 'success', synced: 980, failed: 12, created_at: '2026-04-10T08:00:00Z' },
      { id: 3, action: 'trigger', status: 'failed', synced: 0, failed: 99, created_at: '2026-04-09T08:00:00Z' },
    ],
    total: 3,
  }))

// ==================== 1688 采集 ====================

/**
 * 1688 单链接采集
 * POST /api/v1/collect/1688/single/
 */
export function collect1688Single(payload) {
  if (USE_MOCK) return mockCollect1688Single(payload)
  return request.post('/api/v1/collect/1688/single/', payload)
}

/**
 * 1688 批量采集
 * POST /api/v1/collect/1688/batch/
 */
export function collect1688Batch(payload) {
  if (USE_MOCK) return mockCollect1688Batch(payload)
  return request.post('/api/v1/collect/1688/batch/', payload)
}

// ==================== 平台授权 ====================

/**
 * 1688 授权登录
 * POST /api/v1/collect/1688/auth/login/
 */
export function auth1688Login() {
  if (USE_MOCK) return Promise.resolve({ code: 0, data: { auth_url: 'https://www.1688.com' } })
  return request.post('/api/v1/collect/1688/auth/login/')
}

/**
 * 1688 授权回调
 * GET /api/v1/collect/1688/auth/callback/
 */
export function auth1688Callback(params) {
  if (USE_MOCK) return Promise.resolve({ code: 0, message: '授权成功' })
  return request.get('/api/v1/collect/1688/auth/callback/', { params })
}

/**
 * 1688 授权状态查询
 * GET /api/v1/collect/1688/auth/status/
 */
export function auth1688Status() {
  if (USE_MOCK) return Promise.resolve({ code: 0, data: { authorized: false } })
  return request.get('/api/v1/collect/1688/auth/status/')
}

/**
 * 1688 登出
 * POST /api/v1/collect/1688/auth/logout/
 */
export function auth1688Logout() {
  if (USE_MOCK) return Promise.resolve({ code: 0, message: '已登出' })
  return request.post('/api/v1/collect/1688/auth/logout/')
}

/**
 * TikTok 授权登录
 * POST /api/v1/collect/tiktok/auth/login/
 */
export function authTiktokLogin() {
  if (USE_MOCK) return Promise.resolve({ code: 0, data: { auth_url: 'https://TikTok.com/mock' } })
  return request.post('/api/v1/collect/tiktok/auth/login/')
}

/**
 * TikTok 授权回调
 * GET /api/v1/collect/tiktok/auth/callback/
 */
export function authTiktokCallback(params) {
  if (USE_MOCK) return Promise.resolve({ code: 0, message: '授权成功' })
  return request.get('/api/v1/collect/tiktok/auth/callback/', { params })
}

/**
 * TikTok 授权状态查询
 * GET /api/v1/collect/tiktok/auth/status/
 */
export function authTiktokStatus() {
  if (USE_MOCK) return Promise.resolve({ code: 0, data: { authorized: false } })
  return request.get('/api/v1/collect/tiktok/auth/status/')
}

/**
 * TikTok 登出
 * POST /api/v1/collect/tiktok/auth/logout/
 */
export function authTiktokLogout() {
  if (USE_MOCK) return Promise.resolve({ code: 0, message: '已登出' })
  return request.post('/api/v1/collect/tiktok/auth/logout/')
}

/**
 * Amazon 授权登录
 * POST /api/v1/collect/amazon/auth/login/
 */
export function authAmazonLogin() {
  if (USE_MOCK) return Promise.resolve({ code: 0, data: { auth_url: 'https://Amazon.com/mock' } })
  return request.post('/api/v1/collect/amazon/auth/login/')
}

/**
 * Amazon 授权回调
 * GET /api/v1/collect/amazon/auth/callback/
 */
export function authAmazonCallback(params) {
  if (USE_MOCK) return Promise.resolve({ code: 0, message: '授权成功' })
  return request.get('/api/v1/collect/amazon/auth/callback/', { params })
}

/**
 * Amazon 授权状态查询
 * GET /api/v1/collect/amazon/auth/status/
 */
export function authAmazonStatus() {
  if (USE_MOCK) return Promise.resolve({ code: 0, data: { authorized: false } })
  return request.get('/api/v1/collect/amazon/auth/status/')
}

/**
 * Amazon 登出
 * POST /api/v1/collect/amazon/auth/logout/
 */
export function authAmazonLogout() {
  if (USE_MOCK) return Promise.resolve({ code: 0, message: '已登出' })
  return request.post('/api/v1/collect/amazon/auth/logout/')
}

// ==================== 采集任务 ====================

/**
 * 创建采集任务
 * POST /api/v1/collect/task/
 */
export function createTask(payload) {
  if (USE_MOCK) return mockCreateTask(payload)
  return request.post('/api/v1/collect/task/', payload)
}

/**
 * 采集任务列表
 * GET /api/v1/collect/task/list/
 */
export function fetchTaskList(params) {
  if (USE_MOCK) return mockTaskList()
  return request.get('/api/v1/collect/task/list/', { params })
}

/**
 * 采集任务详情
 * GET /api/v1/collect/task/{id}/
 */
export function fetchTaskDetail(id) {
  if (USE_MOCK) return delay().then(() => ({ code: 0, data: { id, name: '任务详情', status: 'running' } }))
  return request.get(`/api/v1/collect/task/${id}/`)
}

/**
 * 采集任务状态查询
 * GET /api/v1/collect/task/{id}/status/
 */
export function fetchTaskStatus(id) {
  if (USE_MOCK) return delay().then(() => ({ code: 0, data: { status: 'running', progress: Math.floor(Math.random() * 100) } }))
  return request.get(`/api/v1/collect/task/${id}/status/`)
}

/**
 * 取消采集任务
 * POST /api/v1/collect/task/{id}/cancel/
 */
export function cancelTask(id) {
  if (USE_MOCK) return delay().then(() => ({ code: 0, message: '任务已取消' }))
  return request.post(`/api/v1/collect/task/${id}/cancel/`)
}

/**
 * 删除采集任务
 * DELETE /api/v1/collect/task/{id}/
 */
export function deleteTask(id) {
  if (USE_MOCK) return delay().then(() => ({ code: 0, message: '任务已删除' }))
  return request.delete(`/api/v1/collect/task/${id}/`)
}

// ==================== 库存同步 ====================

/**
 * 触发库存同步
 * POST /api/v1/inventory/sync/trigger/
 */
export function triggerInventorySync() {
  if (USE_MOCK) return mockInventorySync()
  return request.post('/api/v1/inventory/sync/trigger/')
}

/**
 * 库存同步日志
 * GET /api/v1/inventory/sync/log/
 */
export function fetchInventoryLog(params) {
  if (USE_MOCK) return mockInventoryLog()
  return request.get('/api/v1/inventory/sync/log/', { params })
}
