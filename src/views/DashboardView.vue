<template>
  <div class="dashboard-container">
    <!-- 顶部统计栏 -->
    <div class="stats-header">
      <div class="stat-card">
        <div class="stat-icon blue">
          <el-icon><ShoppingCart /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-label">今日订单量</div>
          <div class="stat-value">
            <span class="number">{{ stats.orderCount }}</span>
            <span class="unit">单</span>
          </div>
          <div class="stat-trend up">
            <el-icon><ArrowUp /></el-icon>
            <span>+12.5%</span>
          </div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon green">
          <el-icon><Money /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-label">今日销售额</div>
          <div class="stat-value">
            <span class="currency">¥</span>
            <span class="number">{{ formatMoney(stats.salesAmount) }}</span>
          </div>
          <div class="stat-trend up">
            <el-icon><ArrowUp /></el-icon>
            <span>+8.3%</span>
          </div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon orange">
          <el-icon><User /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-label">平均客单价</div>
          <div class="stat-value">
            <span class="currency">¥</span>
            <span class="number">{{ stats.avgOrderValue }}</span>
          </div>
          <div class="stat-trend down">
            <el-icon><ArrowDown /></el-icon>
            <span>-2.1%</span>
          </div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon purple">
          <el-icon><Timer /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-label">实时在线</div>
          <div class="stat-value">
            <span class="number">{{ stats.onlineUsers }}</span>
            <span class="unit">人</span>
          </div>
          <div class="stat-trend up">
            <el-icon><ArrowUp /></el-icon>
            <span>+5.7%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧图表 -->
      <div class="left-panel">
        <div class="chart-card">
          <div class="chart-title">
            <span class="title-icon blue"></span>
            销售额趋势
          </div>
          <div ref="salesChartRef" class="chart-container"></div>
        </div>
        <div class="chart-card">
          <div class="chart-title">
            <span class="title-icon green"></span>
            平台分布
          </div>
          <div ref="platformChartRef" class="chart-container"></div>
        </div>
      </div>

      <!-- 中间地图 -->
      <div class="center-panel">
        <div class="map-card">
          <div class="map-header">
            <div class="map-title">
              <el-icon><MapLocation /></el-icon>
              全球订单实时分布
              <span v-if="selectedRegion" class="selected-tag">
                {{ selectedRegion.name }}
              </span>
            </div>
            <div class="map-legend">
              <span class="legend-item">
                <span class="dot hot"></span> 热门区域
              </span>
              <span class="legend-item">
                <span class="dot normal"></span> 普通区域
              </span>
              <span class="legend-item">
                <span class="dot new"></span> 新订单
              </span>
            </div>
          </div>
          <div ref="worldMapRef" class="map-container"></div>
          
          <!-- 地区详情弹窗 -->
          <div v-if="selectedRegion" class="region-panel">
            <div class="region-header">
              <span class="region-name">{{ selectedRegion.name }}</span>
              <el-button size="small" text @click="selectedRegion = null">
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
            <div class="region-stats">
              <div class="region-stat">
                <div class="stat-icon-small">
                  <el-icon><ShoppingCart /></el-icon>
                </div>
                <div class="stat-content">
                  <div class="stat-label-small">今日订单</div>
                  <div class="stat-value-small">{{ selectedRegion.orders }}</div>
                </div>
              </div>
              <div class="region-stat">
                <div class="stat-icon-small green">
                  <el-icon><Money /></el-icon>
                </div>
                <div class="stat-content">
                  <div class="stat-label-small">销售额</div>
                  <div class="stat-value-small">¥{{ formatMoney(selectedRegion.sales) }}</div>
                </div>
              </div>
              <div class="region-stat">
                <div class="stat-icon-small orange">
                  <el-icon><TrendCharts /></el-icon>
                </div>
                <div class="stat-content">
                  <div class="stat-label-small">平均客单价</div>
                  <div class="stat-value-small">¥{{ selectedRegion.avgOrder }}</div>
                </div>
              </div>
              <div class="region-stat">
                <div class="stat-icon-small purple">
                  <el-icon><Goods /></el-icon>
                </div>
                <div class="stat-content">
                  <div class="stat-label-small">热销品类</div>
                  <div class="stat-value-small">{{ selectedRegion.topCategory }}</div>
                </div>
              </div>
            </div>
            <div class="region-chart">
              <div ref="regionChartRef" class="mini-chart"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧实时订单 -->
      <div class="right-panel">
        <div class="order-card">
          <div class="order-header">
            <div class="order-title">
              <span class="pulse-dot"></span>
              实时订单
            </div>
            <div class="order-count">{{ realtimeOrders.length }}条</div>
          </div>
          <div class="order-list" ref="orderListRef">
            <div 
              class="order-item" 
              v-for="(order, index) in displayOrders" 
              :key="order.id"
              :class="{ 'new-order': index < newOrderCount }"
              @click="highlightRegion(order.country)"
            >
              <div class="order-platform" :class="order.platform">
                <img :src="getPlatformIcon(order.platform)" :alt="order.platform">
              </div>
              <div class="order-info">
                <div class="order-customer">{{ maskCustomer(order.customer) }}</div>
                <div class="order-location">
                  <el-icon><Location /></el-icon>
                  {{ order.country }} · {{ order.city }}
                </div>
              </div>
              <div class="order-amount">
                <div class="amount">¥{{ order.amount }}</div>
                <div class="time">{{ order.time }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="chart-card">
          <div class="chart-title">
            <span class="title-icon orange"></span>
            交付时效
          </div>
          <div class="delivery-stats">
            <div class="delivery-item">
              <div class="delivery-icon">
                <el-icon><Van /></el-icon>
              </div>
              <div class="delivery-info">
                <div class="delivery-label">平均交付</div>
                <div class="delivery-value">5.2<span class="unit">天</span></div>
              </div>
            </div>
            <div class="delivery-item">
              <div class="delivery-icon green">
                <el-icon><CircleCheck /></el-icon>
              </div>
              <div class="delivery-info">
                <div class="delivery-label">准时率</div>
                <div class="delivery-value">94.8<span class="unit">%</span></div>
              </div>
            </div>
            <div class="delivery-item">
              <div class="delivery-icon blue">
                <el-icon><Box /></el-icon>
              </div>
              <div class="delivery-info">
                <div class="delivery-label">在途订单</div>
                <div class="delivery-value">1,247<span class="unit">单</span></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { 
  ArrowUp, ArrowDown, Location, ShoppingCart, Money, User, Timer,
  MapLocation, Van, CircleCheck, Box, TrendCharts, Goods, Close
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'

// ==================== 统计数据 ====================
const stats = reactive({
  orderCount: 1547,
  salesAmount: 9871.75,
  avgOrderValue: 182.5,
  onlineUsers: 328
})

// ==================== 选中地区 ====================
const selectedRegion = ref(null)
const regionChartRef = ref(null)
let regionChart = null

// 地区数据
const regionData = {
  '中国': { name: '中国', orders: 456, sales: 82345.67, avgOrder: 180.6, topCategory: '数码电子', trend: [120, 132, 101, 134, 90, 230, 210] },
  '马来西亚': { name: '马来西亚', orders: 234, sales: 45678.90, avgOrder: 195.2, topCategory: '美妆护肤', trend: [80, 95, 110, 125, 140, 135, 150] },
  '美国': { name: '美国', orders: 328, sales: 98765.43, avgOrder: 301.1, topCategory: '户外运动', trend: [150, 180, 200, 190, 220, 240, 230] },
  '新加坡': { name: '新加坡', orders: 156, sales: 34567.89, avgOrder: 221.6, topCategory: '家居用品', trend: [60, 70, 85, 90, 95, 100, 110] },
  '泰国': { name: '泰国', orders: 189, sales: 28901.23, avgOrder: 152.9, topCategory: '食品饮料', trend: [70, 80, 75, 90, 100, 110, 105] },
  '英国': { name: '英国', orders: 145, sales: 41234.56, avgOrder: 284.4, topCategory: '时尚服饰', trend: [50, 60, 70, 80, 90, 85, 95] },
  '印尼': { name: '印尼', orders: 267, sales: 35678.90, avgOrder: 133.6, topCategory: '母婴用品', trend: [90, 100, 110, 105, 120, 130, 125] },
}

// ==================== 实时订单 ====================
const realtimeOrders = reactive([
  { id: 1, platform: 'tiktok', customer: '张***', country: '中国', city: '深圳', amount: '299.00', time: '1分钟前' },
  { id: 2, platform: 'tiktok', customer: '李***', country: '马来西亚', city: '吉隆坡', amount: '187.50', time: '2分钟前' },
  { id: 3, platform: 'amazon', customer: 'John D.', country: '美国', city: '洛杉矶', amount: '456.00', time: '3分钟前' },
  { id: 4, platform: 'tiktok', customer: '王***', country: '中国', city: '上海', amount: '128.00', time: '4分钟前' },
  { id: 5, platform: 'shopee', customer: '陈***', country: '新加坡', city: '新加坡', amount: '234.50', time: '5分钟前' },
  { id: 6, platform: 'tiktok', customer: '刘***', country: '泰国', city: '曼谷', amount: '89.90', time: '6分钟前' },
  { id: 7, platform: 'amazon', customer: 'Emma W.', country: '英国', city: '伦敦', amount: '567.00', time: '7分钟前' },
  { id: 8, platform: 'tiktok', customer: '赵***', country: '中国', city: '杭州', amount: '199.00', time: '8分钟前' },
  { id: 9, platform: 'shopee', customer: '林***', country: '印尼', city: '雅加达', amount: '156.80', time: '9分钟前' },
  { id: 10, platform: 'tiktok', customer: '黄***', country: '马来西亚', city: '槟城', amount: '278.00', time: '10分钟前' },
])

const newOrderCount = ref(2)
const displayOrders = computed(() => realtimeOrders.slice(0, 8))

function maskCustomer(name) {
  if (name.length <= 2) return name + '***'
  return name.slice(0, 1) + '***' + name.slice(-1)
}

function getPlatformIcon(platform) {
  const icons = {
    tiktok: 'https://sf16-sg.tiktokcdn.com/obj/eden-sg/uhtyvueh7nulogpoguhm/tiktok-icon2.png',
    amazon: 'https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg',
    shopee: 'https://deo.shopeemobile.com/shopee/shopee-pcmall-live-sg/assets/icon_favicon_1_96.png'
  }
  return icons[platform] || ''
}

// ==================== 图表引用 ====================
const salesChartRef = ref(null)
const platformChartRef = ref(null)
const worldMapRef = ref(null)
let salesChart = null
let platformChart = null
let mapChart = null

// ==================== 格式化 ====================
function formatMoney(num) {
  return num.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

// ==================== 初始化图表 ====================
function initSalesChart() {
  salesChart = echarts.init(salesChartRef.value)
  const option = {
    backgroundColor: 'transparent',
    grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
    xAxis: {
      type: 'category',
      data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00'],
      axisLine: { lineStyle: { color: '#e0e6ed' } },
      axisLabel: { color: '#606266', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#f0f2f5' } },
      axisLabel: { color: '#606266', fontSize: 11 }
    },
    series: [{
      data: [120, 82, 191, 334, 290, 430, 310],
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: { color: '#085B9C', width: 3 },
      itemStyle: { color: '#085B9C', borderWidth: 2, borderColor: '#fff' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(8,91,156,0.3)' },
          { offset: 1, color: 'rgba(8,91,156,0.05)' }
        ])
      }
    }]
  }
  salesChart.setOption(option)
}

function initPlatformChart() {
  platformChart = echarts.init(platformChartRef.value)
  const option = {
    backgroundColor: 'transparent',
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '50%'],
      data: [
        { value: 45, name: 'TikTok', itemStyle: { color: '#2ead3e' } },
        { value: 25, name: 'Amazon', itemStyle: { color: '#085B9C' } },
        { value: 20, name: 'Shopee', itemStyle: { color: '#ee5a24' } },
        { value: 10, name: '其他', itemStyle: { color: '#74b9ff' } }
      ],
      label: { color: '#606266', fontSize: 12 },
      labelLine: { lineStyle: { color: '#d0d7de' } }
    }]
  }
  platformChart.setOption(option)
}

