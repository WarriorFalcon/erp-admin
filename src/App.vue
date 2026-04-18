<template>
  <!-- 登录页：全屏展示 -->
  <RouterView v-if="route.meta.hideLayout" />

  <!-- 其他页面：带侧边栏布局 -->
  <el-container v-else class="layout-root">

    <!-- =============== 侧边栏 =============== -->
    <aside class="aside" :class="{ collapsed: isCollapse }">

      <!-- Logo -->
      <div class="logo-area">
        <img src="@/assets/logo.png" alt="辽宁跨境宝盒" class="logo-img" />
        <transition name="logo-fade">
          <span v-if="!isCollapse" class="logo-text">辽宁跨境宝盒</span>
        </transition>
      </div>

      <!-- 菜单 -->
      <nav class="nav-menu">

        <!-- 工作台 -->
        <div class="nav-section-label" v-if="!isCollapse">工作台</div>
        <div
          class="nav-item"
          :class="{ active: route.path === '/' }"
          @click="router.push('/')"
          :title="isCollapse ? '控制台' : ''"
        >
          <el-icon><Odometer /></el-icon>
          <span v-if="!isCollapse">控制台</span>
        </div>

        <!-- 商品 -->
        <div class="nav-section-label" v-if="!isCollapse">商品</div>
        <div class="nav-item" :class="{ active: route.path === '/goods/collect' }" @click="router.push('/goods/collect')" :title="isCollapse ? '商品采集' : ''">
          <el-icon><ShoppingCart /></el-icon>
          <span v-if="!isCollapse">商品采集</span>
        </div>
        <div class="nav-item" :class="{ active: route.path === '/goods/manage' }" @click="router.push('/goods/manage')" :title="isCollapse ? '商品管理' : ''">
          <el-icon><Management /></el-icon>
          <span v-if="!isCollapse">商品管理</span>
        </div>
        <div class="nav-item" :class="{ active: route.path === '/goods/listing' }" @click="router.push('/goods/listing')" :title="isCollapse ? '商品上货' : ''">
          <el-icon><Upload /></el-icon>
          <span v-if="!isCollapse">商品上货</span>
        </div>
        <div class="nav-item" :class="{ active: route.path === '/goods/decision' }" @click="router.push('/goods/decision')" :title="isCollapse ? '选品决策' : ''">
          <el-icon><DataAnalysis /></el-icon>
          <span v-if="!isCollapse">选品决策</span>
          <span v-if="!isCollapse" class="nav-badge">NEW</span>
        </div>

        <!-- 运营 -->
        <div class="nav-section-label" v-if="!isCollapse">运营</div>
        <div class="nav-item" :class="{ active: route.path === '/orders' }" @click="router.push('/orders')" :title="isCollapse ? '订单管理' : ''">
          <el-icon><List /></el-icon>
          <span v-if="!isCollapse">订单管理</span>
        </div>
        <div class="nav-item" :class="{ active: route.path === '/inventory' }" @click="router.push('/inventory')" :title="isCollapse ? '库存管理' : ''">
          <el-icon><Box /></el-icon>
          <span v-if="!isCollapse">库存管理</span>
        </div>
        <div class="nav-item" :class="{ active: route.path === '/logistics' }" @click="router.push('/logistics')" :title="isCollapse ? '物流追踪' : ''">
          <el-icon><Van /></el-icon>
          <span v-if="!isCollapse">物流追踪</span>
        </div>
        <div class="nav-item" :class="{ active: route.path === '/shop' }" @click="router.push('/shop')" :title="isCollapse ? '店铺管理' : ''">
          <el-icon><Shop /></el-icon>
          <span v-if="!isCollapse">店铺管理</span>
        </div>

        <!-- 达人 -->
        <div class="nav-section-label" v-if="!isCollapse">达人</div>
        <div class="nav-item" :class="{ active: route.path === '/kol' }" @click="router.push('/kol')" :title="isCollapse ? '达人检索' : ''">
          <el-icon><User /></el-icon>
          <span v-if="!isCollapse">达人检索</span>
          <span v-if="!isCollapse" class="nav-badge">NEW</span>
        </div>
        <div class="nav-item" :class="{ active: route.path === '/reports' }" @click="router.push('/reports')" :title="isCollapse ? '数据报表' : ''">
          <el-icon><DataLine /></el-icon>
          <span v-if="!isCollapse">数据报表</span>
        </div>

        <!-- 待接入 -->
        <div class="nav-divider" />
        <div class="nav-item disabled" :title="isCollapse ? 'AI客服（待接入）' : ''">
          <el-icon><ChatDotRound /></el-icon>
          <span v-if="!isCollapse">AI 客服</span>
          <span v-if="!isCollapse" class="nav-badge soon">待接入</span>
        </div>

      </nav>

      <!-- 折叠按钮 -->
      <button class="collapse-btn" @click="isCollapse = !isCollapse">
        <el-icon><ArrowLeft v-if="!isCollapse" /><ArrowRight v-else /></el-icon>
        <span v-if="!isCollapse">收起</span>
      </button>
    </aside>

    <!-- =============== 右侧主区 =============== -->
    <div class="main-wrap">

      <!-- 顶部栏 -->
      <header class="topbar">
        <div class="topbar-left">
          <!-- 面包屑 -->
          <nav class="breadcrumb" aria-label="breadcrumb">
            <span class="bc-home" @click="router.push('/')">首页</span>
            <template v-if="currentPageMeta.parent">
              <span class="bc-sep">/</span>
              <span class="bc-item">{{ currentPageMeta.parent }}</span>
            </template>
            <span class="bc-sep">/</span>
            <span class="bc-current">{{ currentPageMeta.title || '概览' }}</span>
          </nav>
        </div>

        <div class="topbar-right">
          <span class="env-chip" :class="envMode">{{ envTagText }}</span>

          <el-dropdown trigger="click">
            <div class="user-btn">
              <div class="user-avatar">张</div>
              <div class="user-info">
                <span class="user-name">张竞祺</span>
                <span class="user-role">前端开发</span>
              </div>
              <el-icon class="chevron"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>个人设置</el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <!-- 页面内容 -->
      <main class="page-main">
        <RouterView v-slot="{ Component }">
          <Transition name="fade-slide" mode="out-in">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </main>
    </div>

  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const isCollapse = ref(false)

