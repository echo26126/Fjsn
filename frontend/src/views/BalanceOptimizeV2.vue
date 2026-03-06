<template>
  <div class="page-container">
    <div class="page-header">
      <span class="page-title">产销平衡优化 V2</span>
      <a-space>
        <a-tag color="green">LP 求解器已就绪</a-tag>
        <a-tag color="blue">2025年12月 · 散装/袋装双品种</a-tag>
      </a-space>
    </div>

    <a-tabs v-model:activeKey="activeTab" @change="onTabChange">

      <!-- ══ Tab 1：基础参数 ══ -->
      <a-tab-pane key="params" tab="📋 基础参数">
        <div class="section-bar">
          <span class="section-title">品种筛选</span>
          <a-radio-group v-model:value="productFilter" button-style="solid" size="small">
            <a-radio-button value="all">全部</a-radio-button>
            <a-radio-button value="散装">散装</a-radio-button>
            <a-radio-button value="袋装">袋装</a-radio-button>
          </a-radio-group>
          <a-button size="small" style="margin-left:12px" @click="reloadParams">🔄 恢复默认</a-button>
        </div>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-card :bordered="false" title="🏭 各基地产能上限（万吨/月）" size="small">
              <a-table :data-source="capacityRows" :columns="capacityCols" size="small" :pagination="false" bordered />
            </a-card>
          </a-col>
          <a-col :span="12">
            <a-card :bordered="false" title="📦 各区域需求预测（万吨/月）" size="small">
              <a-table :data-source="demandRows" :columns="demandCols" size="small" :pagination="false" bordered />
            </a-card>
          </a-col>
        </a-row>

        <a-row :gutter="16" style="margin-top:16px">
          <a-col :span="12">
            <a-card :bordered="false" title="💰 各区域售价（元/吨）" size="small">
              <a-table :data-source="priceRows" :columns="priceCols" size="small" :pagination="false" bordered />
            </a-card>
          </a-col>
          <a-col :span="12">
            <a-card :bordered="false" title="🔧 各基地生产成本（元/吨）" size="small">
              <a-table :data-source="prodCostRows" :columns="prodCostCols" size="small" :pagination="false" bordered />
            </a-card>
          </a-col>
        </a-row>

        <a-row :gutter="16" style="margin-top:16px">
          <a-col :span="10">
            <a-card :bordered="false" title="🚛 其他参数" size="small">
              <a-form layout="inline" size="small">
                <a-form-item label="袋装运输附加费">
                  <a-input-number v-model:value="bagPremium" :min="0" :max="30" :step="1" addon-after="元/吨" style="width:130px" />
                </a-form-item>
                <a-form-item label="库存持有成本">
                  <a-input-number v-model:value="holdingCost" :min="0" :max="50" :step="1" addon-after="元/吨/月" style="width:150px" />
                </a-form-item>
              </a-form>
            </a-card>
          </a-col>
        </a-row>
      </a-tab-pane>

      <!-- ══ Tab 2：权重调节 & 求解 ══ -->
      <a-tab-pane key="solve" tab="⚙️ 权重调节 & 求解">
        <a-row :gutter="24">
          <!-- 左：权重滑块 -->
          <a-col :span="9">
            <a-card :bordered="false" title="权重配置（第二层）" size="small">
              <div class="preset-row">
                <span style="font-size:12px;color:#888;margin-right:8px">预设方案：</span>
                <a-button
                  v-for="(lbl, key) in presetLabels" :key="key" size="small"
                  :type="activePreset === key ? 'primary' : 'default'"
                  style="margin-right:6px"
                  @click="applyPreset(key)"
                >{{ lbl }}</a-button>
                <a-button size="small" @click="resetWeights">重置</a-button>
              </div>

              <div class="weight-list">
                <div v-for="(cfg, key) in weightConfigs" :key="key" class="weight-item">
                  <div class="weight-header">
                    <span class="w-name">{{ cfg.label }}</span>
                    <span class="w-val">{{ (weights as any)[key].toFixed(2) }}</span>
                  </div>
                  <a-slider
                    v-model:value="(weights as any)[key]"
                    :min="cfg.min" :max="cfg.max" :step="cfg.step"
                    :tip-formatter="(v: number) => v.toFixed(2)"
                    @change="activePreset = 'custom'"
                  />
                  <div class="w-hint">{{ cfg.hint }}</div>
                </div>
              </div>

              <a-button
                type="primary" block :loading="solving"
                style="margin-top:16px" @click="runSolve"
              >⚡ 运行 LP 求解</a-button>
            </a-card>
          </a-col>

          <!-- 右：求解结果 -->
          <a-col :span="15">
            <a-empty v-if="!solveResult" description="点击「运行 LP 求解」查看最优方案" style="margin-top:60px" />
            <template v-else>
              <!-- KPI 卡片 -->
              <div class="kpi-strip">
                <div class="kpi-card kpi-profit">
                  <div class="kpi-lbl">净利润</div>
                  <div class="kpi-num">{{ fmtNum(solveResult.profit_breakdown.net_profit) }}</div>
                  <div class="kpi-unit">万元</div>
                </div>
                <div class="kpi-card kpi-revenue">
                  <div class="kpi-lbl">总收入</div>
                  <div class="kpi-num">{{ fmtNum(solveResult.profit_breakdown.revenue) }}</div>
                  <div class="kpi-unit">万元</div>
                </div>
                <div class="kpi-card kpi-transport">
                  <div class="kpi-lbl">运输成本</div>
                  <div class="kpi-num">{{ fmtNum(solveResult.profit_breakdown.transport_cost) }}</div>
                  <div class="kpi-unit">万元</div>
                </div>
                <div class="kpi-card kpi-fulfill">
                  <div class="kpi-lbl">平均满足率</div>
                  <div class="kpi-num">{{ avgFulfillment }}</div>
                  <div class="kpi-unit">%</div>
                </div>
              </div>

              <!-- 利润分解 -->
              <a-card :bordered="false" title="利润分解" size="small" style="margin-top:12px">
                <div class="pb-row"><span>总收入</span><span class="green">+{{ fmtNum(solveResult.profit_breakdown.revenue) }} 万元</span></div>
                <div class="pb-row"><span>生产成本</span><span class="red">-{{ fmtNum(solveResult.profit_breakdown.prod_cost) }} 万元</span></div>
                <div class="pb-row"><span>运输成本</span><span class="red">-{{ fmtNum(solveResult.profit_breakdown.transport_cost) }} 万元</span></div>
                <div class="pb-row"><span>库存持有成本</span><span class="red">-{{ fmtNum(solveResult.profit_breakdown.inventory_cost) }} 万元</span></div>
                <div class="pb-row pb-total"><span>净利润</span><span class="green">{{ fmtNum(solveResult.profit_breakdown.net_profit) }} 万元</span></div>
              </a-card>

              <!-- 供需满足率 -->
              <a-card :bordered="false" title="各区域供需满足率" size="small" style="margin-top:12px">
                <a-table
                  :data-source="solveResult.gap_by_region"
                  :columns="gapCols"
                  size="small" :pagination="false" bordered
                />
              </a-card>

              <!-- 影子价格 Top5 -->
              <a-card :bordered="false" title="关键约束影子价格（Top 5）" size="small" style="margin-top:12px">
                <div v-for="sp in solveResult.shadow_prices.slice(0,5)" :key="sp.constraint_key" class="shadow-item">
                  <div class="si-header">
                    <a-tag :color="sp.is_binding ? 'red' : 'default'" style="font-size:11px">
                      {{ sp.is_binding ? '紧约束' : '松约束' }}
                    </a-tag>
                    <span class="si-name">{{ sp.constraint }}</span>
                    <span class="si-pi">π={{ sp.shadow_price }}</span>
                  </div>
                  <div class="si-hint">{{ sp.interpretation }}</div>
                </div>
              </a-card>
            </template>
          </a-col>
        </a-row>
      </a-tab-pane>

      <!-- ══ Tab 3：多方案对比 ══ -->
      <a-tab-pane key="scenarios" tab="📊 多方案对比">
        <div class="section-bar">
          <span class="section-title">保守 / 均衡 / 激进 三方案对比</span>
          <a-button type="primary" :loading="scenariosLoading" @click="runScenarios">🔄 重新计算</a-button>
        </div>

        <a-empty v-if="!scenariosResult" description="点击「重新计算」运行三方案对比" style="margin-top:60px" />
        <template v-else>
          <a-row :gutter="16">
            <a-col :span="8" v-for="(sc, key) in scenariosResult.scenarios" :key="key">
              <div class="sc-card" :class="key">
                <div class="sc-head">
                  <span class="sc-label">{{ sc.label }}</span>
                  <a-tag :color="riskColor(sc.inventory_risk)" size="small">风险：{{ sc.inventory_risk }}</a-tag>
                </div>
                <div class="sc-desc">{{ sc.description }}</div>
                <div class="sc-metrics">
                  <div class="sc-row"><span>净利润</span><span class="sc-profit">{{ fmtNum(sc.profit) }} 万元</span></div>
                  <div class="sc-row"><span>平均满足率</span><span>{{ sc.fulfillment_rate }}%</span></div>
                  <div class="sc-row"><span>运输成本</span><span>{{ fmtNum(sc.transport_cost) }} 万元</span></div>
                  <div class="sc-row"><span>求解状态</span><a-tag color="green" style="font-size:11px">{{ sc.solve_status }}</a-tag></div>
                </div>
                <div v-if="key === scenariosResult.recommendation" class="sc-badge">⭐ 推荐</div>
              </div>
            </a-col>
          </a-row>

          <a-card :bordered="false" title="各区域供需满足率对比" size="small" style="margin-top:20px">
            <a-table :data-source="scenariosCompareRows" :columns="scenarioCompareCols" size="small" :pagination="false" bordered />
          </a-card>
        </template>
      </a-tab-pane>

      <!-- ══ Tab 4：What-if 模拟 ══ -->
      <a-tab-pane key="whatif" tab="🔬 What-if 模拟">
        <a-row :gutter="20">
          <!-- 左：调整项编辑器 -->
          <a-col :span="11">
            <a-card :bordered="false" size="small">
              <template #title>
                <span>假设场景编辑器</span>
                <a-button size="small" danger style="margin-left:8px" @click="clearAdjustments">🗑 清空</a-button>
              </template>

              <!-- 快捷模板 -->
              <div class="tpl-row">
                <span class="tpl-lbl">快捷模板：</span>
                <a-button v-for="tpl in whatifTemplates" :key="tpl.id" size="small" style="margin-right:6px;margin-bottom:4px" @click="applyTemplate(tpl)">
                  {{ tpl.label }}
                </a-button>
              </div>

              <!-- 调整项列表 -->
              <div class="adj-list">
                <div v-for="(adj, idx) in adjustments" :key="idx" class="adj-item">
                  <a-space wrap size="small">
                    <a-select v-model:value="adj.type" size="small" style="width:95px" @change="() => onAdjTypeChange(adj)">
                      <a-select-option value="capacity">产能</a-select-option>
                      <a-select-option value="price">售价</a-select-option>
                      <a-select-option value="demand">需求</a-select-option>
                      <a-select-option value="prod_cost">生产成本</a-select-option>
                      <a-select-option value="transport">运输成本</a-select-option>
                    </a-select>

                    <a-select v-if="adjNeedsBase(adj.type)" v-model:value="adj.base" size="small" style="width:95px" placeholder="选基地" allow-clear>
                      <a-select-option v-for="b in bases" :key="b" :value="b">{{ b }}</a-select-option>
                    </a-select>

                    <a-select v-if="adjNeedsRegion(adj.type)" v-model:value="adj.region" size="small" style="width:95px" placeholder="选区域" allow-clear>
                      <a-select-option v-for="r in regions" :key="r" :value="r">{{ r }}</a-select-option>
                    </a-select>

                    <a-select v-if="adj.type !== 'transport'" v-model:value="adj.product" size="small" style="width:75px" placeholder="品种">
                      <a-select-option value="散装">散装</a-select-option>
                      <a-select-option value="袋装">袋装</a-select-option>
                      <a-select-option value="">全部</a-select-option>
                    </a-select>

                    <a-select v-model:value="adj.mode" size="small" style="width:75px">
                      <a-select-option value="abs">绝对值</a-select-option>
                      <a-select-option value="pct">百分比</a-select-option>
                    </a-select>

                    <a-input-number
                      v-model:value="adj.value"
                      :step="adj.mode === 'pct' ? 5 : 1"
                      size="small" style="width:85px"
                      :addon-after="adj.mode === 'pct' ? '%' : adjUnit(adj.type)"
                    />

                    <a-button size="small" danger @click="removeAdj(idx)">✕</a-button>
                  </a-space>
                  <div class="adj-preview">→ {{ adjLabel(adj) }}</div>
                </div>

                <a-button dashed block size="small" style="margin-top:8px" @click="addAdjustment">
                  + 添加调整项
                </a-button>
              </div>

              <div style="margin-top:10px">
                <a-checkbox v-model:checked="doDecompose">
                  计算各因素贡献分解（每项单独求解，稍慢）
                </a-checkbox>
              </div>

              <a-button
                type="primary" block :loading="whatifLoading"
                :disabled="adjustments.length === 0"
                style="margin-top:12px" @click="runWhatif"
              >⚡ 运行模拟</a-button>
            </a-card>
          </a-col>

          <!-- 右：模拟结果 -->
          <a-col :span="13">
            <a-empty v-if="!whatifResult" description="添加调整项后点击「运行模拟」" style="margin-top:60px" />
            <template v-else>
              <!-- 利润对比 -->
              <a-card :bordered="false" title="模拟结果" size="small">
                <div class="ws-row"><span>基准利润</span><span>{{ fmtNum(whatifResult.base_profit) }} 万元</span></div>
                <div class="ws-row"><span>模拟利润</span><span>{{ fmtNum(whatifResult.new_profit) }} 万元</span></div>
                <div class="ws-row ws-highlight">
                  <span>利润变化</span>
                  <span :class="whatifResult.profit_delta >= 0 ? 'green' : 'red'">
                    {{ whatifResult.profit_delta >= 0 ? '+' : '' }}{{ whatifResult.profit_delta }} 万元
                    （{{ whatifResult.profit_delta >= 0 ? '+' : '' }}{{ whatifResult.profit_delta_pct }}%）
                  </span>
                </div>
                <div class="wi-rec">💡 {{ whatifResult.recommendation }}</div>
              </a-card>

              <!-- 因素贡献分解 -->
              <a-card
                v-if="whatifResult.decomposition && whatifResult.decomposition.length > 0"
                :bordered="false" title="各因素贡献分解" size="small" style="margin-top:12px"
              >
                <div v-for="d in whatifResult.decomposition" :key="d.index" class="decomp-item">
                  <div class="di-header">
                    <a-tag
                      :color="d.recommendation === '优先执行' ? 'green' : d.recommendation === '可执行' ? 'orange' : 'red'"
                      style="font-size:11px"
                    >{{ d.recommendation }}</a-tag>
                    <span class="di-label">{{ d.label }}</span>
                    <span :class="d.profit_delta >= 0 ? 'green' : 'red'" class="di-delta">
                      {{ d.profit_delta >= 0 ? '+' : '' }}{{ d.profit_delta }} 万元
                    </span>
                  </div>
                  <a-progress
                    :percent="Math.round(Math.abs(d.profit_delta) / maxDecompDelta * 100)"
                    :stroke-color="d.profit_delta >= 0 ? '#52c41a' : '#ff4d4f'"
                    :show-info="false" size="small"
                  />
                </div>
              </a-card>

              <!-- 调配方案变化 -->
              <a-card
                v-if="whatifResult.allocation_diff && whatifResult.allocation_diff.length > 0"
                :bordered="false" title="调配方案变化（Top 10）" size="small" style="margin-top:12px"
              >
                <a-table
                  :data-source="whatifResult.allocation_diff.slice(0,10)"
                  :columns="diffCols"
                  size="small" :pagination="false" bordered
                />
              </a-card>

              <!-- 模拟后满足率 -->
              <a-card :bordered="false" title="模拟后各区域满足率" size="small" style="margin-top:12px">
                <a-table
                  :data-source="whatifResult.new_gap_by_region"
                  :columns="gapCols"
                  size="small" :pagination="false" bordered
                />
              </a-card>
            </template>
          </a-col>
        </a-row>
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import { message } from 'ant-design-vue'
import axios from 'axios'

