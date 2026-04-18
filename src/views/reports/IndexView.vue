<template>
  <div class="page-container">
    <!-- 页面Header -->
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">数据报表</h1>
        <p class="page-desc">全链路经营数据洞察</p>
      </div>
      <div class="page-header-right">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          @change="loadData"
          style="width:260px"
        />
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card stat-collect">
          <div class="stat-icon"><el-icon><ShoppingCart /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">1,234</div>
            <div class="stat-label">采集商品数</div>
            <div class="stat-trend up"><el-icon><Top /></el-icon> +12%</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card stat-goods">
          <div class="stat-icon"><el-icon><Goods /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">5,678</div>
            <div class="stat-label">上货商品数</div>
            <div class="stat-trend up"><el-icon><Top /></el-icon> +8%</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card stat-order">
          <div class="stat-icon"><el-icon><List /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">892</div>
            <div class="stat-label">总订单数</div>
            <div class="stat-trend down"><el-icon><Bottom /></el-icon> -3%</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card stat-sales">
          <div class="stat-icon"><el-icon><Money /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">¥45.2k</div>
            <div class="stat-label">总销售额</div>
            <div class="stat-trend up"><el-icon><Top /></el-icon> +15%</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区 -->
    <el-row :gutter="16" class="chart-row">
      <!-- 销售趋势 -->
      <el-col :xs="24" :lg="16">
        <div class="chart-card">
          <div class="chart-header">
            <span class="chart-title">📈 销售趋势</span>
            <el-radio-group v-model="chartPeriod" size="small" @change="loadData">
              <el-radio-button value="7d">近7天</el-radio-button>
              <el-radio-button value="30d">近30天</el-radio-button>
            </el-radio-group>
          </div>
          <div class="chart-body">
            <v-chart :option="salesChartOption" autoresize style="height:280px" />
          </div>
        </div>
      </el-col>

      <!-- 平台分布 -->
      <el-col :xs="24" :lg="8">
        <div class="chart-card">
          <div class="chart-header">
            <span class="chart-title">🥧 平台分布</span>
          </div>
          <div class="chart-body">
            <v-chart :option="platformChartOption" autoresize style="height:280px" />
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="chart-row">
      <!-- 库存预警 -->
      <el-col :xs="24" :lg="12">
        <div class="chart-card">
          <div class="chart-header">
            <span class="chart-title">⚠️ 库存预警 TOP10</span>
          </div>
          <div class="chart-body">
            <el-table :data="alertItems" size="small" max-height="260">
              <el-table-column label="商品名称" min-width="200" show-overflow-tooltip />
              <el-table-column label="SKU" width="120">
                <template #default="{ row }">
                  <span style="font-size:12px;color:var(--brand)">{{ row.skuId }}</span>
                </template>
              </el-table-column>
              <el-table-column label="当前库存" width="90" align="center">
                <template #default="{ row }">
                  <span :style="{ color: row.status === 'out' ? 'var(--danger)' : 'var(--warning)', fontWeight: 600 }">
                    {{ row.stock }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="安全库存" width="90" align="center" />
              <el-table-column label="状态" width="80" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.status === 'out' ? 'danger' : 'warning'" size="small">
                    {{ row.status === 'out' ? '缺货' : '预警' }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-col>

      <!-- 热销商品 -->
      <el-col :xs="24" :lg="12">
        <div class="chart-card">
          <div class="chart-header">
            <span class="chart-title">🏆 热销商品 TOP10</span>
          </div>
          <div class="chart-body">
            <v-chart :option="hotProductsChartOption" autoresize style="height:260px" />
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart, BarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'

use([CanvasRenderer, LineChart, PieChart, BarChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const dateRange = ref([])
const chartPeriod = ref('7d')
const alertItems = ref([])

// Mock 热销数据
const hotProducts = ref([
  { name: '便携充电宝', sales: 234 },
  { name: '蓝牙耳机', sales: 189 },
  { name: '智能手环', sales: 156 },
  { name: '快充数据线', sales: 132 },
  { name: '迷你音箱', sales: 98 },
  { name: '无线充电器', sales: 87 },
  { name: '扩展坞', sales: 76 },
  { name: '收纳支架', sales: 65 },
  { name: '手机镜头', sales: 54 },
  { name: '手写笔', sales: 43 },
])

const salesChartOption = computed(() => {
  const days = chartPeriod.value === '7d' ? 7 : 30
  const labels = Array.from({ length: days }, (_, i) => {
    const d = new Date()
    d.setDate(d.getDate() - (days - 1 - i))
    return `${d.getMonth() + 1}/${d.getDate()}`
  })
  const salesData = [2100, 2800, 2400, 3100, 2900, 3600, 3200, 4100, 3800, 4500, 4200, 4800, 4400, 5100, 4600, 5300, 4900, 5600, 5200, 5800, 5400, 6000, 5700, 6300, 5900, 6500, 6200, 6800, 6400, 7000]
  const ordersData = [18, 24, 21, 28, 26, 32, 29, 37, 34, 41, 38, 45, 42, 48, 44, 52, 48, 55, 51, 58, 54, 62, 58, 65, 61, 68, 64, 72, 68, 75]

  return {
    tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#e5e7eb', textStyle: { color: '#374151' } },
    legend: { data: ['销售额(¥)', '订单数'], bottom: 0, textStyle: { color: '#6b7280', fontSize: 12 } },
    grid: { left: 50, right: 20, top: 10, bottom: 50 },
    xAxis: { type: 'category', data: labels.slice(-days), axisLine: { lineStyle: { color: '#e5e7eb' } }, axisLabel: { color: '#9ca3af', fontSize: 11 } },
    yAxis: [
      { type: 'value', name: '销售额', axisLine: { show: false }, splitLine: { lineStyle: { color: '#f0f0f0' } }, axisLabel: { color: '#9ca3af', fontSize: 11 } },
      { type: 'value', name: '订单数', axisLine: { show: false }, splitLine: { show: false }, axisLabel: { color: '#9ca3af', fontSize: 11 } },
    ],
    series: [
      {
        name: '销售额(¥)',
        type: 'line',
        data: salesData.slice(-days),
        smooth: true,
        lineStyle: { color: '#2563eb', width: 2.5 },
        areaStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [{ offset: 0, color: 'rgba(37,99,235,0.18)' }, { offset: 1, color: 'rgba(37,99,235,0)' }]
          }
        },
        itemStyle: { color: '#2563eb' }
      },
      {
        name: '订单数',
        type: 'line',
        yAxisIndex: 1,
        data: ordersData.slice(-days),
        smooth: true,
        lineStyle: { color: '#f97316', width: 2 },
        itemStyle: { color: '#f97316' }
      },
    ],
  }
})

const platformChartOption = computed(() => ({
  tooltip: { trigger: 'item', backgroundColor: '#fff', borderColor: '#e5e7eb', textStyle: { color: '#374151' } },
  legend: { bottom: 0, orient: 'vertical', right: 10, top: 'center', textStyle: { color: '#6b7280', fontSize: 12 } },
  series: [{
    type: 'pie',
    radius: ['45%', '75%'],
    center: ['35%', '50%'],
    label: { show: false },
    data: [
      { value: 42, name: 'TikTok Shop', itemStyle: { color: '#00f2ea' } },
      { value: 28, name: 'Amazon', itemStyle: { color: '#FF9900' } },
      { value: 15, name: 'Shopee', itemStyle: { color: '#EE4D2D' } },
      { value: 10, name: 'eBay', itemStyle: { color: '#E53238' } },
      { value: 5, name: '1688', itemStyle: { color: '#F55D23' } },
    ],
  }],
}))

const hotProductsChartOption = computed(() => ({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, backgroundColor: '#fff', borderColor: '#e5e7eb', textStyle: { color: '#374151' } },
  grid: { left: 100, right: 20, top: 10, bottom: 10 },
  xAxis: { type: 'value', axisLine: { show: false }, splitLine: { lineStyle: { color: '#f0f0f0' } }, axisLabel: { fontSize: 11, color: '#9ca3af' } },
  yAxis: { type: 'category', data: hotProducts.value.map((p) => p.name).reverse(), axisLine: { show: false }, axisTick: { show: false }, axisLabel: { fontSize: 11, color: '#6b7280' } },
  series: [{
    type: 'bar',
    data: hotProducts.value.map((p) => p.sales).reverse(),
    itemStyle: {
      color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{ offset: 0, color: '#2563eb' }, { offset: 1, color: '#3b82f6' }] },
      borderRadius: [0, 4, 4, 0]
    },
    barMaxWidth: 18,
  }],
}))

