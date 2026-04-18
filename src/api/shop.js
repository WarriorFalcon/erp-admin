/**
 * 店铺管理 API
 * 包含平台授权列表、店铺信息等
 */

const platforms = [
  { name: '1688', code: '1688', color: '#F55D23', icon: '🟠' },
  { name: 'TikTok Shop', code: 'tiktok', color: '#00f2ea', icon: '🎵' },
  { name: 'Amazon', code: 'amazon', color: '#FF9900', icon: '🟠' },
  { name: 'eBay', code: 'ebay', color: '#E53238', icon: '🔴' },
  { name: 'Shopee', code: 'shopee', color: '#EE4D2D', icon: '🔴' },
]

const shopStatuses = [
  { label: '已授权', value: 'active', type: 'success' },
  { label: '授权待验证', value: 'pending', type: 'warning' },
  { label: '授权过期', value: 'expired', type: 'danger' },
  { label: '未授权', value: 'inactive', type: 'info' },
]

const mockShops = [
  { id: 1, name: '1688官方旗舰店', platformName: '1688', platformCode: '1688', color: '#F55D23', icon: '🟠', ...shopStatuses[0], account: 'seller_123456', bindTime: '2026-01-15', products: 234, todayOrders: 12 },
  { id: 2, name: '1688分销店', platformName: '1688', platformCode: '1688', color: '#F55D23', icon: '🟠', ...shopStatuses[0], account: 'dist_789012', bindTime: '2026-02-20', products: 87, todayOrders: 5 },
  { id: 3, name: 'TK美国本土店', platformName: 'TikTok Shop', platformCode: 'tiktok', color: '#00f2ea', icon: '🎵', ...shopStatuses[0], account: 'tk_us_store', bindTime: '2026-03-01', products: 156, todayOrders: 28 },
  { id: 4, name: 'TK英国店', platformName: 'TikTok Shop', platformCode: 'tiktok', color: '#00f2ea', icon: '🎵', ...shopStatuses[1], account: 'tk_uk_store', bindTime: '2026-03-10', products: 42, todayOrders: 0 },
  { id: 5, name: 'Amazon美国站', platformName: 'Amazon', platformCode: 'amazon', color: '#FF9900', icon: '🟠', ...shopStatuses[0], account: 'amaz_us_001', bindTime: '2026-01-20', products: 312, todayOrders: 19 },
  { id: 6, name: 'Amazon英国站', platformName: 'Amazon', platformCode: 'amazon', color: '#FF9900', icon: '🟠', ...shopStatuses[2], account: 'amaz_uk_002', bindTime: '2025-11-10', products: 88, todayOrders: 0 },
  { id: 7, name: 'eBay澳大利亚站', platformName: 'eBay', platformCode: 'ebay', color: '#E53238', icon: '🔴', ...shopStatuses[0], account: 'ebay_au', bindTime: '2026-02-05', products: 65, todayOrders: 7 },
  { id: 8, name: 'Shopee马来西亚站', platformName: 'Shopee', platformCode: 'shopee', color: '#EE4D2D', icon: '🔴', ...shopStatuses[3], account: 'shp_my', bindTime: '', products: 0, todayOrders: 0 },
]

/**
 * 获取店铺列表
 */
export function getShopList() {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ code: 0, data: mockShops })
    }, 300)
  })
}

/**
 * 获取平台授权 URL（OAuth 跳转地址）
 */
export function getAuthUrl(platformCode) {
  return new Promise((resolve) => {
    setTimeout(() => {
      // Mock OAuth URL（开发测试用，实际由后端返回真实授权链接）
      // 点击后在新窗口打开，开发阶段用于演示授权流程
      const mockUrls = {
        '1688': 'https://login.1688.com/auth/authorize?sellerId=demo',
        'tiktok': 'https://www.tiktok.com/v2/auth/authorize',
        'amazon': 'https://sellercentral.amazon.com/apps/authorize/consent',
        'ebay': 'https://auth.ebay.com/oauth2/authorize',
        'shopee': 'https://partner.shopeemobile.com/api/v1/shop/authorize',
      }
      resolve({ code: 0, data: { url: mockUrls[platformCode] || '' } })
    }, 200)
  })
}

/**
 * 刷新授权
 */
export function refreshAuth(shopId) {
  return new Promise((resolve) => {
    setTimeout(() => resolve({ code: 0, message: '刷新授权成功' }), 300)
  })
}

/**
 * 解绑店铺
 */
export function unbindShop(shopId) {
  return new Promise((resolve) => {
    setTimeout(() => resolve({ code: 0, message: '解绑成功' }), 300)
  })
}
