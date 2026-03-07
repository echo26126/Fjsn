<template>
  <div class="page-container">
    <div class="page-header">
      <span class="page-title">模拟建议</span>
    </div>

    <a-tabs v-model:activeKey="activeTab" class="sim-tabs">
      <a-tab-pane key="base" tab="基础参数">
        <a-spin :spinning="paramsLoading">
          <a-alert
            type="info"
            show-icon
            style="margin-bottom: 12px"
            :message="`单位说明：产能/需求 ${unitMap.capacity}，售价/成品成本/运输成本 ${unitMap.price}`"
          />
          <a-row :gutter="12">
            <a-col :span="12">
              <a-card :bordered="false" :title="`需求参数（${unitMap.demand}）`">
                <a-table :data-source="demandRows" :columns="demandCols" :pagination="false" size="small" row-key="key">
                  <template #bodyCell="{ column, record, text }">
                    <a-input-number
                      v-if="String(column.dataIndex || '').startsWith('p_')"
                      :value="Number(record[column.dataIndex] || 0)"
                      size="small"
                      style="width: 100%"
                      @change="(v) => onProductCellChange(record, String(column.dataIndex), v)"
                    />
                    <span v-else>{{ text }}</span>
                  </template>
                </a-table>
              </a-card>
            </a-col>
            <a-col :span="12">
              <a-card :bordered="false" :title="`售价参数（${unitMap.price}）`">
                <a-table :data-source="priceRows" :columns="priceCols" :pagination="false" size="small" row-key="key">
                  <template #bodyCell="{ column, record, text }">
                    <a-input-number
                      v-if="String(column.dataIndex || '').startsWith('p_')"
                      :value="Number(record[column.dataIndex] || 0)"
                      size="small"
                      style="width: 100%"
                      @change="(v) => onProductCellChange(record, String(column.dataIndex), v)"
                    />
                    <span v-else>{{ text }}</span>
                  </template>
                </a-table>
              </a-card>
            </a-col>
          </a-row>
          <a-row :gutter="12" style="margin-top: 12px">
            <a-col :span="12">
              <a-card :bordered="false" :title="`产能参数（${unitMap.capacity}）`">
                <a-table :data-source="capacityRows" :columns="capacityCols" :pagination="false" size="small" row-key="key">
                  <template #bodyCell="{ column, record, text }">
                    <a-input-number
                      v-if="String(column.dataIndex || '').startsWith('p_')"
                      :value="Number(record[column.dataIndex] || 0)"
                      size="small"
                      style="width: 100%"
                      @change="(v) => onProductCellChange(record, String(column.dataIndex), v)"
                    />
                    <span v-else>{{ text }}</span>
                  </template>
                </a-table>
              </a-card>
            </a-col>
            <a-col :span="12">
              <a-card :bordered="false" :title="`成品成本参数（${unitMap.prod_cost}）`">
                <a-table :data-source="prodCostRows" :columns="prodCostCols" :pagination="false" size="small" row-key="key">
                  <template #bodyCell="{ column, record, text }">
                    <a-input-number
                      v-if="String(column.dataIndex || '').startsWith('p_')"
                      :value="Number(record[column.dataIndex] || 0)"
                      size="small"
                      style="width: 100%"
                      @change="(v) => onProductCellChange(record, String(column.dataIndex), v)"
                    />
                    <span v-else>{{ text }}</span>
                  </template>
                </a-table>
              </a-card>
            </a-col>
          </a-row>
          <a-row :gutter="12" style="margin-top: 12px">
            <a-col :span="12">
              <a-card :bordered="false" :title="`运输成本参数（${unitMap.transport}）`">
                <a-table :data-source="transportRows" :columns="transportCols" :pagination="{ pageSize: 8 }" size="small" row-key="key">
                  <template #bodyCell="{ column, record, text }">
                    <a-input-number
                      v-if="column.dataIndex === 'cost'"
                      :value="Number(record.cost || 0)"
                      size="small"
                      style="width: 100%"
                      @change="(v) => onTransportCostChange(record, v)"
                    />
                    <span v-else>{{ text }}</span>
                  </template>
                </a-table>
              </a-card>
            </a-col>
            <a-col :span="12">
              <a-card :bordered="false" title="库存与费用口径">
                <a-table :data-source="settingRows" :columns="settingCols" :pagination="false" size="small" row-key="name">
                  <template #bodyCell="{ column, record, text }">
                    <a-input-number
                      v-if="column.dataIndex === 'value' && isEditableSetting(record.name)"
                      :value="Number(record.value || 0)"
                      size="small"
                      style="width: 100%"
                      @change="(v) => onSettingValueChange(record, v)"
                    />
                    <span v-else>{{ text }}</span>
                  </template>
                </a-table>
              </a-card>
            </a-col>
          </a-row>
        </a-spin>
      </a-tab-pane>

      <a-tab-pane key="factor" tab="变动模拟">
        <div class="factor-grid">
          <a-card :bordered="false" title="产能">
            <a-space direction="vertical" :size="4" style="width: 100%" class="factor-form">
              <div class="field-row">
                <span class="field-label">基地</span>
                <a-select v-model:value="capacityForm.bases" mode="multiple" allow-clear placeholder="可多选">
                  <a-select-option v-for="base in bases" :key="base" :value="base">{{ base }}</a-select-option>
                </a-select>
              </div>
              <div class="field-row">
                <span class="field-label">型号</span>
                <a-select v-model:value="capacityForm.models" mode="multiple" allow-clear placeholder="可多选" @change="onModelChange(capacityForm)">
                  <a-select-option v-for="model in modelOptions" :key="model" :value="model">{{ model }}</a-select-option>
                </a-select>
              </div>
              <div class="field-row">
                <span class="field-label">规格</span>
                <a-select v-model:value="capacityForm.packages" mode="multiple" allow-clear placeholder="可多选" :disabled="isClinkerSelected(capacityForm.models)">
                  <a-select-option v-for="pkg in packageOptions" :key="pkg" :value="pkg">{{ pkg }}</a-select-option>
                </a-select>
              </div>
              <div class="field-row">
                <span class="field-label">变化方式</span>
                <a-select v-model:value="capacityForm.mode">
                  <a-select-option value="pct">百分比（%）</a-select-option>
                  <a-select-option value="abs">绝对值（{{ unitMap.capacity }}）</a-select-option>
                </a-select>
              </div>
              <div class="field-row">
                <span class="field-label">变化值</span>
                <a-input-number v-model:value="capacityForm.value" style="width: 100%" :addon-after="capacityForm.mode === 'pct' ? '%' : unitMap.capacity" />
              </div>
              <div class="field-tip">口径：绝对值单位 {{ unitMap.capacity }}；百分比单位 %；正值上调，负值下调</div>
              <div class="factor-action">
                <a-button type="primary" @click="addCapacityAdjustments">加入调整</a-button>
              </div>
            </a-space>
          </a-card>

          <a-card :bordered="false" title="售价">
            <a-space direction="vertical" :size="4" style="width: 100%" class="factor-form">
              <div class="field-row">
                <span class="field-label">销售区域</span>
                <a-select v-model:value="priceForm.regions" mode="multiple" allow-clear placeholder="可多选">
                  <a-select-option v-for="region in regions" :key="region" :value="region">{{ region }}</a-select-option>
                </a-select>
              </div>
              <div class="field-row">
                <span class="field-label">型号</span>
                <a-select v-model:value="priceForm.models" mode="multiple" allow-clear placeholder="可多选" @change="onModelChange(priceForm)">
                  <a-select-option v-for="model in modelOptions" :key="model" :value="model">{{ model }}</a-select-option>
                </a-select>
              </div>
              <div class="field-row">
                <span class="field-label">规格</span>
                <a-select v-model:value="priceForm.packages" mode="multiple" allow-clear placeholder="可多选" :disabled="isClinkerSelected(priceForm.models)">
                  <a-select-option v-for="pkg in packageOptions" :key="pkg" :value="pkg">{{ pkg }}</a-select-option>
                </a-select>
              </div>
              <div class="field-row">
                <span class="field-label">变化方式</span>
                <a-select v-model:value="priceForm.mode">
                  <a-select-option value="pct">百分比（%）</a-select-option>
                  <a-select-option value="abs">绝对值（{{ unitMap.price }}）</a-select-option>
                </a-select>
              </div>
              <div class="field-row">
                <span class="field-label">变化值</span>
                <a-input-number v-model:value="priceForm.value" style="width: 100%" :addon-after="priceForm.mode === 'pct' ? '%' : unitMap.price" />
              </div>
              <div class="field-tip">口径：绝对值单位 {{ unitMap.price }}；百分比单位 %；正值上调，负值下调</div>
              <div class="factor-action">
                <a-button type="primary" @click="addPriceAdjustments">加入调整</a-button>
              </div>
            </a-space>
          </a-card>

          <a-card :bordered="false" title="需求">
            <a-space direction="vertical" :size="4" style="width: 100%" class="factor-form">
              <div class="field-row">
                <span class="field-label">销售区域</span>
                <a-select v-model:value="demandForm.regions" mode="multiple" allow-clear placeholder="可多选">
                  <a-select-option v-for="region in regions" :key="region" :value="region">{{ region }}</a-select-option>
                </a-select>
              </div>
              <div class="field-row">
                <span class="field-label">型号</span>
                <a-select v-model:value="demandForm.models" mode="multiple" allow-clear placeholder="可多选" @change="onModelChange(demandForm)">
                  <a-select-option v-for="model in modelOptions" :key="model" :value="model">{{ model }}</a-select-option>
                </a-select>
              </div>
              <div class="field-row">
                <span class="field-label">规格</span>
                <a-select v-model:value="demandForm.packages" mode="multiple" allow-clear placeholder="可多选" :disabled="isClinkerSelected(demandForm.models)">
                  <a-select-option v-for="pkg in packageOptions" :key="pkg" :value="pkg">{{ pkg }}</a-select-option>
                </a-select>
              </div>
              <div class="field-row">
                <span class="field-label">变化方式</span>
                <a-select v-model:value="demandForm.mode">
                  <a-select-option value="pct">百分比（%）</a-select-option>
                  <a-select-option value="abs">绝对值（{{ unitMap.demand }}）</a-select-option>
                </a-select>
              </div>
              <div class="field-row">
                <span class="field-label">变化值</span>
                <a-input-number v-model:value="demandForm.value" style="width: 100%" :addon-after="demandForm.mode === 'pct' ? '%' : unitMap.demand" />
              </div>
              <div class="field-tip">口径：绝对值单位 {{ unitMap.demand }}；百分比单位 %；正值上调，负值下调</div>
              <div class="factor-action">
                <a-button type="primary" @click="addDemandAdjustments">加入调整</a-button>
              </div>
            </a-space>
          </a-card>

          <a-card :bordered="false" title="成品成本">
            <a-space direction="vertical" :size="4" style="width: 100%" class="factor-form">
              <div class="field-row">
                <span class="field-label">基地</span>
                <a-select v-model:value="prodCostForm.bases" mode="multiple" allow-clear placeholder="可多选">
                  <a-select-option v-for="base in bases" :key="base" :value="base">{{ base }}</a-select-option>
                </a-select>
              </div>
              <div class="field-row">
                <span class="field-label">型号</span>
                <a-select v-model:value="prodCostForm.models" mode="multiple" allow-clear placeholder="可多选" @change="onModelChange(prodCostForm)">
                  <a-select-option v-for="model in modelOptions" :key="model" :value="model">{{ model }}</a-select-option>
                </a-select>
              </div>
              <div class="field-row">
                <span class="field-label">规格</span>
                <a-select v-model:value="prodCostForm.packages" mode="multiple" allow-clear placeholder="可多选" :disabled="isClinkerSelected(prodCostForm.models)">
                  <a-select-option v-for="pkg in packageOptions" :key="pkg" :value="pkg">{{ pkg }}</a-select-option>
                </a-select>
              </div>
              <div class="field-row">
                <span class="field-label">变化方式</span>
                <a-select v-model:value="prodCostForm.mode">
                  <a-select-option value="pct">百分比（%）</a-select-option>
                  <a-select-option value="abs">绝对值（{{ unitMap.prod_cost }}）</a-select-option>
                </a-select>
              </div>
              <div class="field-row">
                <span class="field-label">变化值</span>
                <a-input-number v-model:value="prodCostForm.value" style="width: 100%" :addon-after="prodCostForm.mode === 'pct' ? '%' : unitMap.prod_cost" />
              </div>
              <div class="field-tip">口径：绝对值单位 {{ unitMap.prod_cost }}；百分比单位 %；正值上调，负值下调</div>
              <div class="factor-action">
                <a-button type="primary" @click="addProdCostAdjustments">加入调整</a-button>
              </div>
            </a-space>
          </a-card>

          <a-card :bordered="false" title="运距变量">
            <a-space direction="vertical" :size="4" style="width: 100%" class="factor-form">
              <div class="field-row">
                <span class="field-label">基地</span>
                <a-select v-model:value="transportForm.bases" mode="multiple" allow-clear placeholder="可多选">
                  <a-select-option v-for="base in bases" :key="base" :value="base">{{ base }}</a-select-option>
                </a-select>
              </div>
              <div class="field-row">
                <span class="field-label">销售区域</span>
                <a-select v-model:value="transportForm.regions" mode="multiple" allow-clear placeholder="可多选">
                  <a-select-option v-for="region in regions" :key="region" :value="region">{{ region }}</a-select-option>
                </a-select>
              </div>
              <div class="field-row">
                <span class="field-label">运价系数</span>
                <a-input-number v-model:value="transportDistanceRate" style="width: 100%" :min="0" :step="0.01" addon-after="元/吨·公里" />
              </div>
              <div class="field-row">
                <span class="field-label">变化方式</span>
                <a-select v-model:value="transportForm.mode">
                  <a-select-option value="pct">百分比（%）</a-select-option>
                  <a-select-option value="abs">绝对值（公里）</a-select-option>
                </a-select>
              </div>
              <div class="field-row">
                <span class="field-label">变化值</span>
                <a-input-number v-model:value="transportForm.value" style="width: 100%" :addon-after="transportForm.mode === 'pct' ? '%' : '公里'" />
              </div>
              <div class="field-tip">口径：按运距调整，绝对值单位 公里；按运价系数折算为{{ unitMap.transport }}参与求解；当前按基地+销售区域生效</div>
              <div class="factor-action">
                <a-button type="primary" @click="addTransportAdjustments">加入调整</a-button>
              </div>
            </a-space>
          </a-card>
        </div>

        <a-card :bordered="false" title="调整项（支持多项叠加）">
          <a-empty v-if="adjustments.length === 0" description="请先添加调整项" />
          <div v-for="(adj, idx) in adjustments" :key="`${adj.type}-${idx}`" class="adj-line">
            <span>{{ renderAdj(adj) }}</span>
            <a-button size="small" danger @click="removeAdj(idx)">删除</a-button>
          </div>
          <a-space style="margin-top: 10px">
            <a-button @click="clearAdjustments">清空</a-button>
            <a-button type="primary" :loading="running" @click="runSimulation">运行模拟</a-button>
          </a-space>
        </a-card>
      </a-tab-pane>
    </a-tabs>

    <a-card v-if="hasReport" :bordered="false" title="客户建议报告" style="margin-top: 16px">
      <div class="report-head">
        <a-tag color="blue">AI策略摘要</a-tag>
        <span class="report-time">{{ output.generatedAt }}</span>
      </div>
      <div class="report-main"><strong>结论：</strong>{{ output.conclusion }}</div>
      <div v-if="output.highlights.length" class="report-highlights">
        <a-tag v-for="(item, idx) in output.highlights" :key="idx" color="processing">{{ item }}</a-tag>
      </div>
      <div class="report-row"><span>动作一</span><span>{{ output.actions[0] || '-' }}</span></div>
      <div class="report-row"><span>动作二</span><span>{{ output.actions[1] || '-' }}</span></div>
      <div class="report-row"><span>风险提示</span><span>{{ output.risk }}</span></div>
      <div class="report-row"><span>预期收益</span><span>{{ output.profit }}</span></div>
      <div class="report-row"><span>求解状态</span><span>{{ output.status }}</span></div>
      <div class="report-source">建议来源：{{ output.source }}</div>
      <a-space style="margin-top: 10px">
        <a-button @click="showReportModal = true">查看弹窗报告</a-button>
        <a-button @click="exportSuggestion">导出报告</a-button>
      </a-space>
    </a-card>

    <a-modal
      v-if="hasReport"
      v-model:open="showReportModal"
      title="客户建议报告"
      width="760px"
      :footer="null"
    >
      <div class="report-head">
        <a-tag color="blue">AI策略摘要</a-tag>
        <span class="report-time">{{ output.generatedAt }}</span>
      </div>
      <div class="report-main"><strong>结论：</strong>{{ output.conclusion }}</div>
      <div v-if="output.highlights.length" class="report-highlights">
        <a-tag v-for="(item, idx) in output.highlights" :key="idx" color="processing">{{ item }}</a-tag>
      </div>
      <div class="report-row"><span>动作一</span><span>{{ output.actions[0] || '-' }}</span></div>
      <div class="report-row"><span>动作二</span><span>{{ output.actions[1] || '-' }}</span></div>
      <div class="report-row"><span>风险提示</span><span>{{ output.risk }}</span></div>
      <div class="report-row"><span>预期收益</span><span>{{ output.profit }}</span></div>
      <div class="report-row"><span>求解状态</span><span>{{ output.status }}</span></div>
      <div class="report-source">建议来源：{{ output.source }}</div>
      <a-space style="margin-top: 12px">
        <a-button @click="showReportModal = false">关闭</a-button>
        <a-button type="primary" @click="exportSuggestion">导出报告</a-button>
      </a-space>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { optimizerApi, queryApi } from '@/api'