const API = '/api/optimizer'

// ── 状态 ──
const activeTab = ref('solve')
const productFilter = ref('all')
const solving = ref(false)
const scenariosLoading = ref(false)
const whatifLoading = ref(false)
const solveResult = ref<any>(null)
const scenariosResult = ref<any>(null)
const whatifResult = ref<any>(null)
const doDecompose = ref(true)

// ── 参数数据 ──
const bases = ref<string[]>([])
const regions = ref<string[]>([])
const capacityRows = ref<any[]>([])
const demandRows = ref<any[]>([])
const priceRows = ref<any[]>([])
const prodCostRows = ref<any[]>([])
const bagPremium = ref(6)
const holdingCost = ref(8)
const whatifTemplates = ref<any[]>([])

// ── 权重 ──
const activePreset = ref('balanced')
const weights = ref({
  capacity_ratio: 1.0,
  inv_min_ratio: 1.0,
  demand_max_ratio: 1.0,
  demand_flex: 0.85,
  inventory_penalty: 1.0,
  transport_penalty: 1.0,
})

const weightConfigs: Record<string, any> = {
  capacity_ratio:    { label: '产能利用率上限',   min: 0.7, max: 1.0, step: 0.05, hint: '0.7=保留30%余量，1.0=满负荷' },
  inv_min_ratio:     { label: '安全库存下限倍数', min: 0.3, max: 2.0, step: 0.1,  hint: '越大=库存要求越高，越保守' },
  demand_max_ratio:  { label: '需求上限弹性',     min: 0.8, max: 1.2, step: 0.05, hint: '1.0=按预测，1.2=允许超额20%' },
  demand_flex:       { label: '最低保供率',       min: 0.5, max: 1.0, step: 0.05, hint: '0.85=保供85%，越高=保障越强' },
  inventory_penalty: { label: '库存惩罚系数',     min: 0.1, max: 5.0, step: 0.1,  hint: '越大=越倾向减少库存' },
  transport_penalty: { label: '运输成本敏感度',   min: 0.5, max: 2.0, step: 0.1,  hint: '越大=越倾向近距离发运' },
}

