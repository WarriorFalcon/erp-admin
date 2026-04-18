/**
 * axios 请求封装
 * 所有 API 请求统一通过此模块发出
 *
 * 规范：
 * - baseURL 从 .env 的 VITE_API_BASE_URL 读取，绝不写死地址
 * - 自动附加 Authorization token
 * - 统一错误处理，弹出 ElMessage 提示
 * - 响应 data 透传，直接拿到业务数据
 */

import axios from 'axios'
import { ElMessage } from 'element-plus'

const service = axios.create({
  // Vite 环境变量：VITE_API_BASE_URL 在 .env 中配置
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000,
  // 允许携带跨域 cookie
  withCredentials: false,
})

// ==================== 请求拦截器 ====================
service.interceptors.request.use(
  (config) => {
    // 从 localStorage 读取 token，自动附加到 Header
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// ==================== 响应拦截器 ====================
service.interceptors.response.use(
  (response) => {
    // 直接返回 data，调用方不需要 response.data.xxx
    return response.data
  },
  (error) => {
    // 统一错误处理
    let message = '请求失败，请稍后重试'

    if (error.response) {
      const { status, data } = error.response
      switch (status) {
        case 400:
          message = data?.detail || data?.message || '请求参数错误'
          break
        case 401:
          message = '登录已过期，请重新登录'
          // 可选：自动跳转登录页
          // window.location.href = '/login'
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
