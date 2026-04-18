/**
 * 阿里云短信服务封装
 * 文档: https://help.aliyun.com/document_detail/101414.html
 */

import axios from 'axios'

// ===================== 配置 =====================
const USE_MOCK = true  // 开发模式：开启 mock

// 阿里云短信配置（密钥通过后端接口获取，这里仅作类型提示）
const SMS_CONFIG = {
  accessKeyId: 'LTAI5tCyx4TmSJzQmXAmicjX',      // RAM 用户 AccessKey ID
  accessKeySecret: '',  // Secret 从后端获取，不暴露在前端
  signName: '',         // 短信签名（待配置）
  endpoint: 'https://dysmsapi.aliyuncs.com',
  apiVersion: '2017-05-25',
}

// ===================== Mock 数据 =====================
const MOCK_CODES = new Map() // 存储模拟验证码

function generateCode() {
  return String(Math.floor(Math.random() * 900000) + 100000) // 6位数字
}

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

// ===================== 核心接口 =====================

/**
 * 发送短信验证码
 * @param {string} phone - 手机号（如 +8613800138000 或 13800138000）
 * @param {string} templateCode - 短信模板 CODE
 * @param {object} templateParam - 模板参数（如 { code: '123456' }）
 * @returns {Promise<{success: boolean, message: string, requestId: string}>}
 */
export async function sendSmsCode(phone, templateCode, templateParam = {}) {
  if (USE_MOCK) {
    await delay(1000 + Math.random() * 500)
    
    // Mock：生成验证码并存储
    const code = generateCode()
    const normalizedPhone = phone.replace(/^\+86/, '')
    MOCK_CODES.set(normalizedPhone, {
      code,
      expireAt: Date.now() + 5 * 60 * 1000, // 5分钟过期
    })
    
    console.log(`[MOCK SMS] 验证码已发送至 ${phone}: ${code}`)
    
    return {
      success: true,
      message: '发送成功',
      requestId: `mock-${Date.now()}`,
      mockCode: code, // 开发时方便查看
    }
  }

  // 真实调用：通过后端转发（密钥不应暴露在前端）
  const res = await axios.post('/api/sms/send/', {
    phone,
    template_code: templateCode,
    template_param: templateParam,
  })
  
  return {
    success: res.data?.Code === 'OK',
    message: res.data?.Message || '发送成功',
    requestId: res.data?.RequestId,
  }
}

/**
 * 发送验证码（简化版，自动使用默认模板）
 * @param {string} phone - 手机号
 * @returns {Promise<{success: boolean, message: string}>}
 */
export async function sendVerificationCode(phone) {
  // 统一手机号格式
  const normalizedPhone = phone.startsWith('+') ? phone : `+86${phone}`
  
  // 调用通用发送接口
  return sendSmsCode(normalizedPhone, 'SMS_DEFAULT', { code: generateCode() })
}

/**
 * 验证短信验证码
 * @param {string} phone - 手机号
 * @param {string} code - 用户输入的验证码
 * @returns {Promise<{valid: boolean, message: string}>}
 */
export async function verifySmsCode(phone, code) {
  if (USE_MOCK) {
    await delay(300)
    
    const normalizedPhone = phone.replace(/^\+86/, '')
    const record = MOCK_CODES.get(normalizedPhone)
    
    if (!record) {
      return { valid: false, message: '验证码不存在，请先获取' }
    }
    
    if (Date.now() > record.expireAt) {
      MOCK_CODES.delete(normalizedPhone)
      return { valid: false, message: '验证码已过期，请重新获取' }
    }
    
    if (record.code !== code) {
      return { valid: false, message: '验证码错误' }
    }
    
    // 验证成功后删除
    MOCK_CODES.delete(normalizedPhone)
    return { valid: true, message: '验证成功' }
  }

  // 真实调用
  const res = await axios.post('/api/sms/verify/', {
    phone,
    code,
  })
  
  return {
    valid: res.data?.valid || false,
    message: res.data?.message || '验证失败',
  }
}

/**
 * 查询短信发送状态
 * @param {string} phone - 手机号
 * @param {string} sendDate - 发送日期（YYYYMMDD）
 * @returns {Promise<Array>}
 */
export async function querySmsStatus(phone, sendDate) {
  if (USE_MOCK) {
    return [{
      PhoneNum: phone,
      SendStatus: 2, // 2=成功
      ErrCode: 'OK',
      TemplateCode: 'SMS_DEFAULT',
      ReceiveDate: new Date().toISOString(),
      SendDate: sendDate,
    }]
  }

  const res = await axios.get('/api/sms/query/', {
    params: { phone, send_date: sendDate },
  })
  
  return res.data?.SmsSendDetailDTOs?.SmsSendDetailDTO || []
}

/**
 * 批量发送短信（订单通知等）
 * @param {Array<{phone: string, param: object}>} batch - 批量数据
 * @param {string} templateCode - 模板CODE
 * @returns {Promise<{success: boolean, results: Array}>}
 */
export async function sendBatchSms(batch, templateCode) {
  if (USE_MOCK) {
    await delay(1000)
    return {
      success: true,
      results: batch.map((item, index) => ({
        phone: item.phone,
        success: true,
        messageId: `mock-batch-${index}`,
      })),
    }
  }

  const res = await axios.post('/api/sms/send-batch/', {
    batch,
    template_code: templateCode,
  })
  
  return res.data
}

export default {
  sendSmsCode,
  sendVerificationCode,
  verifySmsCode,
  querySmsStatus,
  sendBatchSms,
}
