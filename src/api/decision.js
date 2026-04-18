/**
 * 选品决策 API
 */

const USE_MOCK = true  // 开发阶段使用 Mock

// ===================== Mock 数据 =====================
const MOCK_PRODUCTS = [
  { id: 1, sku: 'SW001', name: '女士泳装-比基尼款', cost_price: 45, freight: 8, commission_rate: 0.08 },
  { id: 2, sku: 'SW002', name: '女士泳装-连体款', cost_price: 68, freight: 10, commission_rate: 0.08 },
  { id: 3, sku: 'ST001', name: '沙滩玩具套装', cost_price: 28, freight: 12, commission_rate: 0.06 },
  { id: 4, sku: 'SW003', name: '儿童泳装-卡通款', cost_price: 35, freight: 8, commission_rate: 0.07 },
  { id: 5, sku: 'ST002', name: '沙滩帐篷-便携款', cost_price: 89, freight: 25, commission_rate: 0.05 },
]

const mockSearchProducts = (keyword) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      const results = MOCK_PRODUCTS.filter(p =>
        p.sku.toLowerCase().includes(keyword.toLowerCase()) ||
        p.name.toLowerCase().includes(keyword.toLowerCase())
      )
      resolve({ code: 200, data: results })
    }, 300)
  })
}

const mockCalculate = (params) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      const { product_id, promotion_cost = 0, expected_gmv = 0 } = params
      const product = MOCK_PRODUCTS.find(p => p.id === product_id) || MOCK_PRODUCTS[0]
      
      // 固定成本 = 采购价 + 运费
      const fixed_cost = product.cost_price + product.freight
      // 变量成本 = 平台佣金
      const variable_cost = expected_gmv * product.commission_rate
      // 总投入 = 宣传费 + 固定成本 + 变量成本
      const total_investment = promotion_cost + fixed_cost + variable_cost
      // ROAS = 预估收入 / 总投入
      const roas = total_investment > 0 ? expected_gmv / total_investment : 0
      
      // 决策标签
      let decision = 'high_risk'
      let decisionText = '高风险'
      let decisionType = 'danger'
      
      if (roas >= 3 && roas <= 5) {
        decision = 'healthy'
        decisionText = '健康/推荐'
        decisionType = 'success'
      } else if (roas > 5) {
        decision = 'hot_potential'
        decisionText = '爆款潜力'
        decisionType = 'warning'
      }
      
      resolve({
        code: 200,
        data: {
          product_id: product.id,
          product_name: product.name,
          sku: product.sku,
          cost_price: product.cost_price,
          freight: product.freight,
          commission_rate: product.commission_rate,
          promotion_cost,
          expected_gmv,
          estimated_revenue: expected_gmv,
          fixed_cost,
          variable_cost,
          total_investment,
          roas: Math.round(roas * 100) / 100,
          decision,
          decision_text: decisionText,
          decision_type: decisionType,
        },
      })
    }, 500)
  })
}

// ===================== 真实接口 =====================
import axios from '@/utils/request'

export const searchProducts = (keyword) =>
  USE_MOCK ? mockSearchProducts(keyword) : axios.get('/api/v1/products/', { params: { search: keyword } })

export const calculateDecision = (params) =>
  USE_MOCK ? mockCalculate(params) : axios.post('/api/v1/decision/calculate/', params)

export default { searchProducts, calculateDecision }
