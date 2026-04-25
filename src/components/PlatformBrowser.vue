<template>
  <Teleport to="body">
    <Transition name="browser-slide">
      <div v-if="visible" class="platform-browser-overlay" @click.self="handleCloseOverlay">
        <div class="platform-browser">
          <!-- 标签栏 -->
          <div class="browser-toolbar">
            <div class="toolbar-left">
              <div class="platform-logo">
                <span class="logo-text">🖥️ 平台浏览器</span>
              </div>
            </div>

            <div class="browser-tabs">
              <div
                v-for="tab in tabs"
                :key="tab.id"
                :class="['browser-tab', {
                  active: tab.id === activeTabId,
                  'is-source': isSourcePlatform(tab.platformKey),
                }]"
                @click="switchTab(tab.id)"
                @dragover.prevent="onDragOverTab(tab)"
                @dragleave="onDragLeaveTab(tab)"
                @drop="onDropExternal($event, tab)"
              >
                <img v-if="getPlatformIcon(tab.platformKey)" :src="getPlatformIcon(tab.platformKey)" class="tab-platform-icon" />
                <span class="tab-title">{{ tab.shopName || getPlatformName(tab.platformKey) }}</span>
                <span v-if="isSourcePlatform(tab.platformKey)" class="tab-source-badge">货源</span>
                <el-icon class="tab-close" @click.stop="closeTab(tab.id)"><Close /></el-icon>
              </div>
            </div>

            <div class="toolbar-right">
              <!-- 注入采集脚本按钮（仅货源平台显示） -->
              <el-tooltip v-if="currentTab && isSourcePlatform(currentTab.platformKey)" content="注入采集脚本，自动识别页面商品" placement="bottom">
                <el-button text size="small" type="primary" @click="injectCollectionScript">
                  <el-icon><MagicStick /></el-icon>
                  采集模式
                </el-button>
              </el-tooltip>
              <el-button text size="small" @click="handleMinimize">
                <el-icon><Minus /></el-icon>
              </el-button>
              <el-button text size="small" type="danger" @click="handleClose">
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
          </div>

          <!-- 拖拽悬浮提示（货源平台拖拽采集） -->
          <Transition name="indicator-fade">
            <div v-if="isDraggingExternal" class="drag-indicator">
              <div class="indicator-inner">
                <el-icon><Aim /></el-icon>
                <span>检测到货源商品 → 放开即采集至一站式上货</span>
              </div>
            </div>
          </Transition>

          <!-- iframe容器 -->
          <div class="browser-content" ref="browserContent">
            <div v-if="tabs.length === 0" class="empty-browser">
              <img src="@/assets/logo.png" class="empty-logo" alt="logo" />
              <p class="empty-title">平台浏览器</p>
              <p class="empty-desc">
                打开货源平台（1688/淘宝）时<br/>
                拖拽商品卡片即可自动采集上货
              </p>
              <div class="empty-platforms">
                <span class="ep-label">支持的货源平台：</span>
                <el-tag size="small" effect="plain">1688</el-tag>
                <el-tag size="small" effect="plain">淘宝</el-tag>
                <el-tag size="small" effect="plain" type="info">拼多多</el-tag>
                <el-tag size="small" effect="plain" type="info">天猫</el-tag>
              </div>
            </div>

            <iframe
              v-for="tab in tabs"
              v-show="tab.id === activeTabId && !tab.loading"
              :key="tab.id"
              :src="tab.url"
              :ref="el => iframeRefs[tab.id] = el"
              class="platform-iframe"
              :class="{ 'source-platform': isSourcePlatform(tab.platformKey) }"
              sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-top-navigation"
              @load="handleIframeLoad(tab.id)"
            />

            <!-- 加载状态 -->
            <div v-if="currentTab?.loading" class="iframe-loading">
              <el-icon class="is-loading"><Loading /></el-icon>
              <span>正在加载页面...</span>
            </div>
          </div>

          <!-- 拖拽采集确认悬浮卡（当 iframe 内拖拽时显示在标签上） -->
          <Transition name="float-fade">
            <div v-if="draggedExternalGoods" class="drop-float-card">
              <div class="float-card-header">
                <el-icon><Goods /></el-icon>
                检测到商品
                <el-tag size="small" type="success">可采集</el-tag>
              </div>
              <div class="float-card-body">
                <div class="float-goods-name">{{ draggedExternalGoods.name || draggedExternalGoods.title || '商品' }}</div>
                <div class="float-goods-price" v-if="draggedExternalGoods.price">
                  ¥{{ draggedExternalGoods.price }}
                </div>
              </div>
              <div class="float-card-actions">
                <el-button type="primary" size="small" @click="confirmExternalCollect">
                  <el-icon><Upload /></el-icon>
                  采集并上货
                </el-button>
                <el-button size="small" @click="draggedExternalGoods = null">
                  取消
                </el-button>
              </div>
            </div>
          </Transition>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, reactive, watch, nextTick } from 'vue'
