<template>
  <div class="page-container">
    <div class="page-header">
      <span class="page-title">销售管理</span>
      <a-space>
        <a-button size="small"><DownloadOutlined /> 导出</a-button>
      </a-space>
    </div>

    <div class="sales-switch-row">
      <a-space size="small" wrap>
        <a-tag color="blue">{{ layerPeriodLabel }}</a-tag>
        <span class="switch-label">基地</span>
        <a-select v-model:value="selectedBase" size="small" style="width: 150px">
          <a-select-option value="all">全部基地</a-select-option>
          <a-select-option v-for="item in appStore.baseOptions" :key="item" :value="item">{{ item }}</a-select-option>
        </a-select>
        <span class="switch-label">区域</span>
        <a-select v-model:value="selectedRegion" size="small" style="width: 150px">
          <a-select-option value="all">全部区域</a-select-option>
          <a-select-option v-for="item in appStore.regionOptions" :key="item" :value="item">{{ item }}</a-select-option>
        </a-select>
        <span class="switch-label">型号</span>
        <a-select
          v-model:value="selectedModel"
          size="small"
          style="width: 180px"
          show-search
          :filter-option="filterModelOption"
        >
          <a-select-option value="all">全部型号</a-select-option>
          <a-select-option v-for="item in modelOptions" :key="item" :value="item">{{ item }}</a-select-option>
        </a-select>
        <span class="switch-label">规格</span>
        <a-radio-group v-model:value="selectedPackage" size="small" button-style="solid">
          <a-radio-button value="all" :disabled="selectedModel === '熟料'">全部</a-radio-button>
          <a-radio-button value="袋" :disabled="selectedModel === '熟料'">袋</a-radio-button>
          <a-radio-button value="散" :disabled="selectedModel === '熟料'">散</a-radio-button>
          <a-radio-button value="熟料">熟料</a-radio-button>
        </a-radio-group>
        <span class="switch-label">穿透区域</span>
        <a-select v-model:value="trendRegion" size="small" style="width: 130px">
          <a-select-option value="all">全部区域</a-select-option>
          <a-select-option v-for="item in trendRegionOptions" :key="item" :value="item">{{ compactRegionName(item) }}</a-select-option>
        </a-select>
      </a-space>
    </div>

    <div class="card-grid card-grid-2" style="margin-bottom: 16px">
      <a-card :bordered="false" title="销售矩阵热力图">
        <div class="chart-toolbar chart-toolbar-space">
          <a-radio-group v-model:value="heatmapMetric" size="small" button-style="solid">
            <a-radio-button value="qty">按量</a-radio-button>
            <a-radio-button value="avgPrice">按价</a-radio-button>
          </a-radio-group>
        </div>
        <div ref="heatmapRef" style="height: 320px"></div>
      </a-card>
      <a-card :bordered="false" title="基地-区域流向图">
        <div class="chart-toolbar chart-toolbar-space">
          <a-radio-group v-model:value="flowMetric" size="small" button-style="solid">
            <a-radio-button value="qty">按量</a-radio-button>
            <a-radio-button value="amount">按金额</a-radio-button>
          </a-radio-group>
        </div>
        <div ref="flowRef" style="height: 320px"></div>
      </a-card>
    </div>

    <div class="card-grid card-grid-2" style="margin-bottom: 16px">
      <a-card :bordered="false" title="区域销售排名">
        <div class="chart-toolbar chart-toolbar-space">
          <a-radio-group v-model:value="rankMetric" size="small" button-style="solid">
            <a-radio-button value="qty">总量排行</a-radio-button>
            <a-radio-button value="amount">总价排行</a-radio-button>
          </a-radio-group>
        </div>
        <div ref="rankRef" style="height: 320px"></div>
      </a-card>
      <a-card :bordered="false" title="销售客户类型占比">
        <div class="chart-toolbar chart-toolbar-space">
          <a-radio-group v-model:value="mixMetric" size="small" button-style="solid">
            <a-radio-button value="qty">按总量</a-radio-button>
            <a-radio-button value="amount">按总价</a-radio-button>
          </a-radio-group>
        </div>
        <div ref="priceVolRef" style="height: 280px"></div>
      </a-card>
    </div>

    <a-card :bordered="false" title="区域地市明细" style="margin-bottom: 16px">
      <div class="drill-tip">
        <a-space size="small" wrap>
          <a-tag color="blue">区域：{{ regionDrill === 'all' ? '全部区域' : compactRegionName(regionDrill) }}</a-tag>
          <a-tag color="purple">客户类型：{{ customerTypeDrill === 'all' ? '全部类型' : customerTypeDrill }}</a-tag>
          <span class="switch-label">客户类型穿透</span>
          <a-select v-model:value="customerTypeDrill" size="small" style="width: 180px">
            <a-select-option value="all">全部类型</a-select-option>
            <a-select-option v-for="item in customerTypeDrillOptions" :key="item" :value="item">{{ item }}</a-select-option>
          </a-select>
        </a-space>
        <a-space size="small">
          <a-button size="small" type="link" @click="clearCustomerTypeDrill">清除类型</a-button>
          <a-button size="small" type="link" @click="clearRegionDrill">清除区域</a-button>
        </a-space>
      </div>
      <a-table :columns="regionColumns" :data-source="regionDetailData" size="small" :pagination="{ pageSize: 8 }" />
    </a-card>

    <a-card :bordered="false" title="销售明细">
      <a-table :columns="columns" :data-source="tableData" size="small" :pagination="{ pageSize: 10 }" />
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import * as echarts from 'echarts'
import { DownloadOutlined } from '@ant-design/icons-vue'
import { useAppStore } from '@/stores/app'
import { queryApi } from '@/api'
import dayjs from 'dayjs'

