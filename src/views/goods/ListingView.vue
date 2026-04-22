<template>
  <div class="page">
    <!-- 页面Header -->
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">商品上货</h1>
        <p class="page-desc">将已采集的商品编辑后上货至目标平台，支持批量操作</p>
      </div>
      <div class="page-header-right">
        <el-button @click="handleScanBarcode">
          <el-icon><FullScreen /></el-icon>
          扫码上货
        </el-button>
        <el-button @click="handlePreview">
          <el-icon><Monitor /></el-icon>
          预览
        </el-button>
        <el-button type="success" :loading="publishLoading" @click="handlePublishBatch">
          <el-icon><Upload /></el-icon>
          批量上货
        </el-button>
      </div>
    </div>

    <!-- 三步工作流指示器 -->
    <div class="workflow-bar">
      <div class="workflow-step done">
        <div class="step-num">1</div>
        <div class="step-label">采集货源<br/><small>1688/多多上货等</small></div>
      </div>
      <div class="workflow-arrow">→</div>
      <div class="workflow-step active">
        <div class="step-num">2</div>
        <div class="step-label">拖拽上货<br/><small>选择目标平台</small></div>
      </div>
      <div class="workflow-arrow">→</div>
      <div class="workflow-step">
        <div class="step-num">3</div>
        <div class="step-label">确认发布<br/><small>AI合规检测</small></div>
      </div>
    </div>

    <!-- 主内容区：左侧商品列表 + 右侧拖拽上货区 -->
    <div class="listing-layout">
      <!-- 左侧：待上货商品列表 -->
      <div class="listing-left">
        <div class="panel-title">
          <span>待上货商品</span>
          <el-badge :value="unpublishedList.length" type="primary" />
        </div>

        <!-- 搜索 -->
        <el-input
          v-model="searchKeyword"
          placeholder="搜索商品名称"
          clearable
          prefix-icon="Search"
          @input="filterList"
          style="margin-bottom: 12px"
        />

        <!-- 商品卡片列表 -->
        <div class="goods-card-list">
          <div
            v-for="item in filteredList"
            :key="item.id"
            class="goods-card"
            :class="{ active: currentGoods?.id === item.id }"
            draggable="true"
            @dragstart="onDragStartGoods($event, item)"
            @dragend="onDragEndGoods"
            @click="selectGoods(item)"
          >
            <el-image :src="item.images?.[0]" fit="cover" class="goods-thumb">
              <template #error>
                <div class="img-placeholder">
                  <el-icon size="28"><Picture /></el-icon>
                </div>
              </template>
            </el-image>
            <div class="goods-card-body">
              <div class="goods-card-name">{{ item.name }}</div>
              <div class="goods-card-meta">
                <span class="platform-tag">{{ item.platform }}</span>
                <span class="cost-tag">成本 ¥{{ item.cost }}</span>
              </div>
            </div>
            <div v-if="item._published" class="published-badge">
              <el-icon><Check /></el-icon>
            </div>
          </div>

          <el-empty v-if="filteredList.length === 0" description="暂无待上货商品" :image-size="60" />
        </div>
      </div>

      <!-- 右侧：拖拽上货主区 -->
      <div
        class="listing-right"
        @dragover.prevent="onDragOverRight"
        @drop="onDropToPlatform($event)"
        :class="{ 'drop-active': isDraggingGoods }"
      >
        <!-- 拖拽提示遮罩 -->
        <Transition name="fade">
          <div v-if="isDraggingGoods" class="drop-overlay">
            <div class="drop-hint-content">
              <el-icon class="drop-arrow-anim"><Bottom /></el-icon>
              <p class="drop-hint-title">松开鼠标即可上货到 <strong>{{ dragOverPlatform || '选中的平台' }}</strong></p>
              <p class="drop-hint-sub">AI将自动检测标题/图片/价格，适配平台规则</p>
            </div>
          </div>
        </Transition>

        <!-- 平台大图标上货区（按市场分区） -->
        <div class="platform-drop-section">
          <div class="section-label">
            <el-icon><Shop /></el-icon>
            选择目标平台（拖拽商品到图标上，或点击选择）
          </div>

          <!-- 分组展示平台 -->
          <div
            v-for="group in PLATFORM_GROUPS"
            :key="group.label"
            class="platform-group"
          >
            <div class="group-label">{{ group.label }}</div>
            <div class="platform-icon-grid">
              <div
                v-for="p in group.platforms"
                :key="p.id"
                :class="['platform-drop-card', {
                  'is-active': dragOverPlatform === p.id,
                  'has-selection': selectedForListing?.platformId === p.id
                }]"
                :style="{ '--pcolor': p.color }"
                @dragover.prevent="onDragOverPlatform(p.id)"
                @dragleave="onDragLeavePlatform(p.id)"
                @drop.prevent="onDropOnPlatform($event, p.id)"
                @click="onClickPlatform(p)"
              >
                <div class="p-icon">
                  <img :src="getPlatformIcon(p.id)" class="p-img" />
                </div>
                <div class="p-name">{{ p.name }}</div>
                <div v-if="dragOverPlatform === p.id" class="p-drop-hint">
                  <el-icon><Upload /></el-icon>
                  放开上货
                </div>
                <div v-else-if="selectedForListing?.platformId === p.id" class="p-selected-badge">
                  <el-icon><Check /></el-icon>
                  已选
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 已选商品预览（拖拽后显示） -->
        <div v-if="selectedForListing" class="selected-goods-preview">
          <div class="preview-label">
            <el-icon><Goods /></el-icon>
            已选商品
            <el-tag type="primary" size="small">{{ selectedForListing.name }}</el-tag>
          </div>
          <div class="preview-actions">
            <el-button type="primary" size="large" @click="confirmListing">
              <el-icon><Upload /></el-icon>
              确认上货至 {{ platforms.find(p => p.id === selectedForListing?.platformId)?.name }}
            </el-button>
            <el-button size="large" @click="selectedForListing = null">
              取消
            </el-button>
          </div>
        </div>

        <!-- 快捷操作区 -->
        <div v-else class="quick-actions">
          <div class="qa-title">快捷操作</div>
          <div class="qa-buttons">
            <el-button type="primary" size="large" @click="openBatchSelect">
              <el-icon><Rank /></el-icon>
              批量选择上货
            </el-button>
            <el-button size="large" @click="handleScanBarcode">
              <el-icon><FullScreen /></el-icon>
              扫码上货
            </el-button>
          </div>
        </div>

        <!-- 编辑面板 -->
        <div class="edit-panel">
        <!-- 图片管理 -->
          <div class="edit-section">
            <div class="section-title">
              <el-icon><Picture /></el-icon>
              商品图片
              <span class="section-tip">（第一张为主图，最多9张）</span>
            </div>

            <!-- AI 生图工具栏 -->
            <div class="ai-image-toolbar">
              <el-input
                v-model="imagePrompt"
                size="small"
                placeholder="描述你想要的商品主图，如：白色背景上的女士真皮手提包，简约电商风格"
                style="flex: 1"
              />
              <el-button
                size="small"
                type="primary"
                :loading="imageGenLoading"
                @click="handleGenerateImage"
                :disabled="!imagePrompt.trim() || editForm.images.length >= 9"
              >
                <el-icon><MagicStick /></el-icon>
                AI文生图
              </el-button>
            </div>

            <!-- 已有图片的AI优化入口 -->
            <div v-if="editForm.images.length > 0" class="ai-image-edit-tip">
              <span class="edit-tip-text">选中图片可</span>
              <el-button
                size="small"
                type="warning"
                plain
                :loading="imageEditLoading"
                @click="openImageEdit"
                :disabled="!currentEditImageIdx && currentEditImageIdx !== 0"
              >
                <el-icon><MagicStick /></el-icon>
                AI优化重绘
              </el-button>
              <span class="edit-tip-text">（调整背景/风格/构图）</span>
            </div>

            <div class="image-grid">
              <div
                v-for="(img, idx) in editForm.images"
                :key="idx"
                class="img-item"
                :class="{ active: currentEditImageIdx === idx }"
                @click="currentEditImageIdx = idx"
              >
                <el-image :src="img" fit="cover" class="img-thumb">
                  <template #error>
                    <div class="img-placeholder"><el-icon size="20"><Picture /></el-icon></div>
                  </template>
                </el-image>
                <div class="img-actions">
                  <el-button size="small" circle @click.stop="moveImage(idx, -1)" :disabled="idx === 0">
                    <el-icon><ArrowLeft /></el-icon>
                  </el-button>
                  <el-button size="small" circle type="danger" @click.stop="removeImage(idx)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                  <el-button size="small" circle @click.stop="moveImage(idx, 1)" :disabled="idx === editForm.images.length - 1">
                    <el-icon><ArrowRight /></el-icon>
                  </el-button>
                </div>
                <div v-if="currentEditImageIdx === idx" class="img-selected-badge">
                  <el-icon><Check /></el-icon>
                </div>
              </div>
              <el-upload
                v-if="editForm.images.length < 9"
                class="img-upload"
                :show-file-list="false"
                :before-upload="handleImageUpload"
                accept="image/*"
              >
                <el-icon><Plus /></el-icon>
                <span>添加图片</span>
              </el-upload>
            </div>

            <!-- AI 生成结果预览 -->
            <div v-if="previewImage" class="ai-image-preview">
              <el-divider content-position="left">
                <el-icon><MagicStick /></el-icon>
                AI生成结果
              </el-divider>
              <div class="preview-inner">
                <el-image :src="previewImage" fit="contain" class="preview-img" />
                <div class="preview-actions">
                  <el-button type="primary" size="small" @click="handleApplyImage">
                    <el-icon><Bottom /></el-icon>
                    设为主图
                  </el-button>
                  <el-button size="small" @click="handleAppendImage">
                    <el-icon><Plus /></el-icon>
                    追加图片
                  </el-button>
                  <el-button size="small" @click="previewImage = ''">
                    <el-icon><Delete /></el-icon>
                    取消
                  </el-button>
                </div>
              </div>
            </div>
          </div>

          <!-- AI智能生成 -->
          <div class="edit-section ai-section">
            <div class="section-title">
              <el-icon><MagicStick /></el-icon>
              AI智能生成
              <el-tag size="small" type="warning" effect="plain" style="margin-left: 8px">Beta</el-tag>
            </div>
            <div class="ai-tools">
              <!-- 标题生成 -->
              <div class="ai-tool-item">
                <div class="ai-tool-info">
                  <div class="ai-tool-name">AI生成标题</div>
                  <div class="ai-tool-desc">跨境电商优化版，含关键词+材质+卖点</div>
                </div>
                <el-button size="small" type="warning" :loading="titleLoading" @click="handleGenerateTitle">
                  <el-icon><MagicStick /></el-icon>
                  生成标题
                </el-button>
              </div>
              <div v-if="editForm.aiTitle" class="ai-result-box">
                <div class="ai-result-text">{{ editForm.aiTitle }}</div>
                <div class="ai-result-actions">
                  <el-button size="small" type="primary" plain @click="handleApplyTitle">
                    <el-icon><Bottom /></el-icon>
                    填入标题
                  </el-button>
                  <el-button size="small" @click="handleRegenerateTitle">
                    <el-icon><RefreshRight /></el-icon>
                    重新生成
                  </el-button>
                </div>
              </div>

              <!-- 卖点生成 -->
              <div class="ai-tool-item">
                <div class="ai-tool-info">
                  <div class="ai-tool-name">AI生成核心卖点</div>
                  <div class="ai-tool-desc">3-5条商品核心卖点，突出差异化竞争优势</div>
                </div>
                <el-button size="small" type="success" :loading="featuresLoading" @click="handleGenerateFeatures">
                  <el-icon><MagicStick /></el-icon>
                  生成卖点
                </el-button>
              </div>
              <div v-if="editForm.aiFeatures.length > 0" class="ai-result-box">
                <div class="features-list">
                  <div v-for="(f, idx) in editForm.aiFeatures" :key="idx" class="feature-item">
                    <span class="feature-icon">{{ f.icon }}</span>
                    <div class="feature-content">
                      <div class="feature-title">{{ f.title }}</div>
                      <div class="feature-desc">{{ f.desc }}</div>
                    </div>
                  </div>
                </div>
                <div class="ai-result-actions">
                  <el-button size="small" type="primary" plain @click="handleApplyFeatures">
                    <el-icon><Bottom /></el-icon>
                    填入描述顶部
                  </el-button>
                  <el-button size="small" :loading="featuresLoading" @click="handleRegenerateFeatures">
                    <el-icon><RefreshRight /></el-icon>
                    重新生成
                  </el-button>
                </div>
              </div>

              <!-- 描述生成 -->
              <div class="ai-tool-item">
                <div class="ai-tool-info">
                  <div class="ai-tool-name">AI生成描述</div>
                  <div class="ai-tool-desc">英文版本用于上货，附中文参考翻译</div>
                </div>
                <el-button size="small" type="warning" :loading="descLoading" @click="handleGenerateDesc">
                  <el-icon><MagicStick /></el-icon>
                  生成描述
                </el-button>
              </div>
              <div v-if="editForm.aiDesc" class="ai-result-box">
                <!-- 英文版（可填入） -->
                <div class="ai-result-header">
                  <el-tag size="small" type="info" effect="plain">🇺🇸 英文版（将填入平台）</el-tag>
                  <el-button size="small" link type="primary" @click="showDescAdjust = !showDescAdjust">
                    <el-icon><Operation /></el-icon>
                    {{ showDescAdjust ? '收起调整' : '调整描述' }}
                  </el-button>
                </div>
                <div class="ai-result-text ai-result-desc">{{ editForm.aiDesc }}</div>

                <!-- 调整选项 -->
                <div v-if="showDescAdjust" class="ai-adjust-panel">
                  <div class="ai-adjust-tip">选择调整方向：</div>
                  <div class="ai-adjust-btns">
                    <el-button
                      v-for="opt in adjustmentOptions"
                      :key="opt.value"
                      size="small"
                      :loading="descRefining && currentAdjustment === opt.value"
                      @click="handleRefineDesc(opt.value)"
                    >
                      {{ opt.label }}
                    </el-button>
                  </div>
                  <div class="ai-adjust-custom">
                    <el-input
                      v-model="customAdjustment"
                      size="small"
                      placeholder="或输入自定义要求，如：更强调送礼属性"
                      @keyup.enter="handleRefineDesc(customAdjustment)"
                    >
                      <template #append>
                        <el-button
                          :loading="descRefining && currentAdjustment === customAdjustment"
                          :disabled="!customAdjustment.trim()"
                          @click="handleRefineDesc(customAdjustment)"
                        >
                          应用
                        </el-button>
                      </template>
                    </el-input>
                  </div>
                </div>

                <!-- 中文参考翻译 -->
                <div v-if="editForm.aiDescCn" class="ai-result-cn">
                  <div class="ai-result-cn-header">
                    <el-tag size="small" type="warning" effect="plain">🇨🇳 中文参考（商家预览）</el-tag>
                    <span class="ai-cn-tip">仅供查看，不会填入平台</span>
                  </div>
                  <div class="ai-result-text ai-result-desc ai-desc-cn">{{ editForm.aiDescCn }}</div>
                </div>

                <div class="ai-result-actions">
                  <el-button size="small" type="primary" plain @click="handleApplyDesc">
                    <el-icon><Bottom /></el-icon>
                    一键填入（英文）
                  </el-button>
                  <el-button size="small" :loading="descLoading" @click="handleRegenerateDesc">
                    <el-icon><RefreshRight /></el-icon>
                    重新生成
                  </el-button>
                </div>
              </div>
            </div>
          </div>

          <!-- 目标平台 -->
          <div class="edit-section">
            <div class="section-title">
              <el-icon><Goods /></el-icon>
              上货平台
            </div>
            <div class="platform-grid">
              <div
                v-for="p in platforms"
                :key="p.id"
                class="platform-item"
                :class="{ selected: editForm.targetPlatforms.includes(p.id) }"
                @click="togglePlatform(p.id)"
              >
                <div class="platform-icon">
                  <img :src="getPlatformIcon(p.id)" class="p-img" />
                </div>
                <div class="platform-name">{{ p.name }}</div>
                <div v-if="editForm.targetPlatforms.includes(p.id)" class="platform-check">
                  <el-icon><Check /></el-icon>
                </div>
              </div>
            </div>
          </div>

          <!-- 价格规则 -->
          <div class="edit-section">
            <div class="section-title">
              <el-icon><Money /></el-icon>
              上货价格规则
            </div>
            <el-form :model="editForm" label-width="90px" size="small">
              <el-form-item label="加价方式">
                <el-radio-group v-model="editForm.pricingType">
                  <el-radio label="markup">固定加价</el-radio>
                  <el-radio label="multiplier">倍率加价</el-radio>
                </el-radio-group>
              </el-form-item>
              <el-form-item v-if="editForm.pricingType === 'markup'" label="加价金额">
                <el-input-number v-model="editForm.markupAmount" :min="0" :precision="2" style="width: 100%" />
              </el-form-item>
              <el-form-item v-if="editForm.pricingType === 'multiplier'" label="加价倍率">
                <el-input-number v-model="editForm.markupRate" :min="1" :precision="2" style="width: 100%" />
              </el-form-item>
              <el-form-item label="上货售价">
                <span class="calculated-price">
                  ¥{{ calculatedPrice }}
                  <span class="price-tip">（成本 ¥{{ editForm.cost }} + {{ editForm.pricingType === 'markup' ? '+' + editForm.markupAmount : '×' + editForm.markupRate }}）</span>
                </span>
              </el-form-item>
            </el-form>
          </div>

          <!-- 底部操作 -->
          <div class="edit-footer">
            <el-button @click="handleSaveDraft">保存草稿</el-button>
            <el-button type="primary" :loading="publishLoading" @click="handlePublish">
              <el-icon><Upload /></el-icon>
              上货至选中平台
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 预览抽屉 -->
    <el-drawer v-model="previewVisible" title="上货预览" size="480px" direction="rtl">
      <div v-if="currentGoods" class="preview-content">
        <div class="preview-goods-name">{{ editForm.name }}</div>
        <el-image
          v-if="editForm.images[0]"
          :src="editForm.images[0]"
          fit="cover"
          style="width: 100%; height: 300px; border-radius: 8px; margin-bottom: 16px"
        />
        <div class="preview-section">
          <div class="preview-label">售价</div>
          <div class="preview-price">¥{{ calculatedPrice }}</div>
        </div>
        <div class="preview-section">
          <div class="preview-label">标题</div>
          <div class="preview-text">{{ editForm.name || editForm.aiTitle || '未填写' }}</div>
        </div>
        <div class="preview-section">
          <div class="preview-label">描述</div>
          <div class="preview-text preview-desc">{{ editForm.description || editForm.aiDesc || '暂无描述' }}</div>
        </div>
        <div class="preview-section">
          <div class="preview-label">目标平台</div>
          <div class="preview-platforms">
            <el-tag v-for="pid in editForm.targetPlatforms" :key="pid" size="small" style="margin-right: 4px">
              {{ platforms.find(p => p.id === pid)?.name }}
            </el-tag>
            <span v-if="editForm.targetPlatforms.length === 0" style="color: #a1a1aa">未选择平台</span>
          </div>
        </div>
      </div>
    </el-drawer>

    <!-- 扫码上货弹窗（占位，等嘉瑞接口后完善） -->
    <el-dialog v-model="scanVisible" title="扫码上货" width="440px" destroy-on-close>
      <div class="scan-dialog-content">
        <div class="scan-placeholder">
          <el-icon :size="64" color="#d0d0d0"><FullScreen /></el-icon>
          <p class="scan-tip">打开摄像头扫描商品条码</p>
          <p class="scan-desc">扫描成功后自动匹配商品库，找到商品后直接进入上货编辑</p>
        </div>
        <!-- 备选：手动输入条码 -->
        <div class="scan-manual">
          <el-divider>或手动输入条码</el-divider>
          <div style="display:flex;gap:8px">
            <el-input v-model="scanInput" placeholder="输入商品条码或1688商品ID" clearable @keyup.enter="handleScanSearch" />
            <el-button type="primary" @click="handleScanSearch">搜索</el-button>
          </div>
          <div v-if="scanResult" class="scan-result" @click="handleScanSelect(scanResult)">
            <el-icon color="#22c55e"><Check /></el-icon>
            <span>找到商品：<strong>{{ scanResult.name }}</strong></span>
            <el-button size="small" type="primary" style="margin-left:auto">选中编辑</el-button>
          </div>
          <div v-if="scanNoResult" class="scan-result scan-no-result">
            <el-icon color="#ef4444"><Close /></el-icon>
            <span>未找到匹配商品，可先 <el-link type="primary" @click="$router.push('/goods/collect')">去采集</el-link></span>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { FullScreen } from '@element-plus/icons-vue'
