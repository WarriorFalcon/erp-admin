<template>
  <div class="login-page">
    <!-- 背景装饰 -->
    <div class="login-bg">
      <div class="bg-shape shape-1"></div>
      <div class="bg-shape shape-2"></div>
      <div class="bg-shape shape-3"></div>
    </div>

    <!-- 登录卡片 -->
    <div class="login-card">
      <!-- Logo区 -->
      <div class="login-logo">
        <img src="@/assets/logo.png" alt="辽宁跨境宝盒" class="logo-img" />
        <h1 class="logo-title">辽宁跨境宝盒</h1>
        <p class="logo-subtitle">跨境电商ERP管理系统</p>
      </div>

      <!-- 表单 -->
      <el-form
        ref="formRef"
        :model="loginForm"
        :rules="rules"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="phone">
          <el-input
            v-model="loginForm.phone"
            placeholder="请输入手机号"
            size="large"
            :prefix-icon="Phone"
            clearable
          />
        </el-form-item>

        <el-form-item prop="code">
          <el-input
            v-model="loginForm.code"
            placeholder="请输入验证码"
            size="large"
            :prefix-icon="Message"
            maxlength="6"
            style="width: calc(100% - 130px)"
          >
            <template #append>
              <el-button 
                :disabled="countdown > 0" 
                @click="handleSendCode"
                class="send-code-btn"
              >
                {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
              </el-button>
            </template>
          </el-input>
        </el-form-item>

        <div class="form-options">
          <el-checkbox v-model="rememberMe">记住手机号</el-checkbox>
        </div>

        <el-button
          type="primary"
          size="large"
          :loading="loading"
          class="login-btn"
          @click="handleLogin"
        >
          登 录
        </el-button>
      </el-form>

      <!-- 底部 -->
      <div class="login-footer">
        <span class="footer-text">还没有账号？</span>
        <el-link type="primary" :underline="false">联系管理员开通</el-link>
      </div>
    </div>

    <!-- 版本信息 -->
    <div class="version-info">
      <span>v1.0.0</span>
      <span class="divider">|</span>
      <span>跨境电商ERP系统</span>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Phone, Message } from '@element-plus/icons-vue'
// MOCK模式：不使用真实API
// import { login, sendSmsCode, verifySmsCode } from '@/api/auth'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const rememberMe = ref(false)
const countdown = ref(0)
let countdownTimer = null

const loginForm = reactive({
  phone: '',
  code: '',
})

const rules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' },
  ],
  code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { pattern: /^\d{6}$/, message: '验证码为6位数字', trigger: 'blur' },
  ],
}

// 发送验证码（MOCK模式）
async function handleSendCode() {
  if (countdown.value > 0) return
  
  // 验证手机号格式
  const phonePattern = /^1[3-9]\d{9}$/
  
  if (!loginForm.phone || !phonePattern.test(loginForm.phone)) {
    ElMessage.warning('请输入正确的手机号')
    return
  }
  
  // MOCK：模拟发送成功
  ElMessage.success(`验证码已发送：123456`)
  
  // 自动填充验证码（方便演示）
  loginForm.code = '123456'
  
  // 开始倒计时
  countdown.value = 60
  countdownTimer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(countdownTimer)
    }
  }, 1000)
}

// 登录（MOCK模式）
async function handleLogin() {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    
    // MOCK：模拟登录延迟
    await new Promise(resolve => setTimeout(resolve, 800))
    
    // MOCK：固定验证码 123456
    if (loginForm.code !== '123456') {
      ElMessage.error('验证码错误，演示码：123456')
      loading.value = false
      return
    }
    
    // MOCK：生成假 token
    const mockToken = 'mock_token_' + Date.now()
    localStorage.setItem('access_token', mockToken)
    localStorage.setItem('refresh_token', mockToken + '_refresh')
    localStorage.setItem('user_phone', loginForm.phone)
    
    if (rememberMe.value) {
      localStorage.setItem('remembered_phone', loginForm.phone)
    }
    
    ElMessage.success('登录成功')
    router.push('/')
    loading.value = false
  })
}