const appStore = useAppStore()
const selectedBase = computed({
  get: () => appStore.selectedBase,
  set: (val: string) => { appStore.selectedBase = val }
})
const selectedRegion = computed({
  get: () => appStore.selectedRegion,
  set: (val: string) => { appStore.selectedRegion = val }
})
const regionColors: Record<string, string> = {
  '安砂销售部': '#3D5898',
  '福州北销售区域': '#6B8FE8',
  '福州南销售区域': '#4C73C9',
  '南平销售区域': '#3D5898',
  '宁德销售区域': '#6B8FE8',
  '莆田销售区域': '#4C73C9',
  '泉州销售区域': '#6B8FE8',
  '三明销售区域': '#3D5898',
  '厦漳销售区域': '#FF9D4D',
  '厦漳区域': '#FF9D4D',
}

// API Data
const salesItems = ref<any[]>([])
const priceTrend = ref<any>({ months: [], qty: [], avg_price: [] })
const modelStats = ref<Array<{ model: string; count: number }>>([])
const customerMix = ref<any>({ by_type: [], by_region_type: [] })

const fetchData = async () => {
  try {
    const sourcePoint = appStore.timeMode === 'year' ? `${appStore.timePoint}-12` : (appStore.timeMode === 'range' ? '2025-12' : appStore.timePoint)
    const resolvedPoint = String(sourcePoint).startsWith('2025-12') ? '2025-12' : '2025-12'
    const res = await queryApi.getSales({
      period: appStore.timeMode,
      point: resolvedPoint,
      base: selectedBase.value === 'all' ? undefined : selectedBase.value,
      region: selectedRegion.value === 'all' ? undefined : selectedRegion.value,
    })
    if (res && res.items) {
      salesItems.value = res.items
    }
    if (res && res.price_trend) {
      priceTrend.value = res.price_trend
    }
    if (res && Array.isArray(res.model_stats)) {
      modelStats.value = res.model_stats
    }
    if (res && res.customer_mix) {
      customerMix.value = res.customer_mix
    } else {
      customerMix.value = { by_type: [], by_region_type: [] }
    }
    renderAllCharts()
  } catch (e) {
    console.error(e)
  }
}