const presetLabels: Record<string, string> = {
  conservative: '保守', balanced: '均衡', aggressive: '激进',
}

const presetWeights: Record<string, any> = {
  conservative: { capacity_ratio: 0.85, inv_min_ratio: 1.5,  demand_max_ratio: 0.90, demand_flex: 0.95, inventory_penalty: 3.0, transport_penalty: 1.3 },
  balanced:     { capacity_ratio: 1.0,  inv_min_ratio: 1.0,  demand_max_ratio: 1.0,  demand_flex: 0.85, inventory_penalty: 1.0, transport_penalty: 1.0 },
  aggressive:   { capacity_ratio: 1.0,  inv_min_ratio: 0.4,  demand_max_ratio: 1.15, demand_flex: 0.70, inventory_penalty: 0.3, transport_penalty: 0.7 },
}

// ── What-if 调整项 ──
const adjustments = ref<any[]>([])

// ── 计算属性 ──
const filteredProducts = computed(() =>
  productFilter.value === 'all' ? ['散装', '袋装'] : [productFilter.value]
)

const avgFulfillment = computed(() => {
  if (!solveResult.value?.gap_by_region) return '0'
  const arr = solveResult.value.gap_by_region
  return (arr.reduce((s: number, g: any) => s + g.fulfillment_rate, 0) / arr.length).toFixed(1)
})

