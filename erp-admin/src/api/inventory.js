/**
 * 库存管理 API
 * 连接到后端真实数据库操作
 */
import request from '@/utils/request'

/**
 * 库存列表
 * GET /api/goods/
 * @param {Object} params - { page, page_size, platform?, keyword?, status? }
 */
export function getInventoryList(params = {}) {
  return request.get('/api/goods/', { params })
}

/**
 * 库存预警
 * GET /api/inventory/alerts
 * @param {Object} params - { threshold? }
 */
export function getInventoryAlerts(params = {}) {
  return request.get('/api/inventory/alerts', { params })
}

/**
 * SKU 详情
 * GET /api/sku/detail/{skuCode}/
 * @param {string} sku - SKU 编码
 */
export function getSkuDetail(sku) {
  return request.get(`/api/sku/detail/${sku}/`)
}

/**
 * 手动触发库存同步
 * POST /api/inventory/sync
 */
export function triggerInventorySync() {
  return request.post('/api/inventory/sync')
}

/**
 * 库存同步日志
 * GET /api/inventory/logs
 */
export function getInventoryLogs(params = {}) {
  return request.get('/api/inventory/logs', { params })
}

/**
 * 库存调整 - 通过 SKU 更新接口
 * PUT /api/sku/bulk-update/
 * @param {Object} data - 批量更新数据
 */
export function adjustInventory(data) {
  return request.put('/api/sku/bulk-update/', data)
}

/**
 * 库存概览统计
 * 通过多个接口组合取得
 */
export function getInventoryOverview() {
  return Promise.all([
    request.get('/api/goods/', { params: { page: 1, page_size: 1 } }),
    request.get('/api/inventory/alerts', { params: { threshold: 0 } }),
  ]).then(([goodsRes, alertsRes]) => {
    const totalSku = goodsRes?.data?.total || goodsRes?.count || 0
    const totalStock = goodsRes?.data?.results?.reduce?.((sum, i) => sum + (i.stock || 0), 0) || 0
    const alerts = alertsRes?.data?.results || []
    const alertCount = alertsRes?.data?.count || alerts.length || 0
    const outOfStockCount = alerts.filter(i => (i.stock || 0) <= 0).length

    return {
      code: 200,
      data: {
        total_sku: totalSku,
        total_stock: totalStock,
        alert_count: alertCount,
        out_of_stock_count: outOfStockCount,
      },
    }
  })
}

/**
 * 仓库列表（目前从前端内置，后续可从后端获取）
 */
export function getWarehouseList() {
  return request.get('/api/shops/').then(res => ({
    code: 200,
    data: res?.data || ['深圳仓', '广州仓', '海外仓(英国)'],
  })).catch(() => ({
    code: 200,
    data: ['深圳仓', '广州仓', '海外仓(英国)'],
  }))
}