import { generateTitle, generateDescription, refineDescription, generateFeatures, generateImage, editImage } from '@/api/ai'
import { getPlatformIcon } from '@/utils/platformIcons'

// ==================== Mock 数据 ====================
const mockGoods = [
  {
    id: 1,
    name: '女士连体泳装 修身显瘦海边度假温泉游泳衣',
    sku_code: 'SWIM-001',
    barcode: '6931024012345',
    platform: '1688',
    cost: 68.00,
    price: 0,
    stock: 80,
    images: [
      '/images/swimwear/O1CN01OtfunX283idPNsyQu_!!2215607027877-0-cib.jpg',
    ],
    source_url: 'https://detail.1688.com/offer/xxx.html',
    _published: false,
  },
  {
    id: 2,
    name: '儿童沙滩玩具套装 挖沙模具戏水户外沙滩套装',
    sku_code: 'TOY-001',
    barcode: '6931024012346',
    platform: '1688',
    cost: 35.00,
    price: 0,
    stock: 200,
    images: [
      '/images/toys/O1CN010FUwrw1e3m3lXVRZu_!!2201641843816-0-cib.jpg',
    ],
    source_url: 'https://detail.1688.com/offer/yyy.html',
    _published: false,
  },
  {
    id: 3,
    name: '女士比基尼泳装 两件套海边度假辣妹游泳衣',
    sku_code: 'SWIM-002',
    barcode: '',
    platform: '1688',
    cost: 45.00,
    price: 0,
    stock: 150,
    images: [
      '/images/swimwear/bikini.webp',
    ],
    source_url: 'https://detail.1688.com/offer/zzz.html',
    _published: false,
  },
]

