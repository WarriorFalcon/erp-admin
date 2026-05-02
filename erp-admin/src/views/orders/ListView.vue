<template>
  <div class="page-container">
    <!-- 页面Header -->
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">订单管理</h1>
        <p class="page-desc">全链路状态追踪 · 多平台订单聚合</p>
      </div>
      <div class="page-header-right">
        <el-button @click="handleExport">
          <el-icon><Download /></el-icon>
          导出
        </el-button>
      </div>
    </div>

    <!-- 状态卡片 -->
    <div class="status-cards">
      <div class="status-card" :class="{ active: filterForm.status === 'pending' }" @click="setStatusFilter('pending')">
        <div class="status-icon pending"><el-icon><Clock /></el-icon></div>
        <div class="status-info">
          <div class="status-num">{{ statusCounts.pending }}</div>
          <div class="status-label">待审核</div>
        </div>
      </div>
      <div class="status-card" :class="{ active: filterForm.status === 'paid' }" @click="setStatusFilter('paid')">
        <div class="status-icon waiting"><el-icon><Box /></el-icon></div>
        <div class="status-info">
          <div class="status-num">{{ statusCounts.paid }}</div>
          <div class="status-label">待发货</div>
        </div>
      </div>
      <div class="status-card" :class="{ active: filterForm.status === 'exception' }" @click="setStatusFilter('exception')">
        <div class="status-icon exception"><el-icon><WarningFilled /></el-icon></div>
        <div class="status-info">
          <div class="status-num">{{ statusCounts.exception }}</div>
          <div class="status-label">物流异常</div>
        </div>
      </div>
      <div class="status-card" :class="{ active: filterForm.status === 'completed' }" @click="setStatusFilter('completed')">
        <div class="status-icon completed"><el-icon><CircleCheck /></el-icon></div>
        <div class="status-info">
          <div class="status-num">{{ statusCounts.completed }}</div>
          <div class="status-label">已完成</div>
        </div>
      </div>
    </div>

    <!-- 筛选区 -->
    <div class="filter-card">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="关键词">
          <el-input id="orderKeyword" v-model="filterForm.keyword" placeholder="订单号/买家/SKU" clearable @keyup.enter="loadData" style="width:180px" />
        </el-form-item>
        <el-form-item label="平台">
          <el-select id="orderPlatform" v-model="filterForm.platform" placeholder="全部平台" clearable style="width:140px">
            <el-option label="全部" value="" />
            <el-option label="TikTok" value="TikTok">
              <span style="display:flex;align-items:center;gap:4px"><img src="/platform-icons/tiktok.svg" style="width:16px;height:16px;object-fit:contain" /> TikTok</span>
            </el-option>
            <el-option label="Amazon" value="Amazon">
              <span style="display:flex;align-items:center;gap:4px"><img src="/platform-icons/amazon.svg" style="width:16px;height:16px;object-fit:contain" /> Amazon</span>
            </el-option>
            <el-option label="Shopee" value="Shopee">
              <span style="display:flex;align-items:center;gap:4px"><img src="/platform-icons/shopee.svg" style="width:16px;height:16px;object-fit:contain" /> Shopee</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="时间类型">
          <el-select id="orderTimeType" v-model="filterForm.timeType" style="width:120px">
            <el-option label="下单时间" value="order" />
            <el-option label="付款时间" value="paid" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="filterForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width:240px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 订单列表 -->
    <div class="list-card">
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column label="订单号" width="180">
          <template #default="{ row }">
            <span class="order-id">{{ row.orderId }}</span>
          </template>
        </el-table-column>
        <el-table-column label="平台" width="110" align="center">
          <template #default="{ row }">
            <el-tag class="platform-tag" :style="{ background: getPlatformColor(row.platform) + '18', color: getPlatformColor(row.platform) }">
              <img :src="getPlatformIcon(row.platform)" class="platform-img" :alt="row.platform" />
              {{ row.platform }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="买家信息" min-width="180">
          <template #default="{ row }">
            <div class="buyer-info">
              <span class="buyer-name">{{ row.buyerName }}</span>
              <span class="buyer-phone">{{ row.buyerPhone }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="SKU" min-width="120">
          <template #default="{ row }">
            <span class="sku-text">{{ row.sku }}</span>
          </template>
        </el-table-column>
        <el-table-column label="数量" width="70" align="center">
          <template #default="{ row }">
            <span>{{ row.quantity }}</span>
          </template>
        </el-table-column>
        <el-table-column label="订单金额" width="110" align="right">
          <template #default="{ row }">
            <span class="amount">¥{{ Number(row.amount).toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.statusType" size="small" effect="light">{{ row.statusLabel }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="下单时间" width="160">
          <template #default="{ row }">
            <span class="date-text">{{ row.orderTime }}</span>
          </template>
        </el-table-column>
        <el-table-column label="收货地" min-width="120" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="address-text">{{ row.address }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" text size="small" @click="handleView(row)">详情</el-button>
            <el-button
              v-if="row.status === 'paid'"
              type="success"
              text
              size="small"
              @click="handleShip(row)"
            >
              发货
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          :page-size="pagination.pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="loadData"
        />
      </div>
    </div>

    <!-- 订单详情抽屉 -->
    <el-drawer v-model="drawerVisible" title="订单详情" size="520px" direction="rtl">
      <div v-if="currentOrder" class="order-detail">
        <!-- 基本信息 -->
        <div class="detail-section">
          <h4>
            <el-icon><Document /></el-icon>
            基本信息
          </h4>
          <div class="detail-grid">
            <div class="detail-item">
              <span class="detail-label">订单号</span>
              <span class="detail-value mono">{{ currentOrder.orderId }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">平台</span>
              <el-tag :style="{ background: getPlatformColor(currentOrder.platform) + '18', color: getPlatformColor(currentOrder.platform) }">
                <img :src="getPlatformIcon(currentOrder.platform)" class="platform-img" :alt="currentOrder.platform" /> {{ currentOrder.platform }}
              </el-tag>
            </div>
            <div class="detail-item">
              <span class="detail-label">下单时间</span>
              <span class="detail-value">{{ currentOrder.orderTime }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">付款时间</span>
              <span class="detail-value">{{ currentOrder.paidTime || '未付款' }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">订单状态</span>
              <el-tag :type="currentOrder.statusType" size="small">{{ currentOrder.statusLabel }}</el-tag>
            </div>
          </div>
        </div>

        <!-- 买家信息 -->
        <div class="detail-section">
          <h4>
            <el-icon><User /></el-icon>
            买家信息
          </h4>
          <div class="detail-grid">
            <div class="detail-item">
              <span class="detail-label">买家姓名</span>
              <span class="detail-value">{{ currentOrder.buyerName }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">联系电话</span>
              <span class="detail-value">{{ currentOrder.buyerPhone }}</span>
            </div>
            <div class="detail-item full">
              <span class="detail-label">收货地址</span>
              <span class="detail-value">{{ currentOrder.address }}</span>
            </div>
          </div>
        </div>

        <!-- 商品清单 -->
        <div class="detail-section">
          <h4>
            <el-icon><Goods /></el-icon>
            商品清单
          </h4>
          <div class="product-list">
            <div v-for="item in currentOrder.items" :key="item.sku" class="product-item">
              <div class="product-img">
                <el-image :src="item.image" fit="cover" style="width:60px;height:60px;border-radius:8px">
                  <template #error>
                    <div class="img-placeholder">📦</div>
                  </template>
                </el-image>
              </div>
              <div class="product-info">
                <div class="product-name">{{ item.name }}</div>
                <div class="product-sku">SKU: {{ item.sku }}</div>
                <div class="product-price">¥{{ item.price }} × {{ item.qty }}</div>
              </div>
            </div>
          </div>
          <div class="order-total">
            <span>订单合计：</span>
            <span class="total-amount">¥{{ Number(currentOrder.amount).toFixed(2) }}</span>
          </div>
        </div>

        <!-- 物流信息 -->
        <div v-if="currentOrder.trackingNo" class="detail-section">
          <h4>
            <el-icon><Van /></el-icon>
            物流信息
          </h4>
          <div class="detail-grid">
            <div class="detail-item">
              <span class="detail-label">运单号</span>
              <span class="detail-value mono">{{ currentOrder.trackingNo }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">物流商</span>
              <span class="detail-value">{{ currentOrder.carrier }}</span>
            </div>
          </div>
        </div>

        <!-- 买家留言 -->
        <div v-if="currentOrder.buyerNote" class="detail-section">
          <h4>
            <el-icon><ChatLineRound /></el-icon>
            买家留言
          </h4>
          <el-alert :title="currentOrder.buyerNote" type="info" :closable="false" />
        </div>

        <!-- 订单修改日志 -->
        <div class="detail-section">
          <h4>
            <el-icon><Clock /></el-icon>
            操作日志
          </h4>
          <el-timeline>
            <el-timeline-item
              v-for="(log, idx) in currentOrder.logs"
              :key="idx"
              :timestamp="log.time"
              :type="log.type"
              size="small"
            >
              <div class="log-content">
                <span class="log-action">{{ log.action }}</span>
                <span class="log-operator">by {{ log.operator }}</span>
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Clock, Box, WarningFilled, CircleCheck, Download, Search, Document, User, Goods, Van, ChatLineRound } from '@element-plus/icons-vue'
import { getOrderList, getOrderStatusCounts, getOrderDetail } from '@/api/order'
import { getPlatformIcon, getPlatformColor } from '@/utils/platformIcons'

// ==================== 状态 ====================
const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const drawerVisible = ref(false)
const currentOrder = ref(null)
const statusCounts = ref({ pending: 0, paid: 0, exception: 0, completed: 0 })

const filterForm = reactive({ keyword: '', platform: '', timeType: 'order', dateRange: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 10 })

// ==================== 方法 ====================
function setStatusFilter(status) {
  if (filterForm.status === status) {
    filterForm.status = ''
  } else {
    filterForm.status = status
  }
  pagination.page = 1
  loadData()
}

// 加载状态统计
async function loadStatusCounts() {
  try {
    const res = await getOrderStatusCounts()
    if (res.code === 200) {
      statusCounts.value = res.data
    }
  } catch (e) {
    console.error('获取状态统计失败:', e)
  }
}

async function loadData() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      pageSize: pagination.pageSize,
      keyword: filterForm.keyword,
      platform: filterForm.platform,
      status: filterForm.status,
      timeType: filterForm.timeType,
      dateRange: filterForm.dateRange
    }
    const res = await getOrderList(params)
    if (res.code === 200) {
      // 适配后端数据格式到前端展示格式
      tableData.value = (res.data?.results || []).map(order => ({
        orderId: order.id,
        platform: order.platform,
        buyerName: order.buyer?.name || order.buyer,
        buyerPhone: order.buyer?.phone || order.phone,
        sku: order.products?.[0]?.sku || '',
        quantity: order.products?.reduce((sum, p) => sum + p.quantity, 0) || 0,
        amount: order.amount,
        status: order.status,
        statusLabel: order.status_text,
        statusType: getStatusType(order.status),
        orderTime: order.order_time,
        paidTime: order.pay_time,
        address: order.shipping?.address,
        trackingNo: order.shipping?.waybill_no,
        carrier: order.shipping?.carrier,
        buyerNote: order.buyer_message,
        items: order.products?.map(p => ({
          name: p.name,
          sku: p.sku,
          price: p.price,
          qty: p.quantity,
          image: p.image
        })) || [],
        logs: order.operation_logs?.map(log => ({
          time: log.time,
          action: log.action,
          operator: log.operator,
          type: log.type || 'primary'
        })) || []
      }))
      total.value = res.data.total
    }
  } catch (e) {
    ElMessage.error('获取订单列表失败')
    console.error(e)
  } finally {
    loading.value = false
  }
}

function getStatusType(status) {
  const map = {
    'pending': 'info',
    'paid': 'warning',
    'shipped': 'success',
    'completed': 'success',
    'exception': 'danger',
    'cancelled': 'danger'
  }
  return map[status] || 'info'
}

function resetFilter() {
  filterForm.keyword = ''
  filterForm.platform = ''
  filterForm.timeType = 'order'
  filterForm.dateRange = ''
  filterForm.status = ''
  pagination.page = 1
  loadData()
}

async function handleView(row) {
  try {
    const res = await getOrderDetail(row.orderId)
    if (res.code === 200) {
      const order = res.data
      currentOrder.value = {
        orderId: order.id,
        platform: order.platform,
        buyerName: order.buyer?.name,
        buyerPhone: order.buyer?.phone,
        amount: order.amount,
        status: order.status,
        statusLabel: order.status_text,
        statusType: getStatusType(order.status),
        orderTime: order.order_time,
        paidTime: order.pay_time,
        address: order.shipping?.address,
        trackingNo: order.shipping?.waybill_no,
        carrier: order.shipping?.carrier,
        buyerNote: order.buyer_message,
        items: order.products?.map(p => ({
          name: p.name,
          sku: p.sku,
          price: p.price,
          qty: p.quantity,
          image: p.image
        })) || [],
        logs: order.operation_logs?.map(log => ({
          time: log.time,
          action: log.action,
          operator: log.operator,
          type: log.type || 'primary'
        })) || []
      }
      drawerVisible.value = true
    }
  } catch (e) {
    // 如果详情接口报错，直接用列表数据
    currentOrder.value = row
    drawerVisible.value = true
  }
}

function handleShip(row) {
  ElMessage.success(`订单 ${row.orderId} 发货操作已提交`)
  loadData()
}

function handleExport() {
  ElMessage.success('导出任务已创建，请稍后下载')
}

onMounted(() => {
  loadStatusCounts()
  loadData()
})
</script>

<style scoped>
/* 状态卡片 */
.status-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}
.status-card {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
  box-shadow: var(--shadow-xs);
}
.status-card:hover {
  box-shadow: var(--shadow-sm);
  transform: translateY(-2px);
}
.status-card.active {
  border-color: var(--brand);
  background: linear-gradient(135deg, rgba(8,91,156,0.05) 0%, rgba(46,173,62,0.05) 100%);
}
.status-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}
.status-icon.pending { background: #EFF6FF; color: #3B82F6; }
.status-icon.waiting { background: #FFF7ED; color: #F59E0B; }
.status-icon.exception { background: #FEF2F2; color: #EF4444; }
.status-icon.completed { background: #F0FDF4; color: #22C55E; }
.status-num {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
}
.status-label {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 4px;
}

/* 筛选区 */
.filter-card {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 16px;
  box-shadow: var(--shadow-xs);
}

/* 列表卡片 */
.list-card {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 20px;
  box-shadow: var(--shadow-xs);
}
.order-id { font-family: monospace; font-size: 13px; color: var(--brand); font-weight: 600; }
.platform-tag {
  font-size: 12px;
  font-weight: 600;
  border: none;
  border-radius: 6px;
  padding: 3px 10px;
}
.platform-img {
  width: 16px;
  height: 16px;
  margin-right: 4px;
  vertical-align: middle;
  object-fit: contain;
}
.buyer-info { display: flex; flex-direction: column; gap: 2px; }
.buyer-name { font-size: 14px; color: var(--text-primary); }
.buyer-phone { font-size: 12px; color: var(--text-muted); }
.sku-text { font-family: monospace; font-size: 12px; color: var(--text-secondary); }
.amount { font-weight: 600; color: var(--danger); }
.date-text { font-size: 12px; color: var(--text-muted); }
.address-text { font-size: 13px; color: var(--text-secondary); }
.pagination-wrap { display: flex; justify-content: flex-end; margin-top: 16px; }

/* 详情抽屉 */
.order-detail { display: flex; flex-direction: column; gap: 24px; }
.detail-section h4 {
  font-size: 14px;
  color: var(--text-primary);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 6px;
}
.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.detail-item { display: flex; flex-direction: column; gap: 4px; }
.detail-item.full { grid-column: 1 / -1; }
.detail-label { font-size: 12px; color: var(--text-muted); }
.detail-value { font-size: 14px; color: var(--text-primary); }
.detail-value.mono { font-family: monospace; font-size: 13px; color: var(--brand); }

.product-list { display: flex; flex-direction: column; gap: 12px; }
.product-item { display: flex; gap: 12px; padding: 12px; background: var(--bg-page); border-radius: 10px; }
.product-img { flex-shrink: 0; }
.img-placeholder { width: 60px; height: 60px; background: #f0f0f0; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 24px; }
.product-info { flex: 1; display: flex; flex-direction: column; gap: 4px; }
.product-name { font-size: 14px; color: var(--text-primary); font-weight: 500; }
.product-sku { font-size: 12px; color: var(--text-muted); font-family: monospace; }
.product-price { font-size: 13px; color: var(--text-secondary); }
.order-total { display: flex; justify-content: flex-end; align-items: center; gap: 8px; margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border); font-size: 14px; }
.total-amount { font-size: 18px; font-weight: 700; color: var(--danger); }

.log-content { display: flex; flex-direction: column; gap: 2px; }
.log-action { font-size: 13px; color: var(--text-primary); }
.log-operator { font-size: 12px; color: var(--text-muted); }
</style>
