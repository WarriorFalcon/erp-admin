/**
 * 用户认证 API
 * 接口 22-24 + 短信验证码
 */

const USE_MOCK = true  // 临时开启 Mock 测试登录

// ===================== Mock 数据 =====================
const MOCK_USER = {
  id: 1,
  username: 'admin',
  phone: '13800138000',
  email: 'admin@example.com',
  nickname: '管理员',
  role: 'admin',
  avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=admin',
  permissions: ['*'],
}

const MOCK_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.mock_token'
const MOCK_REFRESH = 'refresh_mock_token_xxx'

// 存储 Mock 验证码（手机号 -> { code, expireAt }）
const MOCK_CODES = new Map()

// 生成6位验证码
function generateMockCode() {
  return String(Math.floor(Math.random() * 900000) + 100000)
}

// Mock 发送验证码
const mockSendSmsCode = (phone) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      const code = generateMockCode()
      MOCK_CODES.set(phone, {
        code,
        expireAt: Date.now() + 5 * 60 * 1000, // 5分钟过期
      })
      console.log(`[MOCK SMS] 验证码已发送至 ${phone}: ${code}`)
      resolve({
        code: 200,
        message: '发送成功',
        data: { requestId: `mock-${Date.now()}` },
      })
    }, 500)
  })
}

// Mock 验证验证码
const mockVerifySmsCode = (phone, code) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      const record = MOCK_CODES.get(phone)
      
      if (!record) {
        resolve({ code: 400, message: '验证码不存在，请先获取', valid: false })
        return
      }
      
      if (Date.now() > record.expireAt) {
        MOCK_CODES.delete(phone)
        resolve({ code: 400, message: '验证码已过期，请重新获取', valid: false })
        return
      }
      
      if (record.code !== code) {
        resolve({ code: 400, message: '验证码错误', valid: false })
        return
      }
      
      // 验证成功后删除
      MOCK_CODES.delete(phone)
      resolve({
        code: 200,
        message: '验证成功',
        valid: true,
        data: { valid: true },
      })
    }, 300)
  })
}

const mockLogin = (data) => {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      // 支持手机号+验证码登录
      if (data.phone && data.code) {
        const record = MOCK_CODES.get(data.phone)
        if (record && record.code === data.code && Date.now() <= record.expireAt) {
          MOCK_CODES.delete(data.phone)
          resolve({
            code: 200,
            message: '登录成功',
            data: {
              user: { ...MOCK_USER, phone: data.phone },
              access_token: MOCK_TOKEN,
              refresh_token: MOCK_REFRESH,
              expires_in: 3600,
            },
          })
        } else {
          resolve({ code: 401, message: '验证码错误或已过期' })
        }
        return
      }
      
      // 支持用户名+密码登录（兼容旧逻辑）
      if (data.username && data.password) {
        resolve({
          code: 200,
          message: '登录成功',
          data: {
            user: MOCK_USER,
            access_token: MOCK_TOKEN,
            refresh_token: MOCK_REFRESH,
            expires_in: 3600,
          },
        })
      } else {
        resolve({ code: 401, message: '用户名或密码错误' })
      }
    }, 600)
  })
}

const mockRegister = (data) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      if (data.username && data.email && data.password) {
        resolve({
          code: 200,
          message: '注册成功',
          data: {
            user: { ...MOCK_USER, username: data.username, email: data.email },
            access_token: MOCK_TOKEN,
            refresh_token: MOCK_REFRESH,
            expires_in: 3600,
          },
        })
      } else {
        resolve({ code: 400, message: '参数不完整' })
      }
    }, 800)
  })
}

const mockRefreshToken = (data) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        code: 200,
        message: '刷新成功',
        data: {
          access_token: MOCK_TOKEN + '_refreshed',
          expires_in: 3600,
        },
      })
    }, 300)
  })
}

const mockCurrentUser = () => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        code: 200,
        message: 'success',
        data: MOCK_USER,
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

// 请求拦截器：注入 JWT
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：处理 401 刷新 Token
request.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      try {
        const refresh = localStorage.getItem('refresh_token')
        if (!refresh) throw new Error('No refresh token')
        const res = await request.post('/api/auth/refresh', { refresh_token: refresh })
        localStorage.setItem('access_token', res.access_token)
        originalRequest.headers.Authorization = `Bearer ${res.access_token}`
        return request(originalRequest)
      } catch {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// ===================== API 函数 =====================

/**
 * 发送短信验证码
 * POST /api/auth/send-sms
 * @param {string} phone - 手机号
 */
export const sendSmsCode = (phone) =>
  USE_MOCK ? mockSendSmsCode(phone) : request.post('/api/auth/send-sms', { phone })

/**
 * 验证短信验证码
 * POST /api/auth/verify-sms
 * @param {string} phone - 手机号
 * @param {string} code - 验证码
 */
export const verifySmsCode = (phone, code) =>
  USE_MOCK ? mockVerifySmsCode(phone, code) : request.post('/api/auth/verify-sms', { phone, code })

/**
 * 用户注册
 * POST /api/auth/register
 * @param {Object} data - { username, email, password, nickname? }
 */
export const register = (data) =>
  USE_MOCK ? mockRegister(data) : request.post('/api/auth/register', data)

/**
 * 用户登录（支持手机号+验证码 或 用户名+密码）
 * POST /api/auth/login
 * @param {Object} data - { phone, code } 或 { username, password }
 */
export const login = (data) =>
  USE_MOCK ? mockLogin(data) : request.post('/api/auth/login', data)

/**
 * 刷新 Token
 * POST /api/auth/refresh
 * @param {Object} data - { refresh_token }
 */
export const refreshToken = (data) =>
  USE_MOCK ? mockRefreshToken(data) : request.post('/api/auth/refresh', data)

/**
 * 获取当前用户信息
 * GET /api/auth/me
 */
export const getCurrentUser = () =>
  USE_MOCK ? mockCurrentUser() : request.get('/api/auth/me')

export default { sendSmsCode, verifySmsCode, register, login, refreshToken, getCurrentUser }