// ==================== 平台配置 ====================
// 按市场分区：东南亚 / 欧美 / 新兴 / 社交电商 / 其他
const PLATFORM_GROUPS = [
  {
    label: '🌏 东南亚',
    platforms: [
      { id: 'shopee',  name: 'Shopee',   color: '#ee4d2d' },
      { id: 'lazada',  name: 'Lazada',    color: '#0b94d5' },
    ],
  },
  {
    label: '🇺🇸 欧美',
    platforms: [
      { id: 'amazon',  name: 'Amazon',    color: '#ff9900' },
      { id: 'ebay',    name: 'eBay',      color: '#e53238' },
      { id: 'wish',    name: 'Wish',      color: '#2a80c4' },
    ],
  },
  {
    label: '🚀 新兴市场',
    platforms: [
      { id: 'temu',    name: 'Temu',      color: '#ff6b00' },
      { id: 'shein',   name: 'SHEIN',      color: '#e5004c' },
      { id: 'ozon',    name: 'Ozon',      color: '#005bff' },
    ],
  },
  {
    label: '📱 社交电商',
    platforms: [
      { id: 'tiktok',  name: 'TikTok Shop', color: '#00f2ea' },
    ],
  },
  {
    label: '🌐 其他',
    platforms: [
      { id: 'aliexpress', name: 'AliExpress', color: '#ff4747' },
      { id: 'mercado',    name: 'Mercado',    color: '#ffe600' },
    ],
  },
]