import { useAppStore } from '@/stores/app'

const activeTab = ref('factor')
const appStore = useAppStore()
const paramsLoading = ref(false)
const running = ref(false)
const showReportModal = ref(false)
const bases = ref<string[]>([])
const regions = ref<string[]>([])
const products = ref<string[]>([])
const capacityRows = ref<any[]>([])
const demandRows = ref<any[]>([])
const priceRows = ref<any[]>([])
const prodCostRows = ref<any[]>([])
const transportRows = ref<any[]>([])
const settingRows = ref<any[]>([])
const adjustments = ref<any[]>([])
const modelOptions = ref<string[]>([])
const packageOptions = ref<string[]>([])
const modelPackageItems = ref<Array<{ model: string, package: string, product: string }>>([])
const unitMap = ref({
  capacity: '万吨',
  demand: '万吨',
  price: '元/吨',
  prod_cost: '元/吨',
  transport: '元/吨',
})

const capacityForm = reactive({
  mode: 'pct',
  value: 0,
  bases: [] as string[],
  models: [] as string[],
  packages: [] as string[],
})
const priceForm = reactive({
  regions: [] as string[],
  models: [] as string[],
  packages: [] as string[],
  mode: 'pct',
  value: 0,
})
const demandForm = reactive({
  regions: [] as string[],
  models: [] as string[],
  packages: [] as string[],
  mode: 'pct',
  value: 0,
})
const prodCostForm = reactive({
  bases: [] as string[],
  models: [] as string[],
  packages: [] as string[],
  mode: 'pct',
  value: 0,
})
const transportForm = reactive({
  bases: [] as string[],
  regions: [] as string[],
  mode: 'pct',
  value: 0,
})
const transportDistanceRate = ref(0.35)

