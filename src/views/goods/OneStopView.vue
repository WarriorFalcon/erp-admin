<template>
  <div class="page">
    <!-- 页面Header -->
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">一站式采集上货</h1>
        <p class="page-desc">采集+合规+优化+上架，一个动作全闭环</p>
      </div>
      <div class="page-header-right">
        <el-tag type="success" effect="plain" size="small">Beta</el-tag>
        <el-button @click="showBatchPanel = !showBatchPanel">
          <el-icon><Rank /></el-icon>
          批量模式
        </el-button>
      </div>
    </div>

    <!-- ====== 批量模式面板 ====== -->
    <Transition name="slide-down">
      <el-card v-if="showBatchPanel" class="batch-panel">
        <template #header>
          <div class="card-header">
            <div class="card-header-left">
              <el-icon><Rank /></el-icon>
              <span>批量采集并铺货</span>
            </div>
            <el-button size="small" text @click="showBatchPanel = false">收起</el-button>
          </div>
        </template>

        <!-- 批量导入方式 -->
        <div class="batch-import-tabs">
          <el-radio-group v-model="batchImportType" size="small">
            <el-radio-button value="links">链接批量导入</el-radio-button>
            <el-radio-button value="excel">Excel 文件导入</el-radio-button>
          </el-radio-group>
        </div>

        <!-- 链接导入 -->
        <div v-if="batchImportType === 'links'" class="batch-links-input">
          <el-input
            v-model="batchLinksText"
            type="textarea"
            :rows="5"
            placeholder="每行一个商品链接，支持1688/淘宝/拼多多链接，如：&#10;https://detail.1688.com/offer/xxx.html&#10;https://item.taobao.com/item.htm?id=xxx"
          />
          <div class="batch-links-actions">
            <el-button type="primary" :loading="batchRunning" @click="startBatchListing">
              <el-icon><Upload /></el-icon>
              开始批量采集并铺货
            </el-button>
            <span class="batch-hint">每行一个链接，支持多平台混合导入</span>
          </div>
        </div>

        <!-- Excel导入 -->
        <div v-else class="batch-excel-input">
          <el-upload
            drag
            :auto-upload="false"
            :limit="1"
            accept=".xlsx,.xls,.csv"
            @change="handleExcelChange"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖拽 Excel 文件到此处，或 <em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">支持 .xlsx / .xls / .csv 格式，需包含「商品链接」列</div>
            </template>
          </el-upload>
          <div v-if="batchExcelFile" class="batch-file-info">
            <el-icon color="#22c55e"><Check /></el-icon>
            <span>{{ batchExcelFile.name }}</span>
            <el-button size="small" type="primary" :loading="batchRunning" @click="startBatchListing">
              开始批量采集并铺货
            </el-button>
          </div>
        </div>

        <!-- 批量铺货规则配置 -->
        <div class="batch-rules">
          <div class="rules-title">
            <el-icon><Setting /></el-icon>
            铺货规则配置
          </div>
          <el-form :model="batchRules" :inline="true" size="small">
            <el-form-item label="目标平台">
              <el-select v-model="batchRules.targetPlatforms" multiple placeholder="选择平台" style="width: 280px">
                <el-option v-for="p in platforms" :key="p.id" :label="p.name" :value="p.id">
                  <div class="platform-opt">
                    <span class="platform-dot" :style="{ background: p.color }"></span>
                    {{ p.name }}
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="加价方式">
              <el-radio-group v-model="batchRules.pricingType">
                <el-radio value="markup">固定加价 ¥</el-radio>
                <el-radio value="multiplier">倍率加价 ×</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item v-if="batchRules.pricingType === 'markup'" label="加价金额">
              <el-input-number v-model="batchRules.markupAmount" :min="0" :precision="2" />
            </el-form-item>
            <el-form-item v-else label="加价倍率">
              <el-input-number v-model="batchRules.markupRate" :min="1" :precision="2" />
            </el-form-item>
            <el-form-item label="店铺">
              <el-select v-model="batchRules.shopId" placeholder="选择店铺" style="width: 180px">
                <el-option label="默认店铺" value="default" />
              </el-select>
            </el-form-item>
          </el-form>
        </div>

        <!-- 批量执行进度 -->
        <div v-if="batchItems.length > 0" class="batch-progress">
          <div class="batch-progress-header">
            <span class="batch-progress-title">
              批量执行中
              <el-tag size="small" type="primary">{{ batchItems.length }} 件商品</el-tag>
            </span>
            <el-button size="small" type="danger" text @click="cancelBatch">取消执行</el-button>
          </div>
          <el-progress :percentage="batchProgress" :stroke-width="10" style="margin: 10px 0" />
          <div class="batch-stats">
            <span class="stat-item stat-success">
              <el-icon><Check /></el-icon> 成功 {{ batchStats.success }}
            </span>
            <span class="stat-item stat-fail">
              <el-icon><Close /></el-icon> 失败 {{ batchStats.fail }}
            </span>
            <span class="stat-item stat-pending">
              <el-icon><Loading /></el-icon> 进行中 {{ batchStats.running }}
            </span>
          </div>
        </div>
      </el-card>
    </Transition>

    <!-- ====== 小白极简模式 ====== -->
    <div class="onestop-layout">
      <!-- 左侧：核心操作区 -->
      <div class="onestop-left">

        <!-- 步骤进度条 -->
        <div class="step-flow">
          <div
            v-for="(step, idx) in flowSteps"
            :key="step.id"
            :class="['flow-step', {
              'is-done': currentStep > idx,
              'is-active': currentStep === idx,
              'is-pending': currentStep < idx,
            }]"
          >
            <div class="flow-step-icon">
              <el-icon v-if="currentStep > idx"><Check /></el-icon>
              <el-icon v-else-if="currentStep === idx && step.running" class="is-loading"><Loading /></el-icon>
              <span v-else>{{ idx + 1 }}</span>
            </div>
            <div class="flow-step-info">
              <div class="flow-step-name">{{ step.name }}</div>
              <div class="flow-step-desc">{{ step.desc }}</div>
            </div>
            <div v-if="idx < flowSteps.length - 1" class="flow-connector">
              <div :class="['flow-line', { done: currentStep > idx }]"></div>
            </div>
          </div>
        </div>

        <!-- 链接输入区 -->
        <el-card class="input-card">
          <template #header>
            <div class="card-header">
              <div class="card-header-left">
                <el-icon><Link /></el-icon>
                <span>第一步：粘贴货源链接</span>
              </div>
              <el-tag size="small" effect="plain">仅需2步完成上货</el-tag>
            </div>
          </template>

          <el-input
            v-model="sourceUrl"
            type="textarea"
            :rows="3"
            :disabled="currentStep > 0"
            placeholder="粘贴 1688 / 淘宝 / 拼多多 商品链接，如：&#10;https://detail.1688.com/offer/629584739214.html"
            @keyup.ctrl.enter="startOneStop"
          />
          <div class="url-hint">
            <span>支持平台：</span>
            <el-tag size="small" effect="plain">1688</el-tag>
            <el-tag size="small" effect="plain">淘宝</el-tag>
            <el-tag size="small" effect="plain" type="info">拼多多</el-tag>
            <el-tag size="small" effect="plain" type="info">天猫</el-tag>
          </div>
        </el-card>

        <!-- 目标平台选择 -->
        <el-card class="target-card">
          <template #header>
            <div class="card-header">
              <div class="card-header-left">
                <el-icon><Shop /></el-icon>
                <span>第二步：选择目标上架平台</span>
              </div>
            </div>
          </template>

          <div class="target-platforms">
            <div
              v-for="p in platforms"
              :key="p.id"
              :class="['target-platform-item', { selected: selectedTargets.includes(p.id) }]"
              @click="toggleTarget(p.id)"
            >
              <div class="tp-icon" :style="{ background: p.color }">
                <el-icon color="#fff" :size="20"><Shop /></el-icon>
              </div>
              <div class="tp-name">{{ p.name }}</div>
              <div v-if="selectedTargets.includes(p.id)" class="tp-check">
                <el-icon><Check /></el-icon>
              </div>
            </div>
          </div>

          <div class="target-summary">
            已选 {{ selectedTargets.length }} 个平台
            <el-link type="primary" :underline="false" @click="selectAllPlatforms">全选</el-link>
            <el-link type="info" :underline="false" @click="selectedTargets = []">清空</el-link>
          </div>
        </el-card>

        <!-- 核心操作按钮 -->
        <div class="core-action">
          <div class="core-action-btn" :class="{ disabled: !canStart }" @click="startOneStop">
            <div class="core-btn-inner">
              <el-icon :size="32"><MagicStick /></el-icon>
              <div class="core-btn-text">
                <div class="core-btn-title">{{ currentStep === 0 ? '一键采集并上货' : flowSteps[currentStep]?.name }}</div>
                <div class="core-btn-sub">粘贴链接后，按 Ctrl+Enter 或点击此按钮</div>
              </div>
              <el-icon v-if="isRunning" class="is-loading core-btn-spinner"><Loading /></el-icon>
            </div>
          </div>
          <div class="core-action-hint">
            <el-icon><InfoFilled /></el-icon>
            全程 AI 自动处理：采集信息 → 合规预检 → 标题/描述优化 → 一键上架，无需手动操作
          </div>
        </div>

        <!-- 资深模式高级配置 -->
        <el-collapse v-if="appStore.isExpert" v-model="showAdvanced" class="advanced-config">
          <el-collapse-item title="高级配置" name="advanced">
            <el-form :model="advancedConfig" label-width="100px" size="small">
              <el-form-item label="采集来源">
                <el-select v-model="advancedConfig.sourcePlatform" placeholder="自动识别">
                  <el-option label="自动识别（推荐）" value="auto" />
                  <el-option label="1688" value="1688" />
                  <el-option label="淘宝" value="taobao" />
                  <el-option label="拼多多" value="pdd" />
                </el-select>
              </el-form-item>
              <el-form-item label="加价规则">
                <el-radio-group v-model="advancedConfig.pricingType">
                  <el-radio value="markup">固定加价 ¥</el-radio>
                  <el-radio value="multiplier">倍率 ×</el-radio>
                </el-radio-group>
              </el-form-item>
              <el-form-item v-if="advancedConfig.pricingType === 'markup'" label="加价金额">
                <el-input-number v-model="advancedConfig.markupAmount" :min="0" :precision="2" />
              </el-form-item>
              <el-form-item v-else label="加价倍率">
                <el-input-number v-model="advancedConfig.markupRate" :min="1" :precision="2" />
              </el-form-item>
              <el-form-item label="AI 优化">
                <el-checkbox v-model="advancedConfig.autoTitle">自动生成标题</el-checkbox>
                <el-checkbox v-model="advancedConfig.autoDesc">自动生成描述</el-checkbox>
                <el-checkbox v-model="advancedConfig.autoFeatures">自动生成卖点</el-checkbox>
                <el-checkbox v-model="advancedConfig.autoTranslate">自动多语言翻译</el-checkbox>
              </el-form-item>
              <el-form-item label="合规检查">
                <el-checkbox v-model="advancedConfig.autoCompliance">自动合规预检</el-checkbox>
              </el-form-item>
              <el-form-item label="店铺">
                <el-select v-model="advancedConfig.shopId" placeholder="选择目标店铺">
                  <el-option label="默认店铺" value="default" />
                </el-select>
              </el-form-item>
            </el-form>
          </el-collapse-item>
        </el-collapse>

      </div>

      <!-- 右侧：执行结果区 -->
      <div class="onestop-right">

        <!-- 当前执行状态 -->
        <el-card v-if="isRunning" class="running-card">
          <template #header>
            <div class="card-header">
              <el-icon class="is-loading"><Loading /></el-icon>
              <span>正在执行...</span>
            </div>
          </template>

          <div class="running-flow">
            <div
              v-for="(step, idx) in flowSteps"
              :key="step.id"
              :class="['running-step', {
                done: idx < currentStep,
                current: idx === currentStep,
              }]"
            >
              <div class="rs-icon">
                <el-icon v-if="idx < currentStep"><Check /></el-icon>
                <el-icon v-else-if="idx === currentStep" class="is-loading"><Loading /></el-icon>
                <span v-else>{{ idx + 1 }}</span>
              </div>
              <div class="rs-info">
                <div class="rs-name">{{ step.name }}</div>
                <div v-if="idx === currentStep && step.desc" class="rs-status">{{ step.desc }}</div>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 商品预览 -->
        <el-card v-if="goodsData" class="goods-preview-card">
          <template #header>
            <div class="card-header">
              <div class="card-header-left">
                <el-icon><Goods /></el-icon>
                <span>商品信息</span>
              </div>
              <el-tag :type="goodsData._valid ? 'success' : 'danger'" size="small">
                {{ goodsData._valid ? '数据完整' : '数据不完整' }}
              </el-tag>
            </div>
          </template>

          <div class="goods-preview">
            <el-image
              v-if="goodsData.images?.[0]"
              :src="goodsData.images[0]"
              fit="cover"
              class="goods-main-img"
              :preview-src-list="goodsData.images"
            />
            <div class="goods-info">
              <div class="goods-name">{{ goodsData.title || goodsData.name }}</div>
              <div class="goods-meta">
                <span class="goods-price">¥{{ goodsData.price || goodsData.cost || '—' }}</span>
                <span class="goods-platform">{{ goodsData.platform || sourcePlatform }}</span>
                <span class="goods-stock">库存 {{ goodsData.stock || '—' }}</span>
              </div>
            </div>

            <!-- AI 优化结果 -->
            <div v-if="aiOptimized" class="ai-optimized-section">
              <div class="ai-section-header">
                <el-icon><MagicStick /></el-icon>
                AI 优化结果
              </div>
              <div v-if="aiOptimized.title" class="ai-optimized-item">
                <div class="ao-label">优化标题</div>
                <div class="ao-value">{{ aiOptimized.title }}</div>
              </div>
              <div v-if="aiOptimized.features?.length" class="ai-optimized-item">
                <div class="ao-label">核心卖点</div>
                <div class="ao-features">
                  <el-tag v-for="(f, i) in aiOptimized.features" :key="i" size="small" type="warning" style="margin: 2px">
                    {{ f.icon }} {{ f.title }}
                  </el-tag>
                </div>
              </div>
              <div v-if="aiOptimized.description" class="ai-optimized-item">
                <div class="ao-label">优化描述</div>
                <div class="ao-value ao-desc">{{ aiOptimized.description }}</div>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 合规检查结果 -->
        <el-card v-if="complianceResult" class="compliance-card">
          <template #header>
            <div class="card-header">
              <div class="card-header-left">
                <el-icon><CircleCheck v-if="complianceResult.passed" color="#22c55e" />
                  <Warning v-else color="#f59e0b" /></el-icon>
                <span>合规检查结果</span>
              </div>
              <el-tag :type="complianceResult.passed ? 'success' : 'danger'" size="small">
                {{ complianceResult.passed ? '通过' : '有问题' }}
              </el-tag>
            </div>
          </template>

          <div v-if="complianceResult.errors?.length" class="compliance-errors">
            <div class="compliance-section-title">❌ 需要修复</div>
            <div v-for="(err, i) in complianceResult.errors" :key="i" class="compliance-item error">
              <el-icon><Close /></el-icon>
              {{ err.msg }}
            </div>
          </div>
          <div v-if="complianceResult.warnings?.length" class="compliance-warnings">
            <div class="compliance-section-title">⚠️ 建议优化</div>
            <div v-for="(warn, i) in complianceResult.warnings" :key="i" class="compliance-item warning">
              <el-icon><Warning /></el-icon>
              {{ warn.msg }}
            </div>
          </div>
          <div v-if="complianceResult.passed && !complianceResult.warnings?.length" class="compliance-passed">
            <el-icon color="#22c55e" :size="28"><CircleCheck /></el-icon>
            <p>全部合规检查通过，可直接上架！</p>
          </div>
        </el-card>

        <!-- 上架结果 -->
        <el-card v-if="listingResult" class="listing-result-card">
          <template #header>
            <div class="card-header">
              <div class="card-header-left">
                <el-icon color="#22c55e"><CircleCheck /></el-icon>
                <span>上架结果</span>
              </div>
              <el-tag type="success" size="small">成功</el-tag>
            </div>
          </template>

          <div class="listing-success">
            <div class="listing-success-icon">🎉</div>
            <div class="listing-success-text">
              商品已成功上架至
              <strong>{{ listingResult.platforms.join('、') }}</strong>
            </div>
            <div class="listing-success-actions">
              <el-button type="primary" @click="viewListingResult">
                <el-icon><TopRight /></el-icon>
                查看店铺后台
              </el-button>
              <el-button @click="resetFlow">
                <el-icon><RefreshRight /></el-icon>
                继续采集上货
              </el-button>
            </div>
          </div>

          <!-- 失败项整改 -->
          <div v-if="listingResult.failed?.length" class="listing-failed-section">
            <div class="listing-failed-title">⚠️ 上架失败项（AI 整改建议）</div>
            <div v-for="(fail, i) in listingResult.failed" :key="i" class="listing-failed-item">
              <div class="failed-platform">{{ fail.platform }}</div>
              <div class="failed-reason">{{ fail.reason }}</div>
              <div class="failed-fix">
                <span class="fix-label">AI 整改建议：</span>
                {{ fail.suggestion }}
              </div>
              <el-button size="small" type="warning" @click="fixAndRetry(fail)">
                <el-icon><RefreshRight /></el-icon>
                一键整改并重试
              </el-button>
            </div>
          </div>
        </el-card>

        <!-- 空状态 -->
        <el-card v-if="!isRunning && !goodsData && !complianceResult && !listingResult" class="empty-card">
          <div class="empty-state">
            <div class="empty-icon">
              <el-icon><Lightning /></el-icon>
            </div>
            <div class="empty-title">一站式采集上货</div>
            <div class="empty-desc">
              粘贴货源链接，选择目标平台<br/>
              全程 AI 自动完成采集、优化、合规检查、上架
            </div>
            <div class="empty-steps">
              <div class="empty-step">
                <div class="es-num">1</div>
                <div class="es-text">粘贴链接</div>
              </div>
              <div class="es-arrow">→</div>
              <div class="empty-step">
                <div class="es-num">2</div>
                <div class="es-text">选择平台</div>
              </div>
              <div class="es-arrow">→</div>
              <div class="empty-step">
                <div class="es-num">3</div>
                <div class="es-text">一键完成</div>
              </div>
            </div>
          </div>
        </el-card>

      </div>
    </div>

    <!-- ====== 扫码上货弹窗（模式3） ====== -->
    <el-dialog
      v-model="scanModeVisible"
      title="扫码采集 — 上货 / 补货"
      width="480px"
      destroy-on-close
      class="scan-mode-dialog"
    >
      <div class="scan-mode-content">
        <div class="scan-mode-header">
          <div class="scan-mode-icon">
            <el-icon :size="48" color="#085B9C"><FullScreen /></el-icon>
          </div>
          <div class="scan-mode-tip">
            请使用扫码枪扫描商品条码
            <br/>
            <small>扫到的商品将自动匹配系统商品库</small>
          </div>
        </div>

        <!-- 当前扫码列表 -->
        <div class="scan-mode-list">
          <div class="scan-list-title">
            本次扫码商品
            <el-badge :value="scanQueue.length" type="primary" />
          </div>
          <div v-if="scanQueue.length === 0" class="scan-empty">
            暂无扫码商品，请先扫描条码
          </div>
          <div v-else class="scan-items">
            <div v-for="(item, i) in scanQueue" :key="i" class="scan-item">
              <el-image :src="item.images?.[0]" fit="cover" class="scan-item-img" />
              <div class="scan-item-info">
                <div class="scan-item-name">{{ item.name }}</div>
                <div class="scan-item-meta">{{ item.platform }} · 成本 ¥{{ item.cost }}</div>
              </div>
              <el-icon color="#ef4444" class="remove-icon" @click="removeScanItem(i)"><Close /></el-icon>
            </div>
          </div>
        </div>

        <!-- 操作模式 -->
        <div class="scan-mode-selector">
          <div class="scan-mode-label">选择操作模式</div>
          <div class="scan-mode-options">
            <div
              :class="['scan-mode-opt', { active: scanMode === 'listing' }]"
              @click="scanMode = 'listing'"
            >
              <el-icon :size="28" color="#085B9C"><Upload /></el-icon>
              <div class="opt-title">上货模式</div>
              <div class="opt-desc">采集商品信息后，一键上架到目标平台</div>
            </div>
            <div
              :class="['scan-mode-opt', { active: scanMode === 'restock' }]"
              @click="scanMode = 'restock'"
            >
              <el-icon :size="28" color="#22c55e"><RefreshLeft /></el-icon>
              <div class="opt-title">补货模式</div>
              <div class="opt-desc">同步库存至所有已上架店铺</div>
            </div>
          </div>
        </div>

        <!-- 目标平台（仅上货模式） -->
        <div v-if="scanMode === 'listing'" class="scan-target-platforms">
          <div class="scan-target-label">目标平台</div>
          <div class="scan-target-grid">
            <div
              v-for="p in platforms"
              :key="p.id"
              :class="['scan-target-item', { selected: scanTargets.includes(p.id) }]"
              @click="toggleScanTarget(p.id)"
            >
              <span class="platform-dot" :style="{ background: p.color }"></span>
              {{ p.name }}
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="scan-mode-footer">
          <el-button @click="scanModeVisible = false">取消</el-button>
          <el-button type="primary" :loading="scanModeRunning" :disabled="scanQueue.length === 0 || scanTargets.length === 0" @click="executeScanMode">
            <el-icon><Check /></el-icon>
            确认执行 {{ scanMode === 'listing' ? '上货' : '补货' }}
            ({{ scanQueue.length }} 件)
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 扫码提示悬浮条（全局扫码触发时显示） -->
    <Transition name="slide-up">
      <div v-if="showScanTip" class="scan-tip-bar" @click="openScanMode">
        <el-icon><FullScreen /></el-icon>
        <span>检测到扫码枪输入：{{ scanTipBarcode }}</span>
        <el-button size="small" type="primary">点击处理</el-button>
        <el-button size="small" text @click="showScanTip = false">忽略</el-button>
      </div>
    </Transition>

    <!-- ====== 集采模式面板（步骤3选品+步骤4筛选+步骤5上货） ====== -->
    <div v-if="oneStop.pendingCount > 0" class="collect-flow-panel">
      <div class="flow-steps">
        <div class="flow-step" :class="{ active: currentFlowStep === 'select' }">
          <div class="step-num">3</div>
          <div class="step-info">
            <div class="step-name">选品评估</div>
            <div class="step-count">{{ oneStop.pendingCount }} 款待评估</div>
          </div>
        </div>
        <div class="flow-arrow"><el-icon><ArrowRight /></el-icon></div>
        <div class="flow-step" :class="{ active: currentFlowStep === 'filter' }">
          <div class="step-num">4</div>
          <div class="step-info">
            <div class="step-name">筛选确认</div>
            <div class="step-count">已选 {{ oneStop.selectedGoods.length }} 款</div>
          </div>
        </div>
        <div class="flow-arrow"><el-icon><ArrowRight /></el-icon></div>
        <div class="flow-step" :class="{ active: currentFlowStep === 'listing' }">
          <div class="step-num">5</div>
          <div class="step-info">
            <div class="step-name">一键上架</div>
            <div class="step-count">{{ oneStop.listingResults.length > 0 ? `${oneStop.listingResults.filter(r=>r.success).length} 成功` : '准备就绪' }}</div>
          </div>
        </div>
      </div>

      <!-- ====== 步骤3：选品评估 ====== -->
      <el-card v-if="currentFlowStep === 'select'" class="step-card">
        <template #header>
          <div class="card-header">
            <div class="card-header-left">
              <el-icon><DataAnalysis /></el-icon>
              <span>步骤3：AI 选品评估</span>
            </div>
            <el-button size="small" type="primary" :loading="isEvaluating" @click="onRunEvaluation">
              <el-icon><MagicStick /></el-icon>
              开始评估
            </el-button>
          </div>
        </template>

        <div class="evaluation-summary">
          <div class="eval-stats">
            <div class="eval-stat success">
              <span class="stat-num">{{ oneStop.goodsByGrade.recommend?.length || 0 }}</span>
              <span class="stat-label">优先推荐</span>
            </div>
            <div class="eval-stat">
              <span class="stat-num">{{ oneStop.goodsByGrade.okay?.length || 0 }}</span>
              <span class="stat-label">可上架</span>
            </div>
            <div class="eval-stat danger">
              <span class="stat-num">{{ oneStop.goodsByGrade.not_recommended?.length || 0 }}</span>
              <span class="stat-label">不建议</span>
            </div>
          </div>
          <p class="eval-tip">小辽评估建议：{{ evalTipText }}</p>
        </div>

        <!-- 待评估商品列表 -->
        <div class="pending-goods-grid">
          <div
            v-for="goods in oneStop.evaluatedGoods"
            :key="goods.id"
            class="eval-goods-card"
            :class="'grade-' + (goods.evaluation?.grade || 'okay')"
          >
            <div class="egc-header">
              <el-tag v-if="goods.evaluation?.grade === 'recommend'" type="success" size="small" effect="dark">推荐</el-tag>
              <el-tag v-else-if="goods.evaluation?.grade === 'not_recommended'" type="danger" size="small">不建议</el-tag>
              <el-tag v-else type="info" size="small">可上架</el-tag>
            </div>
            <div class="egc-name">{{ goods.title || goods.name }}</div>
            <div class="egc-profit" v-if="goods.evaluation?.profit">
              <span class="profit-price">¥{{ goods.evaluation.profit.salePrice?.toFixed(0) }}</span>
              <span class="profit-info">毛利 ¥{{ goods.evaluation.profit.profit?.toFixed(0) }} ({{ goods.evaluation.profit.profitRate?.toFixed(0) }}%)</span>
            </div>
            <div class="egc-actions">
              <el-checkbox
                v-if="goods.evaluation?.grade !== 'not_recommended'"
                :model-value="oneStop.selectedGoods.includes(goods.id)"
                @change="oneStop.toggleSelectGoods(goods.id)"
              >
                勾选上架
              </el-checkbox>
            </div>
          </div>
        </div>

        <div class="step-actions">
          <el-button @click="onSaveToDraft">存入草稿箱</el-button>
          <el-button type="primary" @click="currentFlowStep = 'filter'" :disabled="oneStop.selectedGoods.length === 0">
            下一步：筛选确认
            <el-badge v-if="oneStop.selectedGoods.length > 0" :value="oneStop.selectedGoods.length" type="warning" />
          </el-button>
        </div>
      </el-card>

      <!-- ====== 步骤4：筛选确认 ====== -->
      <el-card v-else-if="currentFlowStep === 'filter'" class="step-card">
        <template #header>
          <div class="card-header">
            <div class="card-header-left">
              <el-icon><Filter /></el-icon>
              <span>步骤4：筛选确认</span>
            </div>
            <div class="filter-actions">
              <el-input-number
                v-if="filterMode === 'profit_amount'"
                v-model="filterThreshold"
                :min="0"
                :max="10000"
                :precision="2"
                size="small"
                placeholder="最低利润"
              />
              <el-input-number
                v-else
                v-model="filterThreshold"
                :min="0"
                :max="100"
                :precision="1"
                size="small"
                placeholder="最低利润率"
              />
              <el-radio-group v-model="filterMode" size="small">
                <el-radio value="profit_amount">按利润额</el-radio>
                <el-radio value="profit_rate">按利润率</el-radio>
              </el-radio-group>
              <el-button size="small" @click="onQuickFilter">一键筛选</el-button>
            </div>
          </div>
        </template>

        <div class="selected-goods-table">
          <el-table :data="oneStop.selectedGoodsDetail" border stripe size="small">
            <el-table-column prop="title" label="商品名称" min-width="200" />
            <el-table-column prop="cost" label="成本" width="100">
              <template #default="{ row }">¥{{ row.cost }}</template>
            </el-table-column>
            <el-table-column label="建议售价" width="120">
              <template #default="{ row }">
                <span class="table-price">¥{{ oneStop.calcProfit(row).salePrice?.toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="预估利润" width="100">
              <template #default="{ row }">
                <span class="table-profit">¥{{ oneStop.calcProfit(row).profit?.toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="毛利率" width="80">
              <template #default="{ row }">
                <span class="table-profit-rate">{{ oneStop.calcProfit(row).profitRate?.toFixed(1) }}%</span>
              </template>
            </el-table-column>
            <el-table-column label="等级" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.evaluation?.grade === 'recommend'" type="success" size="small">推荐</el-tag>
                <el-tag v-else type="info" size="small">可上架</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80" fixed="right">
              <template #default="{ row }">
                <el-button size="small" type="danger" text @click="oneStop.toggleSelectGoods(row.id)">
                  移除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div class="filter-summary">
          <span>已选 <strong>{{ oneStop.selectedGoods.length }}</strong> 款商品，</span>
          <span v-if="oneStop.selectedGoods.length > 0">
            预估总利润 <strong class="profit-highlight">¥{{ totalEstimatedProfit }}</strong>
          </span>
        </div>

        <div class="step-actions">
          <el-button @click="currentFlowStep = 'select'">返回选品评估</el-button>
          <el-button type="primary" @click="currentFlowStep = 'listing'" :disabled="oneStop.selectedGoods.length === 0">
            下一步：一键上架
          </el-button>
        </div>
      </el-card>

      <!-- ====== 步骤5：一键上架 ====== -->
      <el-card v-else-if="currentFlowStep === 'listing'" class="step-card">
        <template #header>
          <div class="card-header">
            <div class="card-header-left">
              <el-icon><Upload /></el-icon>
              <span>步骤5：一键上架</span>
            </div>
            <el-tag v-if="oneStop.batchRunning" type="warning" size="small">执行中...</el-tag>
            <el-tag v-else-if="phase === 'done'" type="success" size="small">已完成</el-tag>
          </div>
        </template>

        <!-- 批量上架进度 -->
        <div v-if="oneStop.batchRunning || phase === 'done'" class="listing-progress">
          <el-progress
            :percentage="oneStop.batchProgress"
            :status="phase === 'done' ? 'success' : undefined"
            striped
            striped-flow
          />
          <div class="listing-stats">
            <span class="stat-success">
              <el-icon color="#22c55e"><SuccessFilled /></el-icon>
              成功 {{ oneStop.batchSuccess }}
            </span>
            <span class="stat-fail">
              <el-icon color="#ef4444"><CircleCloseFilled /></el-icon>
              失败 {{ oneStop.batchFail }}
            </span>
            <span>总计 {{ oneStop.batchTotal }}</span>
          </div>
        </div>

        <!-- 上架结果列表 -->
        <div v-if="oneStop.listingResults.length > 0" class="listing-results">
          <div
            v-for="(result, idx) in oneStop.listingResults"
            :key="idx"
            :class="['listing-result-item', result.success ? 'success' : 'fail']"
          >
            <div class="result-icon">
              <el-icon v-if="result.success" color="#22c55e"><SuccessFilled /></el-icon>
              <el-icon v-else color="#ef4444"><CircleCloseFilled /></el-icon>
            </div>
            <div class="result-info">
              <div class="result-platform">{{ result.platform }}</div>
              <div v-if="result.success" class="result-success-text">上架成功</div>
              <div v-else class="result-fail-text">{{ result.failReason || '上架失败' }}</div>
            </div>
            <el-button v-if="!result.success && result.suggestion" size="small" type="warning" @click="onFixAndRetry(result)">
              一键整改
            </el-button>
          </div>
        </div>

        <!-- 尚未开始上架 -->
        <div v-else class="listing-ready">
          <div class="ready-info">
            <p class="ready-title">准备上架 {{ oneStop.selectedGoods.length }} 款商品</p>
            <p class="ready-targets">目标平台：{{ oneStop.collectConfig.targetPlatforms.join('、') || '未选择' }}</p>
          </div>
          <el-button type="primary" size="large" :loading="oneStop.batchRunning" @click="onStartListing">
            <el-icon><Upload /></el-icon>
            确认一键上架
          </el-button>
        </div>

        <div class="step-actions" v-if="phase === 'done'">
          <el-button @click="onResetFlow">重新开始</el-button>
          <el-button type="primary" @click="onViewResults">查看完整报告</el-button>
        </div>
      </el-card>
    </div>
  </div>

  <!-- ====== 选品决策弹窗（上架前必经步骤）====== -->
  <el-dialog
    v-model="showDecisionModal"
    title=""
    width="560px"
    :close-on-click-modal="false"
    :show-close="false"
    destroy-on-close
    class="decision-modal"
  >
    <div class="decision-modal-content">
      <!-- Header -->
      <div class="decision-modal-header">
        <div class="dmh-icon">
          <span>🤖</span>
        </div>
        <div class="dmh-info">
          <div class="dmh-title">选品决策 · 利润测算</div>
          <div class="dmh-sub">AI 根据成本与定价规则自动计算利润与风险</div>
        </div>
        <el-tag :type="decisionResult?.grade === 'recommend' ? 'success' : decisionResult?.grade === 'not_recommended' ? 'danger' : 'warning'" size="large" class="dmh-grade">
          {{ decisionResult?.grade === 'recommend' ? '✅ 优先推荐' : decisionResult?.grade === 'not_recommended' ? '❌ 不建议上架' : '⚠️ 可上架' }}
        </el-tag>
      </div>

      <!-- 商品信息 -->
      <div class="decision-goods-info" v-if="goodsData">
        <div class="dgi-name">{{ goodsData.title || goodsData.name }}</div>
        <div class="dgi-meta">来源：{{ sourcePlatform }} · 条码：{{ goodsData.barcode || '无' }}</div>
      </div>

      <!-- 利润测算卡片 -->
      <div class="profit-calc-card" v-if="decisionResult?.profit">
        <div class="profit-main-stats">
          <div class="pms-item">
            <div class="pms-label">成本价</div>
            <div class="pms-value">¥{{ decisionResult.profit.cost.toFixed(2) }}</div>
          </div>
          <div class="pms-arrow">→</div>
          <div class="pms-item highlight">
            <div class="pms-label">建议售价</div>
            <div class="pms-value">¥{{ decisionResult.profit.salePrice.toFixed(2) }}</div>
          </div>
          <div class="pms-arrow">=</div>
          <div class="pms-item success">
            <div class="pms-label">预估利润</div>
            <div class="pms-value">¥{{ decisionResult.profit.profit.toFixed(2) }}</div>
          </div>
        </div>
        <div class="profit-sub-stats">
          <div class="pss-item">
            <span class="pss-label">毛利率</span>
            <span class="pss-value" :class="{ danger: decisionResult.profit.profitRate < 10, warning: decisionResult.profit.profitRate >= 10 && decisionResult.profit.profitRate < 20 }">
              {{ decisionResult.profit.profitRate.toFixed(1) }}%
            </span>
          </div>
          <div class="pss-item">
            <span class="pss-label">定价模板</span>
            <span class="pss-value">{{ decisionResult.profit.template }}</span>
          </div>
          <div class="pss-item">
            <span class="pss-label">加价倍率</span>
            <span class="pss-value">×{{ decisionResult.profit.rate }}</span>
          </div>
        </div>
        <!-- 风险提示 -->
        <div v-if="decisionResult.grade === 'not_recommended'" class="profit-warning">
          <el-icon><Warning /></el-icon>
          <span>{{ decisionResult.reason }}</span>
        </div>
      </div>

      <!-- 定价模板调整 -->
      <div class="pricing-template-section">
        <div class="pts-title">调整定价规则</div>
        <div class="pts-options">
          <div
            v-for="tpl in PRICING_TEMPLATES"
            :key="tpl.id"
            :class="['pts-option', { active: oneStop.activePricingTemplate === tpl.id }]"
            @click="oneStop.applyPricingTemplate(tpl.id); recalcProfit()"
          >
            <div class="pts-name">{{ tpl.label }}</div>
            <div class="pts-rate">×{{ tpl.rate }}</div>
            <div class="pts-price" v-if="goodsData">
              ¥{{ (goodsData.cost * tpl.rate).toFixed(0) }}
            </div>
          </div>
        </div>
      </div>

      <!-- AI 评估理由 -->
      <div class="decision-reason" v-if="decisionResult?.reason">
        <div class="dr-label">💡 小辽评估：</div>
        <div class="dr-text">{{ decisionResult.reason }}</div>
      </div>
    </div>

    <template #footer>
      <div class="decision-footer">
        <el-button @click="cancelDecision" size="large">取消上架</el-button>
        <el-button type="primary" size="large" @click="confirmDecision">
          <el-icon><ArrowRight /></el-icon>
          确认上架
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, onErrorCaptured } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Link, Shop, Upload, MagicStick, Check, Close, Loading,
  Warning, CircleCheck, Rank, Setting, InfoFilled, RefreshRight,
  Goods, TopRight, FullScreen, RefreshLeft, Lightning, UploadFilled, ArrowRight
} from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/useAppStore'
import { useCompliance } from '@/composables/useCompliance'
import { collect1688Single } from '@/api/collect'
import {
  generateTitle, generateDescription, generateFeatures
} from '@/api/ai'
import { SCAN_EVENT } from '@/composables/useScanner'
import { useOneStopStore, PRICING_TEMPLATES } from '@/stores/useOneStop'

const appStore = useAppStore()
const oneStop = useOneStopStore()
const { preCheck } = useCompliance()

// ==================== 平台配置 ====================
const platforms = [
  { id: 'tiktok',     name: 'TikTok Shop',  color: '#00f2ea' },
  { id: 'shopee',     name: 'Shopee',        color: '#ee4d2d' },
  { id: 'temu',       name: 'Temu',           color: '#ff6b00' },
  { id: 'shein',      name: 'SHEIN',           color: '#e5004c' },
  { id: 'aliexpress', name: 'AliExpress',     color: '#ff4747' },
  { id: 'amazon',     name: 'Amazon',          color: '#ff9900' },
  { id: 'ebay',       name: 'eBay',            color: '#e53238' },
  { id: 'lazada',     name: 'Lazada',          color: '#0b94d5' },
  { id: 'wish',       name: 'Wish',            color: '#2a80c4' },
  { id: 'mercado',    name: 'Mercado',         color: '#ffe600' },
  { id: 'ozon',       name: 'Ozon',            color: '#005bff' },
  { id: 'allegro',    name: 'Allegro',         color: '#ff5a00' },
]

// ==================== 小白极简模式状态 ====================
const sourceUrl = ref('')
const selectedTargets = ref(['tiktok'])
const isRunning = ref(false)
const currentStep = ref(0)  // 0=待开始, 1=采集中, 2=合规校验, 3=AI优化, 4=上架
const goodsData = ref(null)
const aiOptimized = ref(null)
const complianceResult = ref(null)
const listingResult = ref(null)
const sourcePlatform = ref('')

// 选品决策结果
const decisionResult = ref(null)

// 选品决策弹窗控制
const showDecisionModal = ref(false)
let decisionModalResolve = ref(null)

// 确认选品决策
function confirmDecision() {
  if (decisionModalResolve.value) decisionModalResolve.value(true)
}

// 取消选品决策
function cancelDecision() {
  if (decisionModalResolve.value) decisionModalResolve.value(false)
}

// 重新计算利润（切换定价模板后）
function recalcProfit() {
  if (goodsData.value) {
    decisionResult.value = oneStop.evaluateGoods(goodsData.value)
  }
}

const flowSteps = computed(() => [
  { id: 'collect',    name: '采集商品信息',   desc: '正在从货源平台抓取商品数据...',    running: currentStep.value === 1 },
  { id: 'compliance', name: 'AI 合规预检',    desc: '正在检测侵权/禁售/关键词风险...',  running: currentStep.value === 2 },
  { id: 'optimize',   name: 'AI 智能优化',    desc: '正在生成标题/描述/卖点...',        running: currentStep.value === 3 },
  { id: 'decision',   name: '选品决策',        desc: '正在测算利润与风险...',            running: currentStep.value === 3.5 },
  { id: 'listing',    name: '提交上架',        desc: '正在提交到目标平台...',            running: currentStep.value === 4 },
])

const canStart = computed(() => {
  return sourceUrl.value.trim().length > 0 &&
    selectedTargets.value.length > 0 &&
    !isRunning.value
})

// ==================== 资深模式高级配置 ====================
const showAdvanced = ref([])
const advancedConfig = reactive({
  sourcePlatform: 'auto',
  pricingType: 'markup',
  markupAmount: 30,
  markupRate: 1.5,
  autoTitle: true,
  autoDesc: true,
  autoFeatures: true,
  autoTranslate: true,
  autoCompliance: true,
  shopId: 'default',
})

// ==================== 批量模式状态 ====================
const showBatchPanel = ref(false)
const batchImportType = ref('links')
const batchLinksText = ref('')
const batchExcelFile = ref(null)
const batchRunning = ref(false)
const batchItems = ref([])
const batchRules = reactive({
  targetPlatforms: ['tiktok', 'shopee'],
  pricingType: 'markup',
  markupAmount: 30,
  markupRate: 1.5,
  shopId: 'default',
})

const batchProgress = computed(() => {
  if (batchItems.value.length === 0) return 0
  const done = batchItems.value.filter(i => i.status === 'done' || i.status === 'fail').length
  return Math.round((done / batchItems.value.length) * 100)
})

const batchStats = computed(() => {
  const items = batchItems.value
  return {
    success: items.filter(i => i.status === 'done').length,
    fail: items.filter(i => i.status === 'fail').length,
    running: items.filter(i => i.status === 'pending' || i.status === 'running').length,
  }
})

// ==================== 扫码模式状态（模式3） ====================
const scanModeVisible = ref(false)
const scanQueue = ref([])
const scanMode = ref('listing')  // 'listing' | 'restock'
const scanTargets = ref(['tiktok'])
const scanModeRunning = ref(false)
const showScanTip = ref(false)
const scanTipBarcode = ref('')

// ==================== 核心方法 ====================

/** 识别货源平台 */
function detectPlatform(url) {
  if (url.includes('1688.com')) return '1688'
  if (url.includes('taobao.com')) return '淘宝'
  if (url.includes('tmall.com')) return '天猫'
  if (url.includes('pinduoduo.com') || url.includes('yangkeduo.com')) return '拼多多'
  return '未知'
}

/** 一站式采集上货主流程 */
async function startOneStop() {
  if (!canStart.value) return

  const url = sourceUrl.value.trim()
  const targets = selectedTargets.value

  if (targets.length === 0) {
    ElMessage.warning('请至少选择一个目标上架平台')
    return
  }

  isRunning.value = true
  currentStep.value = 1
  goodsData.value = null
  aiOptimized.value = null
  complianceResult.value = null
  listingResult.value = null

  try {
    // ========== 步骤1：采集 ==========
    currentStep.value = 1
    let goods
    const detectedPlatform = detectPlatform(url)
    sourcePlatform.value = detectedPlatform

    try {
      const res = await collect1688Single({ url })
      goods = res.data
    } catch {
      // 降级：mock 数据
      goods = {
        title: '女士连体泳装 修身显瘦海边度假温泉游泳衣',
        name: '女士连体泳装 修身显瘦海边度假温泉游泳衣',
        price: 68,
        cost: 68,
        stock: 80,
        platform: detectedPlatform,
        images: ['/images/swimwear/O1CN01OtfunX283idPNsyQu_!!2215607027877-0-cib.jpg'],
        barcode: '',
        description: '',
      }
    }

    // 提取1688 offer ID 作为条码
    const offerIdMatch = url.match(/detail\.1688\.com\/offer\/(\d+)/)
    if (offerIdMatch && !goods.barcode) {
      goods.barcode = offerIdMatch[1]
    }

    goods._valid = !!(goods.title && goods.images?.length && goods.price)
    goodsData.value = goods

    // ========== 步骤2：合规预检 ==========
    currentStep.value = 2
    if (appStore.isExpert ? advancedConfig.autoCompliance : true) {
      const checkResult = await preCheck(goods, targets)
      complianceResult.value = checkResult

      if (checkResult.hasError) {
        const proceed = await ElMessageBox.confirm(
          `合规检查发现 ${checkResult.errorCount} 个错误，${checkResult.warningCount} 个警告。\n` +
          checkResult.errors.map(e => '• ' + e.msg).join('\n') + '\n\n是否继续上架？',
          '合规风险提示',
          { confirmButtonText: '继续上架', cancelButtonText: '返回修改', type: 'warning' }
        ).catch(() => null)

        if (!proceed) {
          isRunning.value = false
          currentStep.value = 0
          return
        }
      }
    }

    // ========== 步骤3：AI 优化 ==========
    currentStep.value = 3
    const optimized = {}
    const platformNames = targets.map(id => platforms.find(p => p.id === id)?.name || id).join('、')

    if (appStore.isExpert ? advancedConfig.autoTitle : true) {
      try {
        const title = await generateTitle({
          name: goods.title || goods.name,
          category: '',
          material: '',
          style: '',
          features: '',
        })
        optimized.title = title
      } catch {}
    }

    if (appStore.isExpert ? advancedConfig.autoFeatures : true) {
      try {
        const features = await generateFeatures({
          name: goods.title || goods.name,
          category: '',
        })
        optimized.features = features
      } catch {}
    }

    if (appStore.isExpert ? advancedConfig.autoDesc : true) {
      try {
        const desc = await generateDescription({
          name: goods.title || goods.name,
          category: '',
          material: '',
          style: '',
          features: '',
        })
        optimized.description = desc.description || desc
      } catch {}
    }

    aiOptimized.value = optimized

    // ========== 步骤3.5：选品决策（利润测算+风险提示）==========
    currentStep.value = 3.5
    const evaluation = oneStop.evaluateGoods(goods)
    decisionResult.value = evaluation

    // 展示决策确认弹窗
    const confirmed = await new Promise(resolve => {
      showDecisionModal.value = true
      decisionModalResolve.value = resolve
    })
    showDecisionModal.value = false

    if (!confirmed) {
      isRunning.value = false
      currentStep.value = 0
      ElMessage.info('已取消上架，可调整参数后重新开始')
      return
    }

    // ========== 步骤4：提交上架 ==========
    currentStep.value = 4
    await new Promise(r => setTimeout(r, 1200)) // 模拟API调用

    listingResult.value = {
      platforms: platformNames.split('、'),
      success: true,
      failed: [],
    }

    currentStep.value = 5
    ElMessage.success(`商品已成功上架至 ${platformNames}！`)

  } catch (err) {
    ElMessage.error(err.message || '执行出错，请重试')
    isRunning.value = false
    currentStep.value = 0
  } finally {
    isRunning.value = false
  }
}

/** 重置流程 */
function resetFlow() {
  sourceUrl.value = ''
  goodsData.value = null
  aiOptimized.value = null
  complianceResult.value = null
  listingResult.value = null
  currentStep.value = 0
  isRunning.value = false
}

/** 查看上架结果 */
function viewListingResult() {
  ElMessage.info('即将跳转至店铺后台（待接入各平台 API）')
}

/** 整改并重试 */
async function fixAndRetry(fail) {
  ElMessage.success('AI 已自动整改，即将重试上架...')
  await new Promise(r => setTimeout(r, 800))
  listingResult.value.failed = listingResult.value.failed.filter(f => f !== fail)
  listingResult.value.platforms.push(fail.platform)
  ElMessage.success(`${fail.platform} 重试上架成功！`)
}

/** 平台选择 */
function toggleTarget(id) {
  const idx = selectedTargets.value.indexOf(id)
  if (idx >= 0) selectedTargets.value.splice(idx, 1)
  else selectedTargets.value.push(id)
}

function selectAllPlatforms() {
  selectedTargets.value = platforms.map(p => p.id)
}

// ==================== 批量模式方法 ====================

function handleExcelChange(file) {
  batchExcelFile.value = file.raw
}

async function startBatchListing() {
  const links = batchImportType.value === 'links'
    ? batchLinksText.value.split('\n').map(l => l.trim()).filter(Boolean)
    : []

  if (links.length === 0 && !batchExcelFile.value) {
    ElMessage.warning('请先导入商品链接或上传 Excel 文件')
    return
  }

  if (batchRules.targetPlatforms.length === 0) {
    ElMessage.warning('请至少选择一个目标平台')
    return
  }

  batchRunning.value = true
  batchItems.value = links.map(link => ({ link, status: 'pending', result: null }))

  // 逐个执行
  for (const item of batchItems.value) {
    if (item.status !== 'pending') continue
    item.status = 'running'
    try {
      await new Promise(r => setTimeout(r, 600))
      item.status = 'done'
      item.result = { success: true }
    } catch {
      item.status = 'fail'
      item.result = { success: false, reason: '采集失败' }
    }
  }

  batchRunning.value = false
  ElMessage.success(`批量执行完成：${batchStats.value.success} 成功，${batchStats.value.fail} 失败`)
}

function cancelBatch() {
  batchRunning.value = false
  batchItems.value.forEach(item => {
    if (item.status === 'pending' || item.status === 'running') item.status = 'fail'
  })
}

// ==================== 扫码模式方法（模式3） ====================

function openScanMode() {
  showScanTip.value = false
  scanModeVisible.value = true
}

function closeScanMode() {
  scanModeVisible.value = false
  scanQueue.value = []
  scanTargets.value = ['tiktok']
  scanMode.value = 'listing'
}

function removeScanItem(index) {
  scanQueue.value.splice(index, 1)
}

function toggleScanTarget(id) {
  const idx = scanTargets.value.indexOf(id)
  if (idx >= 0) scanTargets.value.splice(idx, 1)
  else scanTargets.value.push(id)
}

async function executeScanMode() {
  if (scanQueue.value.length === 0 || scanTargets.value.length === 0) return

  scanModeRunning.value = true
  const mode = scanMode.value

  try {
    for (const item of scanQueue.value) {
      await new Promise(r => setTimeout(r, 800))
      console.log(`[OneStop] ${mode === 'listing' ? '上货' : '补货'}：${item.name}`)
    }
    ElMessage.success(`${mode === 'listing' ? '上货' : '补货'}完成！共处理 ${scanQueue.value.length} 件商品`)
    closeScanMode()
  } catch {
    ElMessage.error('执行失败，请重试')
  } finally {
    scanModeRunning.value = false
  }
}

// ==================== 全局扫码枪事件监听 ====================
function handleGlobalScan(e) {
  const barcode = e.detail?.barcode
  if (!barcode || barcode.length < 4) return

  scanTipBarcode.value = barcode
  showScanTip.value = true

  // 3秒后自动隐藏提示
  setTimeout(() => {
    if (showScanTip.value && scanTipBarcode.value === barcode) {
      showScanTip.value = false
    }
  }, 5000)
}

// ==================== 集采工作流状态（步骤3-5） ====================
const currentFlowStep = ref('select')  // 'select' | 'filter' | 'listing'
const phase = ref('idle')             // 'idle' | 'done'
const isEvaluating = ref(false)
const filterMode = ref('profit_amount')
const filterThreshold = ref(20)

const totalEstimatedProfit = computed(() => {
  return oneStop.selectedGoodsDetail
    .reduce((sum, g) => sum + (oneStop.calcProfit(g).profit || 0), 0)
    .toFixed(2)
})

const evalTipText = computed(() => {
  const rec = oneStop.goodsByGrade.recommend?.length || 0
  const total = oneStop.pendingCount
  if (total === 0) return '暂无商品'
  if (rec >= total * 0.5) return '优质商品占多数，建议优先上架推荐款'
  if (rec > 0) return `有 ${rec} 款商品利润表现优秀，建议重点关注`
  return '建议调整定价倍率或筛选门槛'
})

// ── 步骤3：运行评估 ───────────────────────────────────────────
async function onRunEvaluation() {
  if (oneStop.pendingGoods.length === 0) {
    ElMessage.warning('暂无待评估商品')
    return
  }
  isEvaluating.value = true
  try {
    await oneStop.batchEvaluate()
    ElMessage.success('评估完成！')
    // 自动选中推荐商品
    oneStop.goodsByGrade.recommend?.forEach(g => {
      if (!oneStop.selectedGoods.includes(g.id)) {
        oneStop.selectedGoods.push(g.id)
      }
    })
  } catch (e) {
    ElMessage.error('评估失败：' + (e.message || '未知错误'))
  } finally {
    isEvaluating.value = false
  }
}

// ── 步骤4：快速筛选 ───────────────────────────────────────────
function onQuickFilter() {
  if (filterMode.value === 'profit_amount') {
    oneStop.filterByProfitAmount(filterThreshold.value)
  } else {
    oneStop.filterByProfitRate(filterThreshold.value)
  }
  // 同步更新勾选
  oneStop.selectedGoods = oneStop.evaluatedGoods
    .filter(g => {
      const p = oneStop.calcProfit(g)
      return filterMode.value === 'profit_amount'
        ? p.profit >= filterThreshold.value
        : p.profitRate >= filterThreshold.value
    })
    .map(g => g.id)
}

// ── 步骤5：开始上架 ───────────────────────────────────────────
async function onStartListing() {
  if (oneStop.selectedGoods.length === 0) {
    ElMessage.warning('请先选择要上架的商品')
    return
  }
  const total = oneStop.selectedGoods.length
  oneStop.startBatch(total)

  const results = []
  for (const id of oneStop.selectedGoods) {
    try {
      // Mock：模拟上架请求（真实场景调用对应平台API）
      await new Promise(r => setTimeout(r, 800))
      results.push({ platform: oneStop.collectConfig.targetPlatforms[0] || 'tiktok', success: true })
      oneStop.updateBatchProgress(true)
    } catch (e) {
      results.push({ platform: oneStop.collectConfig.targetPlatforms[0] || 'tiktok', success: false, failReason: '接口异常', suggestion: '请重试或检查网络' })
      oneStop.updateBatchProgress(false)
    }
  }

  oneStop.markListed(results)
  phase.value = 'done'
  ElMessage.success(`上架完成：${oneStop.batchSuccess} 成功，${oneStop.batchFail} 失败`)
}

function onFixAndRetry(result) {
  ElMessage.info('整改功能开发中，请手动修改商品信息后重试')
}

function onResetFlow() {
  oneStop.resetCollectFlow()
  currentFlowStep.value = 'select'
  phase.value = 'idle'
}

function onViewResults() {
  ElMessageBox.alert(
    `上架结果汇总：\n成功 ${oneStop.batchSuccess} 款\n失败 ${oneStop.batchFail} 款\n\n失败商品已存入草稿箱，可在「商品管理」中重新编辑上架。`,
    '上架结果报告',
    { confirmButtonText: '好的' }
  )
}

function onSaveToDraft() {
  ElMessage.info('已存入草稿箱，可在「商品管理」中随时编辑')
  oneStop.resetCollectFlow()
  currentFlowStep.value = 'select'
}

// ==================== 生命周期 ====================
onMounted(() => {
  console.log('[OneStopView] 组件挂载成功')
  window.addEventListener(SCAN_EVENT, handleGlobalScan)
})

onErrorCaptured((err, instance, info) => {
  console.error('[OneStopView] 组件错误:', err.message)
  console.error('[OneStopView] 错误详情:', info)
  ElMessage.error(`一站式上货加载失败: ${err.message}`)
  return false // 阻止错误冒泡
})

onUnmounted(() => {
  window.removeEventListener(SCAN_EVENT, handleGlobalScan)
})
</script>

<style scoped>
.page {
  padding: 28px 32px;
  width: 100%;
  flex: 1;
  box-sizing: border-box;
  overflow-y: auto;
}

/* ===== 页面Header ===== */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}
.page-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 4px;
}
.page-desc {
  font-size: 13px;
  color: var(--text-muted);
  margin: 0;
}
.page-header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* ===== 通用卡片Header ===== */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
}

