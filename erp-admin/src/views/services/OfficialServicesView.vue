<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-header-left"><h1>官方服务</h1><p>合规体检 · 政策申报 · 供应链对接</p></div>
    </div>

    <el-row :gutter="20">
      <!-- 1. 合规体检 -->
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header><div class="sc-header"><el-icon color="#085B9C"><Checked /></el-icon><span>一键合规体检</span></div></template>
          <div v-if="complianceResult" class="sc-result">
            <div class="sc-score"><span>{{ complianceResult.score }}</span>分</div>
            <div class="sc-section"><div class="sc-label green">✅ 通过 ({{complianceResult.passed.length}}项)</div><div v-for="p in complianceResult.passed" :key="p" class="sc-item">{{p}}</div></div>
            <div class="sc-section"><div class="sc-label red">❌ 未通过 ({{complianceResult.failed.length}}项)</div><div v-for="f in complianceResult.failed" :key="f.item" class="sc-item red">{{f.item}}: {{f.reason}}</div></div>
            <div class="sc-section"><div class="sc-label orange">💡 AI整改建议</div><div v-for="s in complianceResult.suggestions" :key="s" class="sc-item">{{s}}</div></div>
          </div>
          <el-button type="primary" :loading="checkLoading" @click="runCheck" style="width:100%;margin-top:12px">{{ complianceResult?'重新体检':'开始体检' }}</el-button>
        </el-card>
      </el-col>

      <!-- 2. 扶持政策 -->
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header><div class="sc-header"><el-icon color="#E6A23C"><Trophy /></el-icon><span>扶持政策申报</span></div></template>
          <div v-loading="policyLoading">
            <div v-for="p in policies" :key="p.id" class="policy-card">
              <h4>{{ p.name }}</h4>
              <div class="policy-meta">
                <el-tag size="small" type="success">{{ p.subsidy }}</el-tag>
                <span style="font-size:12px;color:#909399;margin-left:8px">截止: {{ p.deadline }}</span>
              </div>
              <div class="policy-cond">{{ p.condition }}</div>
              <el-button size="small" type="primary" plain @click="applyPolicy(p.id)" style="margin-top:8px">一键申报</el-button>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 3. 辽宁供应链 -->
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header><div class="sc-header"><el-icon color="#2ead3e"><Shop /></el-icon><span>辽宁本地供应链</span></div></template>
          <div v-loading="supplierLoading">
            <div v-for="s in suppliers" :key="s.id" class="supplier-card">
              <h4>{{ s.name }}</h4>
              <div class="supplier-tags">
                <el-tag size="small">{{ s.category }}</el-tag>
                <el-tag size="small" type="warning">起订: {{ s.moq }}件</el-tag>
                <el-tag v-if="s.dropship" size="small" type="success">一件代发</el-tag>
              </div>
              <div class="supplier-subsidy">{{ s.subsidy }}</div>
              <el-button size="small" type="success" plain @click="contactSupplier(s.id)" style="margin-top:8px">一键对接工厂</el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Checked, Trophy, Shop } from '@element-plus/icons-vue'
import { runComplianceCheck, getPolicies, applyPolicy, getSuppliers } from '@/api/services'

const checkLoading = ref(false); const complianceResult = ref(null)
const policyLoading = ref(false); const policies = ref([])
const supplierLoading = ref(false); const suppliers = ref([])

async function runCheck() { checkLoading.value = true; try { const r = await runComplianceCheck(); complianceResult.value = r?.data || r; ElMessage.success('体检完成') } catch { ElMessage.error('体检失败') } finally { checkLoading.value = false } }
async function loadPolicies() { policyLoading.value = true; try { const r = await getPolicies(); policies.value = r?.data?.policies || [] } finally { policyLoading.value = false } }
async function contactSupplier(id) { ElMessage.success('已发送对接请求，专属客户经理将联系您') }
async function loadSuppliers() { supplierLoading.value = true; try { const r = await getSuppliers(); suppliers.value = r?.data?.suppliers || [] } finally { supplierLoading.value = false } }

onMounted(() => { loadPolicies(); loadSuppliers() })
</script>

<style scoped>
.page-container { padding:24px;max-width:1400px;margin:0 auto }
.page-header { margin-bottom:24px }
.page-header h1 { margin:0 0 4px;font-size:22px }
.page-header p { margin:0;color:#909399;font-size:13px }
.sc-header { display:flex;align-items:center;gap:8px;font-weight:600 }
.sc-score { text-align:center;font-size:28px;font-weight:700;color:#085B9C;padding:12px 0 }
.sc-score span { font-size:48px }
.sc-section { margin-top:12px }
.sc-label { font-weight:600;margin-bottom:6px }.sc-label.green{color:#2ead3e}.sc-label.red{color:#F56C6C}.sc-label.orange{color:#E6A23C}
.sc-item { font-size:12px;color:#606266;padding:2px 0 }.sc-item.red{color:#F56C6C}
.policy-card { padding:12px 0;border-bottom:1px solid #f5f7fa }
.policy-card h4 { margin:0 0 6px;font-size:14px }
.policy-meta { margin-bottom:4px }
.policy-cond { font-size:12px;color:#909399 }
.supplier-card { padding:12px 0;border-bottom:1px solid #f5f7fa }
.supplier-card h4 { margin:0 0 6px;font-size:14px }
.supplier-tags { display:flex;gap:4px;margin-bottom:4px }
.supplier-subsidy { font-size:12px;color:#E6A23C }
</style>