function loadData() {
  // Mock 预警数据
  alertItems.value = [
    { skuId: 'SKU100001', name: '便携式充电宝 20000mAh', stock: 3, safeStock: 20, status: 'low' },
    { skuId: 'SKU100003', name: '智能手表运动版', stock: 0, safeStock: 15, status: 'out' },
    { skuId: 'SKU100005', name: '迷你便携音箱', stock: 5, safeStock: 30, status: 'low' },
    { skuId: 'SKU100007', name: '无线充电器 折叠款', stock: 8, safeStock: 25, status: 'low' },
    { skuId: 'SKU100009', name: '智能手环 健康版', stock: 0, safeStock: 20, status: 'out' },
    { skuId: 'SKU100002', name: '无线蓝牙耳机 Pro', stock: 12, safeStock: 30, status: 'low' },
    { skuId: 'SKU100004', name: 'USB-C 快充数据线', stock: 20, safeStock: 50, status: 'low' },
    { skuId: 'SKU100006', name: '高清手机镜头套装', stock: 4, safeStock: 20, status: 'low' },
    { skuId: 'SKU100008', name: 'Type-C 多口扩展坞', stock: 7, safeStock: 20, status: 'low' },
    { skuId: 'SKU100010', name: '桌面收纳支架', stock: 0, safeStock: 15, status: 'out' },
  ]
}

onMounted(loadData)
</script>

<style scoped>
.stat-row { margin-bottom: 20px; }
.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  background: var(--bg-card);
  border-radius: var(--r-lg);
  padding: 20px;
  box-shadow: var(--shadow-xs);
}
.stat-icon {
  width: 48px; height: 48px;
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px;
  color: #fff;
}
.stat-collect .stat-icon { background: linear-gradient(135deg, #2563eb, #1d4ed8); }
.stat-goods .stat-icon { background: linear-gradient(135deg, #7c3aed, #6d28d9); }
.stat-order .stat-icon { background: linear-gradient(135deg, #0891b2, #0e7490); }
.stat-sales .stat-icon { background: linear-gradient(135deg, #16a34a, #15803d); }
.stat-info { flex: 1; }
.stat-value { font-size: 22px; font-weight: 700; color: var(--text-primary); }
.stat-label { font-size: 13px; color: var(--text-muted); margin-top: 2px; }
.stat-trend { font-size: 12px; font-weight: 500; margin-top: 4px; display: flex; align-items: center; gap: 2px; }
.stat-trend.up { color: var(--success); }
.stat-trend.down { color: var(--danger); }

.chart-row { margin-bottom: 16px; }
.chart-card {
  background: var(--bg-card);
  border-radius: var(--r-lg);
  padding: 20px;
  box-shadow: var(--shadow-xs);
}
.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.chart-title { font-size: 15px; font-weight: 600; color: var(--text-primary); }
.chart-body { width: 100%; }
</style>