const maxDecompDelta = computed(() => {
  if (!whatifResult.value?.decomposition?.length) return 1
  return Math.max(...whatifResult.value.decomposition.map((d: any) => Math.abs(d.profit_delta)), 1)
})

const scenariosCompareRows = computed(() => {
  if (!scenariosResult.value) return []
  const details = scenariosResult.value.details
  return regions.value.map(r => {
    const row: any = { key: r, region: r }
    for (const sc of ['conservative', 'balanced', 'aggressive']) {
      const g = details[sc]?.gap_by_region?.find((x: any) => x.region === r)
      row[sc] = g ? g.fulfillment_rate : 0
    }
    return row
  })
})

// ── 表格列定义 ──
function makeEditableNumCol(field: string, label: string, rows: any[], min: number, max: number, step: number) {
  return {
    title: label, dataIndex: field, align: 'center' as const, width: 110,
    customRender: ({ record }: any) => h('a-input-number', {
      value: record[field],
      min, max, step, size: 'small',
      style: 'width:85px',
      onChange: (v: number) => { record[field] = v },
    }),
  }
}

const capacityCols = computed(() => [
  { title: '基地', dataIndex: 'base', width: 100 },
  ...filteredProducts.value.map(p => ({
    title: p, dataIndex: p, align: 'center' as const, width: 110,
    customRender: ({ record }: any) => h('input', {
      type: 'number', value: record[p], min: 0, max: 50, step: 0.5,
      class: 'tbl-input',
      onInput: (e: Event) => { record[p] = parseFloat((e.target as HTMLInputElement).value) || 0 },
    } as any),
  })),
])