// 高亮地区
function highlightRegion(country) {
  if (regionData[country]) {
    selectedRegion.value = regionData[country]
    // 高亮地图上的对应区域
    if (mapChart) {
      const countryMap = {
        '中国': 'China',
        '马来西亚': 'Malaysia',
        '美国': 'United States',
        '新加坡': 'Singapore',
        '泰国': 'Thailand',
        '英国': 'United Kingdom',
        '印尼': 'Indonesia'
      }
      const mapName = countryMap[country]
      if (mapName) {
        mapChart.dispatchAction({
          type: 'highlight',
          name: mapName
        })
        setTimeout(() => {
          mapChart.dispatchAction({
            type: 'downplay',
            name: mapName
          })
        }, 2000)
      }
    }
    // 初始化地区图表
    setTimeout(() => {
      initRegionChart()
    }, 100)
  }
}

// 初始化地区趋势图
function initRegionChart() {
  if (!regionChartRef.value || !selectedRegion.value) return
  
  if (regionChart) {
    regionChart.dispose()
  }
  
  regionChart = echarts.init(regionChartRef.value)
  const option = {
    backgroundColor: 'transparent',
    grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
    xAxis: {
      type: 'category',
      data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
      axisLine: { lineStyle: { color: '#e0e6ed' } },
      axisLabel: { color: '#606266', fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#f0f2f5' } },
      axisLabel: { color: '#606266', fontSize: 10 }
    },
    series: [{
      data: selectedRegion.value.trend,
      type: 'bar',
      barWidth: '60%',
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#2ead3e' },
          { offset: 1, color: '#085B9C' }
        ]),
        borderRadius: [4, 4, 0, 0]
      }
    }]
  }
  regionChart.setOption(option)
}

