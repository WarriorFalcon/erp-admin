<template>
  <div class="hot-products-page">
    <!-- 页面Header -->
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">爆品推荐</h1>
        <p class="page-desc">精选各平台热销、飙升、高利润商品，支持一键采集上货</p>
      </div>
    </div>

    <!-- 五大榜单Tab -->
    <div class="rank-tabs">
      <div
        v-for="tab in tabs"
        :key="tab.id"
        :class="['rank-tab', { active: activeTab === tab.id }]"
        @click="activeTab = tab.id"
      >
        <el-icon><component :is="tab.icon" /></el-icon>
        <span>{{ tab.name }}</span>
        <el-tag v-if="tab.badge" type="danger" size="small" effect="dark">{{ tab.badge }}</el-tag>
      </div>
    </div>

    <!-- 商品列表 -->
    <div class="products-grid" v-loading="loading">
      <div
        v-for="item in currentList"
        :key="item.id"
        class="product-card"
        draggable="true"
        @dragstart="onDragStart($event, item)"
        @dragend="onDragEnd"
      >
        <div class="product-image">
          <img :src="item.image" :alt="item.name" />
          <div class="platform-badge" :style="{ background: item.platformColor }">
            {{ item.platform }}
          </div>
          <div class="rank-badge" v-if="item.rank">
            #{{ item.rank }}
          </div>
        </div>
        <div class="product-info">
          <h3 class="product-name">{{ item.name }}</h3>
          <div class="product-meta">
            <span class="price">¥{{ item.price }}</span>
            <span class="sales">销量 {{ item.sales }}</span>
          </div>
          <div class="product-stats">
            <span class="stat-item" :class="item.profitRate >= 20 ? 'good' : 'normal'">
              利润率 {{ item.profitRate }}%
            </span>
            <span class="stat-item rating">
              <el-icon><Star /></el-icon>
              {{ item.rating }}
            </span>
          </div>
        </div>
        <div class="product-actions">
          <el-button type="primary" size="small" @click="handleCollect(item)">
            <el-icon><ShoppingCart /></el-icon>
            采集
          </el-button>
          <el-button type="success" size="small" @click="handleQuickList(item)">
            <el-icon><Upload /></el-icon>
            上货
          </el-button>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <el-empty v-if="!loading && currentList.length === 0" description="暂无数据">
      <el-button type="primary" @click="loadData">刷新试试</el-button>
    </el-empty>

    <!-- 加载更多 -->
    <div class="load-more" v-if="currentList.length > 0">
      <el-button @click="loadMore" :loading="loadingMore">加载更多</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  TrendCharts, Money, Star, Promotion, Shop,
  ShoppingCart, Upload, Star as StarIcon, Lightning
} from '@element-plus/icons-vue'

const activeTab = ref('hot')
const loading = ref(false)
const loadingMore = ref(false)

// 五大榜单Tab
const tabs = [
  { id: 'hot', name: '热销榜', icon: 'Lightning', badge: null },
  { id: 'rising', name: '飙升榜', icon: 'TrendCharts', badge: 'NEW' },
  { id: 'profit', name: '高利润榜', icon: 'Money', badge: null },
  { id: 'platform', name: '平台扶持榜', icon: 'Promotion', badge: null },
  { id: 'local', name: '辽宁产业带', icon: 'Shop', badge: 'LOCAL' },
]