const heatmapRef = ref<HTMLElement>()
const flowRef = ref<HTMLElement>()
const priceVolRef = ref<HTMLElement>()
const rankRef = ref<HTMLElement>()
let heatmapChart: echarts.ECharts | null = null
let flowChart: echarts.ECharts | null = null
let trendChart: echarts.ECharts | null = null
let rankChart: echarts.ECharts | null = null
const regionDrill = ref('all')
const customerTypeDrill = ref('all')
const trendRegion = ref('all')
const selectedModel = ref('all')
const selectedPackage = ref<'all' | '袋' | '散' | '熟料'>('all')
const rankMetric = ref<'qty' | 'amount'>('qty')
const heatmapMetric = ref<'qty' | 'avgPrice'>('qty')
const flowMetric = ref<'qty' | 'amount'>('qty')
const mixMetric = ref<'qty' | 'amount'>('qty')

const columns = [
  { title: '库存组织', dataIndex: 'inventoryOrg', width: 130 },
  { title: '基地', dataIndex: 'base', width: 80 },
  { title: '区域', dataIndex: 'region', width: 90 },
  { title: '地市', dataIndex: 'city', width: 80 },
  { title: '客户', dataIndex: 'customer', width: 110 },
  { title: '客户类型', dataIndex: 'customerType', width: 110 },
  { title: '物料名称', dataIndex: 'materialName', width: 150 },
  { title: '型号', dataIndex: 'model', width: 90 },
  { title: '规格', dataIndex: 'package', width: 70 },
  { title: '出库量(万吨)', dataIndex: 'qty', width: 120 },
  { title: '均价(元/吨)', dataIndex: 'price', width: 110 },
  { title: '金额(万元)', dataIndex: 'amount', width: 110 },
]
const regionColumns = [
  { title: '库存组织', dataIndex: 'inventoryOrg', width: 130 },
  { title: '区域', dataIndex: 'region', width: 90 },
  { title: '地市', dataIndex: 'city', width: 80 },
  { title: '客户', dataIndex: 'customer', width: 110 },
  { title: '客户类型', dataIndex: 'customerType', width: 110 },
  { title: '出库量(万吨)', dataIndex: 'qty', width: 120 },
  { title: '均价(元/吨)', dataIndex: 'price', width: 110 },
  { title: '金额(万元)', dataIndex: 'amount', width: 110 },
]

const normalizedRows = computed(() => {
  return filteredCommonItems.value.map((item, i) => ({
    key: i,
    inventoryOrg: item.inventory_org || item.base,
    base: item.base,
    region: item.region,
    city: item.destination || item.region_layer || '',
    customer: item.order_customer || item.invoice_customer || '',
    customerType: item.customer_type || '',
    materialName: item.material_name || item.spec,
    model: normalizeModel(item.spec, item.material_name),
    package: normalizePackage(item.package, item.material_name, item.spec),
    qty: item.qty,
    price: item.avg_price,
    amount: item.amount
  }))
})

const regionScopedRows = computed(() => {
  if (regionDrill.value === 'all') return normalizedRows.value
  return normalizedRows.value.filter(item => item.region === regionDrill.value)
})

const customerTypeDrillOptions = computed(() =>
  Array.from(new Set(regionScopedRows.value.map(item => item.customerType).filter(Boolean)))
)

const drilledRows = computed(() => {
  const source = regionScopedRows.value
  if (customerTypeDrill.value === 'all') return source
  return source.filter(item => item.customerType === customerTypeDrill.value)
})

const tableData = computed(() => drilledRows.value)

const regionDetailData = computed(() => {
  return drilledRows.value
})

const modelOptions = computed(() => {
  if (modelStats.value.length) {
    return modelStats.value.map(item => item.model)
  }
  const map = new Map<string, number>()
  salesItems.value.forEach(item => {
    const model = normalizeModel(item.spec, item.material_name)
    map.set(model, (map.get(model) || 0) + 1)
  })
  return Array.from(map.keys())
})

const trendRegionOptions = computed(() =>
  Array.from(new Set(filteredCommonItems.value.map(item => item.region).filter(Boolean)))
)