// 扁平平台列表（保持向后兼容）
const platforms = PLATFORM_GROUPS.flatMap(g => g.platforms)

// ==================== 状态 ====================
const unpublishedList = ref([])
const filteredList = ref([])
const searchKeyword = ref('')
const currentGoods = ref(null)
const titleLoading = ref(false)
const featuresLoading = ref(false)
const descLoading = ref(false)
const descRefining = ref(false)  // 改写中
const showDescAdjust = ref(false)  // 显示调整选项
const currentAdjustment = ref('')  // 当前选中的调整方向
const customAdjustment = ref('')  // 自定义调整描述
const publishLoading = ref(false)
const previewVisible = ref(false)
const scanVisible = ref(false)
const scanInput = ref('')
const scanResult = ref(null)
const scanNoResult = ref(false)

// AI 生图相关
const imagePrompt = ref('')  // 生图描述词
const imageGenLoading = ref(false)  // 文生图加载中
const imageEditLoading = ref(false)  // 图生图加载中
const previewImage = ref('')  // AI生成结果预览
const currentEditImageIdx = ref(-1)  // 当前选中的待优化图片索引

const editForm = reactive({
  name: '',
  description: '',
  sku_code: '',
  barcode: '',
  cost: 0,
  price: 0,
  source_url: '',
  images: [],
  aiTitle: '',
  aiDesc: '',
  aiDescCn: '',  // AI生成的中文翻译（仅供商家参考）
  aiFeatures: [],  // AI生成的卖点
  targetPlatforms: ['tiktok'],
  pricingType: 'markup',
  markupAmount: 30,
  markupRate: 1.5,
})

// ==================== 计算属性 ====================
const calculatedPrice = computed(() => {
  if (editForm.pricingType === 'markup') {
    return (editForm.cost + editForm.markupAmount).toFixed(2)
  }
  return (editForm.cost * editForm.markupRate).toFixed(2)
})

// ==================== 方法 ====================
// ── 拖拽上货 ───────────────────────────────────────
const isDraggingGoods = ref(false)
const dragOverPlatform = ref(null)
const selectedForListing = ref(null)


function onDragStartGoods(e, item) {
  isDraggingGoods.value = true
  e.dataTransfer.effectAllowed = 'copy'
  const payload = { type: 'goods', id: item.id, name: item.name }
  // 同时设置两种格式，确保 drop 时能正确读取
  try {
    e.dataTransfer.setData('application/json', JSON.stringify(payload))
  } catch {}
  e.dataTransfer.setData('text/plain', JSON.stringify(payload))
  currentGoods.value = item
}

function onDragEndGoods() {
  isDraggingGoods.value = false
  dragOverPlatform.value = null
}

function onDragOverRight(e) {
  if (!isDraggingGoods.value) return
  e.preventDefault()
}

function onDragLeaveRight() {
  // 不清空 platform，让它保持悬停状态
}

function onDragOverPlatform(platformId) {
  dragOverPlatform.value = platformId
}

function onDragLeavePlatform(platformId) {
  if (dragOverPlatform.value === platformId) {
    dragOverPlatform.value = null
  }
}

function onDropOnPlatform(e, platformId) {
  e.preventDefault()
  // 同时尝试 application/json 和 text/plain 两种格式
  let raw = e.dataTransfer.getData('application/json') || e.dataTransfer.getData('text/plain')
  let item = currentGoods.value
  try { if (raw) item = JSON.parse(raw) } catch {}
  if (!item) return

  const platform = platforms.find(p => p.id === platformId)
  selectedForListing.value = { ...item, platformId }
  isDraggingGoods.value = false
  dragOverPlatform.value = null
  ElMessage.success(`已将「${item.name}」选中，准备上货至 ${platform?.name}`)
}

function onDropToPlatform(e) {
  // 如果没有悬停在具体平台，提示用户选择目标平台
  if (!dragOverPlatform.value) {
    ElMessage.warning('请将商品拖拽到具体的目标平台图标上，或点击平台图标选择')
    isDraggingGoods.value = false
  }
}