const output = reactive({
  conclusion: '',
  actions: [] as string[],
  risk: '',
  profit: '',
  status: '',
  source: '',
  generatedAt: '',
  highlights: [] as string[],
})
const hasReport = computed(() => Boolean(output.conclusion))

const buildProductCols = (firstLabel: string, unit: string) => ([
  { title: firstLabel, dataIndex: 'name' },
  ...products.value.map((product, idx) => ({ title: `${product}（${unit}）`, dataIndex: `p_${idx}` })),
])

const capacityCols = computed(() => buildProductCols('基地', unitMap.value.capacity))
const demandCols = computed(() => buildProductCols('销售区域', unitMap.value.demand))
const priceCols = computed(() => buildProductCols('销售区域', unitMap.value.price))
const prodCostCols = computed(() => buildProductCols('基地', unitMap.value.prod_cost))
const transportCols = computed(() => [
  { title: '基地', dataIndex: 'base' },
  { title: '销售区域', dataIndex: 'region' },
  { title: `运输成本（${unitMap.value.transport}）`, dataIndex: 'cost' },
])
const settingCols = [
  { title: '参数', dataIndex: 'name' },
  { title: '值', dataIndex: 'value' },
  { title: '说明', dataIndex: 'desc' },
]

const onProductCellChange = (record: any, dataIndex: string, value: any) => {
  record[dataIndex] = Number(value || 0)
}