const pageMetaMap = {
  '/':               { title: '控制台',     parent: '' },
  '/goods/collect':  { title: '商品采集', parent: '商品模块' },
  '/goods/manage':   { title: '商品管理', parent: '商品模块' },
  '/goods/listing':  { title: '商品上货', parent: '商品模块' },
  '/goods/decision':  { title: '选品决策', parent: '商品模块' },
  '/orders':         { title: '订单管理', parent: '' },
  '/inventory':      { title: '库存管理', parent: '' },
  '/logistics':      { title: '物流追踪', parent: '' },
  '/shop':           { title: '店铺管理', parent: '' },
  '/kol':            { title: '达人检索', parent: '' },
  '/reports':        { title: '数据报表', parent: '' },
}

const currentPageMeta = computed(() => pageMetaMap[route.path] || { title: '', parent: '' })

const envMode = import.meta.env.MODE === 'production' ? 'prod' : 'dev'
const envTagText = import.meta.env.MODE === 'production' ? '生产环境' : '开发环境'

// 退出登录
function handleLogout() {
  // 清除token
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  // 跳转到登录页
  router.push('/login')
}
</script>

<style scoped>
/* ========== 整体布局 ========== */
.layout-root {
  height: 100vh;
  display: flex;
  overflow: hidden;
  background: var(--bg-page);
}

/* ========== 侧边栏（浅色 · 妙手风） ========== */
.aside {
  width: var(--aside-width);
  min-width: var(--aside-width);
  background: var(--aside-bg);
  border-right: 1px solid var(--aside-border-r);
  display: flex;
  flex-direction: column;
  transition: width var(--dur) var(--ease), min-width var(--dur) var(--ease);
  overflow: hidden;
  flex-shrink: 0;
  position: relative;
  z-index: 10;
  box-shadow: 1px 0 0 var(--border);
}
.aside.collapsed {
  width: var(--aside-width-sm);
  min-width: var(--aside-width-sm);
}