// 页面加载时恢复记住的手机号
const savedPhone = localStorage.getItem('remembered_phone')
if (savedPhone) {
  loginForm.phone = savedPhone
  rememberMe.value = true
}

// 组件卸载时清理定时器
onUnmounted(() => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
  }
})
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #f1f5f9 100%);
  position: relative;
  overflow: hidden;
}

/* 背景装饰 - 蓝绿配色 */
.login-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.bg-shape {
  position: absolute;
  border-radius: 50%;
  opacity: 0.1;
}

.shape-1 {
  width: 600px;
  height: 600px;
  background: #085B9C;
  top: -200px;
  right: -100px;
}

.shape-2 {
  width: 400px;
  height: 400px;
  background: #2ead3e;
  bottom: -150px;
  left: -100px;
}

.shape-3 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, #085B9C 0%, #2ead3e 100%);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

/* 登录卡片 */
.login-card {
  position: relative;
  z-index: 10;
  width: 400px;
  background: #fff;
  border-radius: 16px;
  padding: 48px 40px;
  box-shadow: 
    0 4px 6px -1px rgba(0, 0, 0, 0.05),
    0 10px 15px -3px rgba(0, 0, 0, 0.08),
    0 20px 25px -5px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

/* 顶部蓝绿装饰条 */
.login-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #085B9C 0%, #2ead3e 100%);
}

/* Logo区 */
.login-logo {
  text-align: center;
  margin-bottom: 32px;
}

.logo-img {
  width: 80px;
  height: 80px;
  object-fit: contain;
  margin: 0 auto 16px;
  border-radius: 16px;
}

.logo-title {
  font-size: 22px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 6px;
  letter-spacing: -0.02em;
}

.logo-subtitle {
  font-size: 13px;
  color: #64748b;
  margin: 0;
}

/* 表单 */
.login-form {
  margin-top: 8px;
}

.login-form :deep(.el-input__wrapper) {
  border-radius: 10px;
  box-shadow: 0 0 0 1px #e2e8f0;
  transition: all 0.2s;
}

.login-form :deep(.el-input__wrapper:hover),
.login-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px #085B9C;
}

.login-form :deep(.el-input__prefix) {
  color: #94a3b8;
}

.login-form :deep(.el-input-group__append) {
  border-radius: 0 10px 10px 0;
  padding: 0;
  border-left: none;
}

.login-form :deep(.el-input__wrapper:has(.el-input-group__append)) {
  border-radius: 10px 0 0 10px;
}

.send-code-btn {
  height: 38px;
  padding: 0 16px;
  font-size: 13px;
  color: #085B9C;
  font-weight: 500;
  background: transparent;
  border: none;
  white-space: nowrap;
}

.send-code-btn:not(:disabled):hover {
  color: #2ead3e;
  background: #f0fff4;
}

.send-code-btn:disabled {
  color: #94a3b8;
  cursor: not-allowed;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.form-options :deep(.el-checkbox__label) {
  color: #64748b;
  font-size: 13px;
}

.login-btn {
  width: 100%;
  height: 44px;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.05em;
  background: linear-gradient(135deg, #085B9C 0%, #2ead3e 100%);
  border: none;
  box-shadow: 0 4px 14px rgba(8, 91, 156, 0.3);
  transition: all 0.2s;
}

.login-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(8, 91, 156, 0.4);
}

.login-btn:active {
  transform: translateY(0);
}

/* 底部 */
.login-footer {
  margin-top: 28px;
  text-align: center;
  padding-top: 24px;
  border-top: 1px solid #f1f5f9;
}

.footer-text {
  color: #64748b;
  font-size: 13px;
}

/* 版本信息 */
.version-info {
  position: absolute;
  bottom: 24px;
  color: #94a8b8;
  font-size: 12px;
  display: flex;
  gap: 8px;
}

.version-info .divider {
  color: #cbd5e1;
}
</style>