const layerPeriodLabel = computed(() => {
  if (appStore.timeMode === 'year') return `${appStore.timePoint}年`
  if (appStore.timeMode === 'range') {
    const [start, end] = appStore.dateRange
    return `${dayjs(start).format('YYYY年M月D日')} - ${dayjs(end).format('M月D日')}`
  }
  return `${dayjs(`${appStore.timePoint}-01`).format('YYYY年M月')}`
})

const filteredCommonItems = computed(() => {
  return salesItems.value.filter(item => {
    const basePass = selectedBase.value === 'all' || item.base === selectedBase.value
    const regionPass = selectedRegion.value === 'all' || item.region === selectedRegion.value
    const model = normalizeModel(item.spec, item.material_name)
    const pkg = normalizePackage(item.package, item.material_name, item.spec)
    const modelPass = selectedModel.value === 'all' || model === selectedModel.value
    const packagePass = selectedPackage.value === 'all' || pkg === selectedPackage.value
    return basePass && regionPass && modelPass && packagePass
  })
})

const regionTotals = computed(() => {
  const totals = new Map<string, { qty: number; amount: number }>()
  filteredCommonItems.value.forEach(item => {
    if (!totals.has(item.region)) totals.set(item.region, { qty: 0, amount: 0 })
    const hit = totals.get(item.region)!
    hit.qty += Number(item.qty || 0)
    hit.amount += Number(item.amount || 0)
  })
  return Array.from(totals.entries()).map(([name, value]) => ({
    name,
    qty: +value.qty.toFixed(2),
    amount: +value.amount.toFixed(2),
  }))
})

const compactRegionName = (name: string) =>
  name.replace('销售区域', '').replace('区域', '').replace('销售部', '').trim()

const filterModelOption = (input: string, option: any) => {
  const text = String(option?.value || '')
  return text.toLowerCase().includes(input.toLowerCase())
}

const normalizeModel = (spec: string, materialName?: string) => {
  const model = String(spec || '').trim()
  if (model) return model
  return '熟料'
}

const normalizePackage = (pkg: string, materialName?: string, spec?: string) => {
  const text = String(pkg || '').trim()
  if (text.includes('熟料')) return '熟料'
  if (text.includes('袋')) return '袋'
  if (text.includes('散')) return '散'
  const model = String(spec || '').trim()
  if (!model || String(materialName || '').includes('熟料')) return '熟料'
  return ''
}

function clearRegionDrill() {
  selectedRegion.value = 'all'
  regionDrill.value = 'all'
  customerTypeDrill.value = 'all'
}

function clearCustomerTypeDrill() {
  customerTypeDrill.value = 'all'
}

function applyRegionDrill(regionName: string) {
  if (!regionName) return
  regionDrill.value = regionName
  customerTypeDrill.value = 'all'
  selectedRegion.value = regionName
}