async function initWorldMap() {
  // 加载世界地图数据
  try {
    const response = await fetch('https://cdn.jsdelivr.net/npm/echarts/map/json/world.json')
    const worldJson = await response.json()
    echarts.registerMap('world', worldJson)
  } catch (e) {
    console.log('使用简化地图')
  }

  mapChart = echarts.init(worldMapRef.value)
  
  const mapData = [
    { name: 'China', value: 456, cnName: '中国' },
    { name: 'United States', value: 328, cnName: '美国' },
    { name: 'United Kingdom', value: 156, cnName: '英国' },
    { name: 'Germany', value: 89, cnName: '德国' },
    { name: 'France', value: 76, cnName: '法国' },
    { name: 'Japan', value: 234, cnName: '日本' },
    { name: 'South Korea', value: 178, cnName: '韩国' },
    { name: 'Singapore', value: 145, cnName: '新加坡' },
    { name: 'Malaysia', value: 234, cnName: '马来西亚' },
    { name: 'Thailand', value: 189, cnName: '泰国' },
    { name: 'Indonesia', value: 267, cnName: '印尼' },
    { name: 'Australia', value: 67, cnName: '澳洲' },
    { name: 'Canada', value: 54, cnName: '加拿大' },
    { name: 'Brazil', value: 43, cnName: '巴西' },
    { name: 'India', value: 198, cnName: '印度' },
  ]

  const option = {
    backgroundColor: 'transparent',
    geo: {
      map: 'world',
      roam: true,
      zoom: 1.2,
      label: { show: false },
      itemStyle: {
        areaColor: '#e8f4fc',
        borderColor: '#085B9C',
        borderWidth: 0.5
      },
      emphasis: {
        itemStyle: {
          areaColor: '#2ead3e'
        },
        label: {
          show: true,
          color: '#fff'
        }
      }
    },
    visualMap: {
      min: 0,
      max: 500,
      left: 'left',
      bottom: 'bottom',
      text: ['高', '低'],
      textStyle: { color: '#606266' },
      inRange: {
        color: ['#e8f4fc', '#a9cdeb', '#085B9C']
      },
      calculable: true
    },
    series: [{
      type: 'map',
      geoIndex: 0,
      data: mapData
    }, {
      type: 'effectScatter',
      coordinateSystem: 'geo',
      data: [
        { name: '深圳', value: [114.0579, 22.5431, 299] },
        { name: '吉隆坡', value: [101.6869, 3.139, 187] },
        { name: '洛杉矶', value: [-118.2437, 34.0522, 456] },
        { name: '上海', value: [121.4737, 31.2304, 128] },
        { name: '新加坡', value: [103.8198, 1.3521, 234] },
        { name: '曼谷', value: [100.5018, 13.7563, 89] },
        { name: '伦敦', value: [-0.1276, 51.5074, 567] },
        { name: '雅加达', value: [106.8456, -6.2088, 278] },
      ],
      symbolSize: function (val) {
        return val[2] / 25
      },
      rippleEffect: {
        brushType: 'stroke',
        scale: 3,
        period: 4
      },
      itemStyle: {
        color: '#2ead3e'
      }
    }]
  }
  
  mapChart.setOption(option)
  
  // 点击地图事件
  mapChart.on('click', function(params) {
    const countryMap = {
      'China': '中国',
      'Malaysia': '马来西亚',
      'United States': '美国',
      'Singapore': '新加坡',
      'Thailand': '泰国',
      'United Kingdom': '英国',
      'Indonesia': '印尼'
    }
    const cnName = countryMap[params.name]
    if (cnName && regionData[cnName]) {
      selectedRegion.value = regionData[cnName]
      setTimeout(() => {
        initRegionChart()
      }, 100)
    }
  })
}

