/**
 * 订单管理 API
 * MOCK 模式 - 用于演示
 */

const mockOrders = [
  { orderId: 'TK20260416001', platform: 'TikTok', buyerName: 'John Smith', buyerPhone: '+1-555-0123', sku: 'SKU-A001', quantity: 2, amount: 89.99, status: 'completed', statusLabel: '已完成', statusType: 'success', orderTime: '2026-04-15 14:30', paidTime: '2026-04-15 14:32', address: 'Los Angeles, CA 90001, USA', trackingNo: 'SF1234567890', carrier: '顺丰速运', buyerNote: 'Please deliver before 6pm', items: [{ name: '无线蓝牙耳机', sku: 'SKU-A001', price: 44.99, qty: 2, image: 'https://via.placeholder.com/60' }], logs: [{ time: '2026-04-15 14:30', action: '创建订单', operator: 'System', type: 'primary' }, { time: '2026-04-15 14:32', action: '支付成功', operator: 'Payment', type: 'success' }, { time: '2026-04-16 09:00', action: '签收完成', operator: 'System', type: 'success' }] },
  { orderId: 'AM20260416002', platform: 'Amazon', buyerName: 'Emma Wilson', buyerPhone: '+44-20-1234-5678', sku: 'SKU-B023', quantity: 1, amount: 156.50, status: 'paid', statusLabel: '待发货', statusType: 'warning', orderTime: '2026-04-16 09:15', paidTime: '2026-04-16 09:18', address: 'London, W1A 1AA, UK', trackingNo: '', carrier: '', buyerNote: '', items: [{ name: '智能手表Pro', sku: 'SKU-B023', price: 156.50, qty: 1, image: 'https://via.placeholder.com/60' }], logs: [{ time: '2026-04-16 09:15', action: '创建订单', operator: 'System', type: 'primary' }, { time: '2026-04-16 09:18', action: '支付成功', operator: 'Payment', type: 'success' }] },
  { orderId: 'SP20260416003', platform: 'Shopee', buyerName: '林小明', buyerPhone: '+60-12-345-6789', sku: 'SKU-C105', quantity: 3, amount: 67.50, status: 'pending', statusLabel: '待审核', statusType: 'info', orderTime: '2026-04-16 10:00', paidTime: '', address: 'Kuala Lumpur, Malaysia', trackingNo: '', carrier: '', buyerNote: '颜色选错了，想要白色', items: [{ name: '手机壳透明款', sku: 'SKU-C105', price: 22.50, qty: 3, image: 'https://via.placeholder.com/60' }], logs: [{ time: '2026-04-16 10:00', action: '创建订单', operator: 'System', type: 'primary' }] },
  { orderId: 'TK20260416004', platform: 'TikTok', buyerName: 'Sarah Connor', buyerPhone: '+1-555-0456', sku: 'SKU-A002', quantity: 1, amount: 299.00, status: 'exception', statusLabel: '物流异常', statusType: 'danger', orderTime: '2026-04-14 11:20', paidTime: '2026-04-14 11:25', address: 'Chicago, IL 60601, USA', trackingNo: 'YT9876543210', carrier: '圆通速递', buyerNote: '', items: [{ name: '便携充电宝20000mAh', sku: 'SKU-A002', price: 299.00, qty: 1, image: 'https://via.placeholder.com/60' }], logs: [{ time: '2026-04-14 11:20', action: '创建订单', operator: 'System', type: 'primary' }, { time: '2026-04-14 11:25', action: '支付成功', operator: 'Payment', type: 'success' }, { time: '2026-04-15 08:00', action: '发货', operator: 'Admin', type: 'warning' }, { time: '2026-04-16 10:00', action: '物流异常：地址不详', operator: 'System', type: 'danger' }] },
  { orderId: 'AM20260416005', platform: 'Amazon', buyerName: '张伟', buyerPhone: '+1-408-555-7890', sku: 'SKU-D088', quantity: 5, amount: 445.00, status: 'completed', statusLabel: '已完成', statusType: 'success', orderTime: '2026-04-13 16:45', paidTime: '2026-04-13 16:50', address: 'San Francisco, CA 94102, USA', trackingNo: 'SF2345678901', carrier: '顺丰速运', buyerNote: '', items: [{ name: '瑜伽垫加厚款', sku: 'SKU-D088', price: 89.00, qty: 5, image: 'https://via.placeholder.com/60' }], logs: [{ time: '2026-04-13 16:45', action: '创建订单', operator: 'System', type: 'primary' }, { time: '2026-04-13 16:50', action: '支付成功', operator: 'Payment', type: 'success' }, { time: '2026-04-15 12:00', action: '签收完成', operator: 'System', type: 'success' }] },
  { orderId: 'SP20260416006', platform: 'Shopee', buyerName: 'Ahmad Razali', buyerPhone: '+62-812-3456-7890', sku: 'SKU-E112', quantity: 2, amount: 138.00, status: 'paid', statusLabel: '待发货', statusType: 'warning', orderTime: '2026-04-16 08:30', paidTime: '2026-04-16 08:35', address: 'Jakarta, Indonesia', trackingNo: '', carrier: '', buyerNote: '急单，请尽快发货', items: [{ name: '迷你加湿器USB', sku: 'SKU-E112', price: 69.00, qty: 2, image: 'https://via.placeholder.com/60' }], logs: [{ time: '2026-04-16 08:30', action: '创建订单', operator: 'System', type: 'primary' }, { time: '2026-04-16 08:35', action: '支付成功', operator: 'Payment', type: 'success' }] },
  { orderId: 'TK20260416007', platform: 'TikTok', buyerName: 'Maria Garcia', buyerPhone: '+34-612-345-678', sku: 'SKU-F205', quantity: 1, amount: 520.00, status: 'pending', statusLabel: '待审核', statusType: 'info', orderTime: '2026-04-16 11:00', paidTime: '', address: 'Madrid, Spain', trackingNo: '', carrier: '', buyerNote: '', items: [{ name: '电动牙刷超声波', sku: 'SKU-F205', price: 520.00, qty: 1, image: 'https://via.placeholder.com/60' }], logs: [{ time: '2026-04-16 11:00', action: '创建订单', operator: 'System', type: 'primary' }] },
  { orderId: 'AM20260416008', platform: 'Amazon', buyerName: '王芳', buyerPhone: '+1-650-555-3210', sku: 'SKU-G301', quantity: 1, amount: 1280.00, status: 'paid', statusLabel: '待发货', statusType: 'warning', orderTime: '2026-04-15 20:00', paidTime: '2026-04-15 20:05', address: 'Seattle, WA 98101, USA', trackingNo: '', carrier: '', buyerNote: '礼物，请精美包装', items: [{ name: '智能音箱旗舰版', sku: 'SKU-G301', price: 1280.00, qty: 1, image: 'https://via.placeholder.com/60' }], logs: [{ time: '2026-04-15 20:00', action: '创建订单', operator: 'System', type: 'primary' }, { time: '2026-04-15 20:05', action: '支付成功', operator: 'Payment', type: 'success' }] },
]

