<template>
  <div class="kol-page">
    <!-- 顶部标题区 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">达人看板</h1>
        <p class="page-subtitle">KOL Intelligence · 智能匹配 · 多平台数据聚合</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" bg @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
        <el-button type="primary">
          <el-icon><Plus /></el-icon>
          新增达人
        </el-button>
      </div>
    </div>

    <!-- 核心指标卡片 -->
    <div class="stat-cards">
      <div class="stat-card stat-gradient-1">
        <div class="stat-icon">
          <el-icon><User /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">达人总数</div>
        </div>
        <div class="stat-trend up">
          <el-icon><Top /></el-icon>
          +12.5%
        </div>
      </div>

      <div class="stat-card stat-gradient-2">
        <div class="stat-icon">
          <el-icon><Star /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ formatFan(stats.totalFans) }}</div>
          <div class="stat-label">覆盖粉丝总量</div>
        </div>
        <div class="stat-trend up">
          <el-icon><Top /></el-icon>
          +8.3%
        </div>
      </div>

      <div class="stat-card stat-gradient-3">
        <div class="stat-icon">
          <el-icon><TrendCharts /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.avgEngagement }}%</div>
          <div class="stat-label">平均互动率</div>
        </div>
        <div class="stat-trend up">
          <el-icon><Top /></el-icon>
          +2.1%
        </div>
      </div>

      <div class="stat-card stat-gradient-4">
        <div class="stat-icon">
          <el-icon><Bell /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.activeToday }}</div>
          <div class="stat-label">今日活跃</div>
        </div>
        <div class="stat-trend neutral">
          <el-icon><More /></el-icon>
          实时
        </div>
      </div>
    </div>

    <!-- 筛选工具栏 -->
    <div class="filter-bar">
      <div class="filter-left">
        <el-radio-group v-model="activePlatform" size="default">
          <el-radio-button label="全部" value="all" />
          <el-radio-button label="TikTok" value="tiktok">
            <span class="platform-tag tt">TK</span>
          </el-radio-button>
          <el-radio-button label="Instagram" value="instagram">
            <span class="platform-tag ig">IG</span>
          </el-radio-button>
          <el-radio-button label="YouTube" value="youtube">
            <span class="platform-tag yt">YT</span>
          </el-radio-button>
          <el-radio-button label="Amazon" value="amazon">
            <span class="platform-tag am">AM</span>
          </el-radio-button>
        </el-radio-group>
      </div>
      <div class="filter-right">
        <el-select v-model="activeCountry" placeholder="目标市场" style="width: 140px">
          <el-option label="全部地区" value="all" />
          <el-option label="🇺🇸 美国 (US)" value="US" />
          <el-option label="🇬🇧 英国 (UK)" value="UK" />
          <el-option label="🇸🇬 东南亚 (SEA)" value="SEA" />
          <el-option label="🇦🇺 澳洲 (AU)" value="AU" />
        </el-select>
        <el-select v-model="activeLevel" placeholder="粉丝量级" style="width: 140px">
          <el-option label="全部量级" value="all" />
          <el-option label="Nano (1K-10K)" value="nano" />
          <el-option label="Micro (10K-100K)" value="micro" />
          <el-option label="Mega (100K+)" value="mega" />
        </el-select>
        <el-input v-model="searchKeyword" placeholder="搜索达人名称 / ID" style="width: 200px" clearable>
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button type="primary" plain @click="aiMatchVisible = true">
          <el-icon><MagicStick /></el-icon>
          AI智能匹配
        </el-button>
      </div>
    </div>

    <!-- 主体内容区 -->
    <div class="main-grid">
      <!-- 左侧：达人列表 -->
      <div class="kol-list-panel">
        <div class="panel-header">
          <span class="panel-title">达人列表</span>
          <span class="panel-count">{{ filteredKol.length }} 位达人</span>
        </div>

        <div class="kol-list">
          <div
            v-for="kol in filteredKol"
            :key="kol.id"
            class="kol-card"
            :class="{ active: selectedKol?.id === kol.id }"
            @click="selectKol(kol)"
          >
            <div class="kol-avatar-wrap">
              <el-avatar :size="52" :src="kol.avatar" class="kol-avatar">
                {{ kol.name[0] }}
              </el-avatar>
              <span class="kol-platform-badge" :class="kol.platform">{{ kol.platform.toUpperCase() }}</span>
            </div>
            <div class="kol-info">
              <div class="kol-name">{{ kol.name }}</div>
              <div class="kol-meta">
                <span class="kol-country">{{ kol.country }}</span>
                <span class="kol-level" :class="kol.levelTag">{{ kol.level }}</span>
                <span class="kol-style" :class="kol.styleTag">{{ kol.style }}</span>
              </div>
              <div class="kol-stats-row">
                <span><strong>{{ formatFan(kol.fans) }}</strong> 粉丝</span>
                <span><strong>{{ kol.engagement }}%</strong> 互动</span>
                <span><strong>{{ kol.gpm }}</strong> GPM</span>
              </div>
            </div>
            <div class="kol-action">
              <el-button size="small" circle @click.stop="openContact(kol)">
                <el-icon><Message /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：达人详情 -->
      <div class="kol-detail-panel">
        <div v-if="!selectedKol" class="detail-empty">
          <el-icon class="empty-icon"><User /></el-icon>
          <p>点击左侧达人卡片<br>查看详细画像与数据</p>
        </div>

        <div v-else class="detail-content">
          <!-- 达人基本信息卡 -->
          <div class="kol-profile-card">
            <div class="profile-top">
              <el-avatar :size="72" :src="selectedKol.avatar" class="profile-avatar">
                {{ selectedKol.name[0] }}
              </el-avatar>
              <div class="profile-info">
                <h2 class="profile-name">{{ selectedKol.name }}</h2>
                <div class="profile-tags">
                  <el-tag size="small" :type="platformType(selectedKol.platform)">
                    {{ selectedKol.platform.toUpperCase() }}
                  </el-tag>
                  <el-tag size="small" type="info">{{ selectedKol.country }}</el-tag>
                  <el-tag size="small" :type="selectedKol.hasShop ? 'success' : 'info'">
                    {{ selectedKol.hasShop ? '🛒 有店铺' : '暂无店铺' }}
                  </el-tag>
                  <el-tag size="small" :class="selectedKol.styleTag">
                    {{ selectedKol.style }}
                  </el-tag>
                </div>
                <div class="profile-fans">
                  <span class="fans-num">{{ formatFan(selectedKol.fans) }}</span>
                  <span class="fans-unit">粉丝</span>
                  <span class="fans-gender">{{ selectedKol.genderRatio }}</span>
                </div>
              </div>
              <div class="profile-actions">
                <el-button type="primary" @click="openContact(selectedKol)">
                  <el-icon><Message /></el-icon>
                  建联
                </el-button>
                <el-button @click="aiPitchVisible = true">
                  <el-icon><MagicStick /></el-icon>
                  AI邀约
                </el-button>
              </div>
            </div>

            <!-- 粉丝画像 -->
            <div class="profile-charts">
              <div class="sub-chart">
                <div class="sub-chart-title">年龄分布</div>
                <v-chart class="mini-chart" :option="ageChartOption" autoresize />
              </div>
              <div class="sub-chart">
                <div class="sub-chart-title">性别比例</div>
                <v-chart class="mini-chart" :option="genderChartOption" autoresize />
              </div>
              <div class="sub-chart">
                <div class="sub-chart-title">购买力等级</div>
                <v-chart class="mini-chart" :option="purchaseChartOption" autoresize />
              </div>
            </div>
          </div>

          <!-- 粉丝增长曲线 -->
          <div class="chart-card">
            <div class="chart-card-header">
              <span class="chart-card-title">📈 粉丝增长趋势（近30天）</span>
              <el-radio-group v-model="growthRange" size="small">
                <el-radio-button label="7天" value="7" />
                <el-radio-button label="30天" value="30" />
                <el-radio-button label="90天" value="90" />
              </el-radio-group>
            </div>
            <v-chart class="big-chart" :option="fanGrowthOption" autoresize />
          </div>

          <!-- 视频热度热力图 -->
          <div class="chart-card">
            <div class="chart-card-header">
              <span class="chart-card-title">🔥 视频热度热力图（近30条）</span>
            </div>
            <v-chart class="big-chart" :option="heatmapOption" autoresize />
          </div>

          <!-- AI分析区块 -->
          <div class="ai-analysis-card">
            <div class="ai-card-header">
              <div class="ai-badge">
                <el-icon><MagicStick /></el-icon>
                AI 智能分析
              </div>
              <el-button size="small" @click="regenerateAnalysis">重新分析</el-button>
            </div>

            <div class="ai-analysis-content">
              <div class="analysis-item">
                <div class="analysis-label">内容调性</div>
                <div class="analysis-value">
                  <el-tag type="warning">{{ selectedKol.style }}</el-tag>
                  <span class="analysis-desc">{{ selectedKol.styleDesc }}</span>
                </div>
              </div>
              <div class="analysis-item">
                <div class="analysis-label">AI 综合评分</div>
                <div class="analysis-value">
                  <el-rate v-model="selectedKol.aiScore" disabled show-score text-color="#667eea" />
                </div>
              </div>
              <div class="analysis-item">
                <div class="analysis-label">粉丝真实购买意向</div>
                <div class="analysis-value">
                  <el-progress
                    :percentage="selectedKol.purchaseIntent"
                    :color="purchaseIntentColor(selectedKol.purchaseIntent)"
                    :stroke-width="8"
                  />
                  <span class="analysis-desc">抓取评论关键词分析</span>
                </div>
              </div>
              <div class="analysis-item">
                <div class="analysis-label">评论区热词</div>
                <div class="word-cloud">
                  <el-tag v-for="w in selectedKol.keywords" :key="w" size="small" class="word-tag">
                    {{ w }}
                  </el-tag>
                </div>
              </div>
              <div class="analysis-item">
                <div class="analysis-label">AI 评估结论</div>
                <div class="ai-conclusion">{{ selectedKol.aiConclusion }}</div>
              </div>
            </div>
          </div>

          <!-- 建联渠道 -->
          <div class="contact-card">
            <div class="contact-header">
              <span class="contact-title">📞 建联渠道</span>
              <el-tag size="small" type="info">{{ selectedKol.timezone }} · 最佳联系时段 {{ selectedKol.bestTime }}</el-tag>
            </div>
            <div class="contact-channels">
              <div v-if="selectedKol.email" class="contact-item" @click="copyToClipboard(selectedKol.email)">
                <div class="contact-icon email-icon">
                  <el-icon><Message /></el-icon>
                </div>
                <div class="contact-info">
                  <div class="contact-type">Email</div>
                  <div class="contact-val">{{ selectedKol.email }}</div>
                </div>
                <el-icon class="contact-copy"><DocumentCopy /></el-icon>
              </div>
              <div v-if="selectedKol.whatsapp" class="contact-item" @click="copyToClipboard(selectedKol.whatsapp)">
                <div class="contact-icon wa-icon">
                  <el-icon><ChatDotRound /></el-icon>
                </div>
                <div class="contact-info">
                  <div class="contact-type">WhatsApp</div>
                  <div class="contact-val">{{ selectedKol.whatsapp }}</div>
                </div>
                <el-icon class="contact-copy"><DocumentCopy /></el-icon>
              </div>
              <div v-if="selectedKol.instagram" class="contact-item" @click="copyToClipboard(selectedKol.instagram)">
                <div class="contact-icon ig-icon">
                  <el-icon><Picture /></el-icon>
                </div>
                <div class="contact-info">
                  <div class="contact-type">Instagram</div>
                  <div class="contact-val">{{ selectedKol.instagram }}</div>
                </div>
                <el-icon class="contact-copy"><DocumentCopy /></el-icon>
              </div>
            </div>
          </div>

          <!-- 样品与合同管理 -->
          <div class="fulfillment-card">
            <div class="fulfillment-header">
              <span>📦 跨境样品与合同闭环</span>
              <el-button type="primary" size="small" @click="createSampleOrder(selectedKol)">
                <el-icon><Plus /></el-icon>
                生成样品订单
              </el-button>
            </div>
            <div class="fulfillment-status">
              <div class="fulfillment-step done">
                <div class="step-dot" />
                <span>达人信息录入</span>
              </div>
              <div class="step-line done" />
              <div class="fulfillment-step" :class="{ done: selectedKol.sampleOrdered, active: !selectedKol.sampleOrdered }">
                <div class="step-dot" />
                <span>样品订单生成</span>
              </div>
              <div class="step-line" />
              <div class="fulfillment-step">
                <div class="step-dot" />
                <span>跨境物流发货</span>
              </div>
              <div class="step-line" />
              <div class="fulfillment-step">
                <div class="step-dot" />
                <span>达人确认收货</span>
              </div>
              <div class="step-line" />
              <div class="fulfillment-step">
                <div class="step-dot" />
                <span>素材回传入库</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- AI 智能匹配弹窗 -->
    <el-dialog v-model="aiMatchVisible" title="AI 智能匹配达人" width="680px" :close-on-click-modal="false">
      <div class="ai-match-form">
        <el-form label-position="top">
          <el-form-item label="品牌 / 产品名称">
            <el-input v-model="matchForm.product" placeholder="输入品牌名或产品关键词，如：女士防晒霜" />
          </el-form-item>
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="目标市场">
                <el-select v-model="matchForm.country" placeholder="选择目标市场" style="width:100%">
                  <el-option label="美国 (US)" value="US" />
                  <el-option label="英国 (UK)" value="UK" />
                  <el-option label="东南亚 (SEA)" value="SEA" />
                  <el-option label="澳洲 (AU)" value="AU" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="目标平台">
                <el-select v-model="matchForm.platform" placeholder="选择平台" style="width:100%">
                  <el-option label="TikTok" value="tiktok" />
                  <el-option label="Instagram" value="instagram" />
                  <el-option label="YouTube" value="youtube" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="粉丝量级">
                <el-select v-model="matchForm.level" placeholder="选择量级" style="width:100%">
                  <el-option label="Nano (1K-10K)" value="nano" />
                  <el-option label="Micro (10K-100K)" value="micro" />
                  <el-option label="Mega (100K+)" value="mega" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="预算范围">
                <el-select v-model="matchForm.budget" placeholder="选择预算" style="width:100%">
                  <el-option label="1万以下" value="low" />
                  <el-option label="1-5万" value="mid" />
                  <el-option label="5-20万" value="high" />
                  <el-option label="20万以上" value="vip" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="内容风格偏好">
            <el-checkbox-group v-model="matchForm.styles">
              <el-checkbox label="硬广推销型" />
              <el-checkbox label="测评拆解型" />
              <el-checkbox label="生活方式植入型" />
              <el-checkbox label="剧情搞笑型" />
              <el-checkbox label="干货知识型" />
            </el-checkbox-group>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="aiMatchVisible = false">取消</el-button>
        <el-button type="primary" :loading="matchLoading" @click="doAiMatch">
          <el-icon v-if="!matchLoading"><MagicStick /></el-icon>
          {{ matchLoading ? 'AI 匹配中...' : '开始 AI 匹配' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- AI 邀约信弹窗 -->
    <el-dialog v-model="aiPitchVisible" title="AI 生成合作邀约信" width="700px">
      <div v-if="!pitchResult">
        <p style="color:var(--text-secondary);margin-bottom:16px">
          为达人 <strong>{{ selectedKol?.name }}</strong> 生成个性化合作邀约信（AI 自动翻译为当地语种）
        </p>
        <el-form label-position="top">
          <el-form-item label="合作形式">
            <el-radio-group v-model="pitchForm.type">
              <el-radio label="样品合作" />
              <el-radio label="付费推广" />
              <el-radio label="佣金分成" />
              <el-radio label="长期签约" />
            </el-radio-group>
          </el-form-item>
          <el-form-item label="产品卖点（AI 自动提炼）">
            <el-input v-model="pitchForm.productInfo" placeholder="输入产品核心卖点，如：高倍防晒、清爽不油腻" />
          </el-form-item>
          <el-form-item label="附加要求">
            <el-input v-model="pitchForm.extra" type="textarea" :rows="2" placeholder="如：希望对方有美妆类视频经验" />
          </el-form-item>
        </el-form>
      </div>
      <div v-else class="pitch-result">
        <el-tabs v-model="pitchLang">
          <el-tab-pane label="🇺🇸 英文原版" name="en">
            <div class="pitch-content">{{ pitchResult.en }}</div>
            <div class="pitch-actions">
              <el-button size="small" @click="copyToClipboard(pitchResult.en)">
                <el-icon><DocumentCopy /></el-icon> 复制英文
              </el-button>
            </div>
          </el-tab-pane>
          <el-tab-pane label="🇨🇳 中文参考" name="cn">
            <div class="pitch-content">{{ pitchResult.cn }}</div>
            <div class="pitch-actions">
              <el-button size="small" @click="copyToClipboard(pitchResult.cn)">
                <el-icon><DocumentCopy /></el-icon> 复制中文
              </el-button>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
      <template #footer>
        <template v-if="!pitchResult">
          <el-button @click="aiPitchVisible = false">取消</el-button>
          <el-button type="primary" :loading="pitchLoading" @click="generatePitch">
            {{ pitchLoading ? '生成中...' : '生成邀约信' }}
          </el-button>
        </template>
        <template v-else>
          <el-button @click="pitchResult = null">重新生成</el-button>
          <el-button type="primary" @click="aiPitchVisible = false">完成</el-button>
        </template>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, shallowRef } from 'vue'
import { ElMessage } from 'element-plus'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart, PieChart, HeatmapChart } from 'echarts/charts'
import {
  TitleComponent, TooltipComponent, GridComponent,
  LegendComponent, VisualMapComponent
} from 'echarts/components'
import {
  Refresh, Plus, User, Star, TrendCharts, Bell,
  Search, MagicStick, Message, Top, More, DocumentCopy, Picture, ChatDotRound, Avatar
} from '@element-plus/icons-vue'

