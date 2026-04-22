// 合规预检 composable
// 提供商品合规性检查功能
import { ref } from 'vue'

/**
 * 合规预检配置
 * @returns {{
 *   preCheck: function(message: string): { pass: boolean, errors: string[], warnings: string[] },
 *   setEnabled: function(enabled: boolean): void
 * }}
 */
export function useCompliance() {
  // 合规规则开关（可由用户控制）
  const enabled = ref(true)

  /**
   * 对商品信息进行合规预检
   * @param {string} message - 商品标题/描述等文本
   * @returns {{ pass: boolean, errors: string[], warnings: string[] }}
   */
  function preCheck(message) {
    if (!enabled.value) {
      return { pass: true, errors: [], warnings: [] }
    }

    const errors = []
    const warnings = []

    // 示例规则（实际项目中替换为真实业务规则）
    // 确保 message 是字符串再做处理
    const msg = typeof message === 'string' ? message : JSON.stringify(message || '')
    if (!msg.trim()) {
      errors.push('商品信息不能为空')
    }

    if (msg.length > 5000) {
      warnings.push('商品信息过长，可能被平台截断')
    }

    return {
      pass: errors.length === 0,
      errors,
      warnings,
    }
  }

  function setEnabled(val) {
    enabled.value = val
  }

  return { preCheck, setEnabled, enabled }
}
