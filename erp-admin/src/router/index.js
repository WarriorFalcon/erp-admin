import { createRouter, createWebHistory } from 'vue-router'

// 跨境ERP路由配置
// 核心页面使用直接导入（避免开发环境懒加载切换空白），非核心页面保留懒加载
import DashboardView from '@/views/DashboardView.vue'
import LoginView from '@/views/LoginView.vue'
import OneStopView from '@/views/goods/OneStopView.vue'
import OrderListView from '@/views/orders/ListView.vue'
import ShopIndexView from '@/views/shop/IndexView.vue'
import ReportsIndexView from '@/views/reports/IndexView.vue'
import InventoryIndexView from '@/views/inventory/IndexView.vue'
import LogisticsIndexView from '@/views/logistics/IndexView.vue'
import CreatorSearchView from '@/views/creator/CreatorSearch.vue'
import CreatorBoardView from '@/views/creator/CreatorBoard.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { title: '登录', hideLayout: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { title: '注册', hideLayout: true },
    },
    {
      path: '/',
      name: 'dashboard',
      component: DashboardView,
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
      path: '/goods/hot',
      name: 'goods-hot',
      component: () => import('@/views/goods/HotProductsView.vue'),
      meta: { title: '爆品推荐', icon: 'Lightning' },
    },
    {
      path: '/goods/onestop',
      name: 'goods-onestop',
      component: OneStopView,
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
      component: OrderListView,
      meta: { title: '订单管理', icon: 'List' },
    },
    // ==================== 库存模块 ====================
    {
      path: '/inventory',
      name: 'inventory',
      component: InventoryIndexView,
      meta: { title: '库存管理', icon: 'Box' },
    },
    // ==================== 物流模块 ====================
    {
      path: '/logistics',
      name: 'logistics',
      component: LogisticsIndexView,
      meta: { title: '物流追踪', icon: 'Van' },
    },
    // ==================== 店铺模块 ====================
    {
      path: '/shop',
      name: 'shop',
      component: ShopIndexView,
      meta: { title: '店铺管理', icon: 'Shop' },
    },
    // ==================== 数据报表 ====================
    {
      path: '/reports',
      name: 'reports',
      component: ReportsIndexView,
      meta: { title: '数据报表', icon: 'DataLine' },
    },
    {
      path: '/settings/team',
      name: 'team',
      component: () => import('@/views/settings/TeamView.vue'),
      meta: { title: '团队管理', icon: 'User' },
    },
    {
      path: '/services/official',
      name: 'official-services',
      component: () => import('@/views/services/OfficialServicesView.vue'),
      meta: { title: '官方服务', icon: 'Stamp' },
    },
    // ==================== 达人模块 ====================
    {
      path: '/creator/search',
      name: 'creator-search',
      component: CreatorSearchView,
      meta: { title: '达人检索', icon: 'User' },
    },
    {
      path: '/creator/board',
      name: 'creator-board',
      component: CreatorBoardView,
      meta: { title: '达人看板', icon: 'DataBoard' },
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