use([CanvasRenderer, LineChart, BarChart, PieChart, HeatmapChart,
  TitleComponent, TooltipComponent, GridComponent, LegendComponent, VisualMapComponent])

// ========== Mock 数据 ==========
const mockKolList = [
  {
    id: 1, name: 'Sophie Chen', platform: 'tiktok', country: '🇺🇸 US', level: 'Mega', levelTag: 'mega-tag',
    style: '生活方式植入', styleTag: 'lifestyle-tag', fans: 2800000, engagement: 8.7, gpm: '¥42',
    hasShop: true, aiScore: 4.8, purchaseIntent: 82,
    styleDesc: '视频以日常生活场景为主，自然植入产品，种草力强，适合美妆/护肤/家居类品牌',
    aiConclusion: '⭐⭐⭐⭐⭐ 强烈推荐。粉丝购买意向高，内容调性与品牌高度契合，建议优先建联。',
    keywords: ['Where to buy', 'Love this', 'Amazing', 'Holy grail', 'Repurchase'],
    email: 'sophie.chen@tiktok.com', whatsapp: '+1 555-0101', instagram: '@sophie.chen_official',
    timezone: 'EST (纽约)', bestTime: '9:00-11:00', sampleOrdered: false,
    avatar: 'https://picsum.photos/seed/sophie/150/150',
    ageData: [{ name: '18-24', value: 35 }, { name: '25-34', value: 45 }, { name: '35-44', value: 15 }, { name: '45+', value: 5 }],
    genderData: [{ name: '女', value: 78 }, { name: '男', value: 22 }],
    purchaseData: [{ name: '高', value: 42 }, { name: '中', value: 38 }, { name: '低', value: 20 }],
    fanGrowthData: [2.1, 2.3, 2.5, 2.6, 2.7, 2.65, 2.8],
    heatmapData: generateHeatmap()
  },
  {
    id: 2, name: 'Marcus Williams', platform: 'tiktok', country: '🇺🇸 US', level: 'Micro', levelTag: 'micro-tag',
    style: '测评拆解型', styleTag: 'review-tag', fans: 87000, engagement: 12.3, gpm: '¥58',
    hasShop: false, aiScore: 4.5, purchaseIntent: 75,
    styleDesc: '深度测评视频著称，分析成分、功效、价格，适合科技/3C/工具类产品',
    aiConclusion: '⭐⭐⭐⭐ 推荐。互动率高，粉丝粘性强，测评风格有助于建立产品信任感。',
    keywords: ['Honest review', 'Worth it', 'Comparison', '5 stars', 'Best buy'],
    email: 'marcus.w@ig.com', whatsapp: '+1 555-0202', instagram: '@marcus.techreview',
    timezone: 'PST (洛杉矶)', bestTime: '18:00-20:00', sampleOrdered: true,
    avatar: 'https://picsum.photos/seed/marcus/150/150',
    ageData: [{ name: '18-24', value: 40 }, { name: '25-34', value: 42 }, { name: '35-44', value: 12 }, { name: '45+', value: 6 }],
    genderData: [{ name: '女', value: 55 }, { name: '男', value: 45 }],
    purchaseData: [{ name: '高', value: 35 }, { name: '中', value: 45 }, { name: '低', value: 20 }],
    fanGrowthData: [0.75, 0.78, 0.82, 0.85, 0.86, 0.87, 0.87],
    heatmapData: generateHeatmap()
  },
  {
    id: 3, name: 'Aiko Tanaka', platform: 'instagram', country: '🇸🇬 SEA', level: 'Mega', levelTag: 'mega-tag',
    style: '美妆教程型', styleTag: 'beauty-tag', fans: 1560000, engagement: 6.2, gpm: '¥31',
    hasShop: true, aiScore: 4.6, purchaseIntent: 68,
    styleDesc: '日系美妆教程为主，粉丝忠诚度高，适合美妆护肤、个护类产品',
    aiConclusion: '⭐⭐⭐⭐ 推荐。日系美妆垂类达人，在东南亚华人群体中影响力大。',
    keywords: ['Tutorial', 'Haul', 'Must have', 'Skin care', 'K-beauty'],
    email: 'aiko.tanaka@ig.com', whatsapp: '+65 9123-4567', instagram: '@aiko.beauty',
    timezone: 'SGT (新加坡)', bestTime: '20:00-22:00', sampleOrdered: false,
    avatar: 'https://picsum.photos/seed/aiko/150/150',
    ageData: [{ name: '18-24', value: 50 }, { name: '25-34', value: 35 }, { name: '35-44', value: 10 }, { name: '45+', value: 5 }],
    genderData: [{ name: '女', value: 92 }, { name: '男', value: 8 }],
    purchaseData: [{ name: '高', value: 30 }, { name: '中', value: 48 }, { name: '低', value: 22 }],
    fanGrowthData: [1.3, 1.35, 1.4, 1.45, 1.5, 1.53, 1.56],
    heatmapData: generateHeatmap()
  },
  {
    id: 4, name: 'Alex Rivera', platform: 'youtube', country: '🇬🇧 UK', level: 'Micro', levelTag: 'micro-tag',
    style: '剧情搞笑型', styleTag: 'comedy-tag', fans: 52000, engagement: 9.8, gpm: '¥25',
    hasShop: false, aiScore: 4.2, purchaseIntent: 61,
    styleDesc: '幽默短剧植入品牌，自然不生硬，娱乐性强，适合快消品、零食、游戏类产品',
    aiConclusion: '⭐⭐⭐⭐ 值得尝试。高互动率，搞笑风格有助于品牌破圈传播。',
    keywords: ['Haha', 'This is hilarious', 'Need this', 'Link in bio', 'omg'],
    email: 'alex.rivera@yt.com', whatsapp: '+44 7700-900123', instagram: '@alexrivera_comedy',
    timezone: 'GMT (伦敦)', bestTime: '12:00-14:00', sampleOrdered: false,
    avatar: 'https://picsum.photos/seed/alexr/150/150',
    ageData: [{ name: '18-24', value: 55 }, { name: '25-34', value: 30 }, { name: '35-44', value: 10 }, { name: '45+', value: 5 }],
    genderData: [{ name: '女', value: 48 }, { name: '男', value: 52 }],
    purchaseData: [{ name: '高', value: 22 }, { name: '中', value: 40 }, { name: '低', value: 38 }],
    fanGrowthData: [0.42, 0.44, 0.46, 0.48, 0.50, 0.51, 0.52],
    heatmapData: generateHeatmap()
  },
  {
    id: 5, name: 'Emily Johnson', platform: 'amazon', country: '🇺🇸 US', level: 'Mega', levelTag: 'mega-tag',
    style: 'Amazon评测', styleTag: 'amazon-tag', fans: 3200000, engagement: 5.1, gpm: '¥89',
    hasShop: true, aiScore: 4.9, purchaseIntent: 91,
    styleDesc: 'Amazon Top Reviewer，测评视频带动销量能力极强，选品严格，带货转化率高',
    aiConclusion: '⭐⭐⭐⭐⭐ 强烈推荐。Amazon头部测评人，GPM极高，是跨境电商带货首选。',
    keywords: ['Verified purchase', 'Highly recommend', '5 stars', 'Value for money', 'Best seller'],
    email: 'emily.reviews@amazon.com', whatsapp: '', instagram: '@emily.amazonreviews',
    timezone: 'EST (纽约)', bestTime: '14:00-16:00', sampleOrdered: true,
    avatar: 'https://picsum.photos/seed/emily/150/150',
    ageData: [{ name: '18-24', value: 20 }, { name: '25-34', value: 40 }, { name: '35-44', value: 28 }, { name: '45+', value: 12 }],
    genderData: [{ name: '女', value: 65 }, { name: '男', value: 35 }],
    purchaseData: [{ name: '高', value: 60 }, { name: '中', value: 30 }, { name: '低', value: 10 }],
    fanGrowthData: [2.8, 2.9, 3.0, 3.1, 3.15, 3.18, 3.2],
    heatmapData: generateHeatmap()
  },
  // 泳装/沙滩类达人（新增 6-10）
  {
    id: 6, name: 'Mia Santos', platform: 'instagram', country: '🇧🇷 BR', level: 'Mega', levelTag: 'mega-tag',
    style: '泳装穿搭型', styleTag: 'swimwear-tag', fans: 4200000, engagement: 7.8, gpm: '¥56',
    hasShop: true, aiScore: 4.7, purchaseIntent: 79,
    styleDesc: '南美沙滩泳装风格，粉丝购买力强，带货泳装/比基尼/防晒品类效果极佳',
    aiConclusion: '⭐⭐⭐⭐⭐ 强烈推荐。泳装垂类顶级达人，与商品高度契合，优先合作。',
    keywords: ['Praia', 'Biquini', 'Summer vibes', 'Love this', 'Where to shop'],
    email: 'mia.santos@ig.com', whatsapp: '+55 21 98765-4321', instagram: '@mia.santos.beach',
    timezone: 'BRT (圣保罗)', bestTime: '10:00-12:00', sampleOrdered: false,
    avatar: 'https://picsum.photos/seed/mia/150/150',
    ageData: [{ name: '18-24', value: 60 }, { name: '25-34', value: 30 }, { name: '35-44', value: 8 }, { name: '45+', value: 2 }],
    genderData: [{ name: '女', value: 95 }, { name: '男', value: 5 }],
    purchaseData: [{ name: '高', value: 55 }, { name: '中', value: 35 }, { name: '低', value: 10 }],
    fanGrowthData: [3.5, 3.7, 3.9, 4.0, 4.1, 4.15, 4.2],
    heatmapData: generateHeatmap()
  },
  {
    id: 7, name: 'Tyler Brooks', platform: 'tiktok', country: '🇺🇸 US', level: 'Mid', levelTag: 'mid-tag',
    style: '户外玩具测评', styleTag: 'toys-tag', fans: 320000, engagement: 11.2, gpm: '¥38',
    hasShop: false, aiScore: 4.3, purchaseIntent: 72,
    styleDesc: '两个孩子的爸爸账号，户外沙滩/儿童玩具测评，互动率高，适合沙滩玩具/儿童户外产品',
    aiConclusion: '⭐⭐⭐⭐ 推荐。儿童户外垂类达人，家长粉购买转化率高，适合沙滩玩具带货。',
    keywords: ['Kids love it', 'Beach day', '5 stars', 'Durable', 'Perfect gift'],
    email: 'tyler.brooks@tt.com', whatsapp: '+1 555-0707', instagram: '@tyler.brooks.dad',
    timezone: 'CST (芝加哥)', bestTime: '19:00-21:00', sampleOrdered: true,
    avatar: 'https://picsum.photos/seed/tyler/150/150',
    ageData: [{ name: '18-24', value: 15 }, { name: '25-34', value: 50 }, { name: '35-44', value: 28 }, { name: '45+', value: 7 }],
    genderData: [{ name: '女', value: 62 }, { name: '男', value: 38 }],
    purchaseData: [{ name: '高', value: 45 }, { name: '中', value: 40 }, { name: '低', value: 15 }],
    fanGrowthData: [0.25, 0.27, 0.29, 0.30, 0.31, 0.315, 0.32],
    heatmapData: generateHeatmap()
  },
  {
    id: 8, name: 'Luna Park', platform: 'youtube', country: '🇰🇷 KR', level: 'Mega', levelTag: 'mega-tag',
    style: '度假Vlog型', styleTag: 'vlog-tag', fans: 2800000, engagement: 8.4, gpm: '¥47',
    hasShop: true, aiScore: 4.6, purchaseIntent: 76,
    styleDesc: '韩国度假Vlogger，济州岛/东南亚海边度假内容，带火多款泳装和沙滩装备',
    aiConclusion: '⭐⭐⭐⭐⭐ 强烈推荐。度假风格与泳装高度契合，粉丝种草购买力强。',
    keywords: ['여행', '비치', '해변', '추천해요', 'Must visit'],
    email: 'luna.park@yt.com', whatsapp: '+82 10-1234-5678', instagram: '@luna.park.vlog',
    timezone: 'KST (首尔)', bestTime: '20:00-22:00', sampleOrdered: false,
    avatar: 'https://picsum.photos/seed/luna/150/150',
    ageData: [{ name: '18-24', value: 45 }, { name: '25-34', value: 40 }, { name: '35-44', value: 12 }, { name: '45+', value: 3 }],
    genderData: [{ name: '女', value: 88 }, { name: '男', value: 12 }],
    purchaseData: [{ name: '高', value: 50 }, { name: '中', value: 38 }, { name: '低', value: 12 }],
    fanGrowthData: [2.2, 2.35, 2.5, 2.6, 2.7, 2.75, 2.8],
    heatmapData: generateHeatmap()
  },
  {
    id: 9, name: 'Diego Costa', platform: 'tiktok', country: '🇪🇸 ES', level: 'Mid', levelTag: 'mid-tag',
    style: '沙滩运动型', styleTag: 'sports-tag', fans: 180000, engagement: 13.5, gpm: '¥29',
    hasShop: false, aiScore: 4.1, purchaseIntent: 65,
    styleDesc: '西班牙冲浪/沙滩运动达人，内容覆盖沙滩玩具/冲浪装备/防晒护理，欧洲市场影响力大',
    aiConclusion: '⭐⭐⭐⭐ 值得尝试。欧洲沙滩垂类达人，竞争少，合作性价比高。',
    keywords: ['Playa', 'Surf', 'De compras', 'Me encanta', 'Beach life'],
    email: 'diego.costa@tt.com', whatsapp: '+34 612-345-678', instagram: '@diego.costa.surf',
    timezone: 'CET (马德里)', bestTime: '11:00-13:00', sampleOrdered: false,
    avatar: 'https://picsum.photos/seed/diego/150/150',
    ageData: [{ name: '18-24', value: 48 }, { name: '25-34', value: 35 }, { name: '35-44', value: 12 }, { name: '45+', value: 5 }],
    genderData: [{ name: '女', value: 42 }, { name: '男', value: 58 }],
    purchaseData: [{ name: '高', value: 30 }, { name: '中', value: 45 }, { name: '低', value: 25 }],
    fanGrowthData: [0.14, 0.15, 0.16, 0.165, 0.17, 0.175, 0.18],
    heatmapData: generateHeatmap()
  },
  {
    id: 10, name: 'Sarah Kim', platform: 'instagram', country: '🇺🇸 US', level: 'Macro', levelTag: 'macro-tag',
    style: '辣妹穿搭型', styleTag: 'fashion-tag', fans: 890000, engagement: 9.1, gpm: '¥63',
    hasShop: true, aiScore: 4.5, purchaseIntent: 77,
    styleDesc: '洛杉矶辣妹时尚穿搭，泳装/比基尼为主，美国核心市场，粉丝消费能力强',
    aiConclusion: '⭐⭐⭐⭐ 推荐。美国辣妹时尚达人，与比基尼产品高度契合，转化率预期较高。',
    keywords: ['Slay', 'Outfit inspo', 'On sale', 'Obsessed', 'Shop link'],
    email: 'sarah.kim@ig.com', whatsapp: '+1 555-1010', instagram: '@sarah.kim.fashion',
    timezone: 'PST (洛杉矶)', bestTime: '18:00-20:00', sampleOrdered: true,
    avatar: 'https://picsum.photos/seed/sarah/150/150',
    ageData: [{ name: '18-24', value: 55 }, { name: '25-34', value: 32 }, { name: '35-44', value: 10 }, { name: '45+', value: 3 }],
    genderData: [{ name: '女', value: 90 }, { name: '男', value: 10 }],
    purchaseData: [{ name: '高', value: 48 }, { name: '中', value: 40 }, { name: '低', value: 12 }],
    fanGrowthData: [0.72, 0.76, 0.80, 0.83, 0.86, 0.875, 0.89],
    heatmapData: generateHeatmap()
  },
]

