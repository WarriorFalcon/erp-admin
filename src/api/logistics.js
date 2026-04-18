/**
 * 物流追踪 API
 * MOCK 模式 - 用于演示
 */

const mockShipments = [
  { waybillNo: 'SF1234567890', orderId: 'TK20260416001', carrier: '顺丰速运', carrierIcon: '📦', from: '深圳', to: '洛杉矶', currentLoc: '洛杉矶中转站', fee: 158, status: 'transit', statusLabel: '运输中', statusType: 'primary', lastUpdate: '2026-04-16 08:30', tracks: [{ time: '2026-04-14 10:00', status: '已揽收', location: '深圳福田营业部', nodeType: 'success', nodeColor: '#22C55E' }, { time: '2026-04-14 18:00', status: '离开深圳', location: '深圳转运中心', nodeType: 'primary', nodeColor: '#3B82F6' }, { time: '2026-04-15 06:00', status: '到达香港', location: '香港国际机场', nodeType: 'primary', nodeColor: '#3B82F6' }, { time: '2026-04-16 08:30', status: '清关中', location: '洛杉矶海关', nodeType: 'warning', nodeColor: '#F59E0B', isTimeout: true }] },
  { waybillNo: 'YT9876543210', orderId: 'TK20260416004', carrier: '圆通速递', carrierIcon: '📮', from: '广州', to: '芝加哥', currentLoc: '地址不详，滞留', fee: 186, status: 'exception', statusLabel: '异常', statusType: 'danger', lastUpdate: '2026-04-16 10:00', exceptionReason: '收件地址不详，无法派送', tracks: [{ time: '2026-04-15 08:00', status: '已揽收', location: '广州白云区', nodeType: 'success', nodeColor: '#22C55E' }, { time: '2026-04-15 20:00', status: '到达广州中心', location: '广州转运中心', nodeType: 'primary', nodeColor: '#3B82F6' }, { time: '2026-04-16 10:00', status: '异常', location: '待核实地址', nodeType: 'danger', nodeColor: '#EF4444' }] },
  { waybillNo: 'DHL20260415A1', orderId: 'AM20260416002', carrier: 'DHL', carrierIcon: '✈️', from: '深圳', to: '伦敦', currentLoc: '伦敦配送站', fee: 268, status: 'delivering', statusLabel: '派送中', statusType: 'warning', lastUpdate: '2026-04-16 09:15', tracks: [{ time: '2026-04-13 10:00', status: '已揽收', location: '深圳仓库', nodeType: 'success', nodeColor: '#22C55E' }, { time: '2026-04-13 22:00', status: '离开深圳', location: '深圳宝安机场', nodeType: 'primary', nodeColor: '#3B82F6' }, { time: '2026-04-14 14:00', status: '到达伦敦', location: '伦敦希思罗机场', nodeType: 'primary', nodeColor: '#3B82F6' }, { time: '2026-04-15 08:00', status: '清关完成', location: '伦敦海关', nodeType: 'success', nodeColor: '#22C55E' }, { time: '2026-04-16 09:15', status: '派送中', location: '伦敦配送站', nodeType: 'warning', nodeColor: '#F59E0B' }] },
  { waybillNo: 'ZT7654321098', orderId: 'SP20260416003', carrier: '中通快递', carrierIcon: '📬', from: '杭州', to: '吉隆坡', currentLoc: '吉隆坡仓库', fee: 98, status: 'delivered', statusLabel: '已签收', statusType: 'success', lastUpdate: '2026-04-15 16:30', tracks: [{ time: '2026-04-12 09:00', status: '已揽收', location: '杭州萧山', nodeType: 'success', nodeColor: '#22C55E' }, { time: '2026-04-13 12:00', status: '离开杭州', location: '杭州转运中心', nodeType: 'primary', nodeColor: '#3B82F6' }, { time: '2026-04-14 18:00', status: '到达吉隆坡', location: '吉隆坡国际机场', nodeType: 'primary', nodeColor: '#3B82F6' }, { time: '2026-04-15 14:00', status: '派送中', location: '吉隆坡配送站', nodeType: 'primary', nodeColor: '#3B82F6' }, { time: '2026-04-15 16:30', status: '已签收', location: '收件人签收', nodeType: 'success', nodeColor: '#22C55E' }] },
  { waybillNo: 'SF3456789012', orderId: 'AM20260416005', carrier: '顺丰速运', carrierIcon: '📦', from: '深圳', to: '旧金山', currentLoc: '旧金山网点', fee: 198, status: 'delivering', statusLabel: '派送中', statusType: 'warning', lastUpdate: '2026-04-16 07:45', tracks: [{ time: '2026-04-13 14:00', status: '已揽收', location: '深圳南山', nodeType: 'success', nodeColor: '#22C55E' }, { time: '2026-04-14 08:00', status: '离开深圳', location: '深圳转运中心', nodeType: 'primary', nodeColor: '#3B82F6' }, { time: '2026-04-15 10:00', status: '清关完成', location: '旧金山海关', nodeType: 'success', nodeColor: '#22C55E' }, { time: '2026-04-16 07:45', status: '派送中', location: '旧金山网点', nodeType: 'warning', nodeColor: '#F59E0B' }] },
  { waybillNo: 'YD6789012345', orderId: 'SP20260416006', carrier: '韵达快递', carrierIcon: '📭', from: '广州', to: '雅加达', currentLoc: '广州待发出', fee: 76, status: 'pending', statusLabel: '待揽收', statusType: 'info', lastUpdate: '2026-04-16 08:00', tracks: [{ time: '2026-04-16 08:00', status: '待揽收', location: '广州白云区', nodeType: 'info', nodeColor: '#94A3B8' }] },
  { waybillNo: 'DHL20260416B2', orderId: 'AM20260416008', carrier: 'DHL', carrierIcon: '✈️', from: '深圳', to: '西雅图', currentLoc: '深圳机场', fee: 288, status: 'transit', statusType: 'primary', lastUpdate: '2026-04-16 11:00', tracks: [{ time: '2026-04-15 20:00', status: '已揽收', location: '深圳仓库', nodeType: 'success', nodeColor: '#22C55E' }, { time: '2026-04-16 11:00', status: '运输中', location: '深圳宝安机场', nodeType: 'primary', nodeColor: '#3B82F6' }] },
]