// Mock数据
const mockData = {
  hot: [
    { id: 1, name: '夏季新款防晒衣女轻薄透气户外钓鱼衫', platform: 'Shein', platformColor: '#000', image: 'https://picsum.photos/200/200?random=1', price: 89, sales: '10万+', profitRate: 35, rating: 4.8, rank: 1 },
    { id: 2, name: '瑜伽运动套装女健身服显瘦跑步服', platform: 'TikTok', platformColor: '#FF0050', image: 'https://picsum.photos/200/200?random=2', price: 128, sales: '8万+', profitRate: 42, rating: 4.9, rank: 2 },
    { id: 3, name: '韩版宽松百搭oversize短袖T恤', platform: 'Temu', platformColor: '#FF6B35', image: 'https://picsum.photos/200/200?random=3', price: 45, sales: '15万+', profitRate: 28, rating: 4.6, rank: 3 },
    { id: 4, name: '男士速干沙滩裤运动休闲短裤', platform: 'Shopee', platformColor: '#FF8000', image: 'https://picsum.photos/200/200?random=4', price: 68, sales: '6万+', profitRate: 38, rating: 4.7, rank: 4 },
    { id: 5, name: '儿童卡通拖鞋男童女童室内拖鞋', platform: 'Shein', platformColor: '#000', image: 'https://picsum.photos/200/200?random=5', price: 29, sales: '12万+', profitRate: 45, rating: 4.5, rank: 5 },
    { id: 6, name: '女士手提包时尚单肩包斜挎包', platform: 'TikTok', platformColor: '#FF0050', image: 'https://picsum.photos/200/200?random=6', price: 158, sales: '5万+', profitRate: 52, rating: 4.8, rank: 6 },
  ],
  rising: [
    { id: 7, name: '筋膜枪迷你便携式按摩枪肌肉放松', platform: 'TikTok', platformColor: '#FF0050', image: 'https://picsum.photos/200/200?random=7', price: 199, sales: '2万+', profitRate: 55, rating: 4.9, growth: '+320%' },
    { id: 8, name: '折叠太阳镜偏光驾驶墨镜防紫外线', platform: 'Shein', platformColor: '#000', image: 'https://picsum.photos/200/200?random=8', price: 59, sales: '1.5万+', profitRate: 48, rating: 4.7, growth: '+280%' },
    { id: 9, name: '无线蓝牙耳机降噪运动入耳式', platform: 'Temu', platformColor: '#FF6B35', image: 'https://picsum.photos/200/200?random=9', price: 89, sales: '3万+', profitRate: 38, rating: 4.6, growth: '+250%' },
    { id: 10, name: '便携式榨汁杯无线充电搅拌杯', platform: 'Shopee', platformColor: '#FF8000', image: 'https://picsum.photos/200/200?random=10', price: 79, sales: '2.5万+', profitRate: 42, rating: 4.8, growth: '+200%' },
  ],
  profit: [
    { id: 11, name: '真丝发圈高档丝绸发绳头饰', platform: 'Shein', platformColor: '#000', image: 'https://picsum.photos/200/200?random=11', price: 25, cost: 5, sales: '8千+', profitRate: 78, rating: 4.9 },
    { id: 12, name: '日式收纳盒桌面储物盒整理盒', platform: 'Temu', platformColor: '#FF6B35', image: 'https://picsum.photos/200/200?random=12', price: 39, cost: 8, sales: '5千+', profitRate: 72, rating: 4.7 },
    { id: 13, name: '创意冰箱贴磁性贴装饰贴', platform: 'Shopee', platformColor: '#FF8000', image: 'https://picsum.photos/200/200?random=13', price: 15, cost: 3, sales: '2万+', profitRate: 68, rating: 4.5 },
    { id: 14, name: 'ins风桌面摆件轻奢装饰品', platform: 'TikTok', platformColor: '#FF0050', image: 'https://picsum.photos/200/200?random=14', price: 68, cost: 15, sales: '3千+', profitRate: 65, rating: 4.8 },
  ],
  platform: [
    { id: 15, name: 'TikTok爆款电动牙刷智能声波', platform: 'TikTok', platformColor: '#FF0050', image: 'https://picsum.photos/200/200?random=15', price: 89, sales: '1.2万+', profitRate: 48, rating: 4.9 },
    { id: 16, name: 'Temu新兴类目露营帐篷折叠椅', platform: 'Temu', platformColor: '#FF6B35', image: 'https://picsum.photos/200/200?random=16', price: 299, sales: '8千+', profitRate: 42, rating: 4.7 },
    { id: 17, name: 'Shein夏季新款连衣裙碎花裙', platform: 'Shein', platformColor: '#000', image: 'https://picsum.photos/200/200?random=17', price: 128, sales: '2万+', profitRate: 38, rating: 4.8 },
  ],
  local: [
    { id: 18, name: '沈阳服装工厂爆款针织衫', platform: '辽宁', platformColor: '#005BAC', image: 'https://picsum.photos/200/200?random=18', price: 78, sales: '5千+', profitRate: 52, rating: 4.6 },
    { id: 19, name: '大连海鲜干货即食海参礼盒', platform: '辽宁', platformColor: '#005BAC', image: 'https://picsum.photos/200/200?random=19', price: 398, sales: '2千+', profitRate: 45, rating: 4.9 },
    { id: 20, name: '鞍山箱包工厂新款旅行包', platform: '辽宁', platformColor: '#005BAC', image: 'https://picsum.photos/200/200?random=20', price: 168, sales: '3千+', profitRate: 48, rating: 4.7 },
  ],
}

const currentList = computed(() => mockData[activeTab.value] || [])

// 拖拽相关
function onDragStart(e, item) {
  e.dataTransfer.setData('application/json', JSON.stringify({ type: 'goods', id: item.id, name: item.name }))
  e.dataTransfer.setData('text/plain', JSON.stringify({ type: 'goods', id: item.id, name: item.name }))
}

function onDragEnd() {
  // 拖拽结束
}

// 操作
function handleCollect(item) {
  ElMessage.success(`已将「${item.name}」加入采集待处理`)
}

function handleQuickList(item) {
  ElMessage.success(`已将「${item.name}」加入上货队列`)
}

function loadMore() {
  // TODO: 加载更多数据
  ElMessage.info('暂无更多数据')
}

function loadData() {
  // 刷新数据
  ElMessage.success('数据已刷新')
}

onMounted(() => {
  // 初始加载
})
</script>

<style scoped>
.hot-products-page {
  padding: 20px;
}

/* Tab切换 */
.rank-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.rank-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  background: var(--el-fill-color-light);
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.rank-tab:hover {
  background: var(--el-fill-color);
}

.rank-tab.active {
  background: var(--el-color-primary);
  color: #fff;
}

/* 商品网格 */
.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}

.product-card {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 12px;
  overflow: hidden;
  cursor: grab;
  transition: all 0.2s;
}

.product-card:hover {
  border-color: var(--el-color-primary-light-5);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.product-card:active {
  cursor: grabbing;
}

.product-image {
  position: relative;
  aspect-ratio: 1;
  background: var(--el-fill-color-light);
}

.product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.platform-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  color: #fff;
  font-weight: 600;
}

.rank-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0,0,0,0.3);
}

.product-info {
  padding: 12px;
}

.product-name {
  font-size: 14px;
  font-weight: 500;
  margin: 0 0 8px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.product-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.price {
  font-size: 16px;
  font-weight: 700;
  color: var(--el-color-danger);
}

.sales {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.product-stats {
  display: flex;
  gap: 8px;
}

.stat-item {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--el-fill-color-light);
}

.stat-item.good {
  background: rgba(103, 194, 58, 0.1);
  color: #67C23A;
}

.stat-item.rating {
  display: flex;
  align-items: center;
  gap: 2px;
  color: #E6A23C;
}

.product-actions {
  display: flex;
  gap: 8px;
  padding: 0 12px 12px;
}

.product-actions .el-button {
  flex: 1;
}

/* 加载更多 */
.load-more {
  text-align: center;
  margin-top: 20px;
}
</style>