import { Close, Minus, Upload, Loading, MagicStick, Aim, Goods } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

// ── State ──────────────────────────────────────────────────
const visible = ref(false)
const tabs = ref([])
const activeTabId = ref(null)
const iframeRefs = reactive({})
const isDragOverAny = ref(false)
const isDraggingExternal = ref(false)   // 货源平台拖拽状态
const draggedExternalGoods = ref(null)   // 外部拖拽的商品数据
let tabIdCounter = 0

// ── Computed ───────────────────────────────────────────────
const currentTab = computed(() => tabs.value.find(t => t.id === activeTabId.value))

// ── 货源平台判断 ──────────────────────────────────────────────
// 1688、淘宝等为货源平台，希音、Temu等既是货源也可上架
const SOURCE_PLATFORMS = ['1688', 'taobao', 'pdd', 'tmall']
const SELL_PLATFORMS = ['shopee', 'tiktok', 'temu', 'shein', 'aliexpress', 'amazon', 'ebay', 'lazada', 'wish', 'mercado', 'ozon', 'allegro']

function isSourcePlatform(platformKey) {
  return SOURCE_PLATFORMS.includes(platformKey) ||
    (platformKey && (platformKey.includes('1688') || platformKey.includes('taobao') || platformKey.includes('pinduoduo')))
}

// ── 平台URL映射 ────────────────────────────────────────────
const PLATFORM_URLS = {
  shopee: 'https://seller.shopee.cn/portal/home',
  temu: 'https://seller.temu.com/portal',
  shein: "https://seller.shein.com/portal/home",
  tiktok: 'https://seller.tiktok.com/portal/home',
  aliexpress: 'https://sell.aliexpress.com',
  amazon: 'https://sellercentral.amazon.com',
  ebay: 'https://www.ebay.com/sh/lst/manage',
  lazada: 'https://center.lazada.com',
}

// ── 平台图标 ────────────────────────────────────────────────
function getPlatformIcon(key) {
  return `/platform-icons/${key}.svg`
}

function getPlatformName(key) {
  const names = {
    shopee: 'Shopee', temu: 'Temu', shein: '希音',
    tiktok: 'TikTok', aliexpress: '速卖通', amazon: 'Amazon',
    ebay: 'eBay', lazada: 'Lazada', wish: 'Wish', mercado: 'Mercado'
  }
  return names[key] || key
}

// ── Tab操作 ─────────────────────────────────────────────────
function openTab({ platformKey, shopId, shopName, url, authToken }) {
  const id = ++tabIdCounter
  const tabUrl = url || PLATFORM_URLS[platformKey] || `https://www.${platformKey}.com`

  const tab = {
    id,
    platformKey,
    shopId,
    shopName,
    url: tabUrl,
    authToken,
    loading: true,
  }

  tabs.value.push(tab)
  activeTabId.value = id
  visible.value = true

  // 通过 postMessage 注入授权信息
  nextTick(() => {
    setTimeout(() => {
      injectAuthToken(tab)
    }, 2000)  // 等待 iframe 加载完成
  })
}

function closeTab(id) {
  const index = tabs.value.findIndex(t => t.id === id)
  if (index === -1) return

  tabs.value.splice(index, 1)

  if (activeTabId.value === id) {
    activeTabId.value = tabs.value.length > 0 ? tabs.value[tabs.value.length - 1].id : null
  }

  if (tabs.value.length === 0) {
    visible.value = false
  }
}

function switchTab(id) {
  activeTabId.value = id
  emit('tab-change', currentTab.value)
}

function handleIframeLoad(tabId) {
  const tab = tabs.value.find(t => t.id === tabId)
  if (tab) tab.loading = false

  // 加载完成后注入授权
  nextTick(() => {
    injectAuthToken(tab)
  })
}