function renderHeatmapChart() {
  const isDark = appStore.theme === 'dark'
  const axisColor = isDark ? '#b8c0cc' : '#4f5b6b'
  const splitLineColor = isDark ? '#2a2f3a' : '#e7ebf0'
  if (!heatmapRef.value) return
  if (!heatmapChart) heatmapChart = echarts.init(heatmapRef.value)
  const sourceRows = trendRegion.value === 'all'
    ? filteredCommonItems.value
    : filteredCommonItems.value.filter(item => item.region === trendRegion.value)
  const bases = Array.from(new Set(sourceRows.map(item => item.base)))
  const regions = Array.from(new Set(sourceRows.map(item => item.region)))
  const matrixMap = new Map<string, { qty: number; amount: number; priceTotal: number; count: number }>()
  sourceRows.forEach(item => {
    const key = `${item.base}__${item.region}`
    const hit = matrixMap.get(key) || { qty: 0, amount: 0, priceTotal: 0, count: 0 }
    hit.qty += Number(item.qty || 0)
    hit.amount += Number(item.amount || 0)
    hit.priceTotal += Number(item.avg_price || 0)
    hit.count += 1
    matrixMap.set(key, hit)
  })
  const matrix = Array.from(matrixMap.entries()).map(([key, val]) => {
    const [base, region] = key.split('__')
    const qty = +val.qty.toFixed(2)
    const avgPrice = +(val.priceTotal / Math.max(1, val.count)).toFixed(0)
    return {
      value: [regions.indexOf(region), bases.indexOf(base), heatmapMetric.value === 'qty' ? qty : avgPrice],
      base,
      region,
      qty,
      amount: +val.amount.toFixed(2),
      avgPrice,
    }
  })
  const metricLabel = heatmapMetric.value === 'qty' ? '销量' : '均价'
  const metricUnit = heatmapMetric.value === 'qty' ? '万吨' : '元/吨'
  const visualMax = Math.max(1, ...matrix.map(row => Number(row.value[2]) || 0))
  const lightPalette = heatmapMetric.value === 'qty'
    ? ['#d9ebff', '#78b1ff', '#2a79ff', '#0d56d9']
    : ['#e7e9ff', '#9aa5ff', '#5f6ff0', '#3348d1']
  const darkPalette = heatmapMetric.value === 'qty'
    ? ['#163259', '#245eb0', '#2a79ff', '#5ba0ff']
    : ['#2a2f4f', '#4a56b8', '#6e79ff', '#96a3ff']
  heatmapChart.setOption({
    tooltip: {
      formatter: (p: any) => `${p.data.base} → ${p.data.region}<br/>销量：${p.data.qty} 万吨<br/>均价：${p.data.avgPrice} 元/吨<br/>金额：${p.data.amount} 万元`
    },
    grid: { top: 20, right: 54, bottom: 38, left: 82 },
    xAxis: {
      type: 'category',
      data: regions.map(name => compactRegionName(name)),
      axisLabel: { rotate: 18, fontSize: 10, color: axisColor },
      axisLine: { lineStyle: { color: splitLineColor } }
    },
    yAxis: {
      type: 'category',
      data: bases,
      axisLabel: { fontSize: 11, color: axisColor },
      axisLine: { lineStyle: { color: splitLineColor } }
    },
    visualMap: {
      min: 0,
      max: visualMax,
      text: [metricLabel, '低'],
      textStyle: { color: axisColor },
      inRange: { color: isDark ? darkPalette : lightPalette },
      calculable: true,
      orient: 'vertical',
      right: 4,
      top: 'middle',
      itemHeight: 140,
      itemWidth: 10
    },
    series: [{
      type: 'heatmap',
      data: matrix,
      label: {
        show: true,
        formatter: (p: any) => heatmapMetric.value === 'qty'
          ? Number(p.value[2] || 0).toFixed(2)
          : Math.round(Number(p.value[2] || 0)),
        color: '#ffffff',
        fontWeight: 700,
        textBorderColor: 'rgba(0,0,0,0.35)',
        textBorderWidth: 2,
      },
      itemStyle: {
        borderColor: isDark ? '#1f2e4c' : '#ffffff',
        borderWidth: 1
      },
      emphasis: { itemStyle: { shadowBlur: 12, shadowColor: isDark ? 'rgba(43,120,255,0.55)' : 'rgba(43,120,255,0.35)' } }
    }]
  })
  heatmapChart.off('click')
  heatmapChart.on('click', (params: any) => {
    const regionName = params?.data?.region
    if (!regionName) return
    applyRegionDrill(regionName)
  })
}