function onClickPlatform(p) {
  if (!currentGoods.value) {
    ElMessage.warning('请先从左侧选择一个商品，再点击目标平台')
    return
  }
  selectedForListing.value = { ...currentGoods.value, platformId: p.id }
}

function confirmListing() {
  if (!selectedForListing.value) return
  const platform = platforms.find(p => p.id === selectedForListing.value.platformId)
  ElMessageBox.confirm(
    `确认将「${selectedForListing.value.name}」上货至 ${platform?.name}？\n\nAI将自动检测标题/图片/价格，并适配平台合规规则。`,
    '确认上货',
    { confirmButtonText: '确认发布', cancelButtonText: '取消', type: 'success' }
  ).then(() => {
    // 标记为已发布
    const idx = unpublishedList.value.findIndex(i => i.id === selectedForListing.value.id)
    if (idx !== -1) unpublishedList.value[idx]._published = true
    ElMessage.success(`「${selectedForListing.value.name}」已成功上货至 ${platform?.name}！`)
    selectedForListing.value = null
  }).catch(() => {})
}

function openBatchSelect() {
  ElMessage.info('批量选择模式：勾选左侧商品后，点击「批量上货」按钮')
}

function filterList() {
  const kw = searchKeyword.value.toLowerCase()
  filteredList.value = unpublishedList.value.filter(item =>
    !item._published && item.name.toLowerCase().includes(kw)
  )
}

function selectGoods(item) {
  currentGoods.value = item
  editForm.name = item.name
  editForm.description = item.description || ''
  editForm.sku_code = item.sku_code || ''
  editForm.barcode = item.barcode || ''
  editForm.cost = item.cost || 0
  editForm.price = item.price || 0
  editForm.source_url = item.source_url || ''
  editForm.images = item.images || []
  editForm.aiTitle = ''
  editForm.aiDesc = ''
  editForm.aiDescCn = ''
}

async function handleGenerateTitle() {
  if (!editForm.name) {
    ElMessage.warning('请先填写商品名称')
    return
  }
  titleLoading.value = true
  try {
    const title = await generateTitle({
      name: editForm.name,
      category: '箱包皮具',
      material: '',
      style: '',
      features: '',
    })
    editForm.aiTitle = title
    ElMessage.success('标题生成成功，点击"填入标题"应用到商品')
  } catch (e) {
    ElMessage.error(e.message || '生成失败')
  } finally {
    titleLoading.value = false
  }
}

async function handleGenerateDesc() {
  if (!editForm.name) {
    ElMessage.warning('请先填写商品名称')
    return
  }
  descLoading.value = true
  try {
    const result = await generateDescription({
      name: editForm.name,
      category: '箱包皮具',
      material: '',
      style: '',
      features: '',
    })
    editForm.aiDesc = result.description
    editForm.aiDescCn = result.description_cn
    ElMessage.success('描述生成成功，可一键填入英文，或调整优化')
  } catch (e) {
    ElMessage.error(e.message || '生成失败')
  } finally {
    descLoading.value = false
  }
}

function handleApplyTitle() {
  if (!editForm.aiTitle) return
  editForm.name = editForm.aiTitle
  ElMessage.success('已填入标题，可直接编辑修改')
}

function handleApplyDesc() {
  if (!editForm.aiDesc) return
  editForm.description = editForm.aiDesc
  ElMessage.success('已填入描述，可直接编辑修改')
}

function handleApplyFeatures() {
  if (editForm.aiFeatures.length === 0) return
  const featuresText = editForm.aiFeatures
    .map(f => `• ${f.icon} ${f.title}：${f.desc}`)
    .join('\n')
  const featuresBlock = `【Core Selling Points】\n${featuresText}\n\n`
  editForm.description = featuresBlock + (editForm.description || '')
  ElMessage.success('已填入卖点，可直接编辑修改')
}

function handleRegenerateTitle() {
  handleGenerateTitle()
}

async function handleGenerateFeatures() {
  if (!editForm.name) {
    ElMessage.warning('请先填写商品名称')
    return
  }
  featuresLoading.value = true
  try {
    const features = await generateFeatures({
      name: editForm.name,
      category: '箱包皮具',
    })
    editForm.aiFeatures = features
    ElMessage.success('核心卖点生成成功！')
  } catch (e) {
    ElMessage.error(e.message || '生成失败')
  } finally {
    featuresLoading.value = false
  }
}

function handleRegenerateFeatures() {
  handleGenerateFeatures()
}

function handleRegenerateDesc() {
  handleGenerateDesc()
}

// 常用调整方向
const adjustmentOptions = [
  { label: '更简短', value: '把描述改得更简短，每个bullet point控制在10个词以内' },
  { label: '更详细', value: '把描述改得更详细，增加更多产品细节和使用场景' },
  { label: '更促销', value: '语气更促销，增加紧迫感和购买引导' },
  { label: '突出材质', value: '重点强调材质优势和工艺品质' },
  { label: '适合TikTok', value: '适合TikTok短视频风格，更年轻化、有吸引力' },
  { label: '适合Amazon', value: '更适合Amazon平台的SEO风格，关键词密度更高' },
]

async function handleRefineDesc(adjustment) {
  if (!editForm.aiDesc) {
    ElMessage.warning('请先生成描述')
    return
  }
  descRefining.value = true
  showDescAdjust.value = false
  currentAdjustment.value = adjustment
  try {
    const result = await refineDescription(editForm.aiDesc, adjustment)
    editForm.aiDesc = result.description
    editForm.aiDescCn = result.description_cn
    ElMessage.success('描述已调整，可一键填入英文或继续调整')
  } catch (e) {
    ElMessage.error(e.message || '调整失败')
  } finally {
    descRefining.value = false
  }
}

function togglePlatform(id) {
  const idx = editForm.targetPlatforms.indexOf(id)
  if (idx >= 0) {
    editForm.targetPlatforms.splice(idx, 1)
  } else {
    editForm.targetPlatforms.push(id)
  }
}

function removeImage(idx) {
  editForm.images.splice(idx, 1)
}

function moveImage(idx, dir) {
  const newIdx = idx + dir
  if (newIdx < 0 || newIdx >= editForm.images.length) return
  const temp = editForm.images[idx]
  editForm.images[idx] = editForm.images[newIdx]
  editForm.images[newIdx] = temp
}

function handleImageUpload(file) {
  // TODO: 调用上传接口获取图片URL
  const url = URL.createObjectURL(file)
  if (editForm.images.length < 9) {
    editForm.images.push(url)
  }
  return false
}

function handlePreview() {
  if (!currentGoods.value) {
    ElMessage.warning('请先选择一个商品')
    return
  }
  previewVisible.value = true
}

function handleScanBarcode() {
  scanVisible.value = true
  scanInput.value = ''
  scanResult.value = null
  scanNoResult.value = false
}

