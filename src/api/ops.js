/**
 * 运维与系统接口
 * 接口 27-34
 */

const USE_MOCK = false  // 生产模式

// ===================== Mock 数据 =====================
const mockDeadLetterList = (params) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        code: 200,
        message: 'success',
        data: {
          items: [
            { id: 1, queue: 'collect_1688', message_id: 'msg_001', payload: { url: 'https://detail.1688.com/offer/xxx' }, error: '连接超时', failed_at: '2026-04-10T09:00:00Z', retry_count: 3 },
            { id: 2, queue: 'sync_amazon', message_id: 'msg_002', payload: { sku_id: 1001 }, error: 'SKU不存在', failed_at: '2026-04-10T08:30:00Z', retry_count: 3 },
          ],
          total: 2,
          page: params?.page || 1,
          page_size: params?.page_size || 10,
        },
      })
    }, 300)
  })
}

const mockAuditLog = (params) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        code: 200,
        message: 'success',
        data: {
          items: [
            { id: 1, user: 'admin', action: 'LOGIN', resource: '/api/auth/login', ip: '127.0.0.1', timestamp: '2026-04-10T09:00:00Z' },
            { id: 2, user: 'admin', action: 'CREATE_TASK', resource: '/api/tasks/', ip: '127.0.0.1', timestamp: '2026-04-10T09:30:00Z' },
          ],
          total: 2,
          page: params?.page || 1,
          page_size: params?.page_size || 10,
        },
      })
    }, 300)
  })
}

const mockPermissionList = () => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        code: 200,
        message: 'success',
        data: {
          items: [
            { id: 1, name: '商品管理', code: 'goods:read', description: '查看商品' },
            { id: 2, name: '商品管理', code: 'goods:write', description: '编辑商品' },
            { id: 3, name: '采集管理', code: 'collect:read', description: '查看采集任务' },
            { id: 4, name: '采集管理', code: 'collect:write', description: '创建采集任务' },
            { id: 5, name: '系统管理', code: 'admin:ops', description: '运维操作' },
          ],
          total: 5,
        },
      })
    }, 300)
  })
}

const mockHealth = () => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        code: 200,
        message: 'success',
        data: {
          status: 'healthy',
          components: {
            database: { status: 'up', latency_ms: 12 },
            cache: { status: 'up', latency_ms: 3 },
            queue: { status: 'up', latency_ms: 8 },
          },
          uptime: 86400,
          version: '1.0.0',
        },
      })
    }, 200)
  })
}

const mockSchema = () => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        code: 200,
        data: { $schema: 'http://json-schema.org/draft-07/schema#', type: 'object', properties: {} },
      })
    }, 300)
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
 * 死信队列列表（接口27）
 * GET /api/ops/dead-letter/
 * @param {Object} params - { queue?, page, page_size }
 */
export const getDeadLetterList = (params) =>
  USE_MOCK ? mockDeadLetterList(params) : request.get('/api/ops/dead-letter/', { params })

/**
 * 重新处理死信消息（接口27）
 * POST /api/ops/dead-letter/{id}/retry/
 * @param {number} id
 */
export const retryDeadLetter = (id) =>
  USE_MOCK
    ? Promise.resolve({ code: 200, message: '已重新加入队列' })
    : request.post(`/api/ops/dead-letter/${id}/retry/`)

/**
 * 审计日志列表（接口28）
 * GET /api/ops/audit/
 * @param {Object} params - { user?, action?, start_date?, end_date?, page, page_size }
 */
export const getAuditLog = (params) =>
  USE_MOCK ? mockAuditLog(params) : request.get('/api/ops/audit/', { params })

/**
 * 权限列表（接口29）
 * GET /api/ops/permissions/
 */
export const getPermissionList = () =>
  USE_MOCK ? mockPermissionList() : request.get('/api/ops/permissions/')

/**
 * 健康检查（接口31）
 * GET /api/health/
 */
export const healthCheck = () =>
  USE_MOCK ? mockHealth() : request.get('/api/health/')

/**
 * OpenAPI Schema（接口32）
 * GET /api/schema/
 */
export const getSchema = () =>
  USE_MOCK ? mockSchema() : request.get('/api/schema/')

/**
 * Swagger UI（接口33）
 * 返回 Swagger 地址
 */
export const getSwaggerUrl = () => `${import.meta.env.VITE_API_BASE_URL || ''}/api/docs`

/**
 * Redoc（接口34）
 * 返回 Redoc 地址
 */
export const getRedocUrl = () => `${import.meta.env.VITE_API_BASE_URL || ''}/api/redoc`

export default {
  getDeadLetterList,
  retryDeadLetter,
  getAuditLog,
  getPermissionList,
  healthCheck,
  getSchema,
  getSwaggerUrl,
  getRedocUrl,
}