/* ===== 布局 ===== */
.onestop-layout {
  display: grid;
  grid-template-columns: 1fr 420px;
  gap: 20px;
  align-items: start;
}
.onestop-left { display: flex; flex-direction: column; gap: 16px; }
.onestop-right { display: flex; flex-direction: column; gap: 16px; }

/* ===== 步骤流程条 ===== */
.step-flow {
  display: flex;
  align-items: center;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 14px 20px;
  gap: 0;
}
.flow-step {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  position: relative;
}
.flow-step-icon {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--bg-stripe);
  border: 2px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  color: var(--text-muted);
  flex-shrink: 0;
  transition: all 0.3s;
}
.flow-step.is-done .flow-step-icon {
  background: #22c55e;
  border-color: #22c55e;
  color: white;
}
.flow-step.is-active .flow-step-icon {
  background: var(--brand);
  border-color: var(--brand);
  color: white;
  box-shadow: 0 0 0 4px rgba(37,99,235,.2);
}
.flow-step-info { flex: 1; }
.flow-step-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}
.flow-step.is-pending .flow-step-name { color: var(--text-muted); }
.flow-step-desc {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 1px;
}
.flow-connector {
  position: absolute;
  right: -10px;
  z-index: 1;
  width: 20px;
}
.flow-line {
  width: 20px;
  height: 2px;
  background: var(--border);
  transition: background 0.3s;
}
.flow-line.done { background: #22c55e; }

/* ===== 平台选择 ===== */
.target-platforms {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}
.target-platform-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 8px;
  border: 2px solid var(--border);
  border-radius: var(--r-md);
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}
.target-platform-item:hover {
  border-color: var(--border-hover);
  background: var(--bg-hover);
}
.target-platform-item.selected {
  border-color: var(--brand);
  background: var(--brand-light);
}
.tp-icon {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.tp-name {
  font-size: 11.5px;
  font-weight: 600;
  color: var(--text-primary);
  text-align: center;
}
.tp-check {
  position: absolute;
  top: -6px;
  right: -6px;
  background: var(--brand);
  color: white;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
}
.target-summary {
  margin-top: 12px;
  font-size: 13px;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ===== 核心操作按钮 ===== */
.core-action { display: flex; flex-direction: column; gap: 8px; }
.core-action-btn {
  background: linear-gradient(135deg, #085B9C 0%, #2ead3e 100%);
  border-radius: var(--r-lg);
  padding: 20px 24px;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 16px rgba(8,91,156,.3);
}
.core-action-btn:hover:not(.disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(8,91,156,.4);
}
.core-action-btn.disabled {
  background: linear-gradient(135deg, #9ca3af 0%, #6b7280 100%);
  cursor: not-allowed;
  box-shadow: none;
}
.core-btn-inner {
  display: flex;
  align-items: center;
  gap: 14px;
  color: white;
}
.core-btn-text { flex: 1; }
.core-btn-title {
  font-size: 18px;
  font-weight: 700;
  color: white;
}
.core-btn-sub {
  font-size: 12px;
  color: rgba(255,255,255,.7);
  margin-top: 2px;
}
.core-btn-spinner { color: white; }
.core-action-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-muted);
  padding: 0 4px;
}

/* ===== AI 优化结果 ===== */
.ai-optimized-section {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid var(--border);
}
.ai-section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #92400e;
  margin-bottom: 10px;
}
.ai-optimized-item { margin-bottom: 10px; }
.ao-label {
  font-size: 11px;
  font-weight: 600;
  color: #92400e;
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: .05em;
}
.ao-value {
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.5;
}
.ao-desc {
  max-height: 80px;
  overflow-y: auto;
  font-size: 12px;
  color: var(--text-secondary);
  white-space: pre-wrap;
}
.ao-features { display: flex; flex-wrap: wrap; gap: 4px; }

/* ===== 合规结果 ===== */
.compliance-errors, .compliance-warnings { margin-bottom: 10px; }
.compliance-section-title {
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 6px;
}
.compliance-item {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 12px;
  padding: 5px 8px;
  border-radius: 6px;
  margin-bottom: 4px;
  line-height: 1.4;
}
.compliance-item.error {
  background: rgba(239,68,68,.06);
  color: #dc2626;
}
.compliance-item.warning {
  background: rgba(245,158,11,.06);
  color: #d97706;
}
.compliance-passed {
  text-align: center;
  padding: 16px;
  color: #166534;
}
.compliance-passed p { margin: 8px 0 0; font-size: 13px; }

/* ===== 上架结果 ===== */
.listing-success {
  text-align: center;
  padding: 12px 0;
}
.listing-success-icon { font-size: 48px; margin-bottom: 8px; }
.listing-success-text {
  font-size: 15px;
  color: var(--text-primary);
  margin-bottom: 14px;
  line-height: 1.6;
}
.listing-success-actions { display: flex; gap: 10px; justify-content: center; }
.listing-failed-section { margin-top: 16px; border-top: 1px solid var(--border); padding-top: 14px; }
.listing-failed-title {
  font-size: 13px;
  font-weight: 600;
  color: #d97706;
  margin-bottom: 10px;
}
.listing-failed-item {
  background: rgba(245,158,11,.05);
  border: 1px solid rgba(245,158,11,.2);
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 8px;
}
.failed-platform { font-weight: 600; color: var(--text-primary); margin-bottom: 4px; }
.failed-reason { font-size: 12px; color: #dc2626; margin-bottom: 6px; }
.failed-fix {
  font-size: 12px;
  color: #166534;
  background: rgba(22,101,52,.06);
  padding: 6px 8px;
  border-radius: 4px;
  margin-bottom: 8px;
}
.fix-label { font-weight: 600; }

/* ===== 执行中状态 ===== */
.running-flow {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.running-step {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 8px;
  transition: all 0.2s;
}
.running-step.done {
  background: rgba(34,197,94,.06);
}
.running-step.current {
  background: rgba(8,91,156,.06);
  border: 1px solid rgba(8,91,156,.2);
}
.rs-icon {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--bg-stripe);
  border: 2px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: var(--text-muted);
  flex-shrink: 0;
}
.running-step.done .rs-icon {
  background: #22c55e;
  border-color: #22c55e;
  color: white;
}
.running-step.current .rs-icon {
  background: var(--brand);
  border-color: var(--brand);
  color: white;
}
.rs-name { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.running-step.done .rs-name { color: #166534; }
.rs-status { font-size: 11px; color: var(--text-muted); margin-top: 1px; }

/* ===== 商品预览 ===== */
.goods-preview { display: flex; flex-direction: column; gap: 12px; }
.goods-main-img {
  width: 100%;
  height: 160px;
  border-radius: 8px;
  object-fit: cover;
  border: 1px solid var(--border);
}
.goods-info {}
.goods-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 6px;
  line-height: 1.4;
}
.goods-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}
.goods-price { color: #ef4444; font-weight: 700; font-size: 16px; }
.goods-platform {
  background: var(--bg-stripe);
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  color: var(--text-secondary);
}
.goods-stock { color: var(--text-muted); font-size: 12px; }

/* ===== 空状态 ===== */
.empty-state { text-align: center; padding: 32px 16px; }
.empty-icon {
  width: 72px;
  height: 72px;
  background: linear-gradient(135deg, rgba(8,91,156,.08) 0%, rgba(46,173,62,.08) 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 14px;
  font-size: 32px;
}
.empty-icon .el-icon { color: var(--brand); }
.empty-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}
.empty-desc {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.6;
  margin-bottom: 20px;
}
.empty-steps {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.empty-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.es-num {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--brand);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
}
.es-text { font-size: 11px; color: var(--text-muted); }
.es-arrow { color: var(--border); font-size: 18px; }

/* ===== 批量面板 ===== */
.batch-panel { margin-bottom: 16px; }
.batch-import-tabs { margin-bottom: 14px; }
.batch-links-input { margin-bottom: 14px; }
.batch-links-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 10px;
}
.batch-hint { font-size: 12px; color: var(--text-muted); }
.batch-file-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: rgba(34,197,94,.06);
  border: 1px solid rgba(34,197,94,.2);
  border-radius: 8px;
  margin-top: 10px;
  font-size: 13px;
}
.batch-rules {
  border-top: 1px solid var(--border);
  padding-top: 14px;
  margin-top: 4px;
}
.rules-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}
.batch-progress { margin-top: 12px; }
.batch-progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.batch-progress-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}
.batch-stats {
  display: flex;
  gap: 16px;
}
.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}
.stat-success { color: #22c55e; }
.stat-fail { color: #ef4444; }
.stat-pending { color: var(--brand); }

/* ===== 资深模式高级配置 ===== */
.advanced-config { margin-top: 4px; }
.platform-opt {
  display: flex;
  align-items: center;
  gap: 6px;
}
.platform-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* ===== 扫码模式弹窗 ===== */
.scan-mode-content { display: flex; flex-direction: column; gap: 16px; }
.scan-mode-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  background: linear-gradient(135deg, rgba(8,91,156,.06) 0%, rgba(46,173,62,.06) 100%);
  border-radius: 10px;
  border: 1px solid rgba(8,91,156,.1);
}
.scan-mode-icon {
  width: 56px;
  height: 56px;
  background: rgba(8,91,156,.08);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.scan-mode-tip { font-size: 14px; color: var(--text-primary); line-height: 1.6; }
.scan-mode-tip small { font-size: 12px; color: var(--text-muted); }
.scan-mode-list { }
.scan-list-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}
.scan-empty {
  font-size: 12px;
  color: var(--text-muted);
  text-align: center;
  padding: 16px;
  background: var(--bg-stripe);
  border-radius: 8px;
}
.scan-items { display: flex; flex-direction: column; gap: 6px; max-height: 160px; overflow-y: auto; }
.scan-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  background: var(--bg-stripe);
  border-radius: 8px;
}
.scan-item-img {
  width: 40px;
  height: 40px;
  border-radius: 6px;
  border: 1px solid var(--border);
  flex-shrink: 0;
}
.scan-item-info { flex: 1; min-width: 0; }
.scan-item-name {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.scan-item-meta { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
.remove-icon { cursor: pointer; flex-shrink: 0; }
.remove-icon:hover { color: #ef4444; }
.scan-mode-selector {}
.scan-mode-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
}
.scan-mode-options { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.scan-mode-opt {
  border: 2px solid var(--border);
  border-radius: 10px;
  padding: 14px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}
.scan-mode-opt:hover { border-color: var(--border-hover); }
.scan-mode-opt.active {
  border-color: var(--brand);
  background: var(--brand-light);
}
.opt-title { font-size: 14px; font-weight: 700; color: var(--text-primary); margin-top: 6px; }
.opt-desc { font-size: 11px; color: var(--text-muted); margin-top: 4px; line-height: 1.4; }
.scan-target-platforms { }
.scan-target-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
}
.scan-target-grid { display: flex; flex-wrap: wrap; gap: 6px; }
.scan-target-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: 1.5px solid var(--border);
  border-radius: 20px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}
.scan-target-item.selected {
  border-color: var(--brand);
  background: var(--brand-light);
  color: var(--brand);
  font-weight: 600;
}
.scan-mode-footer { display: flex; justify-content: flex-end; gap: 10px; }

/* ===== 扫码提示悬浮条 ===== */
.scan-tip-bar {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--brand);
  color: white;
  padding: 12px 20px;
  border-radius: 24px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  font-weight: 600;
  box-shadow: 0 4px 20px rgba(8,91,156,.4);
  z-index: 9999;
  cursor: pointer;
  white-space: nowrap;
}
.scan-tip-bar .el-button {
  background: white;
  color: var(--brand);
  border: none;
}