function renderFlowChart() {
  if (!flowRef.value) return
  if (!flowChart) flowChart = echarts.init(flowRef.value)
  const sourceRows = trendRegion.value === 'all'
    ? filteredCommonItems.value
    : filteredCommonItems.value.filter(item => item.region === trendRegion.value)
  const sourceNodeName = (item: any) => {
    const org = String(item.inventory_org || '').trim()
    if (!org || org === item.base) return String(item.base || '')
    return `${item.base}(${org})`
  }
  const baseNodes = Array.from(new Set(sourceRows.map(item => sourceNodeName(item)).filter(Boolean)))
  const regionNodes = Array.from(new Set(sourceRows.map(item => item.region).filter(Boolean)))
  const linksMap = new Map<string, { source: string; target: string; qty: number; amount: number; inventoryOrg: string; base: string; region: string }>()
  sourceRows.forEach(item => {
    const source = sourceNodeName(item)
    const target = item.region
    if (!source || !target) return
    const key = `${source}__${target}`
    const hit = linksMap.get(key) || {
      source,
      target,
      qty: 0,
      amount: 0,
      inventoryOrg: String(item.inventory_org || item.base || ''),
      base: String(item.base || ''),
      region: String(item.region || ''),
    }
    hit.qty += Number(item.qty || 0)
    hit.amount += Number(item.amount || 0)
    linksMap.set(key, hit)
  })
  const links = Array.from(linksMap.values())
  const linkSeries = links.map(item => ({
    source: item.source,
    target: item.target,
    value: flowMetric.value === 'qty' ? +item.qty.toFixed(2) : +item.amount.toFixed(2),
    qty: +item.qty.toFixed(2),
    amount: +item.amount.toFixed(2),
    inventoryOrg: item.inventoryOrg,
    base: item.base,
    region: item.region,
  }))
  const nodeData = [
    ...baseNodes.map(name => ({ name, nodeType: 'base' })),
    ...regionNodes.map(name => ({ name, nodeType: 'region' })),
  ]
  flowChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: (p: any) => {
        if (p.dataType === 'edge') {
          return `${p.data.base} → ${p.data.region}<br/>库存组织：${p.data.inventoryOrg}<br/>销量：${p.data.qty} 万吨<br/>金额：${p.data.amount} 万元`
        }
        const isRegionNode = regionNodes.includes(p.name)
        return isRegionNode ? `区域：${p.name}` : `基地：${p.name}`
      }
    },
    series: [{
      type: 'sankey',
      layout: 'none',
      data: nodeData,
      links: linkSeries,
      emphasis: { focus: 'adjacency' },
      nodeAlign: 'left',
      lineStyle: { color: 'gradient', curveness: 0.5 },
      itemStyle: { borderWidth: 1, borderColor: '#b8c0cc' },
      label: { fontSize: 11 },
    }]
  })
  flowChart.off('click')
  flowChart.on('click', (params: any) => {
    if (params?.dataType === 'edge' && params?.data?.region) {
      applyRegionDrill(params.data.region)
    }
  })
}

function renderTrendChart() {
  if (!priceVolRef.value) return
  if (!trendChart) trendChart = echarts.init(priceVolRef.value)
  const metric = mixMetric.value
  const rows = trendRegion.value === 'all'
    ? [...(customerMix.value?.by_type || [])]
    : [...(customerMix.value?.by_region_type || [])].filter((item: any) => item.region === trendRegion.value)
  const typeMap = new Map<string, { value: number; ratio: number }>()
  rows.forEach((item: any) => {
    const key = String(item.customer_type || '未分类')
    const value = Number(item[metric] || 0)
    const ratio = Number(
      trendRegion.value === 'all'
        ? (metric === 'qty' ? item.qty_ratio : item.amount_ratio)
        : (metric === 'qty' ? item.region_qty_ratio : item.region_amount_ratio)
    )
    typeMap.set(key, { value, ratio })
  })
  const labels = Array.from(typeMap.keys())
  const values = labels.map(label => Number(typeMap.get(label)?.value || 0))
  const ratios = labels.map(label => Number(typeMap.get(label)?.ratio || 0))
  const unit = metric === 'qty' ? '万吨' : '万元'
  const seriesName = metric === 'qty' ? '总量' : '总价'
  const pieData = labels.map((name, idx) => ({
    name,
    value: Number(values[idx] || 0),
    ratio: Number(ratios[idx] || 0),
  }))
  trendChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: (p: any) => `${p.name}<br/>${seriesName}：${Number(p.value || 0).toFixed(2)} ${unit}<br/>占比：${(Number(p.data?.ratio || 0) * 100).toFixed(2)}%`
    },
    legend: {
      type: 'scroll',
      orient: 'vertical',
      right: 8,
      top: 'middle',
      textStyle: { fontSize: 11 },
    },
    series: [
      {
        name: seriesName,
        type: 'pie',
        radius: ['38%', '68%'],
        center: ['38%', '50%'],
        data: pieData,
        minAngle: 4,
        label: {
          show: true,
          formatter: (p: any) => `${p.name}\n${(Number(p.data?.ratio || 0) * 100).toFixed(1)}%`,
          fontSize: 10,
        },
        labelLine: { length: 10, length2: 8 },
        emphasis: { scale: true, scaleSize: 8 },
      },
    ],
  })
  trendChart.off('click')
  trendChart.on('click', (params: any) => {
    const customerType = String(params?.name || '')
    if (!customerType) return
    customerTypeDrill.value = customerType
    if (trendRegion.value !== 'all') {
      applyRegionDrill(trendRegion.value)
    }
  })
}