// ── 授权注入 ───────────────────────────────────────────────
function injectAuthToken(tab) {
  if (!tab?.authToken || !iframeRefs[tab.id]) return
  try {
    iframeRefs[tab.id].contentWindow?.postMessage({
      type: 'AUTH_TOKEN',
      token: tab.authToken,
    }, '*')
  } catch (e) {
    // 跨域限制无法注入，属正常
  }
}

// ── 拖拽处理（标签页级）───────────────────────────────────────
function onDragOverTab(tab) {
  if (isSourcePlatform(tab.platformKey)) {
    isDraggingExternal.value = true
  }
  isDragOverAny.value = true
}

function onDragLeaveTab(tab) {
  if (isSourcePlatform(tab.platformKey)) {
    // 简单处理：如果离开当前标签，则清除拖拽状态
    // 实际应用中可维护一个 Set 来精确跟踪每个 tab 的状态
    if (activeTabId.value === tab.id) {
      // 仍在当前活动标签内，不清除
    }
  }
  isDragOverAny.value = false
}

/**
 * 处理来自货源平台的外部拖拽（模式2核心）
 * 用户在内置浏览器中拖拽1688/淘宝商品时触发
 */
function onDropExternal(e, tab) {
  isDraggingExternal.value = false
  isDragOverAny.value = false

  if (!isSourcePlatform(tab.platformKey)) {
    // 非货源平台：走原有上货逻辑（内部商品拖拽）
    onDropInternal(e, tab)
    return
  }

  // 货源平台：尝试从 iframe 获取商品数据
  // 由于跨域限制，尝试通过 postMessage 从 iframe 获取数据
  try {
    // 向 iframe 发送采集请求
    iframeRefs[tab.id]?.contentWindow?.postMessage({
      type: 'ONESTOP_REQUEST_PRODUCT',
      tabId: tab.id,
      platformKey: tab.platformKey,
    }, '*')
  } catch (err) {
    // 跨域无法通信，显示手动提示
    ElMessage.info('由于跨域限制，请点击「采集模式」按钮启用自动采集，或使用一站式页面的粘贴链接功能')
  }
}

/**
 * 处理内部商品卡片的拖拽（原有逻辑）
 */
function onDropInternal(e, tab) {
  try {
    const jsonData = e.dataTransfer.getData('application/json')
    if (!jsonData) {
      ElMessage.warning('无法识别拖拽的数据格式')
      return
    }

    const payload = JSON.parse(jsonData)
    if (payload.type !== 'goods') {
      ElMessage.warning('仅支持拖拽商品卡片')
      return
    }

    // 触发上货确认
    emit('goods-dropped', {
      goods: payload.data,
      targetTab: tab,
    })

  } catch (err) {
    console.error('[PlatformBrowser] 解析拖拽数据失败:', err)
    ElMessage.error('数据解析失败')
  }
}

/**
 * 确认从外部采集商品，触发一站式上货流程
 */
function confirmExternalCollect() {
  if (!draggedExternalGoods.value) return
  emit('external-collect', {
    goods: draggedExternalGoods.value,
    platformKey: currentTab.value?.platformKey,
  })
  draggedExternalGoods.value = null
  ElMessage.success('已发送至一站式采集上货流程')
}

/**
 * 注入采集脚本到 iframe
 * 用于在货源平台页面自动识别商品 DOM 并采集数据
 */
