/**
 * 商品管理 API
 * 接口前缀：/api/v1/goods/
 */

import request from '@/utils/request'

const USE_MOCK = false  // 生产模式

// Mock
const mockGoodsList = () =>
  Promise.resolve({
    data: [],
    total: 0,
  })

/** 商品列表 */
export function fetchGoodsList(params) {
  if (USE_MOCK) return mockGoodsList()
  return request.get('/api/v1/goods/list', { params })
}

/** 商品详情 */
export function fetchGoodsDetail(id) {
  if (USE_MOCK) return Promise.resolve({ data: {} })
  return request.get(`/api/v1/goods/detail/${id}/`)
}

/** 上架商品到目标平台
 * POST /api/v1/goods/listing/
 * @param {Object} payload - { goods_id, platform, title, description, price, images }
 */
export function listingGoods(payload) {
  if (USE_MOCK) {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          code: 0,
          message: '上架成功',
          data: {
            platform: payload.platform,
            item_id: `item_${Date.now()}`,
            url: `https://${payload.platform}.com/item/${Date.now()}`,
            status: 'published',
          },
        })
      }, 1200)
    })
  }
  return request.post('/api/v1/goods/listing/', payload)
}

/** 批量上架
 * POST /api/v1/goods/listing/batch/
 */
export function listingGoodsBatch(payload) {
  if (USE_MOCK) {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          code: 0,
          message: '批量上架任务已创建',
          data: {
            task_id: `batch_${Date.now()}`,
            total: payload.items?.length || 0,
          },
        })
      }, 800)
    })
  }
  return request.post('/api/v1/goods/listing/batch/', payload)
}