function renderRankChart() {
  if (!rankRef.value) return
  if (!rankChart) rankChart = echarts.init(rankRef.value)
  const metric = rankMetric.value
  const sorted = [...regionTotals.value].sort((a, b) => Number(b[metric]) - Number(a[metric]))
  rankChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { top: 10, right: 20, bottom: 30, left: 60 },
    xAxis: { type: 'value', name: metric === 'qty' ? '万吨' : '万元' },
    yAxis: { type: 'category', data: sorted.map(r => compactRegionName(r.name)), axisLabel: { fontSize: 11 } },
    series: [{
      type: 'bar',
      data: sorted.map(r => ({
        value: Number(r[metric]),
        itemStyle: { color: regionColors[r.name] || '#1f6fff', borderRadius: [0, 4, 4, 0] }
      }))
    }]
  })
  rankChart.off('click')
  rankChart.on('click', (params: any) => {
    const regionName = sorted[params?.dataIndex || 0]?.name
    if (!regionName) return
    applyRegionDrill(regionName)
  })
}

function renderAllCharts() {
  renderHeatmapChart()
  renderFlowChart()
  renderRankChart()
  renderTrendChart()
}

const handleResize = () => {
  heatmapChart?.resize()
  flowChart?.resize()
  trendChart?.resize()
  rankChart?.resize()
}
onMounted(() => { 
  fetchData()
  window.addEventListener('resize', handleResize) 
})
watch([() => appStore.queryNonce, () => appStore.timePoint], () => { fetchData() })
watch([() => appStore.timeMode, () => appStore.dateRange], () => { fetchData() }, { deep: true })
watch([selectedBase, selectedRegion], () => { fetchData() })
watch(selectedRegion, (val) => {
  if (val === 'all') {
    regionDrill.value = 'all'
    customerTypeDrill.value = 'all'
  } else {
    regionDrill.value = val
    customerTypeDrill.value = 'all'
  }
})
watch(() => appStore.theme, () => { renderAllCharts() })
watch(selectedModel, (val) => {
  if (val === '熟料' && selectedPackage.value !== '熟料') {
    selectedPackage.value = '熟料'
  }
})
watch([selectedModel, selectedPackage, rankMetric, heatmapMetric, trendRegion, flowMetric, mixMetric], () => { renderAllCharts() })
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  heatmapChart?.dispose()
  flowChart?.dispose()
  trendChart?.dispose()
  rankChart?.dispose()
  heatmapChart = null
  flowChart = null
  trendChart = null
  rankChart = null
})
</script>

<style scoped>
.sales-switch-row {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 10px;
}

.switch-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.chart-toolbar {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.chart-toolbar-space {
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.drill-tip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  padding: 6px 10px;
  border-radius: 6px;
  background: color-mix(in srgb, var(--primary-color) 12%, var(--card-bg));
  color: var(--text-primary);
}
</style>
