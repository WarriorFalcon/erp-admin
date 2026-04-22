// 一站式上货状态管理
import { defineStore } from 'pinia'
import { ref } from 'vue'

// 定价规则模板
export const PRICING_TEMPLATES = [
  { id: 'normal', label: '普通定价', rate: 1.5 },
  { id: 'promotion', label: '活动价', rate: 1.3 },
  { id: 'premium', label: '高端定价', rate: 2.0 },
  { id: 'cost_plus', label: '成本加成', rate: 1.2 },
]

export const useOneStopStore = defineStore('oneStop', () => {
  // 当前上货任务列表
  const taskList = ref([])

  // 上货结果
  const listingResults = ref([])

  // 批量模式开关
  const batchMode = ref(false)

  // 当前选中的定价模板
  const activePricingTemplate = ref('normal')

  // AI 评估结果 { [goodsId]: { grade, profit, reason, platformFit } }
  const aiEvaluations = ref({})

  // 应用定价模板
  function applyPricingTemplate(id) {
    activePricingTemplate.value = id
  }

  // 计算单个商品利润
  function calcProfit(goods) {
    const cost = parseFloat(goods.cost || goods.cost_price || 0)
    const freight = parseFloat(goods.freight || 0)
    const tpl = PRICING_TEMPLATES.find(t => t.id === activePricingTemplate.value) || PRICING_TEMPLATES[0]
    const salePrice = cost * tpl.rate
    const profit = salePrice - cost - freight
    const profitRate = cost > 0 ? (profit / cost) * 100 : 0
    return {
      cost,
      freight,
      salePrice,
      profit,
      profitRate,
      template: tpl.label,
      rate: tpl.rate,
    }
  }

  // 评估商品等级
  function evaluateGoods(goods) {
    const profit = calcProfit(goods)
    let grade = 'okay'
    let reason = '符合基本要求'

    if (profit.profit < 5) {
      grade = 'not_recommended'
      reason = `利润过低（仅 ¥${profit.profit.toFixed(2)}），扣除运费后几乎无盈利空间`
    } else if (profit.profit >= 20 && profit.profitRate >= 30) {
      grade = 'recommend'
      reason = `利润空间良好（¥${profit.profit.toFixed(2)}），毛利率 ${profit.profitRate.toFixed(1)}%，建议优先上架`
    } else if (profit.profit >= 10) {
      grade = 'okay'
      reason = '利润处于合理区间，可以上架'
    } else {
      grade = 'okay'
      reason = '建议适当提高定价倍率以提升利润空间'
    }

    // 平台适配性评估
    const platformFit = {}
    const platforms = ['tiktok', 'shopee', 'temu', 'shein', 'amazon']
    platforms.forEach(p => {
      if (profit.profitRate >= 40) platformFit[p] = 'high'
      else if (profit.profitRate >= 20) platformFit[p] = 'medium'
      else platformFit[p] = 'low'
    })

    aiEvaluations.value[goods.id] = { grade, profit, reason, platformFit }
    return aiEvaluations.value[goods.id]
  }

  // 批量评估商品
  function evaluateBatch(goodsList) {
    return goodsList.map(g => evaluateGoods(g))
  }

  return {
    taskList,
    listingResults,
    batchMode,
    activePricingTemplate,
    aiEvaluations,
    applyPricingTemplate,
    calcProfit,
    evaluateGoods,
    evaluateBatch,
    PRICING_TEMPLATES,
  }
})
