/**
 * 库存管理 API
 * MOCK 模式 - 用于演示
 */

const mockInventory = [
  { skuId: 'SKU-A001', name: '无线蓝牙耳机Pro', warehouse: '深圳仓', warehouseClass: 'sz', stock: 245, available: 230, locked: 15, safeStock: 100, status: 'normal', statusType: 'success', statusLabel: '正常', lastIn: '2026-04-10', lastOut: '2026-04-15', alarmDays: 30, consumeRate: 8 },
  { skuId: 'SKU-B023', name: '智能手表运动版', warehouse: '深圳仓', warehouseClass: 'sz', stock: 45, available: 40, locked: 5, safeStock: 50, status: 'low', statusType: 'warning', statusLabel: '预警', lastIn: '2026-04-08', lastOut: '2026-04-16', alarmDays: 5, consumeRate: 9 },
  { skuId: 'SKU-C105', name: '手机壳透明款', warehouse: '广州仓', warehouseClass: 'gz', stock: 580, available: 550, locked: 30, safeStock: 200, status: 'normal', statusType: 'success', statusLabel: '正常', lastIn: '2026-04-12', lastOut: '2026-04-15', alarmDays: 58, consumeRate: 10 },
  { skuId: 'SKU-D088', name: '瑜伽垫加厚15mm', warehouse: '广州仓', warehouseClass: 'gz', stock: 0, available: 0, locked: 0, safeStock: 30, status: 'out', statusType: 'danger', statusLabel: '缺货', lastIn: '2026-03-28', lastOut: '2026-04-13', alarmDays: 0, consumeRate: 5 },
  { skuId: 'SKU-E112', name: '迷你加湿器USB', warehouse: '海外仓(英国)', warehouseClass: 'uk', stock: 89, available: 85, locked: 4, safeStock: 40, status: 'normal', statusType: 'success', statusLabel: '正常', lastIn: '2026-04-05', lastOut: '2026-04-14', alarmDays: 17, consumeRate: 5 },
  { skuId: 'SKU-F205', name: '电动牙刷超声波', warehouse: '深圳仓', warehouseClass: 'sz', stock: 23, available: 20, locked: 3, safeStock: 30, status: 'low', statusType: 'warning', statusLabel: '预警', lastIn: '2026-04-03', lastOut: '2026-04-16', alarmDays: 4, consumeRate: 6 },
  { skuId: 'SKU-G301', name: '智能音箱旗舰版', warehouse: '海外仓(英国)', warehouseClass: 'uk', stock: 15, available: 15, locked: 0, safeStock: 20, status: 'low', statusType: 'warning', statusLabel: '预警', lastIn: '2026-03-30', lastOut: '2026-04-12', alarmDays: 3, consumeRate: 5 },
  { skuId: 'SKU-H412', name: '便携充电宝20000mAh', warehouse: '广州仓', warehouseClass: 'gz', stock: 312, available: 300, locked: 12, safeStock: 150, status: 'normal', statusType: 'success', statusLabel: '正常', lastIn: '2026-04-14', lastOut: '2026-04-15', alarmDays: 26, consumeRate: 12 },
  { skuId: 'SKU-J556', name: '蓝牙音箱防水款', warehouse: '深圳仓', warehouseClass: 'sz', stock: 8, available: 8, locked: 0, safeStock: 25, status: 'out', statusType: 'danger', statusLabel: '缺货', lastIn: '2026-03-25', lastOut: '2026-04-10', alarmDays: 0, consumeRate: 4 },
  { skuId: 'SKU-K678', name: '数据线快充编织款', warehouse: '广州仓', warehouseClass: 'gz', stock: 890, available: 870, locked: 20, safeStock: 300, status: 'normal', statusType: 'success', statusLabel: '正常', lastIn: '2026-04-15', lastOut: '2026-04-16', alarmDays: 72, consumeRate: 12 },
]

const mockLogs = [
  { type: 'in', skuId: 'SKU-A001', quantity: 100, operator: '张竞祺', remark: '批量入库', date: '2026-04-10 14:30' },
  { type: 'out', skuId: 'SKU-B023', quantity: 15, operator: '系统', remark: '订单出库 TK20260415', date: '2026-04-15 10:20' },
  { type: 'in', skuId: 'SKU-D088', quantity: 50, operator: '张竞祺', remark: '供应商补货', date: '2026-04-08 09:00' },
  { type: 'out', skuId: 'SKU-H412', quantity: 8, operator: '系统', remark: '订单出库 AM20260415', date: '2026-04-15 16:45' },
  { type: 'out', skuId: 'SKU-C105', quantity: 20, operator: '系统', remark: '订单出库 SP20260414', date: '2026-04-14 11:30' },
  { type: 'in', skuId: 'SKU-K678', quantity: 200, operator: '张竞祺', remark: '新批次入库', date: '2026-04-15 08:00' },
]

export function getInventoryList(params = {}) {
  return new Promise((resolve) => {
    setTimeout(() => {
      let data = [...mockInventory]
      if (params.warehouse && params.warehouse !== 'all') {
        data = data.filter(i => i.warehouse === params.warehouse)
      }
      if (params.keyword) {
        const kw = params.keyword.toLowerCase()
        data = data.filter(i => i.skuId.toLowerCase().includes(kw) || i.name.toLowerCase().includes(kw))
      }
      if (params.status) data = data.filter(i => i.status === params.status)
      const total = data.length
      const start = ((params.page || 1) - 1) * (params.pageSize || 10)
      resolve({ code: 200, data: { results: data.slice(start, start + (params.pageSize || 10)), total } })
    }, 300)
  })
}

export function getInventoryAlerts() {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ code: 200, data: mockInventory.filter(i => i.status !== 'normal') })
    }, 200)
  })
}

export function getSkuDetail(sku) {
  return new Promise((resolve) => {
    setTimeout(() => {
      const item = mockInventory.find(i => i.skuId === sku)
      resolve({
        code: 200,
        data: {
          ...item,
          consumption_trend: Array.from({length: 7}, (_, i) => ({
            date: `2026-04-${10 + i}`,
            stock: Math.max(0, item.stock - item.consumeRate * (7 - i))
          }))
        }
      })
    }, 200)
  })
}

export function adjustInventory(data) {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ code: 200, message: '库存调整成功' })
    }, 300)
  })
}

export function getInventoryLogs(params = {}) {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ code: 200, data: { results: mockLogs, total: mockLogs.length } })
    }, 200)
  })
}

export function getInventoryOverview() {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        code: 200,
        data: {
          total_sku: new Set(mockInventory.map(i => i.skuId)).size,
          total_stock: mockInventory.reduce((sum, i) => sum + i.stock, 0),
          alert_count: mockInventory.filter(i => i.status !== 'normal').length,
          out_of_stock_count: mockInventory.filter(i => i.status === 'out').length
        }
      })
    }, 200)
  })
}

export function getWarehouseList() {
  return Promise.resolve({
    code: 200,
    data: ['深圳仓', '广州仓', '海外仓(英国)']
  })
}