const onTransportCostChange = (record: any, value: any) => {
  record.cost = Number(value || 0)
}

const isEditableSetting = (name: string) => ['袋装运输附加', '库存持有成本'].includes(name)

const onSettingValueChange = (record: any, value: any) => {
  record.value = Number(value || 0)
}

const buildParamsOverride = () => {
  const mapProductRow = (rows: any[]) => {
    const obj: Record<string, Record<string, number>> = {}
    rows.forEach((row: any) => {
      const key = String(row.name || '')
      if (!key) return
      obj[key] = {}
      products.value.forEach((product: string, idx: number) => {
        obj[key][product] = Number(row[`p_${idx}`] || 0)
      })
    })
    return obj
  }
  const transportCost: Record<string, Record<string, number>> = {}
  transportRows.value.forEach((row: any) => {
    const base = String(row.base || '')
    const region = String(row.region || '')
    if (!base || !region) return
    if (!transportCost[base]) transportCost[base] = {}
    transportCost[base][region] = Number(row.cost || 0)
  })
  const bagPremium = Number(settingRows.value.find((r: any) => r.name === '袋装运输附加')?.value || 0)
  const holdingCost = Number(settingRows.value.find((r: any) => r.name === '库存持有成本')?.value || 0)
  return {
    capacity: mapProductRow(capacityRows.value),
    demand: mapProductRow(demandRows.value),
    price: mapProductRow(priceRows.value),
    prod_cost: mapProductRow(prodCostRows.value),
    transport_cost: transportCost,
    bag_transport_premium: bagPremium,
    holding_cost: holdingCost,
  }
}

