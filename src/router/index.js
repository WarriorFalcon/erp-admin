import { createRouter, createWebHistory } from 'vue-router'

// 跨境ERP路由配置
// 所有页面使用懒加载（路由级代码分割）
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { title: '登录', hideLayout: true },
    },
    {
      path: '/',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { title: '控制台', icon: 'Odometer' },
    },
    {
      path: '/dashboard',
      redirect: '/',
    },
    // ==================== 商品模块 ====================
    {
      path: '/goods/collect',
      name: 'goods-collect',
      component: () => import('@/views/goods/CollectView.vue'),
      meta: { title: '商品采集', icon: 'ShoppingCart' },
    },
    {
      path: '/goods/manage',
      name: 'goods-manage',
      component: () => import('@/views/goods/ManageView.vue'),
      meta: { title: '商品管理', icon: 'Goods' },
    },
    {
      path: '/goods/listing',
      name: 'goods-listing',
      component: () => import('@/views/goods/ListingView.vue'),
      meta: { title: '商品上货', icon: 'Upload' },
    },
    {
      path: '/goods/onestop',
      name: 'goods-onestop',
      component: () => import('@/views/goods/OneStopView.vue'),
      meta: { title: '一站式采集上货', icon: 'MagicStick' },
    },
    {
      path: '/goods/decision',
      name: 'goods-decision',
      component: () => import('@/views/goods/DecisionView.vue'),
      meta: { title: '选品决策', icon: 'DataAnalysis' },
    },
    // ==================== 订单模块 ====================
    {
      path: '/orders',
      name: 'orders',
      component: () => import('@/views/orders/ListView.vue'),
      meta: { title: '订单管理', icon: 'List' },
    },
    // ==================== 库存模块 ====================
    {
      path: '/inventory',
      name: 'inventory',
      component: () => import('@/views/inventory/IndexView.vue'),
      meta: { title: '库存管理', icon: 'Box' },
    },
    // ==================== 物流模块 ====================
    {
      path: '/logistics',
      name: 'logistics',
      component: () => import('@/views/logistics/IndexView.vue'),
      meta: { title: '物流追踪', icon: 'Van' },
    },
    // ==================== 店铺模块 ====================
    {
      path: '/shop',
      name: 'shop',
      component: () => import('@/views/shop/IndexView.vue'),
      meta: { title: '店铺管理', icon: 'Shop' },
    },
    // ==================== 达人检索 ====================
    {
      path: '/kol',
      name: 'kol',
      component: () => import('@/views/kol/Dashboard.vue'),
      meta: { title: '达人检索', icon: 'User' },
    },
    // ==================== 数据报表 ====================
    {
      path: '/reports',
      name: 'reports',
      component: () => import('@/views/reports/IndexView.vue'),
      meta: { title: '数据报表', icon: 'DataLine' },
    },
    // ==================== 插件市场（P2） ====================
    {
      path: '/plugins',
      name: 'plugins',
      component: () => import('@/views/plugins/IndexView.vue'),
      meta: { title: '插件市场', icon: 'Grid' },
    },
  ],
})

// 全局路由守卫：页面标题 + 登录拦截
router.beforeEach((to, from) => {
  // 更新页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - 辽宁跨境宝盒`
  }
  
  // 登录页：若已登录则直接跳转工作台
  if (to.path === '/login') {
    const token = localStorage.getItem('access_token')
    if (token) return '/'
    return true
  }
  
  // 其他页面：检查登录状态
  const token = localStorage.getItem('access_token')
  if (!token) {
    return '/login'
  }
  return true
})

export default router