const demandCols = computed(() => [
  { title: '区域', dataIndex: 'region', width: 100 },
  ...filteredProducts.value.map(p => ({
    title: p, dataIndex: p, align: 'center' as const, width: 110,
    customRender: ({ record }: any) => h('input', {
      type: 'number', value: record[p], min: 0, max: 30, step: 0.5,
      class: 'tbl-input',
      onInput: (e: Event) => { record[p] = parseFloat((e.target as HTMLInputElement).value) || 0 },
    } as any),
  })),
])

const priceCols = computed(() => [
  { title: '区域', dataIndex: 'region', width: 100 },
  ...filteredProducts.value.map(p => ({
    title: p, dataIndex: p, align: 'center' as const, width: 110,
    customRender: ({ record }: any) => h('input', {
      type: 'number', value: record[p], min: 200, max: 600, step: 5,
      class: 'tbl-input',
      onInput: (e: Event) => { record[p] = parseFloat((e.target as HTMLInputElement).value) || 0 },
    } as any),
  })),
])

const prodCostCols = computed(() => [
  { title: '基地', dataIndex: 'base', width: 100 },
  ...filteredProducts.value.map(p => ({
    title: p, dataIndex: p, align: 'center' as const, width: 110,
    customRender: ({ record }: any) => h('input', {
      type: 'number', value: record[p], min: 150, max: 500, step: 5,
      class: 'tbl-input',
      onInput: (e: Event) => { record[p] = parseFloat((e.target as HTMLInputElement).value) || 0 },
    } as any),
  })),
])