// ==================== 模拟实时数据更新 ====================
let timers = []

function startRealtimeUpdate() {
  // 模拟新订单
  timers.push(setInterval(() => {
    const platforms = ['tiktok', 'amazon', 'shopee']
    const countries = ['中国', '马来西亚', '美国', '新加坡', '泰国', '印尼', '英国']
    const cities = ['深圳', '洛杉矶', '吉隆坡', '新加坡', '曼谷', '雅加达', '伦敦', '上海']
    const names = ['张', '李', '王', '陈', '刘', '赵', '黄', '林', 'John', 'Emma']
    
    const newOrder = {
      id: Date.now(),
      platform: platforms[Math.floor(Math.random() * platforms.length)],
      customer: names[Math.floor(Math.random() * names.length)] + '***',
      country: countries[Math.floor(Math.random() * countries.length)],
      city: cities[Math.floor(Math.random() * cities.length)],
      amount: (Math.random() * 500 + 50).toFixed(2),
      time: '刚刚'
    }
    
    realtimeOrders.unshift(newOrder)
    if (realtimeOrders.length > 20) realtimeOrders.pop()
    
    newOrderCount.value = 1
    setTimeout(() => newOrderCount.value = 0, 1000)
    
    // 更新统计
    stats.orderCount++
    stats.salesAmount += parseFloat(newOrder.amount)
    
    // 高亮地图对应区域
    highlightRegion(newOrder.country)
  }, 5000))
}