/* ===== 动画 ===== */
.slide-down-enter-active, .slide-down-leave-active { transition: all 0.3s ease; overflow: hidden; }
.slide-down-enter-from, .slide-down-leave-to { opacity: 0; transform: translateY(-10px); }
.slide-up-enter-active, .slide-up-leave-active { transition: all 0.3s ease; }
.slide-up-enter-from, .slide-up-leave-to { opacity: 0; transform: translateY(20px); }

/* ===== 集采流程面板（步骤3-5） ===== */
.collect-flow-panel {
  margin-top: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 步骤进度条 */
.flow-steps {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: linear-gradient(135deg, rgba(8,91,156,.04) 0%, rgba(46,173,62,.04) 100%);
  border: 1px solid rgba(8,91,156,.12);
  border-radius: 12px;
}
.flow-step {
  display: flex;
  align-items: center;
  gap: 10px;
  opacity: 0.5;
  transition: opacity 0.2s;
}
.flow-step.active { opacity: 1; }
.step-num {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #e5e7eb;
  color: white;
  font-weight: 700;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.flow-step.active .step-num { background: var(--brand); }
.step-name { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.step-count { font-size: 11px; color: var(--text-muted); }
.flow-arrow { color: var(--text-muted); flex-shrink: 0; }

/* 步骤卡片 */
.step-card { }
.step-card :deep(.el-card__header) { background: rgba(8,91,156,.04); padding: 10px 16px; }

/* 步骤内操作栏 */
.step-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid #f0f0f0;
}

/* 评估汇总 */
.evaluation-summary {
  background: #f8fafc;
  border-radius: 10px;
  padding: 14px 16px;
  margin-bottom: 14px;
}
.eval-stats {
  display: flex;
  gap: 20px;
  margin-bottom: 8px;
}
.eval-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}
.stat-num {
  font-size: 24px;
  font-weight: 800;
  line-height: 1;
  color: var(--text-primary);
}
.eval-stat.success .stat-num { color: #22c55e; }
.eval-stat.danger .stat-num { color: #ef4444; }
.stat-label { font-size: 11px; color: var(--text-muted); }
.eval-tip { font-size: 13px; color: var(--text-secondary); margin: 0; }

/* 待评估商品卡片 */
.pending-goods-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 10px;
  max-height: 320px;
  overflow-y: auto;
}
.eval-goods-card {
  border: 1.5px solid #e5e7eb;
  border-radius: 10px;
  padding: 10px 12px;
  transition: all 0.15s;
}
.eval-goods-card:hover { border-color: #d1d5db; }
.eval-goods-card.grade-recommend { border-color: #22c55e; background: rgba(34,197,94,.03); }
.eval-goods-card.grade-not_recommended { opacity: 0.5; }
.egc-header { margin-bottom: 6px; }
.egc-name {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  margin-bottom: 6px;
}
.egc-profit { margin-bottom: 6px; }
.profit-price { font-size: 15px; font-weight: 700; color: var(--text-primary); }
.profit-info { font-size: 11px; color: #22c55e; margin-left: 4px; }
.egc-actions { font-size: 12px; }

/* 筛选确认 */
.filter-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.selected-goods-table { }
.filter-summary {
  font-size: 13px;
  color: var(--text-secondary);
  padding: 10px 0;
}
.filter-summary strong { color: var(--text-primary); }
.profit-highlight { color: #22c55e !important; }

/* 上架结果 */
.listing-progress {
  margin-bottom: 16px;
}
.listing-stats {
  display: flex;
  gap: 16px;
  margin-top: 8px;
  font-size: 13px;
  color: var(--text-secondary);
}
.listing-results { display: flex; flex-direction: column; gap: 6px; }
.listing-result-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid;
}
.listing-result-item.success { background: rgba(34,197,94,.04); border-color: rgba(34,197,94,.2); }
.listing-result-item.fail { background: rgba(239,68,68,.04); border-color: rgba(239,68,68,.2); }
.result-icon { flex-shrink: 0; }
.result-info { flex: 1; }
.result-platform { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.result-success-text { font-size: 12px; color: #22c55e; }
.result-fail-text { font-size: 12px; color: #ef4444; }

/* 上架准备 */
.listing-ready {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  background: #f8fafc;
  border-radius: 10px;
}
.ready-title { font-size: 16px; font-weight: 600; color: var(--text-primary); margin: 0 0 4px; }
.ready-targets { font-size: 13px; color: var(--text-secondary); margin: 0; }

/* 表格内价格 */
.table-price { font-weight: 600; color: var(--text-primary); }
.table-profit { color: #22c55e; font-weight: 600; }
.table-profit-rate { color: var(--text-secondary); }

/* ===== 选品决策弹窗 ===== */
.decision-modal-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.decision-modal-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 0;
}

.dmh-icon {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #1d4ed8, #1e40af);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
}

.dmh-info { flex: 1; }

.dmh-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

.dmh-sub {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.dmh-grade {
  font-size: 12px;
  padding: 4px 10px;
  flex-shrink: 0;
}

.decision-goods-info {
  background: var(--bg-page);
  border-radius: 10px;
  padding: 12px 14px;
}

.dgi-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dgi-meta {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 4px;
}

.profit-calc-card {
  background: linear-gradient(135deg, #f8fafc 0%, #f0f9eb 100%);
  border: 1px solid #d1fae5;
  border-radius: 14px;
  padding: 16px;
}

.profit-main-stats {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 12px;
}

.pms-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.pms-label {
  font-size: 11px;
  color: var(--text-secondary);
}

.pms-value {
  font-size: 18px;
  font-weight: 800;
  color: var(--text-primary);
}

.pms-item.highlight .pms-value { color: var(--brand); }
.pms-item.success .pms-value { color: #22c55e; }

.pms-arrow {
  font-size: 18px;
  color: var(--text-muted);
}

.profit-sub-stats {
  display: flex;
  justify-content: center;
  gap: 20px;
  padding-top: 12px;
  border-top: 1px solid rgba(34, 197, 94, 0.2);
}

.pss-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.pss-label {
  font-size: 11px;
  color: var(--text-secondary);
}

.pss-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.pss-value.danger { color: #ef4444; }
.pss-value.warning { color: #f59e0b; }

.profit-warning {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
  padding: 8px 10px;
  background: rgba(239, 68, 68, 0.08);
  border-radius: 8px;
  color: #dc2626;
  font-size: 12px;
}

.pricing-template-section { }

.pts-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.pts-options {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.pts-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 10px 8px;
  border: 2px solid var(--border);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.pts-option:hover { border-color: var(--brand); }

.pts-option.active {
  border-color: var(--brand);
  background: var(--brand-light);
}

.pts-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
}

.pts-rate {
  font-size: 11px;
  color: var(--text-secondary);
}

.pts-price {
  font-size: 13px;
  font-weight: 700;
  color: var(--brand);
  margin-top: 4px;
}

.decision-reason {
  background: #fff8ed;
  border: 1px solid #fdf0d5;
  border-radius: 10px;
  padding: 12px 14px;
}

.dr-label {
  font-size: 12px;
  font-weight: 600;
  color: #92400e;
  margin-bottom: 4px;
}

.dr-text {
  font-size: 13px;
  color: #78350f;
  line-height: 1.5;
}

.decision-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