export function getShipmentList(params = {}) {
  return new Promise((resolve) => {
    setTimeout(() => {
      let data = [...mockShipments]
      if (params.keyword) {
        const kw = params.keyword.toLowerCase()
        data = data.filter(s => s.waybillNo.toLowerCase().includes(kw) || s.orderId.toLowerCase().includes(kw))
      }
      if (params.carrier) data = data.filter(s => s.carrier === params.carrier)
      if (params.status) data = data.filter(s => s.status === params.status)
      const total = data.length
      const start = ((params.page || 1) - 1) * (params.pageSize || 10)
      resolve({ code: 200, data: { results: data.slice(start, start + (params.pageSize || 10)), total } })
    }, 300)
  })
}

export function getLogisticsStats() {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        code: 200,
        data: {
          pending: mockShipments.filter(s => s.status === 'pending').length,
          transit: mockShipments.filter(s => s.status === 'transit').length,
          delivering: mockShipments.filter(s => s.status === 'delivering').length,
          delivered: mockShipments.filter(s => s.status === 'delivered').length,
          exception: mockShipments.filter(s => s.status === 'exception').length,
        }
      })
    }, 200)
  })
}

export function getShipmentTrack(waybillNo) {
  return new Promise((resolve) => {
    setTimeout(() => {
      const shipment = mockShipments.find(s => s.waybillNo === waybillNo)
      resolve({
        code: 200,
        data: {
          waybill_no: waybillNo,
          tracks: shipment?.tracks || []
        }
      })
    }, 200)
  })
}

export function syncLogistics(waybillNos = []) {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ code: 200, message: '同步成功', data: { updated: waybillNos.length || mockShipments.length } })
    }, 500)
  })
}

export function getCarrierList() {
  return Promise.resolve({
    code: 200,
    data: ['顺丰速运', '圆通速递', '中通快递', '韵达快递', 'DHL']
  })
}

export function subscribeTrack(waybillNo, callbackUrl) {
  return Promise.resolve({ code: 200, message: '订阅成功' })
}

export { getShipmentTrack as getTrack }