function generateHeatmap() {
  const data = []
  for (let i = 0; i < 30; i++) {
    for (let j = 0; j < 7; j++) {
      data.push([j, i, Math.random() * 100])
    }
  }
  return data
}

const stats = ref({ total: 15234, totalFans: 16450000, avgEngagement: 8.4, activeToday: 358 })

const selectedKol = ref(mockKolList[0])
const activePlatform = ref('all')
const activeCountry = ref('all')
const activeLevel = ref('all')
const searchKeyword = ref('')
const growthRange = ref('30')

const aiMatchVisible = ref(false)
const aiPitchVisible = ref(false)
const matchLoading = ref(false)
const pitchLoading = ref(false)
const pitchResult = ref(null)
const pitchLang = ref('en')

const matchForm = ref({ product: '', country: '', platform: '', level: '', budget: '', styles: [] })
const pitchForm = ref({ type: '样品合作', productInfo: '', extra: '' })

const filteredKol = computed(() => {
  return mockKolList.filter(k => {
    if (activePlatform.value !== 'all' && k.platform !== activePlatform.value) return false
    if (activeCountry.value !== 'all' && !k.country.includes(activeCountry.value)) return false
    if (activeLevel.value !== 'all' && k.levelTag !== activeLevel.value + '-tag') return false
    if (searchKeyword.value && !k.name.toLowerCase().includes(searchKeyword.value.toLowerCase())) return false
    return true
  })
})