const buildItems = (type: string, mode: string, value: number, baseList: string[], regionList: string[], productList: string[]) => {
  const items: any[] = []
  for (const base of baseList) {
    for (const region of regionList) {
      for (const product of productList) {
        const row: any = { type, mode, value }
        if (base) row.base = base
        if (region) row.region = region
        if (type !== 'transport' && product) row.product = product
        items.push(row)
      }
    }
  }
  return items
}

const resolveProductsByModelAndPackage = (models: string[], packages: string[]) => {
  const byModel = (v: string) => !models.length || models.includes(v)
  const byPackage = (v: string) => !packages.length || packages.includes(v)
  const set = new Set<string>()
  modelPackageItems.value.forEach((item) => {
    if (byModel(item.model) && byPackage(item.package)) {
      set.add(item.product)
    }
  })
  return set.size ? [...set] : [...products.value]
}

const isClinkerSelected = (models: string[]) => models.includes('熟料')

const onModelChange = (form: { models: string[]; packages: string[] }) => {
  if (isClinkerSelected(form.models)) {
    form.packages = ['熟料']
    return
  }
  form.packages = form.packages.filter(pkg => pkg !== '熟料')
}

const addCapacityAdjustments = () => {
  if (!capacityForm.bases.length) {
    message.warning('请至少选择一个基地')
    return
  }
  const items = buildItems(
    'capacity',
    capacityForm.mode,
    Number(capacityForm.value || 0),
    capacityForm.bases,
    [''],
    resolveProductsByModelAndPackage(capacityForm.models, capacityForm.packages),
  )
  adjustments.value = [...adjustments.value, ...items]
}