// ==================== 生命周期 ====================
onMounted(() => {
  initSalesChart()
  initPlatformChart()
  initWorldMap()
  startRealtimeUpdate()
  
  window.addEventListener('resize', () => {
    salesChart?.resize()
    platformChart?.resize()
    mapChart?.resize()
    regionChart?.resize()
  })
})

onUnmounted(() => {
  timers.forEach(t => clearInterval(t))
  salesChart?.dispose()
  platformChart?.dispose()
  mapChart?.dispose()
  regionChart?.dispose()
})
</script>

<style scoped>
.dashboard-container {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 20px;
}

/* 顶部统计栏 */
.stats-header {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #fff;
}

.stat-icon.blue {
  background: linear-gradient(135deg, #085B9C, #4a8ed4);
}

.stat-icon.green {
  background: linear-gradient(135deg, #2ead3e, #5bc75e);
}

.stat-icon.orange {
  background: linear-gradient(135deg, #ee5a24, #f39c12);
}

.stat-icon.purple {
  background: linear-gradient(135deg, #8e44ad, #bb8fce);
}

.stat-info {
  flex: 1;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 4px;
}

.stat-value {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.stat-value .number {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
}

.stat-value .currency {
  font-size: 16px;
  font-weight: 600;
  color: #606266;
}

.stat-value .unit {
  font-size: 14px;
  color: #909399;
  margin-left: 2px;
}

.stat-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  margin-top: 4px;
}

.stat-trend.up {
  color: #2ead3e;
}

.stat-trend.down {
  color: #f56c6c;
}

/* 主内容区 */
.main-content {
  display: grid;
  grid-template-columns: 280px 1fr 320px;
  gap: 20px;
}

/* 左侧面板 */
.left-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 右侧面板 */
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 图表卡片 */
.chart-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}

.chart-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

.title-icon {
  width: 4px;
  height: 16px;
  border-radius: 2px;
}

.title-icon.blue {
  background: #085B9C;
}

.title-icon.green {
  background: #2ead3e;
}

.title-icon.orange {
  background: #ee5a24;
}

.chart-container {
  height: 180px;
}

/* 中间地图 */
.center-panel {
  position: relative;
}

.map-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  height: 100%;
  position: relative;
}

.map-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.map-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.map-title .el-icon {
  color: #085B9C;
}

.selected-tag {
  background: linear-gradient(135deg, #2ead3e, #085B9C);
  color: #fff;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.map-legend {
  display: flex;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #606266;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot.hot {
  background: #2ead3e;
}

.dot.normal {
  background: #085B9C;
}

.dot.new {
  background: #ee5a24;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.map-container {
  height: calc(100% - 50px);
  min-height: 400px;
}

/* 地区详情面板 */
.region-panel {
  position: absolute;
  right: 20px;
  top: 60px;
  width: 260px;
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  z-index: 100;
}

.region-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

.region-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.region-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 16px;
}

.region-stat {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-icon-small {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: #f0f7ff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #085B9C;
  font-size: 14px;
}

.stat-icon-small.green {
  background: #f0fff4;
  color: #2ead3e;
}

.stat-icon-small.orange {
  background: #fff7f0;
  color: #ee5a24;
}

.stat-icon-small.purple {
  background: #f9f0ff;
  color: #8e44ad;
}

.stat-content {
  flex: 1;
}

.stat-label-small {
  font-size: 11px;
  color: #909399;
  margin-bottom: 2px;
}

.stat-value-small {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
}

.region-chart {
  height: 100px;
}

.mini-chart {
  width: 100%;
  height: 100%;
}

/* 实时订单 */
.order-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  flex: 1;
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.order-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: #2ead3e;
  border-radius: 50%;
  animation: pulse-dot 1.5s infinite;
}

@keyframes pulse-dot {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.5); opacity: 0.5; }
  100% { transform: scale(1); opacity: 1; }
}