/* Logo */
.logo-area {
  height: var(--header-h);
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 16px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.logo-img {
  width: 32px;
  height: 32px;
  border-radius: var(--r-md);
  object-fit: cover;
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(8,91,156,.35);
}
.logo-text {
  color: var(--text-primary);
  font-size: 15px;
  font-weight: 700;
  letter-spacing: -.01em;
  white-space: nowrap;
}
.logo-fade-enter-active, .logo-fade-leave-active { transition: opacity .15s; }
.logo-fade-enter-from, .logo-fade-leave-to { opacity: 0; }

/* 导航 */
.nav-menu {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 8px 10px 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.nav-menu::-webkit-scrollbar { width: 0; }

.nav-section-label {
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: .06em;
  text-transform: uppercase;
  color: var(--aside-section);
  padding: 14px 8px 4px;
  white-space: nowrap;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 0 10px;
  height: 38px;
  border-radius: var(--r-md);
  color: var(--aside-text);
  font-size: 13.5px;
  font-weight: 500;
  cursor: pointer;
  transition: background var(--dur) var(--ease), color var(--dur) var(--ease);
  white-space: nowrap;
  position: relative;
  user-select: none;
}
.nav-item:hover {
  background: var(--aside-hover);
  color: var(--brand);
}
.nav-item.active {
  background: var(--aside-active-bg);
  color: var(--aside-active-text);
  font-weight: 600;
}
.nav-item.active .el-icon { color: var(--brand); }
.nav-item.disabled {
  opacity: .5;
  cursor: not-allowed;
}
.nav-item .el-icon {
  font-size: 15px;
  flex-shrink: 0;
  color: var(--text-secondary);
  transition: color var(--dur) var(--ease);
}
.nav-item:hover .el-icon { color: var(--brand); }

.nav-badge {
  margin-left: auto;
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: var(--r-full);
  background: var(--brand);
  color: #fff;
  flex-shrink: 0;
  line-height: 16px;
}
.nav-badge.soon {
  background: #f3f4f6;
  color: var(--text-muted);
}

.nav-divider {
  height: 1px;
  background: var(--border);
  margin: 6px 4px;
}

/* 折叠按钮 */
.collapse-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 11px 16px;
  background: none;
  border: none;
  border-top: 1px solid var(--border);
  color: var(--text-muted);
  font-size: 12.5px;
  cursor: pointer;
  transition: color var(--dur) var(--ease), background var(--dur) var(--ease);
  width: 100%;
  white-space: nowrap;
  flex-shrink: 0;
  font-family: inherit;
}
.collapse-btn:hover {
  color: var(--brand);
  background: var(--bg-hover);
}
.collapse-btn .el-icon { font-size: 13px; flex-shrink: 0; }

/* ========== 主区 ========== */
.main-wrap {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 顶部栏 */
.topbar {
  height: var(--header-h);
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
  gap: 16px;
  box-shadow: 0 1px 0 var(--border);
}

/* 面包屑 */
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
}
.bc-home {
  color: var(--text-secondary);
  cursor: pointer;
  transition: color var(--dur);
}
.bc-home:hover { color: var(--brand); }
.bc-sep {
  color: #d1d5db;
  font-size: 12px;
}
.bc-item { color: var(--text-secondary); }
.bc-current { color: var(--text-primary); font-weight: 600; }

/* 右侧工具栏 */
.topbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.env-chip {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 9px;
  border-radius: var(--r-full);
  letter-spacing: .03em;
  line-height: 18px;
}
.env-chip.dev {
  background: #fffbeb;
  color: #b45309;
  border: 1px solid #fde68a;
}
.env-chip.prod {
  background: #f0fdf4;
  color: #15803d;
  border: 1px solid #bbf7d0;
}

/* 顶栏工具按钮（通知等） */
.topbar-icon-btn {
  width: 34px;
  height: 34px;
  border-radius: var(--r-md);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-secondary);
  transition: background var(--dur) var(--ease), color var(--dur) var(--ease);
  border: 1px solid transparent;
}
.topbar-icon-btn:hover {
  background: var(--bg-hover);
  border-color: var(--border);
  color: var(--brand);
}
.topbar-icon-btn .el-icon { font-size: 16px; }

/* 用户按钮 */
.user-btn {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 4px 10px 4px 5px;
  border-radius: var(--r-md);
  cursor: pointer;
  transition: background var(--dur) var(--ease);
  border: 1px solid transparent;
}
.user-btn:hover {
  background: var(--bg-hover);
  border-color: var(--border);
}
.user-avatar {
  width: 30px;
  height: 30px;
  background: var(--brand);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}
.user-info {
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.user-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.2;
}
.user-role {
  font-size: 11px;
  color: var(--text-muted);
  line-height: 1;
}
.chevron {
  font-size: 11px;
  color: var(--text-muted);
}

/* 主内容 */
.page-main {
  flex: 1;
  overflow-y: auto;
  background: var(--bg-page);
  display: flex;
  flex-direction: column;
}
</style>