const gapCols = [
  { title: '区域', dataIndex: 'region', width: 90 },
  { title: '需求(万吨)', dataIndex: 'demand', align: 'center' as const, width: 90 },
  { title: '供应(万吨)', dataIndex: 'supplied', align: 'center' as const, width: 90 },
  {
    title: '满足率', dataIndex: 'fulfillment_rate', align: 'center' as const,
    customRender: ({ record }: any) => {
      const r = record.fulfillment_rate
      const color = r >= 100 ? '#52c41a' : r >= 85 ? '#faad14' : '#ff4d4f'
      return h('div', { style: 'display:flex;align-items:center;gap:6px' }, [
        h('div', {
          style: `height:8px;border-radius:4px;background:${color};width:${Math.min(r, 120)}px;max-width:100px`
        }),
        h('span', { style: `color:${color};font-weight:600;font-size:12px` }, `${r}%`),
      ])
    },
  },
]

const scenarioCompareCols = computed(() => [
  { title: '区域', dataIndex: 'region', width: 90 },
  ...(['conservative', 'balanced', 'aggressive'] as const).map(sc => ({
    title: { conservative: '保守方案', balanced: '均衡方案', aggressive: '激进方案' }[sc],
    dataIndex: sc, align: 'center' as const,
    customRender: ({ record }: any) => {
      const r = record[sc]
      const color = r >= 100 ? '#52c41a' : r >= 85 ? '#faad14' : '#ff4d4f'
      return h('span', { style: `color:${color};font-weight:600` }, `${r}%`)
    },
  })),
])

const diffCols = [
  { title: '基地', dataIndex: 'from_base', width: 90 },
  { title: '区域', dataIndex: 'to_region', width: 90 },
  { title: '品种', dataIndex: 'product', align: 'center' as const, width: 60 },
  { title: '基准(万吨)', dataIndex: 'base_qty', align: 'center' as const, width: 85 },
  { title: '模拟(万吨)', dataIndex: 'new_qty', align: 'center' as const, width: 85 },
  {
    title: '变化', dataIndex: 'delta', align: 'center' as const,
    customRender: ({ record }: any) => {
      const color = record.delta >= 0 ? '#52c41a' : '#ff4d4f'
      return h('span', { style: `color:${color};font-weight:600` },
        `${record.delta >= 0 ? '+' : ''}${record.delta}`)
    },
  },
]

// ── 初始化 ──
onMounted(loadParams)

async function loadParams() {
  try {
    const res = await axios.get(`${API}/params`)
    const data = res.data
    bases.value = data.bases
    regions.value = data.regions
    bagPremium.value = data.bag_transport_premium
    holdingCost.value = data.holding_cost
    whatifTemplates.value = data.whatif_templates || []

    capacityRows.value = data.bases.map((b: string) => ({ key: b, base: b, ...data.capacity[b] }))
    demandRows.value = data.regions.map((r: string) => ({ key: r, region: r, ...data.demand[r] }))
    priceRows.value = data.regions.map((r: string) => ({ key: r, region: r, ...data.price[r] }))
    prodCostRows.value = data.bases.map((b: string) => ({ key: b, base: b, ...data.prod_cost[b] }))
  } catch {
    message.error('加载参数失败，请检查后端服务')
  }
}

function reloadParams() { loadParams() }

// ── 权重操作 ──
function applyPreset(key: string) {
  activePreset.value = key
  Object.assign(weights.value, presetWeights[key])
}

function resetWeights() {
  activePreset.value = 'balanced'
  Object.assign(weights.value, presetWeights.balanced)
}

