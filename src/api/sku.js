/**
 * SKU 管理 API
 * 接口前缀：/api/v1/sku/
 */
import request from '@/utils/request'

const USE_MOCK = false  // 生产模式

const delay = (ms = 600) => new Promise(r => setTimeout(r, ms))

const mockSkuList = () =>
  delay().then(() => ({
    code: 0,
    data: [
      { id: 'SKU001', name: '女士纯棉T恤-白色-M', sku_code: 'CLO-T-WHT-M', barcode: '6931024012345', price: 49.5, cost: 22.0, stock: 200, platform: '1688', status: 'active', created_at: '2026-04-10' },
      { id: 'SKU002', name: '女士纯棉T恤-黑色-M', sku_code: 'CLO-T-BLK-M', barcode: '6931024012346', price: 49.5, cost: 22.0, stock: 150, platform: '1688', status: 'active', created_at: '2026-04-10' },
      { id: 'SKU003', name: '无线蓝牙耳机-黑色', sku_code: 'ELEC-BT-BLK', barcode: '6901234567890', price: 128.0, cost: 55.0, stock: 45, platform: 'Amazon', status: 'active', created_at: '2026-04-09' },
      { id: 'SKU004', name: '运动休闲裤-灰色-L', sku_code: 'CLO-PT-GRY-L', barcode: '', price: 89.0, cost: 38.0, stock: 8, platform: '1688', status: 'warning', created_at: '2026-04-08' },
      { id: 'SKU005', name: '防晒霜SPF50-50ml', sku_code: 'BEAU-SPF50-50', barcode: '', price: 65.0, cost: 28.0, stock: 0, platform: 'TikTok', status: 'offline', created_at: '2026-04-07' },
    ],
    total: 5,
  }))

const mockSkuDetail = (id) =>
  delay().then(() => ({
    code: 0,
    data: {
      id,
      name: '女士纯棉T恤-白色-M',
      sku_code: 'CLO-T-SHT-WHT-M',
      barcode: '6931024012345',
      price: 49.5,
      cost: 22.0,
      stock: 200,
      platform: '1688',
      source_url: 'https://detail.1688.com/offer/123456.html',
      images: ['https://via.placeholder.com/400x400/667eea/ffffff?text=SKU图片'],
      attributes: { color: '白色', size: 'M', material: '纯棉' },
      status: 'active',
      created_at: '2026-04-10T10:00:00Z',
      updated_at: '2026-04-10T18:00:00Z',
    },
  }))

/**
 * SKU 列表
 * GET /api/v1/sku/list/
 */
export function fetchSkuList(params) {
  if (USE_MOCK) return mockSkuList()
  return request.get('/api/v1/sku/list/', { params })
}

/**
 * SKU 详情
 * GET /api/v1/sku/{id}/
 */
export function fetchSkuDetail(id) {
  if (USE_MOCK) return mockSkuDetail(id)
  return request.get(`/api/v1/sku/${id}/`)
}

/**
 * SKU 创建
 * POST /api/v1/sku/
 */
export function createSku(data) {
  if (USE_MOCK) return delay().then(() => ({ code: 0, message: '创建成功', data: { id: `SKU${Date.now()}`, ...data } }))
  return request.post('/api/v1/sku/', data)
}

/**
 * SKU 更新
 * PUT /api/v1/sku/{id}/
 */
export function updateSku(id, data) {
  if (USE_MOCK) return delay().then(() => ({ code: 0, message: '更新成功' }))
  return request.put(`/api/v1/sku/${id}/`, data)
}

/**
 * SKU 删除
 * DELETE /api/v1/sku/{id}/
 */
export function deleteSku(id) {
  if (USE_MOCK) return delay().then(() => ({ code: 0, message: '删除成功' }))
  return request.delete(`/api/v1/sku/${id}/`)
}

/**
 * SKU 批量删除
 * POST /api/v1/sku/batch/delete/
 */
export function batchDeleteSku(ids) {
  if (USE_MOCK) return delay().then(() => ({ code: 0, message: `已删除 ${ids.length} 条` }))
  return request.post('/api/v1/sku/batch/delete/', { ids })
}

/**
 * SKU 批量上架
 * POST /api/v1/sku/batch/online/
 */
export function batchOnlineSku(ids) {
  if (USE_MOCK) return delay().then(() => ({ code: 0, message: `已上架 ${ids.length} 条` }))
  return request.post('/api/v1/sku/batch/online/', { ids })
}

/**
 * SKU 批量下架
 * POST /api/v1/sku/batch/offline/
 */
export function batchOfflineSku(ids) {
  if (USE_MOCK) return delay().then(() => ({ code: 0, message: `已下架 ${ids.length} 条` }))
  return request.post('/api/v1/sku/batch/offline/', { ids })
}

/**
 * SKU 导入
 * POST /api/v1/sku/import/
 */
export function importSku(file) {
  if (USE_MOCK) return delay(1500).then(() => ({ code: 0, message: '导入成功', data: { success: 98, failed: 2 } }))
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/api/v1/sku/import/', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
}

/**
 * SKU 导出
 * POST /api/v1/sku/export/
 */
export function exportSku(params) {
  if (USE_MOCK) return delay(1000).then(() => ({ code: 0, message: '导出任务已创建', data: { task_id: `exp_${Date.now()}` } }))
  return request.post('/api/v1/sku/export/', {}, { params })
}

/**
 * SKU 搜索
 * GET /api/v1/sku/search/
 */
export function searchSku(keyword) {
  if (USE_MOCK) return delay().then(() => ({ code: 0, data: [{ id: 'SKU001', name: `搜索结果: ${keyword}` }] }))
  return request.get('/api/v1/sku/search/', { params: { keyword } })
}