function handleScanSearch() {
  if (!scanInput.value.trim()) {
    ElMessage.warning('请输入条码')
    return
  }
  // TODO: 调用后端接口匹配商品条码
  // Mock逻辑：在当前列表中匹配
  const found = unpublishedList.value.find(
    item => item.barcode === scanInput.value.trim()
  )
  if (found) {
    scanResult.value = found
    scanNoResult.value = false
    ElMessage.success('找到商品！')
  } else {
    scanResult.value = null
    scanNoResult.value = true
    ElMessage.warning('未找到匹配商品，请检查条码或先去采集')
  }
}

// 扫码枪模式：扫码后自动搜索并选中
function handleBarcodeScan(barcode) {
  scanInput.value = barcode
  handleScanSearch()
  if (scanResult.value) {
    // 找到后自动选中
    nextTick(() => handleScanSelect(scanResult.value))
  }
}

function handleScanSelect(item) {
  selectGoods(item)
  scanVisible.value = false
  // 滚动到右侧编辑面板
  document.querySelector('.listing-right')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function handleSaveDraft() {
  ElMessage.success('草稿已保存')
}

async function handlePublish() {
  if (editForm.targetPlatforms.length === 0) {
    ElMessage.warning('请至少选择一个上货平台')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确认上货至 ${editForm.targetPlatforms.length} 个平台？`,
      '确认上货',
      { type: 'info' }
    )
    publishLoading.value = true
    // TODO: 调用上货接口
    await new Promise(r => setTimeout(r, 1500))
    currentGoods.value._published = true
    ElMessage.success('上货成功！')
    previewVisible.value = false
  } catch {
    // 用户取消
  } finally {
    publishLoading.value = false
  }
}

async function handlePublishBatch() {
  const items = filteredList.value.filter(item => !item._published)
  if (items.length === 0) {
    ElMessage.warning('没有可上货的商品')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确认批量上货 ${items.length} 件商品至 ${editForm.targetPlatforms.length} 个平台？`,
      '批量上货',
      { type: 'info' }
    )
    publishLoading.value = true
    // TODO: 调用批量上货接口
    await new Promise(r => setTimeout(r, 2000))
    items.forEach(item => { item._published = true })
    ElMessage.success(`批量上货成功！共 ${items.length} 件`)
  } catch {
    // 用户取消
  } finally {
    publishLoading.value = false
  }
}

onMounted(() => {
  unpublishedList.value = mockGoods.filter(g => !g._published)
  filterList()
})

// ==================== AI 图像生成 ====================

/** 文生图：根据商品信息生成主图 */
async function handleGenerateImage() {
  const prompt = imagePrompt.value.trim()
  if (!prompt) {
    ElMessage.warning('请输入图片描述')
    return
  }
  if (editForm.images.length >= 9) {
    ElMessage.warning('图片数量已达上限（9张）')
    return
  }
  imageGenLoading.value = true
  try {
    // 构建增强 prompt（结合商品名称让描述更精准）
    const productName = editForm.name || ''
    const enhancedPrompt = productName
      ? `${productName}, ${prompt}, e-commerce product photography, clean white background, high quality, professional`
      : `${prompt}, e-commerce product photography, clean white background, high quality, professional`

    const result = await generateImage(enhancedPrompt)
    const imgData = result.imageBase64 || result.imageUrl
    if (imgData) {
      previewImage.value = imgData
      ElMessage.success('AI 图片生成成功，可预览后选择设为主图或追加')
    } else {
      ElMessage.error('图片生成失败，请稍后重试')
    }
  } catch (e) {
    ElMessage.error(e.message || 'AI 生图异常')
  } finally {
    imageGenLoading.value = false
  }
}

/** 将预览图设为主图（替换第一张） */
function handleApplyImage() {
  if (!previewImage.value) return
  if (editForm.images.length === 0) {
    editForm.images.push(previewImage.value)
  } else {
    editForm.images.splice(0, 1, previewImage.value)
  }
  previewImage.value = ''
  ElMessage.success('已设为主图')
}

/** 将预览图追加到图片列表末尾 */
function handleAppendImage() {
  if (!previewImage.value) return
  if (editForm.images.length >= 9) {
    ElMessage.warning('图片数量已达上限（9张）')
    return
  }
  editForm.images.push(previewImage.value)
  previewImage.value = ''
  ElMessage.success('已追加图片')
}

/** 打开图生图编辑弹窗 */
function openImageEdit() {
  const idx = currentEditImageIdx.value
  if (idx < 0 || idx >= editForm.images.length) {
    ElMessage.warning('请先点击选中一张图片，再点击优化重绘')
    return
  }
  ElMessageBox.prompt('请输入图片优化指令，如：更换为纯白背景 / 添加阴影效果 / 更清晰的细节', 'AI 图片优化', {
    confirmButtonText: '生成',
    cancelButtonText: '取消',
    inputPlaceholder: '例如：更换为纯白背景，突出商品质感',
  }).then(({ value }) => {
    if (!value?.trim()) return
    handleEditImage(value.trim(), idx)
  }).catch(() => {})
}

/** 图生图：基于选中图片重绘 */
async function handleEditImage(instruction, imgIdx) {
  const imgUrl = editForm.images[imgIdx]
  imageEditLoading.value = true
  try {
    // 将图片URL转换为 base64（本地URL或网络URL）
    let imageBase64 = ''
    try {
      const resp = await fetch(imgUrl)
      const blob = await resp.blob()
      const reader = new FileReader()
      imageBase64 = await new Promise((resolve, reject) => {
        reader.onload = () => resolve(reader.result)
        reader.onerror = reject
        reader.readAsDataURL(blob)
      })
    } catch {
      // 如果 fetch 失败（比如跨域），直接用 URL
      imageBase64 = imgUrl
    }

    const productName = editForm.name || ''
    const enhancedPrompt = productName
      ? `${productName}, ${instruction}, maintain product identity, high quality e-commerce image`
      : `${instruction}, maintain original product, high quality e-commerce image`

    const result = await editImage(enhancedPrompt, imageBase64)
    const imgData = result.imageBase64 || result.imageUrl
    if (imgData) {
      editForm.images.splice(imgIdx, 1, imgData)
      ElMessage.success('图片优化完成')
    } else {
      ElMessage.error('图片优化失败，请稍后重试')
    }
  } catch (e) {
    ElMessage.error(e.message || 'AI 图片优化异常')
  } finally {
    imageEditLoading.value = false
  }
}
</script>

<style scoped>
/* ===== 页面容器 ===== */
.page {
  padding: 22px 26px;
  width: 100%;
  flex: 1;
  box-sizing: border-box;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* ===== 拖拽引导Banner ===== */
.drag-guide-banner {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 20px;
  background: linear-gradient(135deg, rgba(8, 91, 156, 0.08) 0%, rgba(46, 173, 62, 0.08) 100%);
  border: 2px dashed rgba(8, 91, 156, 0.3);
  border-radius: 12px;
  margin-bottom: 16px;
}

.drag-guide-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #085B9C 0%, #2ead3e 100%);
  color: white;
  flex-shrink: 0;
  animation: floatUp 2s ease-in-out infinite;
}

@keyframes floatUp {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}