// ── 构建参数覆盖 ──
function buildParamsOverride() {
  const capacity: any = {}
  capacityRows.value.forEach(r => { capacity[r.base] = { 散装: r['散装'], 袋装: r['袋装'] } })
  const demand: any = {}
  demandRows.value.forEach(r => { demand[r.region] = { 散装: r['散装'], 袋装: r['袋装'] } })
  const price: any = {}
  priceRows.value.forEach(r => { price[r.region] = { 散装: r['散装'], 袋装: r['袋装'] } })
  const prod_cost: any = {}
  prodCostRows.value.forEach(r => { prod_cost[r.base] = { 散装: r['散装'], 袋装: r['袋装'] } })
  return { capacity, demand, price, prod_cost, bag_transport_premium: bagPremium.value, holding_cost: holdingCost.value }
}

// ── LP 求解 ──
async function runSolve() {
  solving.value = true
  try {
    const res = await axios.post(`${API}/solve`, { weights: weights.value, params_override: buildParamsOverride() })
    solveResult.value = res.data
    message.success(`求解完成，净利润 ${fmtNum(res.data.profit_breakdown.net_profit)} 万元`)
  } catch (e: any) {
    message.error('求解失败：' + (e.response?.data?.detail || e.message))
  } finally {
    solving.value = false
  }
}

// ── 三方案对比 ──
async function runScenarios() {
  scenariosLoading.value = true
  try {
    const res = await axios.post(`${API}/scenarios`, { params_override: buildParamsOverride() })
    scenariosResult.value = res.data
    message.success('三方案计算完成')
  } catch (e: any) {
    message.error('场景计算失败：' + (e.response?.data?.detail || e.message))
  } finally {
    scenariosLoading.value = false
  }
}

// ── What-if 模拟 ──
async function runWhatif() {
  if (!adjustments.value.length) { message.warning('请先添加调整项'); return }
  whatifLoading.value = true
  try {
    const res = await axios.post(`${API}/whatif`, {
      adjustments: adjustments.value,
      weights: weights.value,
      params_override: buildParamsOverride(),
      decompose: doDecompose.value,
    })
    whatifResult.value = res.data
    const d = res.data.profit_delta
    if (d >= 0) message.success(`模拟完成，利润 +${d} 万元`)
    else message.warning(`模拟完成，利润 ${d} 万元`)
  } catch (e: any) {
    message.error('模拟失败：' + (e.response?.data?.detail || e.message))
  } finally {
    whatifLoading.value = false
  }
}

// ── What-if 调整项操作 ──
function addAdjustment() {
  adjustments.value.push({ type: 'capacity', base: '', region: '', product: '散装', mode: 'abs', value: 1.0 })
}
function removeAdj(idx: number) { adjustments.value.splice(idx, 1) }
function clearAdjustments() { adjustments.value = []; whatifResult.value = null }
function applyTemplate(tpl: any) {
  adjustments.value = tpl.adjustments.map((a: any) => ({ ...a }))
  message.info(`已加载模板：${tpl.label}`)
}
function onAdjTypeChange(adj: any) { adj.base = ''; adj.region = ''; adj.product = '散装' }
function adjNeedsBase(type: string) { return ['capacity', 'prod_cost', 'transport'].includes(type) }
function adjNeedsRegion(type: string) { return ['price', 'demand', 'transport'].includes(type) }
function adjUnit(type: string) {
  return ({ capacity: '万吨', demand: '万吨', price: '元/吨', prod_cost: '元/吨', transport: '元/吨' } as any)[type] || ''
}
function adjLabel(adj: any) {
  const typeMap: any = { capacity: '产能', price: '售价', demand: '需求', prod_cost: '生产成本', transport: '运输成本' }
  const obj = adj.base || adj.region || '全部'
  const prod = adj.product ? `·${adj.product}` : ''
  const sign = adj.value >= 0 ? '+' : ''
  const unit = adj.mode === 'pct' ? '%' : adjUnit(adj.type)
  return `${obj}${prod} ${typeMap[adj.type] || adj.type} ${sign}${adj.value}${unit}`
}

// ── 辅助 ──
function fmtNum(n: number) { return n?.toLocaleString('zh-CN', { maximumFractionDigits: 1 }) ?? '0' }
function riskColor(risk: string) { return risk === '低' ? 'green' : risk === '中' ? 'orange' : 'red' }
function onTabChange(key: string) {
  if (key === 'scenarios' && !scenariosResult.value) runScenarios()
}
</script>