const addPriceAdjustments = () => {
  if (!priceForm.regions.length) {
    message.warning('请至少选择一个区域')
    return
  }
  const productsSelected = resolveProductsByModelAndPackage(priceForm.models, priceForm.packages)
  const items = buildItems('price', priceForm.mode, Number(priceForm.value || 0), [''], priceForm.regions, productsSelected)
  adjustments.value = [...adjustments.value, ...items]
}

const addDemandAdjustments = () => {
  if (!demandForm.regions.length) {
    message.warning('请至少选择一个区域')
    return
  }
  const productsSelected = resolveProductsByModelAndPackage(demandForm.models, demandForm.packages)
  const items = buildItems('demand', demandForm.mode, Number(demandForm.value || 0), [''], demandForm.regions, productsSelected)
  adjustments.value = [...adjustments.value, ...items]
}

const addProdCostAdjustments = () => {
  if (!prodCostForm.bases.length) {
    message.warning('请至少选择一个基地')
    return
  }
  const items = buildItems(
    'prod_cost',
    prodCostForm.mode,
    Number(prodCostForm.value || 0),
    prodCostForm.bases,
    [''],
    resolveProductsByModelAndPackage(prodCostForm.models, prodCostForm.packages),
  )
  adjustments.value = [...adjustments.value, ...items]
}

const addTransportAdjustments = () => {
  if (!transportForm.bases.length || !transportForm.regions.length) {
    message.warning('请至少选择基地与区域')
    return
  }
  const rawValue = Number(transportForm.value || 0)
  const rate = Number(transportDistanceRate.value || 0)
  const solverValue = transportForm.mode === 'abs' ? rawValue * rate : rawValue
  const items = buildItems('transport', transportForm.mode, solverValue, transportForm.bases, transportForm.regions, ['']).map((item: any) => ({
    ...item,
    biz_type: 'distance',
    display_mode: transportForm.mode,
    display_value: rawValue,
    display_unit: transportForm.mode === 'pct' ? '%' : '公里',
  }))
  adjustments.value = [...adjustments.value, ...items]
}

const renderAdj = (adj: any) => {
  if (adj.type === 'transport' && adj.biz_type === 'distance') {
    const modeLabel = adj.display_mode === 'pct' ? '百分比' : '绝对值'
    const sign = Number(adj.display_value) >= 0 ? '+' : ''
    const target = [adj.base ? `基地:${adj.base}` : '', adj.region ? `销售区域:${adj.region}` : ''].filter(Boolean).join(' / ') || '全局'
    const mapped = `${Number(adj.value || 0) >= 0 ? '+' : ''}${Number(adj.value || 0).toFixed(2)}${unitMap.value.transport}`
    return `运距 | ${target} | ${modeLabel} ${sign}${adj.display_value}${adj.display_unit}（折算${mapped}）`
  }
  const unit = adj.mode === 'pct'
    ? '%'
    : (adj.type === 'capacity'
      ? unitMap.value.capacity
      : (adj.type === 'demand' ? unitMap.value.demand : unitMap.value.price))
  const typeLabelMap: Record<string, string> = {
    capacity: '产能',
    price: '售价',
    demand: '需求',
    prod_cost: '成品成本',
    transport: '运输成本',
  }
  const modeLabel = adj.mode === 'pct' ? '百分比' : '绝对值'
  const sign = Number(adj.value) >= 0 ? '+' : ''
  const targetParts = [
    adj.base ? `基地:${adj.base}` : '',
    adj.region ? `销售区域:${adj.region}` : '',
    adj.product ? `规格:${adj.product}` : '',
  ].filter(Boolean)
  const target = targetParts.join(' / ') || '全局'
  return `${typeLabelMap[adj.type] || adj.type} | ${target} | ${modeLabel} ${sign}${adj.value}${unit}`
}

const removeAdj = (idx: number) => {
  adjustments.value.splice(idx, 1)
}
const clearAdjustments = () => {
  adjustments.value = []
}