.drag-guide-text {
  flex: 1;
  font-size: 13px;
  color: var(--el-text-color-regular);
}

.drag-guide-text strong {
  color: #085B9C;
  font-weight: 700;
}

.drag-guide-platforms {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.platform-chip {
  padding: 3px 10px;
  border-radius: 20px;
  background: #fff;
  border: 1px solid rgba(8, 91, 156, 0.3);
  font-size: 12px;
  font-weight: 600;
}

.platform-chip.more {
  border-color: rgba(8, 91, 156, 0.3);
  color: var(--el-text-color-secondary);
}

/* ===== 布局 ===== */
.listing-layout {
  display: flex;
  gap: 16px;
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

/* ===== 工作流指示条 ===== */
.workflow-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  padding: 14px 24px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 12px;
  margin-bottom: 16px;
}

.workflow-step {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 20px;
  border-radius: 8px;
  transition: all 0.25s;
}

.workflow-step.active {
  background: rgba(8, 91, 156, 0.08);
}

.workflow-step.done .step-num {
  background: #2ead3e;
  color: #fff;
}

.workflow-step.active .step-num {
  background: #085B9C;
  color: #fff;
}

.step-num {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--el-fill-color-light);
  color: var(--el-text-color-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

.step-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1.4;
}

.step-label small {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  font-weight: 400;
}

.workflow-arrow {
  font-size: 18px;
  color: var(--el-border-color);
  padding: 0 4px;
}

/* ===== 左侧面板 ===== */
.listing-left {
  width: 272px;
  flex-shrink: 0;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow: hidden;
  box-shadow: var(--shadow-xs);
}
.panel-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.goods-card-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.goods-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px;
  border-radius: var(--r-md);
  border: 1.5px solid transparent;
  cursor: pointer;
  position: relative;
  transition: all var(--dur) var(--ease);
  background: transparent;
}
.goods-card:hover { background: var(--bg-hover); }
.goods-card.active {
  background: var(--brand-light);
  border-color: var(--brand);
}
.goods-thumb {
  width: 46px; height: 46px;
  border-radius: var(--r-sm);
  flex-shrink: 0;
  border: 1px solid var(--border);
}
.img-placeholder {
  width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
  background: var(--bg-secondary);
  color: var(--text-placeholder);
}
.goods-card-body { flex: 1; min-width: 0; }
.goods-card-name {
  font-size: 12.5px;
  color: var(--text-primary);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.goods-card-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 3px;
}
.platform-tag {
  font-size: 10px;
  background: var(--bg-stripe);
  color: var(--text-secondary);
  padding: 1px 6px;
  border-radius: var(--r-sm);
  border: 1px solid var(--border);
}
.cost-tag {
  font-size: 11px;
  color: var(--brand);
  font-weight: 600;
}
.published-badge {
  position: absolute;
  top: 4px; right: 4px;
  background: var(--success);
  color: #fff;
  width: 17px; height: 17px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  box-shadow: 0 2px 6px rgba(16,185,129,.4);
}

/* ===== 右侧拖拽上货区 ===== */
.listing-right {
  flex: 1;
  overflow-y: auto;
  background: var(--el-bg-color);
  border: 2px dashed var(--el-border-color-light);
  border-radius: var(--r-lg);
  position: relative;
  transition: border-color 0.25s, background 0.25s;
}

.listing-right.drop-active {
  border-color: var(--el-color-primary);
  background: rgba(8, 91, 156, 0.03);
}

/* 拖拽遮罩 */
.drop-overlay {
  position: absolute;
  inset: 0;
  background: rgba(8, 91, 156, 0.82);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--r-lg);
}

.drop-hint-content {
  text-align: center;
  color: white;
}

.drop-hint-title {
  font-size: 20px;
  font-weight: 700;
  margin: 12px 0 8px;
}

.drop-hint-sub {
  font-size: 14px;
  opacity: 0.8;
}

.drop-arrow-anim {
  font-size: 52px;
  color: #2ead3e;
  animation: bounceDown 0.8s ease-in-out infinite;
}

@keyframes bounceDown {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(10px); }
}

/* 平台上货区 */
.platform-drop-section {
  padding: 24px;
  position: relative;
  z-index: 101; /* 浮在遮罩层之上，保证拖拽到平台图标 */
}

.section-label {
  font-size: 14px;
  font-weight: 700;
  color: var(--el-text-color-regular);
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 分组布局 */
.platform-group {
  margin-bottom: 20px;
}

.platform-group:last-child {
  margin-bottom: 0;
}

.group-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  margin-bottom: 10px;
  padding-left: 4px;
}

/* 平台大图标网格 */
.platform-icon-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 14px;
}

.platform-drop-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 18px 8px;
  background: var(--el-bg-color);
  border: 2px solid var(--el-border-color-light);
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  user-select: none;
}

.platform-drop-card:hover {
  border-color: var(--pcolor, var(--el-color-primary));
  background: var(--el-fill-color-light);
  transform: translateY(-2px);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
}

.platform-drop-card.is-active {
  border-color: var(--pcolor, var(--el-color-primary));
  background: color-mix(in srgb, var(--pcolor) 12%, white);
  transform: scale(1.06);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--pcolor) 25%, transparent);
}

.p-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
  background: transparent; /* 透明底，SVG 自身带品牌色 */
}
.p-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  padding: 4px;
}

.p-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  text-align: center;
}

.p-drop-hint {
  position: absolute;
  bottom: -2px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--pcolor, var(--el-color-primary));
  color: white;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 10px;
  border-radius: 20px;
  white-space: nowrap;
}

.p-selected-badge {
  background: #2ead3e;
  color: white;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 20px;
}

/* 已选商品预览 */
.selected-goods-preview {
  margin: 0 24px 20px;
  padding: 20px;
  background: linear-gradient(135deg, rgba(8, 91, 156, 0.08) 0%, rgba(46, 173, 62, 0.08) 100%);
  border: 2px solid rgba(8, 91, 156, 0.2);
  border-radius: 14px;
}

.preview-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-regular);
  margin-bottom: 14px;
}

.preview-actions {
  display: flex;
  gap: 12px;
}

.preview-actions .el-button {
  flex: 1;
  height: 44px;
  font-size: 15px;
  font-weight: 700;
}

/* 快捷操作区 */
.quick-actions {
  padding: 24px;
  margin-top: 0;
}

.qa-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  margin-bottom: 12px;
}

.qa-buttons {
  display: flex;
  gap: 12px;
}

.qa-buttons .el-button {
  flex: 1;
  height: 44px;
  font-size: 14px;
}

/* 空面板 */
.empty-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-muted);
  font-size: 14px;
}

.edit-panel { padding: 20px; }

.edit-section {
  margin-bottom: 22px;
  padding-bottom: 22px;
  border-bottom: 1px solid var(--border);
}
.edit-section:last-of-type { border-bottom: none; }

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.section-title::before {
  content: '';
  display: inline-block;
  width: 3px; height: 13px;
  background: var(--brand);
  border-radius: 2px;
  flex-shrink: 0;
}
.section-title .el-icon { color: var(--brand); }
.section-tip { font-size: 11px; color: var(--text-muted); font-weight: 400; margin-left: 4px; }