function injectCollectionScript() {
  const tab = currentTab.value
  if (!tab || !iframeRefs[tab.id]) {
    ElMessage.warning('请先打开货源平台页面')
    return
  }

  // 采集脚本：在外部页面执行，监听拖拽事件并采集商品数据
  const collectScript = `
    (function() {
      // 防止重复注入
      if (window.__erpCollectInjected__) return
      window.__erpCollectInjected__ = true

      // 监听 mousedown/mouseup 识别用户点击了商品卡片
      let selectedEl = null

      document.addEventListener('mouseup', function(e) {
        // 向上查找最近的商品元素（各平台命名不同）
        let el = e.target
        for (let i = 0; i < 5; i++) {
          if (!el) break
          // 检测是否为商品卡片（1688/淘宝的通用选择器）
          if (
            el.matches?.('[data-id]') ||
            el.matches?.('.offer-item') ||
            el.matches?.('.item') ||
            el.matches?.('.product-item') ||
            el.matches?.('[class*="offer"]') ||
            el.matches?.('[class*="product"]') ||
            el.matches?.('[class*="item"]')
          ) {
            selectedEl = el
            break
          }
          el = el.parentElement
        }
      })

      // 监听拖拽开始事件
      document.addEventListener('dragstart', function(e) {
        if (!selectedEl) return

        // 尝试从 DOM 提取商品信息
        const data = extractProductData(selectedEl)
        if (data) {
          // 通过 postMessage 发送数据
          window.parent.postMessage({
            type: 'ONESTOP_COLLECT_PRODUCT',
            product: data,
          }, '*')
        }
      }, true)

      function extractProductData(el) {
        try {
          // 尝试多种方式提取商品数据
          const getText = (sel) => {
            const n = el.querySelector(sel)
            return n ? n.innerText?.trim() : ''
          }

          // 提取标题
          const title =
            getText('h2') || getText('.title') || getText('[class*="title"]') ||
            el.querySelector('a')?.href || document.title

          // 提取价格
          const priceText = getText('[class*="price"]') || getText('.price')
          const price = parseFloat(priceText?.replace(/[^0-9.]/g, '')) || 0

          // 提取图片
          const imgEl = el.querySelector('img')
          const image = imgEl?.src || ''

          // 提取链接
          const link = el.querySelector('a')?.href || ''

          if (title || price || image) {
            return {
              name: title,
              title: title,
              price: price,
              images: image ? [image] : [],
              sourceUrl: link,
              platform: '1688',
              _source: 'iframeInject',
              _timestamp: Date.now(),
            }
          }
        } catch (err) {
          console.error('[ERP Collect] 提取商品数据失败:', err)
        }
        return null
      }

      // 通知父窗口采集脚本已就绪
      window.parent.postMessage({
        type: 'ONESTOP_SCRIPT_READY',
        platformKey: '${tab?.platformKey || ''}',
      }, '*')
    })()
  `

  try {
    // 通过注入脚本方式在 iframe 中执行
    iframeRefs[tab.id].contentWindow?.postMessage({
      type: 'ONESTOP_INJECT_SCRIPT',
      script: collectScript,
    }, '*')
    ElMessage.success('采集脚本已注入，请在货源页面拖拽商品卡片')
  } catch (err) {
    ElMessage.warning('注入采集脚本失败，请尝试使用粘贴链接方式')
  }
}

// ── 浏览器控制 ──────────────────────────────────────────────
function handleMinimize() {
  visible.value = false
}

function handleClose() {
  tabs.value = []
  activeTabId.value = null
  visible.value = false
  emit('close')
}

function handleCloseOverlay() {
  // 点击遮罩层最小化而非关闭
  visible.value = false
}

// ── 监听跨窗口 postMessage ──────────────────────────────────
function setupPostMessageListener() {
  window.addEventListener('message', (e) => {
    const { type, url, platformKey, product, tabId } = e.data || {}

    if (type === 'OPEN_PLATFORM') {
      // 收到来自页面组件的请求，自动打开标签页
      openTab({ platformKey, url })
    }

    if (type === 'ONESTOP_COLLECT_PRODUCT') {
      // 收到 iframe 内采集脚本发来的商品数据（模式2核心）
      if (product) {
        draggedExternalGoods.value = product
        // 找到对应的 tab
        if (tabId) {
          switchTab(tabId)
        }
      }
    }

    if (type === 'ONESTOP_SCRIPT_READY') {
      ElMessage.success(`采集脚本已在 ${getPlatformName(platformKey)} 就绪，拖拽商品即可采集`)
    }
  })
}

setupPostMessageListener()

// ── 暴露方法给外部调用 ─────────────────────────────────────
defineExpose({
  openTab,
  closeTab,
  minimize: handleMinimize,
  show: () => { visible.value = true },
  hide: () => { visible.value = false },
  isSourcePlatform,  // 暴露货源判断函数
})
</script>

<style scoped>
.platform-browser-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 9000;
  display: flex;
  align-items: flex-end;
  justify-content: flex-end;
}

.platform-browser {
  width: 85vw;
  height: 80vh;
  background: #fff;
  border-radius: 12px 12px 0 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 -4px 24px rgba(0, 0, 0, 0.15);
}

