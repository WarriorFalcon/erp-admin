/**
 * 选品决策状态管理
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { searchProducts, calculateDecision } from '@/api/decision'

export const useDecisionStore = defineStore('decision', () => {
  // 当前选中的商品
  const currentProduct = ref(null)
  
  // 搜索结果列表
  const searchResults = ref([])
  
  // 用户调节的参数
  const calcParams = ref({
    promotion_cost: 1000,    // 预期宣传费用
    expected_gmv: 5000,      // 预估GMV
  })
  
  // 最近一次计算结果
  const lastResult = ref(null)
  
  // 加载状态
  const loading = ref(false)
  const calculating = ref(false)
  
  // 搜索商品（防抖由组件处理）
  async function search(keyword) {
    if (!keyword?.trim()) {
      searchResults.value = []
      return
    }
    loading.value = true
    try {
      const res = await searchProducts(keyword)
      searchResults.value = res.data || []
      
      // 如果API返回空，使用Mock数据演示
      if (searchResults.value.length === 0) {
        searchResults.value = getMockProducts(keyword)
      }
    } catch (e) {
      console.error('搜索失败，使用Mock数据', e)
      searchResults.value = getMockProducts(keyword)
    } finally {
      loading.value = false
    }
  }
  
  // Mock商品数据（用于演示）
  function getMockProducts(keyword) {
    const mockProducts = [
      { id: 1, sku: 'SKU001', name: '女士连体泳装 修身显瘦海边度假温泉游泳衣', cost_price: 45.00, freight: 8.00, commission_rate: 0.15 },
      { id: 2, sku: 'SKU002', name: '儿童沙滩玩具套装 挖沙铲桶组合', cost_price: 28.50, freight: 5.00, commission_rate: 0.12 },
      { id: 3, sku: 'SKU003', name: '男士速干泳裤 专业运动训练游泳装备', cost_price: 35.00, freight: 6.00, commission_rate: 0.14 },
      { id: 4, sku: 'SKU004', name: '防晒沙滩巾 超大吸水速干浴巾', cost_price: 52.00, freight: 7.00, commission_rate: 0.13 },
      { id: 5, sku: 'SKU005', name: '浮潜面镜套装 防雾潜水镜呼吸管', cost_price: 68.00, freight: 9.00, commission_rate: 0.16 },
      { id: 6, sku: 'SKU006', name: '充气游泳圈 加厚安全儿童救生圈', cost_price: 22.00, freight: 4.50, commission_rate: 0.11 },
      { id: 7, sku: 'SKU007', name: '防水手机袋 触屏拍照游泳潜水套', cost_price: 15.00, freight: 3.00, commission_rate: 0.10 },
      { id: 8, sku: 'SKU008', name: '沙滩遮阳伞 户外防晒便携折叠伞', cost_price: 88.00, freight: 12.00, commission_rate: 0.18 },
    ]
    
    // 根据关键词过滤
    const lowerKeyword = keyword.toLowerCase()
    return mockProducts.filter(p => 
      p.name.toLowerCase().includes(lowerKeyword) ||
      p.sku.toLowerCase().includes(lowerKeyword)
    )
  }
  
  // 选择商品
  function selectProduct(product) {
    currentProduct.value = product
    // 重置参数
    calcParams.value = {
      promotion_cost: 1000,
      expected_gmv: 5000,
    }
    lastResult.value = null
  }
  
  // 执行测算
  async function calculate() {
    if (!currentProduct.value) return
    calculating.value = true
    try {
      const res = await calculateDecision({
        product_id: currentProduct.value.id,
        ...calcParams.value,
      })
      lastResult.value = res.data
      return res.data
    } catch (e) {
      console.error('测算失败，使用本地计算', e)
      // 本地计算ROAS
      lastResult.value = calculateLocal()
      return lastResult.value
    } finally {
      calculating.value = false
    }
  }
  
  // 本地计算ROAS（Mock模式）
  function calculateLocal() {
    const product = currentProduct.value
    const { promotion_cost, expected_gmv } = calcParams.value
    
    // 计算成本
    const fixed_cost = product.cost_price + product.freight
    const commission = expected_gmv * product.commission_rate
    const variable_cost = commission
    const total_investment = fixed_cost + promotion_cost + variable_cost
    
    // 计算收入（假设毛利率30%）
    const gross_margin_rate = 0.30
    const estimated_revenue = expected_gmv * gross_margin_rate
    
    // 计算ROAS
    const roas = total_investment > 0 ? (estimated_revenue / total_investment) : 0
    
    // 决策建议
    let decision_text, decision_type
    if (roas < 3) {
      decision_text = '高风险'
      decision_type = 'danger'
    } else if (roas <= 5) {
      decision_text = '推荐'
      decision_type = 'success'
    } else {
      decision_text = '爆款潜力'
      decision_type = 'warning'
    }
    
    return {
      roas: parseFloat(roas.toFixed(2)),
      estimated_revenue: Math.round(estimated_revenue),
      total_investment: parseFloat(total_investment.toFixed(2)),
      fixed_cost: parseFloat(fixed_cost.toFixed(2)),
      variable_cost: parseFloat(variable_cost.toFixed(2)),
      promotion_cost: parseFloat(promotion_cost.toFixed(2)),
      decision_text,
      decision_type,
    }
  }
  
  // 重置
  function reset() {
    currentProduct.value = null
    searchResults.value = []
    calcParams.value = {
      promotion_cost: 1000,
      expected_gmv: 5000,
    }
    lastResult.value = null
  }
  
  return {
    currentProduct,
    searchResults,
    calcParams,
    lastResult,
    loading,
    calculating,
    search,
    selectProduct,
    calculate,
    reset,
  }
})