/* ===== 图片区 ===== */
.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(88px, 1fr));
  gap: 10px;
}
.img-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: var(--r-md);
  overflow: hidden;
  border: 1px solid var(--border);
}
.img-thumb { width: 100%; height: 100%; object-fit: cover; }
.img-actions {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  background: rgba(0,0,0,.52);
  display: flex;
  justify-content: center;
  gap: 4px;
  padding: 5px;
  opacity: 0;
  transition: opacity var(--dur);
}
.img-item:hover .img-actions { opacity: 1; }
.img-upload {
  aspect-ratio: 1;
  border: 2px dashed var(--border-hover);
  border-radius: var(--r-md);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 5px;
  cursor: pointer;
  font-size: 11px;
  color: var(--text-muted);
  transition: all var(--dur);
}
.img-upload:hover { border-color: var(--brand); color: var(--brand); background: var(--brand-light); }

/* ===== AI 生图工具栏 ===== */
.ai-image-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.ai-image-edit-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  font-size: 12px;
  color: var(--text-muted);
}
.edit-tip-text { color: var(--text-muted); }

/* 选中图片高亮 */
.img-item.active { border-color: var(--brand); box-shadow: 0 0 0 2px rgba(37,99,235,.25); }
.img-selected-badge {
  position: absolute;
  top: 4px; right: 4px;
  background: var(--brand);
  color: #fff;
  border-radius: 50%;
  width: 18px; height: 18px;
  display: flex; align-items: center; justify-content: center;
  font-size: 10px;
}

/* AI 生成结果预览 */
.ai-image-preview {
  margin-top: 12px;
  padding: 12px;
  background: var(--bg-stripe);
  border-radius: var(--r-md);
  border: 1px dashed var(--brand);
}
.preview-inner {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 10px;
}
.preview-img {
  width: 120px;
  height: 120px;
  border-radius: var(--r-md);
  border: 1px solid var(--border);
  background: #fff;
  flex-shrink: 0;
}
.preview-actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* ===== AI 区 ===== */
.ai-section {
  background: var(--bg-stripe);
  margin: 0 -20px;
  padding: 18px 20px;
  border-bottom: 1px solid var(--border);
}
.ai-tool-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 9px 0;
}
.ai-tool-info { flex: 1; }
.ai-tool-name { font-size: 13.5px; color: var(--text-primary); font-weight: 500; }
.ai-tool-desc { font-size: 12px; color: var(--text-muted); margin-top: 2px; }

.ai-result-box {
  background: var(--warning-light);
  border: 1px solid rgba(217,119,6,.2);
  border-radius: var(--r-md);
  padding: 13px;
  margin-bottom: 10px;
}
.ai-result-text {
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.65;
  margin-bottom: 10px;
  word-break: break-all;
}
.ai-result-desc {
  max-height: 110px;
  overflow-y: auto;
  white-space: pre-wrap;
}
.ai-result-actions { display: flex; gap: 8px; }
.ai-result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.ai-adjust-panel {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--r-sm);
  padding: 10px;
  margin: 8px 0;
}
.ai-adjust-tip { font-size: 12px; color: var(--text-secondary); margin-bottom: 8px; }
.ai-adjust-btns { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.ai-adjust-btns .el-button { font-size: 12px; }
.ai-adjust-custom { margin-top: 8px; }

.ai-result-cn {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed #e0c040;
}
.ai-result-cn-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.ai-cn-tip { font-size: 11px; color: var(--text-muted); }
.ai-desc-cn { font-size: 12px; color: var(--text-secondary); max-height: 100px; }

/* ===== 卖点列表 ===== */
.features-list { display: flex; flex-direction: column; gap: 8px; margin-bottom: 10px; }
.feature-item { display: flex; align-items: flex-start; gap: 8px; }
.feature-icon { font-size: 18px; flex-shrink: 0; line-height: 1.4; }
.feature-content { flex: 1; }
.feature-title { font-size: 13px; color: var(--text-primary); font-weight: 500; }
.feature-desc { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }

/* ===== 平台选择 ===== */
.platform-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}
.platform-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 11px;
  border: 1.5px solid var(--border);
  border-radius: var(--r-md);
  cursor: pointer;
  transition: all var(--dur);
  position: relative;
}
.platform-item:hover { border-color: var(--border-hover); background: var(--bg-hover); }
.platform-item.selected { border-color: var(--brand); background: var(--brand-light); }
.platform-icon {
  width: 26px; height: 26px;
  border-radius: var(--r-sm);
  display: flex; align-items: center; justify-content: center;
  overflow: hidden; flex-shrink: 0;
  background: transparent; /* 透明底，SVG 自身带品牌色 */
}
.platform-icon .p-img {
  width: 100%; height: 100%;
  object-fit: contain;
  padding: 2px;
}
.platform-name { font-size: 12.5px; color: var(--text-primary); font-weight: 500; }
.platform-check {
  position: absolute;
  top: -6px; right: -6px;
  background: var(--brand);
  color: #fff;
  width: 17px; height: 17px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 10px;
  box-shadow: var(--shadow-brand);
}

/* ===== 价格 ===== */
.calculated-price { font-size: 22px; color: var(--danger); font-weight: 700; }
.price-tip { font-size: 12px; color: var(--text-muted); font-weight: 400; margin-left: 8px; }

/* ===== 底部 ===== */
.edit-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 6px;
}

/* ===== 预览抽屉 ===== */
.preview-content { padding: 0 4px; }
.preview-goods-name { font-size: 17px; font-weight: 700; color: var(--text-primary); margin-bottom: 14px; }
.preview-section { margin-bottom: 14px; }
.preview-label { font-size: 11px; color: var(--text-muted); margin-bottom: 4px; text-transform: uppercase; letter-spacing: .04em; }
.preview-price { font-size: 24px; color: var(--danger); font-weight: 700; }
.preview-text { font-size: 14px; color: var(--text-primary); line-height: 1.65; }
.preview-desc { white-space: pre-wrap; }

/* ===== 扫码弹窗 ===== */
.scan-dialog-content { text-align: center; }
.scan-placeholder {
  padding: 30px 0 14px;
  background: var(--bg-stripe);
  border-radius: var(--r-lg);
  border: 2px dashed var(--border-hover);
  margin-bottom: 14px;
}
.scan-tip { font-size: 15px; color: var(--text-primary); font-weight: 500; margin: 12px 0 4px; }
.scan-desc { font-size: 12px; color: var(--text-muted); }
.scan-manual { text-align: left; }
.scan-result {
  display: flex; align-items: center; gap: 8px;
  padding: 11px;
  background: rgba(16,185,129,.06);
  border: 1px solid rgba(16,185,129,.25);
  border-radius: var(--r-md);
  margin-top: 10px;
  cursor: pointer;
  transition: background var(--dur);
}
.scan-result:hover { background: rgba(16,185,129,.12); }
.scan-no-result { background: rgba(239,68,68,.05); border-color: rgba(239,68,68,.2); }
</style>