function selectKol(kol) { selectedKol.value = kol }
function openContact(kol) { ElMessage.success(`已打开与 ${kol.name} 的建联渠道`) }
function refreshData() { ElMessage.success('数据已刷新') }
function regenerateAnalysis() { ElMessage.success('AI 分析已重新生成') }
function copyToClipboard(text) {
  navigator.clipboard.writeText(text)
  ElMessage.success('已复制到剪贴板')
}
function createSampleOrder(kol) {
  // 样品订单：商品成本 + 国际运费（mock 数据）
  const productCost = (Math.random() * 50 + 15).toFixed(2) // 商品成本 15-65 元
  const shippingFee = (Math.random() * 80 + 30).toFixed(2) // 国际运费 30-110 元
  const total = (parseFloat(productCost) + parseFloat(shippingFee)).toFixed(2)
  kol.sampleOrdered = true
  // 存储订单信息用于展示
  kol.sampleOrderInfo = {
    productCost,
    shippingFee,
    total,
    date: new Date().toLocaleDateString('zh-CN'),
    trackingNo: `SMP${Date.now().toString().slice(-10)}`,
  }
  ElMessage.success(`已为 ${kol.name} 生成样品订单（¥${total}）`)
}
async function doAiMatch() {
  matchLoading.value = true
  await new Promise(r => setTimeout(r, 1800))
  matchLoading.value = false
  aiMatchVisible.value = false
  ElMessage.success('AI 匹配完成！已找到 23 位符合条件的达人')
}
async function generatePitch() {
  pitchLoading.value = true
  await new Promise(r => setTimeout(r, 1500))
  pitchLoading.value = false
  pitchResult.value = {
    en: `Hi ${selectedKol.value.name},

We're a cross-border beauty brand specializing in skincare products and we'd love to collaborate with you!

We've been following your content and love your [测评拆解型/lifestyle] style. We think our new [${matchForm.value.product || 'product'}] would be a perfect fit for your audience.

We're offering:
• Free product samples for honest review
• Competitive commission on sales generated
• Long-term partnership opportunity

Would you be interested? We'd love to discuss further!

Best regards,
The Brand Team`,
    cn: `尊敬的 ${selectedKol.value.name}，

我们是专注于跨境美妆的品牌，非常欣赏您的内容风格，希望与您开展合作！

我们认为我们的新产品非常适合您的受众群体。我们提供：
• 免费样品用于真实测评
• 有竞争力的销售佣金分成
• 长期合作机会

期待您的回复！

此致敬礼
品牌团队`
  }
}
function formatFan(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M'
  if (n >= 1000) return (n / 1000).toFixed(0) + 'K'
  return n
}
function platformType(p) {
  const map = { tiktok: 'danger', instagram: 'warning', youtube: 'info', amazon: 'success' }
  return map[p] || ''
}
function purchaseIntentColor(v) {
  if (v >= 80) return '#67c23a'
  if (v >= 60) return '#e6a23c'
  return '#f56c6c'
}