.order-count {
  font-size: 12px;
  color: #909399;
}

.order-list {
  max-height: 320px;
  overflow-y: auto;
}

.order-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 8px;
  background: #f5f7fa;
  transition: all 0.3s;
  cursor: pointer;
}

.order-item:hover {
  background: #e8f4fc;
  transform: translateX(4px);
}

.order-item.new-order {
  background: linear-gradient(90deg, #f0fff4, #e8f4fc);
  animation: slideIn 0.5s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.order-platform {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  overflow: hidden;
}

.order-platform img {
  width: 20px;
  height: 20px;
  object-fit: contain;
}

.order-info {
  flex: 1;
  min-width: 0;
}

.order-customer {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.order-location {
  font-size: 11px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 4px;
}

.order-amount {
  text-align: right;
}

.order-amount .amount {
  font-size: 14px;
  font-weight: 600;
  color: #f56c6c;
  margin-bottom: 2px;
}

.order-amount .time {
  font-size: 11px;
  color: #c0c4cc;
}

/* 交付时效 */
.delivery-stats {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.delivery-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.delivery-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: #e8f4fc;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #085B9C;
  font-size: 18px;
}

.delivery-icon.green {
  background: #f0fff4;
  color: #2ead3e;
}

.delivery-icon.blue {
  background: #f0f7ff;
  color: #085B9C;
}

.delivery-info {
  flex: 1;
}

.delivery-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 2px;
}

.delivery-value {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
}

.delivery-value .unit {
  font-size: 12px;
  font-weight: 400;
  color: #909399;
  margin-left: 2px;
}
</style>