<style scoped>
.section-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary, #303133);
}

/* KPI 卡片 */
.kpi-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 4px;
}
.kpi-card {
  border-radius: 8px;
  padding: 12px;
  text-align: center;
  color: #fff;
}
.kpi-profit   { background: linear-gradient(135deg, #667eea, #764ba2); }
.kpi-revenue  { background: linear-gradient(135deg, #11998e, #38ef7d); }
.kpi-transport { background: linear-gradient(135deg, #f093fb, #f5576c); }
.kpi-fulfill  { background: linear-gradient(135deg, #4facfe, #00f2fe); }
.kpi-lbl  { font-size: 11px; opacity: 0.85; }
.kpi-num  { font-size: 22px; font-weight: 700; line-height: 1.3; }
.kpi-unit { font-size: 11px; opacity: 0.85; }

/* 利润分解 */
.pb-row {
  display: flex;
  justify-content: space-between;
  padding: 5px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 13px;
}
.pb-total {
  font-weight: 700;
  border-top: 2px solid #e4e7ed;
  border-bottom: none;
  padding-top: 8px;
}
.green { color: #52c41a; }
.red   { color: #ff4d4f; }

/* 影子价格 */
.shadow-item {
  margin-bottom: 8px;
  padding: 8px;
  background: #fafafa;
  border-radius: 4px;
  border: 1px solid #f0f0f0;
}
.si-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.si-name { font-size: 13px; font-weight: 500; flex: 1; }
.si-pi { font-size: 12px; color: #888; }
.si-hint { font-size: 12px; color: #666; }

/* 权重滑块 */
.preset-row { display: flex; align-items: center; flex-wrap: wrap; margin-bottom: 14px; }
.weight-list { display: flex; flex-direction: column; gap: 12px; }
.weight-item { }
.weight-header { display: flex; justify-content: space-between; margin-bottom: 2px; }
.w-name { font-size: 13px; }
.w-val  { font-size: 13px; font-weight: 600; color: #1677ff; }
.w-hint { font-size: 11px; color: #999; margin-top: 2px; }

/* 方案卡片 */
.sc-card {
  border-radius: 8px;
  padding: 16px;
  border: 2px solid #e4e7ed;
  position: relative;
  margin-bottom: 16px;
}
.sc-card.conservative { border-color: #52c41a; background: #f6ffed; }
.sc-card.balanced     { border-color: #1677ff; background: #e6f4ff; }
.sc-card.aggressive   { border-color: #ff4d4f; background: #fff2f0; }
.sc-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.sc-label { font-size: 15px; font-weight: 700; }
.sc-desc { font-size: 12px; color: #888; margin-bottom: 12px; }
.sc-metrics { display: flex; flex-direction: column; gap: 8px; }
.sc-row { display: flex; justify-content: space-between; font-size: 13px; }
.sc-profit { color: #1677ff; font-size: 15px; font-weight: 700; }
.sc-badge {
  position: absolute; top: -10px; right: 12px;
  background: #1677ff; color: #fff;
  font-size: 11px; padding: 2px 8px; border-radius: 10px;
}

/* What-if */
.tpl-row { display: flex; align-items: center; flex-wrap: wrap; margin-bottom: 10px; }
.tpl-lbl { font-size: 12px; color: #888; margin-right: 6px; }
.adj-list { display: flex; flex-direction: column; gap: 8px; max-height: 380px; overflow-y: auto; }
.adj-item { background: #fafafa; border: 1px solid #e4e7ed; border-radius: 6px; padding: 8px; }
.adj-preview { font-size: 11px; color: #1677ff; margin-top: 4px; }

/* What-if 结果 */
.ws-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #f0f0f0; font-size: 13px; }
.ws-highlight { font-weight: 700; font-size: 15px; border-bottom: none; padding-top: 10px; }
.wi-rec {
  margin-top: 10px; padding: 8px 12px;
  background: #e6f4ff; border-radius: 4px;
  font-size: 13px; color: #1677ff;
}

/* 因素分解 */
.decomp-item { margin-bottom: 10px; }
.di-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.di-label { font-size: 13px; flex: 1; }
.di-delta { font-size: 13px; font-weight: 600; }

/* 可编辑表格输入框 */
:deep(.tbl-input) {
  width: 80px;
  padding: 2px 6px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 12px;
  text-align: center;
  outline: none;
}
:deep(.tbl-input:focus) {
  border-color: #1677ff;
  box-shadow: 0 0 0 2px rgba(22,119,255,0.1);
}
</style>