/* 工具栏 */
.browser-toolbar {
  display: flex;
  align-items: center;
  height: 44px;
  background: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
  padding: 0 8px;
  gap: 8px;
  flex-shrink: 0;
}

.toolbar-left {
  flex-shrink: 0;
}

.logo-text {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  white-space: nowrap;
}

/* 标签栏 */
.browser-tabs {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 2px;
  overflow-x: auto;
  min-width: 0;
}

.browser-tabs::-webkit-scrollbar {
  height: 0;
}

.browser-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 6px 6px 0 0;
  cursor: pointer;
  font-size: 12px;
  white-space: nowrap;
  background: #e8e8e8;
  color: var(--el-text-color-secondary);
  transition: all 0.15s;
  max-width: 180px;
  position: relative;
}

.browser-tab:hover {
  background: #d8d8d8;
}

.browser-tab.active {
  background: #fff;
  color: var(--el-text-color-primary);
  font-weight: 600;
  box-shadow: 0 -1px 0 #fff;
}

.browser-tab.drag-over {
  background: var(--el-color-primary-light-9);
  border: 2px dashed var(--el-color-primary);
}

.tab-platform-icon {
  width: 16px;
  height: 16px;
  border-radius: 2px;
  flex-shrink: 0;
}

.tab-title {
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.tab-close {
  font-size: 11px;
  opacity: 0.6;
  flex-shrink: 0;
}

.tab-close:hover {
  opacity: 1;
  color: #f56c6c;
}

.toolbar-right {
  display: flex;
  gap: 2px;
  flex-shrink: 0;
}

/* 拖拽指示器 */
.drag-indicator {
  position: absolute;
  top: 44px;
  left: 0;
  right: 0;
  height: 48px;
  background: var(--el-color-primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  pointer-events: none;
}

.indicator-inner {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
}

/* 内容区 */
.browser-content {
  flex: 1;
  position: relative;
  background: #f0f0f0;
  overflow: hidden;
}

.platform-iframe {
  width: 100%;
  height: 100%;
  border: none;
  background: #fff;
}

.iframe-loading {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--el-text-color-secondary);
  font-size: 14px;
  background: rgba(255,255,255,0.9);
}

.empty-browser {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
}

.empty-logo {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  opacity: 0.6;
}

.empty-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin: 0;
}

.empty-desc {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  text-align: center;
  margin: 0;
  line-height: 1.6;
}

.empty-platforms {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
}
.ep-label { font-size: 12px; color: var(--text-muted); }

/* 货源平台标签 */
.tab-source-badge {
  font-size: 9px;
  background: #22c55e;
  color: white;
  padding: 1px 5px;
  border-radius: 8px;
  font-weight: 700;
  flex-shrink: 0;
}

/* 货源平台 iframe */
.platform-iframe.source-platform {
  border-top: 3px solid #22c55e;
}

/* 拖拽指示器动画 */
.indicator-fade-enter-active, .indicator-fade-leave-active {
  transition: opacity 0.2s ease;
}
.indicator-fade-enter-from, .indicator-fade-leave-to {
  opacity: 0;
}

/* 拖拽采集确认悬浮卡 */
.drop-float-card {
  position: absolute;
  bottom: 20px;
  right: 20px;
  width: 260px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0,0,0,.15);
  border: 2px solid #22c55e;
  z-index: 100;
  overflow: hidden;
}

.float-card-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 14px 8px;
  font-size: 13px;
  font-weight: 700;
  color: #166534;
  background: rgba(34,197,94,.06);
}

.float-card-body {
  padding: 8px 14px;
}

.float-goods-name {
  font-size: 13px;
  color: var(--el-text-color-primary);
  font-weight: 500;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.float-goods-price {
  font-size: 16px;
  font-weight: 700;
  color: #ef4444;
}

.float-card-actions {
  display: flex;
  gap: 8px;
  padding: 8px 14px 12px;
}

.float-fade-enter-active, .float-fade-leave-active {
  transition: all 0.3s ease;
}
.float-fade-enter-from, .float-fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

/* 动画 */

.browser-slide-enter-active,
.browser-slide-leave-active {
  transition: opacity 0.3s ease;
}

.browser-slide-enter-from,
.browser-slide-leave-to {
  opacity: 0;
}
</style>