const runSimulation = async () => {
  if (!adjustments.value.length) {
    message.warning('请先添加调整项')
    return
  }
  running.value = true
  try {
    const res = await optimizerApi.runWhatIf({
      adjustments: adjustments.value,
      decompose: true,
      params_override: buildParamsOverride(),
    })
    const delta = Number(res?.profit_delta || 0)
    const deltaPct = Number(res?.profit_delta_pct || 0)
    const trend = delta >= 0 ? '提升' : '下降'
    const baseRec = String(res?.recommendation || '建议按当前调整组合执行并持续观察区域兑现。')
    const decomposition = Array.isArray(res?.decomposition) ? res.decomposition : []
    const highlights = decomposition.slice(0, 3).map((item: any) => {
      const name = String(item?.factor || item?.label || item?.name || '关键因子')
      const v = Number(item?.delta_profit ?? item?.impact ?? item?.value ?? 0)
      const sign = v >= 0 ? '+' : ''
      return `${name}${sign}${v.toFixed(1)}万元`
    })
    const topAdjustments = adjustments.value.slice(0, 2).map((adj: any) => renderAdj(adj))
    output.conclusion = `预计利润${trend}${Math.abs(delta).toFixed(1)}万元（${Math.abs(deltaPct).toFixed(2)}%），建议按组合方案分步执行。`
    output.actions = [
      topAdjustments[0] ? `优先执行：${topAdjustments[0]}` : '优先执行当前组合中收益贡献最高的调整项',
      topAdjustments[1] ? `第二步执行：${topAdjustments[1]}` : baseRec,
    ]
    output.risk = delta < 0
      ? '当前组合存在利润下行风险，建议缩小调幅并先小范围试运行。'
      : '需关注区域兑现和执行节奏，建议按周复盘并动态校正。'
    output.profit = `${res?.profit_delta >= 0 ? '+' : ''}${res?.profit_delta || 0} 万元（${res?.profit_delta_pct || 0}%）`
    output.status = res?.new_solve_status || '-'
    output.source = 'What-If计算引擎（后续可接入Agent建议）'
    output.generatedAt = new Date().toLocaleString()
    output.highlights = highlights
    showReportModal.value = false
    message.success('模拟运行完成')
  } finally {
    running.value = false
  }
}