export function getOrderList(params = {}) {
  return new Promise((resolve) => {
    setTimeout(() => {
      let data = [...mockOrders]
      if (params.keyword) {
        const kw = params.keyword.toLowerCase()
        data = data.filter(o => o.orderId.toLowerCase().includes(kw) || o.buyerName.toLowerCase().includes(kw) || o.sku.toLowerCase().includes(kw))
      }
      if (params.platform) data = data.filter(o => o.platform === params.platform)
      if (params.status) data = data.filter(o => o.status === params.status)
      const total = data.length
      const start = ((params.page || 1) - 1) * (params.pageSize || 10)
      resolve({ code: 200, data: { results: data.slice(start, start + (params.pageSize || 10)), total } })
    }, 300)
  })
}

export function getOrderStatusCounts() {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        code: 200,
        data: {
          pending: mockOrders.filter(o => o.status === 'pending').length,
          paid: mockOrders.filter(o => o.status === 'paid').length,
          exception: mockOrders.filter(o => o.status === 'exception').length,
          completed: mockOrders.filter(o => o.status === 'completed').length,
        }
      })
    }, 200)
  })
}

export function getOrderDetail(id) {
  return new Promise((resolve) => {
    setTimeout(() => {
      const order = mockOrders.find(o => o.orderId === id)
      resolve({ code: 200, data: order })
    }, 200)
  })
}

export function confirmOrder(id) {
  return Promise.resolve({ code: 200, message: '确认成功' })
}

export function shipOrder(id, data) {
  return Promise.resolve({ code: 200, message: '发货成功' })
}

export function cancelOrder(id, reason) {
  return Promise.resolve({ code: 200, message: '取消成功' })
}

export function addOrderRemark(id, remark) {
  return Promise.resolve({ code: 200, message: '备注添加成功' })
}

export function exportOrders(params) {
  return Promise.resolve({ code: 200, message: '导出任务已创建' })
}

export function updateOrderStatus(id, status) {
  return Promise.resolve({ code: 200, message: '状态更新成功' })
}
