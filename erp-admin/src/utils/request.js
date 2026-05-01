/**
 * axios 请求封装
 * 所有 API 请求统一通过此模块发出
 *
 * 规范：
 * - baseURL 从 .env 的 VITE_API_BASE_URL 读取，绝不写死地址
 * - 自动附加 Authorization token
 * - 401 时自动尝试 refresh token 续期
 * - 统一错误处理，弹出 ElMessage 提示
 * - 响应 data 透传，直接拿到业务数据
 */

import axios from 'axios'
import { ElMessage } from 'element-plus'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000,
  withCredentials: false,
})

// ── Token 刷新状态管理 ──
let isRefreshing = false
let failedQueue = []

function processQueue(error, token = null) {
  failedQueue.forEach(prom => {
    if (error) prom.reject(error)
    else prom.resolve(token)
  })
  failedQueue = []
}

function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  // 只跳转一次，避免重复触发
  if (window.location.pathname !== '/login') {
    window.location.href = '/login'
  }
}

async function tryRefreshToken() {
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) return null

  try {
    // 用裸 axios 请求，避免进入本拦截器死循环
    const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
    const res = await axios.post(`${baseURL}/api/auth/refresh`, {
      refresh_token: refreshToken,
    }, { timeout: 10000 })

    const payload = res.data
    // 兼容两种响应格式: { code:200, data:{ access_token, refresh_token } }
    // 或 { access_token, refresh_token }
    const data = payload?.data || payload
    if (data?.access_token) {
      localStorage.setItem('access_token', data.access_token)
      if (data.refresh_token) {
        localStorage.setItem('refresh_token', data.refresh_token)
      }
      return data.access_token
    }
    return null
  } catch (e) {
    return null
  }
}

// ==================== 请求拦截器 ====================
service.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ==================== 响应拦截器 ====================
service.interceptors.response.use(
  (response) => {
    return response.data
  },
  async (error) => {
    const originalRequest = error.config

    // ── 401 处理：尝试 Token 自动刷新 ──
    if (error.response?.status === 401 && !originalRequest._retry) {
      // 不要对 refresh 请求本身重试
      if (originalRequest.url?.includes('/api/auth/refresh')) {
        logout()
        return Promise.reject(error)
      }

      if (isRefreshing) {
        // 已有刷新在进行中，将请求加入等待队列
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(token => {
          originalRequest.headers['Authorization'] = `Bearer ${token}`
          return service(originalRequest)
        }).catch(err => {
          return Promise.reject(err)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const newToken = await tryRefreshToken()
        if (newToken) {
          processQueue(null, newToken)
          originalRequest.headers['Authorization'] = `Bearer ${newToken}`
          return service(originalRequest)
        } else {
          processQueue(new Error('refresh failed'), null)
          ElMessage.error('登录已过期，请重新登录')
          logout()
          return Promise.reject(error)
        }
      } catch (refreshError) {
        processQueue(refreshError, null)
        ElMessage.error('登录已过期，请重新登录')
        logout()
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    // ── 通用错误处理 ──
    let message = '请求失败，请稍后重试'
    if (error.response) {
      const { status, data } = error.response
      switch (status) {
        case 400:
          message = data?.detail || data?.message || '请求参数错误'
          break
        case 401:
          message = '登录已过期，请重新登录'
          break
        case 403:
          message = '没有权限执行此操作'
          break
        case 404:
          message = '请求的资源不存在'
          break
        case 422:
          message = data?.detail || '数据验证失败'
          break
        case 500:
          message = '服务器内部错误，请联系管理员'
          break
        default:
          message = data?.detail || data?.message || `请求失败 (${status})`
      }
    } else if (error.request) {
      message = '网络连接失败，请检查网络'
    } else {
      message = error.message || '请求配置错误'
    }

    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default service