// ========== ECharts 配置（浅色主题） ==========
const chartTextColor = '#9ca3af'
const chartLineColor = '#f3f4f6'
const tooltipStyle = { backgroundColor: '#fff', borderColor: '#e5e7eb', textStyle: { color: '#111827' }, extraCssText: 'box-shadow: 0 4px 16px rgba(0,0,0,.08)' }

const fanGrowthOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: { trigger: 'axis', ...tooltipStyle },
  grid: { top: 20, right: 20, bottom: 30, left: 50 },
  xAxis: {
    type: 'category',
    data: ['第1周', '第2周', '第3周', '第4周', '第5周', '第6周', '第7周'],
    boundaryGap: false,
    axisLine: { lineStyle: { color: chartLineColor } },
    axisLabel: { color: chartTextColor },
    splitLine: { lineStyle: { color: chartLineColor } }
  },
  yAxis: {
    type: 'value',
    axisLabel: { formatter: v => (v / 1000000).toFixed(1) + 'M', color: chartTextColor },
    splitLine: { lineStyle: { color: chartLineColor } }
  },
  series: [{
    data: selectedKol.value?.fanGrowthData,
    type: 'line',
    smooth: true,
    areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(37,99,235,.15)' }, { offset: 1, color: 'rgba(37,99,235,.02)' }] } },
    lineStyle: { color: '#2563eb', width: 2 },
    itemStyle: { color: '#2563eb', borderWidth: 2, borderColor: '#fff' }
  }]
}))

const heatmapOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: { formatter: p => `${['周一', '周二', '周三', '周四', '周五', '周六', '周日'][p.value[0]]} 第${p.value[1] + 1}条视频<br>热度: ${p.value[2].toFixed(0)}`, ...tooltipStyle },
  grid: { top: 10, right: 60, bottom: 30, left: 50 },
  xAxis: { type: 'category', data: Array.from({ length: 30 }, (_, i) => i + 1), splitArea: { show: true }, axisLabel: { interval: 4, color: chartTextColor }, axisLine: { lineStyle: { color: chartLineColor } } },
  yAxis: { type: 'category', data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'], axisLabel: { color: chartTextColor }, axisLine: { lineStyle: { color: chartLineColor } } },
  visualMap: { min: 0, max: 100, calculable: true, orient: 'vertical', right: 0, top: 'center', textStyle: { color: chartTextColor }, inRange: { color: ['#eff6ff', '#2563eb'] } },
  series: [{ type: 'heatmap', data: selectedKol.value?.heatmapData, label: { show: false }, itemStyle: { borderRadius: 3, borderWidth: 2, borderColor: '#f9fafb' } }]
}))

const pieLabel = { fontSize: 10, color: chartTextColor }

const ageChartOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: { trigger: 'item', ...tooltipStyle },
  series: [{ type: 'pie', radius: ['45%', '70%'], label: pieLabel, data: selectedKol.value?.ageData || [], itemStyle: { borderWidth: 2, borderColor: '#fff' } }]
}))

const genderChartOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: { trigger: 'item', ...tooltipStyle },
  series: [{ type: 'pie', radius: ['45%', '70%'], label: pieLabel, data: selectedKol.value?.genderData || [], itemStyle: { borderRadius: 4, borderWidth: 2, borderColor: '#fff' } }]
}))

const purchaseChartOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: { trigger: 'axis', ...tooltipStyle },
  grid: { top: 5, right: 5, bottom: 5, left: 5 },
  xAxis: { type: 'category', data: ['高', '中', '低'], axisLabel: { fontSize: 10 }, show: false },
  yAxis: { show: false },
  series: [{ type: 'bar', data: selectedKol.value?.purchaseData.map(d => d.value) || [], itemStyle: { color: '#2563eb', borderRadius: [4, 4, 0, 0] } }]
}))
</script>

<style scoped>
/* =============================================
   全局基础
   ============================================= */
.kol-page {
  padding: 24px 28px;
  background: var(--bg-page);
  min-height: 100vh;
}

/* =============================================
   顶部标题
   ============================================= */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 22px;
}
.page-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}
.page-subtitle {
  font-size: 13px;
  color: var(--text-secondary);
}
.header-actions { display: flex; gap: 10px; }

/* =============================================
   指标卡片
   ============================================= */
.stat-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 20px;
}
.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 18px 20px;
  display: flex;
  align-items: flex-start;
  gap: 14px;
  transition: box-shadow var(--dur) var(--ease), transform var(--dur) var(--ease);
  cursor: default;
}
.stat-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}
.stat-gradient-1 { --sc: #2563eb; }
.stat-gradient-2 { --sc: #dc2626; }
.stat-gradient-3 { --sc: #16a34a; }
.stat-gradient-4 { --sc: #d97706; }

.stat-icon {
  width: 42px; height: 42px;
  border-radius: var(--r-md);
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; color: #fff;
  flex-shrink: 0;
  background: var(--sc, #2563eb);
}

.stat-info { flex: 1; min-width: 0; }
.stat-value { font-size: 24px; font-weight: 700; color: var(--text-primary); line-height: 1.2; letter-spacing: -.02em; }
.stat-label { font-size: 12.5px; color: var(--text-secondary); margin-top: 4px; }
.stat-trend {
  font-size: 11px; font-weight: 600; padding: 3px 8px; border-radius: var(--r-full);
  display: flex; align-items: center; gap: 2px;
  white-space: nowrap; position: absolute; top: 14px; right: 14px;
}
.stat-trend.up { background: #f0fdf4; color: #16a34a; }
.stat-trend.neutral { background: var(--brand-light); color: var(--brand); }

/* =============================================
   筛选栏
   ============================================= */
.filter-bar {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 12px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}
.filter-right { display: flex; align-items: center; gap: 10px; }
.platform-tag {
  font-size: 10px; font-weight: 700; padding: 1px 4px;
  border-radius: 3px; color: #fff; margin-left: 4px;
}
.tt { background: #ff0050; }
.ig { background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888); }
.yt { background: #ff0000; }
.am { background: #ff9900; color: #fff; }

/* Element Plus 在筛选栏的覆盖（使用全局变量，不再硬编码暗色） */
.filter-bar :deep(.el-input__wrapper),
.filter-bar :deep(.el-select__wrapper) {
  background: var(--bg-card) !important;
}
.filter-bar :deep(.el-input__inner),
.filter-bar :deep(.el-select__placeholder) {
  color: var(--text-primary) !important;
}
.filter-bar :deep(.el-radio-button__inner) {
  background: var(--bg-stripe) !important;
  border-color: var(--border) !important;
  color: var(--text-secondary) !important;
}
.filter-bar :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: var(--brand) !important;
  border-color: var(--brand) !important;
  color: #fff !important;
  box-shadow: -1px 0 0 0 var(--brand) !important;
}

/* =============================================
   主体网格
   ============================================= */
.main-grid {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 20px;
  align-items: start;
}

/* =============================================
   达人列表面板
   ============================================= */
.kol-list-panel {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  overflow: hidden;
}
.panel-header {
  padding: 14px 18px;
  border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between;
}
.panel-title { font-size: 13.5px; font-weight: 600; color: var(--text-primary); }
.panel-count {
  font-size: 11px; color: var(--text-secondary);
  background: var(--bg-stripe);
  padding: 2px 8px; border-radius: var(--r-full);
}
.kol-list {
  max-height: 640px; overflow-y: auto; padding: 8px;
  scrollbar-width: thin;
  scrollbar-color: #d1d5db transparent;
}
.kol-list::-webkit-scrollbar { width: 4px; }
.kol-list::-webkit-scrollbar-track { background: transparent; }
.kol-list::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 4px; }

.kol-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: var(--r-md);
  cursor: pointer;
  transition: all var(--dur) var(--ease);
  border: 1px solid transparent;
  margin-bottom: 2px;
}
.kol-card:hover {
  background: var(--bg-hover);
  border-color: var(--border);
}
.kol-card.active {
  background: var(--brand-light);
  border-color: rgba(37,99,235,.35);
}

.kol-avatar-wrap { position: relative; flex-shrink: 0; }
.kol-avatar { border: 2px solid var(--border); }
.kol-card.active .kol-avatar { border-color: var(--brand); }
.kol-platform-badge {
  position: absolute; bottom: -2px; right: -2px;
  font-size: 9px; font-weight: 700; color: #fff;
  padding: 1px 3px; border-radius: 3px;
}
.kol-platform-badge.tiktok { background: #ff0050; }
.kol-platform-badge.instagram { background: linear-gradient(45deg, #f09433, #e6683c, #dc2743); }
.kol-platform-badge.youtube { background: #ff0000; }
.kol-platform-badge.amazon { background: #ff9900; }

.kol-info { flex: 1; min-width: 0; }
.kol-name { font-size: 13.5px; font-weight: 600; color: var(--text-primary); margin-bottom: 4px; }
.kol-meta { display: flex; align-items: center; gap: 4px; margin-bottom: 4px; flex-wrap: wrap; }
.kol-country { font-size: 11px; color: var(--text-muted); }
.kol-level, .kol-style { font-size: 10px; padding: 1px 5px; border-radius: var(--r-xs); }
.nano-tag   { background: #f0fdf4; color: #16a34a; }
.micro-tag  { background: #eff6ff; color: #2563eb; }
.mega-tag   { background: #f5f3ff; color: #7c3aed; }
.lifestyle-tag { background: #fdf4ff; color: #a21caf; }
.review-tag  { background: #fff7ed; color: #c2410c; }
.beauty-tag  { background: #fdf4ff; color: #9333ea; }
.comedy-tag  { background: #f0fdf4; color: #15803d; }
.amazon-tag  { background: #fff7ed; color: #d97706; }

.kol-stats-row {
  display: flex; gap: 10px; font-size: 11px; color: var(--text-muted);
}
.kol-stats-row strong { color: var(--text-primary); }
.kol-action { flex-shrink: 0; }

/* =============================================
   达人详情面板
   ============================================= */
.kol-detail-panel {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  overflow: hidden;
  min-height: 500px;
}
.detail-empty {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  height: 500px; color: var(--text-muted); gap: 12px;
}
.empty-icon { font-size: 48px; opacity: 0.4; }
.detail-empty p { font-size: 13px; text-align: center; line-height: 1.6; color: var(--text-muted); }

/* 基本信息卡 */
.kol-profile-card {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-stripe);
}
.profile-top {
  display: flex; align-items: flex-start; gap: 16px; margin-bottom: 18px;
}
.profile-avatar {
  border: 2px solid var(--brand);
  flex-shrink: 0;
}
.profile-info { flex: 1; min-width: 0; }
.profile-name { font-size: 18px; font-weight: 700; color: var(--text-primary); margin-bottom: 8px; }
.profile-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
.profile-fans { display: flex; align-items: baseline; gap: 6px; }
.fans-num {
  font-size: 22px; font-weight: 700;
  color: var(--brand);
}
.fans-unit { font-size: 13px; color: var(--text-secondary); }
.fans-gender { font-size: 12px; color: var(--text-muted); margin-left: 8px; }
.profile-actions { display: flex; gap: 8px; flex-shrink: 0; }

/* 小图表区 */
.profile-charts {
  display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px;
}
.sub-chart {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--r-md); padding: 10px;
}
.sub-chart-title { font-size: 11px; color: var(--text-secondary); margin-bottom: 4px; text-align: center; }
.mini-chart { height: 80px; }

/* 图表卡 */
.chart-card {
  padding: 18px 22px;
  border-bottom: 1px solid var(--border);
}
.chart-card-header {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;
}
.chart-card-title { font-size: 13.5px; font-weight: 600; color: var(--text-primary); }
.big-chart { height: 200px; }

/* AI分析卡 */
.ai-analysis-card {
  padding: 18px 22px;
  border-bottom: 1px solid var(--border);
  background: var(--brand-light);
}
.ai-card-header {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px;
}
.ai-badge {
  display: flex; align-items: center; gap: 6px;
  font-size: 13.5px; font-weight: 700;
  color: var(--brand);
}
.ai-analysis-content { display: flex; flex-direction: column; gap: 14px; }
.analysis-item { display: flex; gap: 12px; align-items: flex-start; }
.analysis-label { width: 110px; font-size: 13px; color: var(--text-secondary); padding-top: 4px; flex-shrink: 0; }
.analysis-value { flex: 1; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.analysis-desc { font-size: 12px; color: var(--text-muted); }
.word-cloud { display: flex; flex-wrap: wrap; gap: 6px; }
.word-tag { font-size: 11px !important; }
.ai-conclusion {
  font-size: 13px; color: var(--text-primary); line-height: 1.7;
  background: rgba(102,126,234,0.12);
  padding: 12px 14px; border-radius: var(--r-md);
  border-left: 3px solid var(--brand);
  background: var(--bg-card);
}

/* 建联渠道 */
.contact-card {
  padding: 18px 22px;
  border-bottom: 1px solid var(--border);
}
.contact-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.contact-title { font-size: 13.5px; font-weight: 600; color: var(--text-primary); }
.contact-channels { display: flex; flex-direction: column; gap: 8px; }
.contact-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 12px; border-radius: var(--r-md);
  background: var(--bg-stripe);
  border: 1px solid var(--border);
  cursor: pointer; transition: all var(--dur) var(--ease);
}
.contact-item:hover {
  background: var(--bg-hover);
  border-color: var(--brand);
  transform: translateX(3px);
}
.contact-icon {
  width: 34px; height: 34px; border-radius: var(--r-md);
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 15px; flex-shrink: 0;
}
.email-icon { background: var(--brand); }
.wa-icon { background: #25d366; }
.ig-icon { background: linear-gradient(45deg, #f09433, #e6683c, #dc2743); }
.contact-type { font-size: 11.5px; color: var(--text-muted); }
.contact-val { font-size: 13px; color: var(--text-primary); font-weight: 500; }
.contact-copy { color: var(--text-muted); font-size: 14px; margin-left: auto; }

/* 样品闭环 */
.fulfillment-card { padding: 18px 22px; }
.fulfillment-header {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 18px;
  font-size: 13.5px; font-weight: 600; color: var(--text-primary);
}
.fulfillment-status {
  display: flex; align-items: center; gap: 0;
}
.fulfillment-step {
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  flex: 1; position: relative;
}
.fulfillment-step span { font-size: 11px; color: var(--text-muted); text-align: center; }
.step-dot {
  width: 12px; height: 12px; border-radius: 50%;
  background: #e5e7eb; border: 2px solid #d1d5db;
}
.fulfillment-step.done .step-dot { background: var(--success); border-color: var(--success); }
.fulfillment-step.active .step-dot { background: #fff; border-color: var(--brand); box-shadow: 0 0 0 3px rgba(37,99,235,.2); }
.fulfillment-step.done span { color: var(--success); }
.fulfillment-step.active span { color: var(--brand); font-weight: 600; }
.step-line {
  flex: 1; height: 2px; background: #e5e7eb; margin-bottom: 20px;
}
.step-line.done { background: var(--success); }

/* AI匹配弹窗 */
.ai-match-form { margin-top: 8px; }

/* 邀约信 */
.pitch-result { margin-top: 8px; }
.pitch-content {
  background: var(--bg-stripe);
  border: 1px solid var(--border);
  padding: 14px; border-radius: var(--r-md);
  font-size: 13px; line-height: 1.8; color: var(--text-primary);
  white-space: pre-wrap; min-height: 180px;
}
.pitch-actions { margin-top: 12px; }
</style>

<style>
/* 弹窗样式已由 src/styles/global.css 统一处理，无需额外覆盖 */
</style>