const exportSuggestion = () => {
  if (!hasReport.value) return
  const lines = [
    `建议来源：${output.source}`,
    `生成时间：${output.generatedAt}`,
    `结论：${output.conclusion}`,
    `动作一：${output.actions[0] || '-'}`,
    `动作二：${output.actions[1] || '-'}`,
    `风险提示：${output.risk}`,
    `利润变化：${output.profit}`,
    `求解状态：${output.status}`,
    ...(output.highlights.length ? ['', '关键影响：', ...output.highlights.map((h, i) => `${i + 1}. ${h}`)] : []),
    '',
    '调整项：',
    ...adjustments.value.map((adj, idx) => `${idx + 1}. ${renderAdj(adj)}`),
  ]
  const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `模拟建议_${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const loadParams = async () => {
  paramsLoading.value = true
  try {
    const params = await optimizerApi.getParams()
    bases.value = params?.bases || []
    regions.value = appStore.regionOptions?.length ? [...appStore.regionOptions] : (params?.regions || [])
    products.value = params?.products || ['散装', '袋装']
    unitMap.value = {
      capacity: params?.unit_map?.capacity || '万吨',
      demand: params?.unit_map?.demand || '万吨',
      price: params?.unit_map?.price || '元/吨',
      prod_cost: params?.unit_map?.prod_cost || '元/吨',
      transport: params?.unit_map?.transport || '元/吨',
    }
    const toProductRow = (name: string, values: Record<string, number>) => {
      const row: any = { key: name, name }
      products.value.forEach((product: string, idx: number) => {
        row[`p_${idx}`] = Number(values?.[product] || 0)
      })
      return row
    }
    capacityRows.value = bases.value.map((base: string) => toProductRow(base, params?.capacity?.[base] || {}))
    demandRows.value = regions.value.map((region: string) => toProductRow(region, params?.demand?.[region] || {}))
    priceRows.value = regions.value.map((region: string) => toProductRow(region, params?.price?.[region] || {}))
    prodCostRows.value = bases.value.map((base: string) => toProductRow(base, params?.prod_cost?.[base] || {}))
    transportRows.value = []
    for (const base of bases.value) {
      for (const region of regions.value) {
        transportRows.value.push({
          key: `${base}_${region}`,
          base,
          region,
          cost: Number(params?.transport_cost?.[base]?.[region] || 0),
        })
      }
    }
    settingRows.value = [
      { name: '袋装运输附加', value: Number(params?.bag_transport_premium || 0), desc: unitMap.value.transport },
      { name: '库存持有成本', value: Number(params?.holding_cost || 0), desc: `${unitMap.value.price}·月` },
      { name: '总基地数', value: bases.value.length, desc: '个' },
      { name: '总区域数', value: regions.value.length, desc: '个' },
      { name: '总品种数', value: products.value.length, desc: '类' },
    ]
  } finally {
    paramsLoading.value = false
  }
}

const loadModelAndPackageOptions = async () => {
  try {
    const res = await queryApi.getSales({ period: 'month', point: '2025-12' })
    const items = Array.isArray(res?.items) ? res.items : []
    const modelSet = new Set<string>()
    const packageSet = new Set<string>()
    const pairs: Array<{ model: string, package: string, product: string }> = []
    const normalizeModel = (v: any) => {
      const text = String(v || '').trim()
      return text || '熟料'
    }
    const normalizePackage = (v: any) => {
      const text = String(v || '').trim()
      if (text.includes('熟料')) return '熟料'
      if (text.includes('袋')) return '袋'
      return '散'
    }
    items.forEach((it: any) => {
      const model = normalizeModel(it?.spec || it?.model)
      const pkg = normalizePackage(it?.package)
      const product = pkg === '袋' ? '袋装' : '散装'
      modelSet.add(model)
      packageSet.add(pkg)
      pairs.push({ model, package: pkg, product })
    })
    modelOptions.value = [...modelSet]
    packageOptions.value = [...packageSet]
    modelPackageItems.value = pairs
  } catch {
    modelOptions.value = ['P.O42.5', 'P.C42.5', '熟料']
    packageOptions.value = ['散', '袋', '熟料']
    modelPackageItems.value = [
      { model: 'P.O42.5', package: '散', product: '散装' },
      { model: 'P.O42.5', package: '袋', product: '袋装' },
      { model: 'P.C42.5', package: '散', product: '散装' },
      { model: 'P.C42.5', package: '袋', product: '袋装' },
      { model: '熟料', package: '熟料', product: '散装' },
    ]
  }
}

onMounted(async () => {
  await Promise.all([loadParams(), loadModelAndPackageOptions()])
})
</script>

<style scoped>
.sim-tabs :deep(.ant-tabs-nav-list) {
  display: flex;
  column-gap: 20px;
}

.sim-tabs :deep(.ant-tabs-tab) {
  order: 2;
  margin: 0 !important;
  padding-inline: 2px;
}

.sim-tabs :deep(.ant-tabs-tab:nth-child(2)) {
  order: 1;
}

.factor-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(220px, 1fr));
  gap: 10px;
  margin-bottom: 10px;
}

.field-row {
  display: grid;
  grid-template-columns: 64px 1fr;
  align-items: center;
  gap: 5px;
}

.field-label {
  font-size: 12px;
  color: #4e5969;
  text-align: right;
  line-height: 1.2;
}

.field-tip {
  font-size: 12px;
  color: #86909c;
  margin-left: 69px;
  line-height: 1.2;
  margin-top: 0;
}

.factor-grid :deep(.ant-card-head) {
  min-height: 42px;
}

.factor-grid :deep(.ant-card-head-title) {
  padding: 10px 0;
}

.factor-grid :deep(.ant-card) {
  height: 100%;
}

.factor-grid :deep(.ant-card-body) {
  height: calc(100% - 42px);
  padding: 10px 12px;
}

.factor-form {
  display: flex;
  flex-direction: column;
  width: 100%;
  min-height: 100%;
}

.factor-action {
  margin-top: auto;
  padding-top: 8px;
  width: 100%;
  display: flex;
  justify-content: flex-end;
}

.factor-grid :deep(.ant-select-selector),
.factor-grid :deep(.ant-input-number),
.factor-grid :deep(.ant-input-number-input-wrap input) {
  min-height: 30px;
  height: 30px;
}

.factor-grid :deep(.ant-select-selection-item),
.factor-grid :deep(.ant-select-selection-placeholder),
.factor-grid :deep(.ant-input-number-input) {
  line-height: 28px !important;
}

.factor-grid :deep(.ant-btn) {
  height: 30px;
  padding: 0 12px;
}

.report-main {
  font-size: 14px;
  color: #1d2129;
  line-height: 1.8;
  margin-top: 8px;
  padding: 12px;
  border-radius: 8px;
  background: linear-gradient(135deg, #f7faff 0%, #f2f9ff 100%);
  border: 1px solid #d9ecff;
}

.report-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.report-time {
  color: #86909c;
  font-size: 12px;
}

.report-highlights {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.report-row {
  margin-top: 8px;
  display: flex;
  gap: 12px;
  color: #4e5969;
}

.report-row span:first-child {
  width: 72px;
  color: #86909c;
}

.report-meta {
  margin-top: 8px;
  color: #4e5969;
}

.report-source {
  margin-top: 6px;
  color: #86909c;
  font-size: 12px;
}

.adj-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px dashed #f0f0f0;
}
</style>
