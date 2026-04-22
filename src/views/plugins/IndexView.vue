<template>
  <div class="plugins-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div>
        <h2 class="page-title">插件市场</h2>
        <p class="page-desc">
          按需扩展系统能力，插件独立运行，不污染主程序
        </p>
      </div>
      <div class="header-actions">
        <el-button @click="checkUpdates">
          <el-icon><Refresh /></el-icon>
          检查更新
        </el-button>
      </div>
    </div>

    <!-- 已安装插件 -->
    <div class="plugin-section">
      <div class="section-header">
        <h3 class="section-title">
          <el-icon><FolderChecked /></el-icon>
          已安装插件
          <el-tag type="info" size="small">{{ installedPlugins.length }}</el-tag>
        </h3>
      </div>

      <div v-if="installedPlugins.length === 0" class="empty-state">
        <el-empty description="暂无已安装插件" />
      </div>

      <div v-else class="plugin-grid">
        <div
          v-for="plugin in installedPlugins"
          :key="plugin.key"
          class="plugin-card installed"
        >
          <div class="plugin-icon-wrap">
            <img v-if="plugin.icon" :src="plugin.icon" class="plugin-icon" />
            <el-icon v-else :size="32"><Box /></el-icon>
          </div>
          <div class="plugin-content">
            <div class="plugin-name">{{ plugin.name }}</div>
            <div class="plugin-desc">{{ plugin.description }}</div>
            <div class="plugin-meta">
              <el-tag size="small" type="success">v{{ plugin.version }}</el-tag>
              <span class="plugin-author">by {{ plugin.author }}</span>
            </div>
          </div>
          <div class="plugin-actions">
            <el-switch
              :model-value="plugin.enabled"
              @change="togglePlugin(plugin)"
              size="small"
            />
            <el-dropdown trigger="click">
              <el-button text size="small">
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item>查看详情</el-dropdown-item>
                  <el-dropdown-item divided>卸载插件</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
    </div>

    <!-- 推荐插件（小白模式） -->
    <div v-mode="'beginner'" class="plugin-section">
      <div class="section-header">
        <h3 class="section-title">
          <el-icon><Star /></el-icon>
          官方必备插件包
          <el-tag type="warning" size="small">小白推荐</el-tag>
        </h3>
      </div>

      <div class="plugin-grid">
        <div
          v-for="plugin in recommendedPlugins"
          :key="plugin.key"
          class="plugin-card"
        >
          <div class="plugin-icon-wrap">
            <img v-if="plugin.icon" :src="plugin.icon" class="plugin-icon" />
            <el-icon v-else :size="32"><Box /></el-icon>
          </div>
          <div class="plugin-content">
            <div class="plugin-name">{{ plugin.name }}</div>
            <div class="plugin-desc">{{ plugin.description }}</div>
            <div class="plugin-meta">
              <el-tag size="small" type="info">v{{ plugin.version }}</el-tag>
              <span class="plugin-author">by {{ plugin.author }}</span>
            </div>
          </div>
          <div class="plugin-actions">
            <el-button type="primary" size="small" @click="installPlugin(plugin)">
              一键安装
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 全量插件（资深模式） -->
    <div v-mode="'expert'" class="plugin-section">
      <div class="section-header">
        <h3 class="section-title">
          <el-icon><Grid /></el-icon>
          全量插件
          <el-tag type="info" size="small">{{ allPlugins.length }}</el-tag>
        </h3>
        <el-input
          v-model="searchKeyword"
          placeholder="搜索插件..."
          size="small"
          style="width: 200px;"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <div class="plugin-grid">
        <div
          v-for="plugin in filteredPlugins"
          :key="plugin.key"
          :class="['plugin-card', { installed: plugin.installed }]"
        >
          <div class="plugin-icon-wrap">
            <img v-if="plugin.icon" :src="plugin.icon" class="plugin-icon" />
            <el-icon v-else :size="32"><Box /></el-icon>
          </div>
          <div class="plugin-content">
            <div class="plugin-name">{{ plugin.name }}</div>
            <div class="plugin-desc">{{ plugin.description }}</div>
            <div class="plugin-meta">
              <el-tag size="small" :type="plugin.official ? 'success' : 'info'">
                {{ plugin.official ? '官方' : '第三方' }}
              </el-tag>
              <el-tag size="small" type="info">v{{ plugin.version }}</el-tag>
              <span class="plugin-author">by {{ plugin.author }}</span>
            </div>
          </div>
          <div class="plugin-actions">
            <template v-if="plugin.installed">
              <el-button text size="small" type="primary">已安装</el-button>
            </template>
            <template v-else>
              <el-button type="primary" size="small" @click="installPlugin(plugin)">
                安装
              </el-button>
            </template>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import {
  Refresh, FolderChecked, Star, Grid, Box,
  MoreFilled, Search
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

// ── 模拟数据 ───────────────────────────────────────────────
const searchKeyword = ref('')

const recommendedPlugins = [
  {
    key: 'auto-ship',
    name: '智能批量发货',
    description: '一键批量打单发货，自动匹配最优物流渠道，支持多平台订单合并',
    version: '1.2.0',
    author: '辽宁跨境宝盒官方',
    icon: '',
    official: true,
  },
  {
    key: 'ai-report',
    name: 'AI经营日报',
    description: '自动生成每日/每周/每月经营报告，智能分析经营亮点与问题',
    version: '1.0.0',
    author: '辽宁跨境宝盒官方',
    icon: '',
    official: true,
  },
]

const allPlugins = [
  ...recommendedPlugins,
  {
    key: 'price-monitor',
    name: '竞品价格监控',
    description: '实时监控竞品价格变化，自动提醒并推荐最优定价策略',
    version: '2.1.0',
    author: '第三方',
    icon: '',
    official: false,
  },
  {
    key: 'auto-reply',
    name: 'AI客服自动回复',
    description: '基于AI的智能客服，自动回复常见问题，支持多语言',
    version: '1.5.0',
    author: '辽宁跨境宝盒官方',
    icon: '',
    official: true,
  },
  {
    key: 'data-export',
    name: '数据批量导出',
    description: '支持一键导出订单、库存、商品数据为Excel/CSV格式',
    version: '1.0.0',
    author: '第三方',
    icon: '',
    official: false,
  },
  {
    key: 'fba-calculator',
    name: 'FBA成本计算器',
    description: '亚马逊FBA物流成本精确计算，支持利润模拟与定价推荐',
    version: '1.3.0',
    author: '第三方',
    icon: '',
    official: false,
  },
  // ── 新增插件（2026.04.22）────────────
  {
    key: 'tiktok-analytics',
    name: 'TikTok数据洞察',
    description: 'TikTok热门视频分析、带货趋势追踪、达人合作管理',
    version: '1.0.0',
    author: '辽宁跨境宝盒官方',
    icon: '',
    official: true,
  },
  {
    key: 'auto-stock',
    name: '智能库存预警',
    description: '多仓库库存实时同步，自动计算安全库存，提前预警避免断货',
    version: '2.0.0',
    author: '辽宁跨境宝盒官方',
    icon: '',
    official: true,
  },
  {
    key: 'multi-account',
    name: '多账号管理',
    description: '一个界面管理多个店铺账号，防关联安全隔离，数据隔离不串号',
    version: '1.8.0',
    author: '第三方',
    icon: '',
    official: false,
  },
  {
    key: 'auto-review',
    name: '评价自动回复',
    description: '自动识别好评/差评，支持模板+AI生成回复，保持店铺高评分',
    version: '1.1.0',
    author: '第三方',
    icon: '',
    official: false,
  },
  {
    key: 'seo-optimizer',
    name: 'Listing SEO优化',
    description: '自动分析竞品标题关键词，推荐高流量标题模板，提升搜索排名',
    version: '1.4.0',
    author: '辽宁跨境宝盒官方',
    icon: '',
    official: true,
  },
  {
    key: 'finance-report',
    name: '财务报表生成',
    description: '月/年利润表、资产负债表、退款明细，自动生成可下载报表',
    version: '1.0.0',
    author: '第三方',
    icon: '',
    official: false,
  },
  {
    key: 'auto-rmb',
    name: '多币种自动换汇',
    description: '实时汇率自动换算，利润按人民币结算，支持USD/EUR/GBP多币种',
    version: '1.2.0',
    author: '第三方',
    icon: '',
    official: false,
  },
  {
    key: 'wechat-bot',
    name: '微信订单通知',
    description: '订单状态变更、库存预警自动推送到微信，实时掌握店铺动态',
    version: '1.0.0',
    author: '辽宁跨境宝盒官方',
    icon: '',
    official: true,
  },
  {
    key: 'bulk-edit',
    name: '批量商品编辑',
    description: '批量修改商品标题、价格、库存，支持正则替换和模板填充',
    version: '2.0.0',
    author: '第三方',
    icon: '',
    official: false,
  },
]

const installedPlugins = ref([])

const filteredPlugins = computed(() => {
  if (!searchKeyword.value) return allPlugins
  const kw = searchKeyword.value.toLowerCase()
  return allPlugins.filter(p =>
    p.name.toLowerCase().includes(kw) ||
    p.description.toLowerCase().includes(kw)
  )
})

// ── 操作 ───────────────────────────────────────────────────
function installPlugin(plugin) {
  ElMessage.success(`「${plugin.name}」安装成功，功能已启用`)
  installedPlugins.value.push({ ...plugin, installed: true })
}

function togglePlugin(plugin) {
  plugin.enabled = !plugin.enabled
  ElMessage.success(`「${plugin.name}」${plugin.enabled ? '已启用' : '已禁用'}`)
}

function checkUpdates() {
  ElMessage.success('已是最新版本，无需更新')
}
</script>

<style scoped>
.plugins-page {
  padding: 24px;
  max-width: 1200px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin: 0 0 4px;
}

.page-desc {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.plugin-section {
  margin-bottom: 40px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin: 0;
}

.empty-state {
  padding: 40px 0;
}

.plugin-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.plugin-card {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-extra-light);
  border-radius: 10px;
  transition: all 0.2s;
}

.plugin-card:hover {
  border-color: var(--el-color-primary-light-5);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.plugin-card.installed {
  border-color: var(--el-color-success-light-5);
  background: var(--el-color-success-light-9);
}

.plugin-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  background: var(--el-fill-color-light);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: var(--el-text-color-secondary);
  overflow: hidden;
}

.plugin-icon {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.plugin-content {
  flex: 1;
  min-width: 0;
}

.plugin-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.plugin-desc {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.5;
  margin-bottom: 8px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.plugin-meta {
  display: flex;
  align-items: center;
  gap: 6px;
}

.plugin-author {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
}

.plugin-actions {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
</style>
