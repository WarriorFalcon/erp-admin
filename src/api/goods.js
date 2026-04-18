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
