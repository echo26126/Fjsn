<template>
  <div class="page-container">
    <div class="page-header">
      <span class="page-title">销售管理</span>
      <a-space>
        <a-button size="small"><DownloadOutlined /> 导出</a-button>
      </a-space>
    </div>

    <div class="card-grid card-grid-2" style="margin-bottom: 16px">
      <a-card :bordered="false" title="销售矩阵热力图">
        <div ref="heatmapRef" style="height: 320px"></div>
      </a-card>
      <a-card :bordered="false" title="量价联动趋势">
        <div ref="priceVolRef" style="height: 320px"></div>
      </a-card>
    </div>

    <div class="card-grid card-grid-2" style="margin-bottom: 16px">
      <a-card :bordered="false" title="区域销售排名">
        <div ref="rankRef" style="height: 280px"></div>
      </a-card>
      <a-card :bordered="false" title="规格结构指标">
        <div ref="packageRef" style="height: 280px"></div>
      </a-card>
    </div>

    <a-card :bordered="false" title="区域地市明细" style="margin-bottom: 16px">
      <div v-if="regionDrill !== 'all'" class="drill-tip">
        <span>已按区域穿透：{{ compactRegionName(regionDrill) }}</span>
        <a-button size="small" type="link" @click="clearRegionDrill">清除</a-button>
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

const fetchData = async () => {
  try {
    const res = await queryApi.getSales({
      base: selectedBase.value === 'all' ? undefined : selectedBase.value,
      region: selectedRegion.value === 'all' ? undefined : selectedRegion.value
    })
    if (res && res.items) {
      salesItems.value = res.items
    }
    if (res && res.price_trend) {
      priceTrend.value = res.price_trend
    }
    initCharts()
  } catch (e) {
    console.error(e)
  }
}

const heatmapRef = ref<HTMLElement>()
const priceVolRef = ref<HTMLElement>()
const rankRef = ref<HTMLElement>()
const packageRef = ref<HTMLElement>()
let charts: echarts.ECharts[] = []
const regionDrill = ref('all')

const columns = [
  { title: '基地', dataIndex: 'base', width: 80 },
  { title: '区域', dataIndex: 'region', width: 90 },
  { title: '地市', dataIndex: 'city', width: 80 },
  { title: '客户', dataIndex: 'customer', width: 110 },
  { title: '型号', dataIndex: 'spec', width: 100 },
  { title: '袋/散', dataIndex: 'package', width: 70 },
  { title: '出库量(万吨)', dataIndex: 'qty', width: 120 },
  { title: '均价(元/吨)', dataIndex: 'price', width: 110 },
  { title: '金额(万元)', dataIndex: 'amount', width: 110 },
]
const regionColumns = [
  { title: '区域', dataIndex: 'region', width: 90 },
  { title: '地市', dataIndex: 'city', width: 80 },
  { title: '客户', dataIndex: 'customer', width: 110 },
  { title: '出库量(万吨)', dataIndex: 'qty', width: 120 },
  { title: '均价(元/吨)', dataIndex: 'price', width: 110 },
  { title: '金额(万元)', dataIndex: 'amount', width: 110 },
]

const tableData = computed(() => {
  const fullData = salesItems.value.map((item, i) => ({
    key: i,
    base: item.base,
    region: item.region,
    city: item.region.replace('区域', '市'), // Mock mapping
    customer: `${item.region.substring(0, 2)}客户${i}`, // Mock mapping
    spec: item.spec,
    package: item.package,
    qty: item.qty,
    price: item.avg_price,
    amount: item.amount
  }))
  if (regionDrill.value === 'all') return fullData
  return fullData.filter(item => item.region === regionDrill.value)
})

const regionDetailData = computed(() => {
  return tableData.value
})

const regionTotals = computed(() => {
  const totals = new Map<string, number>()
  salesItems.value.forEach(item => {
    totals.set(item.region, (totals.get(item.region) || 0) + item.qty)
  })
  return Array.from(totals.entries()).map(([name, value]) => ({ name, value }))
})

const compactRegionName = (name: string) =>
  name.replace('销售区域', '').replace('区域', '').replace('销售部', '').trim()

const formatPeriodLabel = (raw: string) => {
  if (/^\d{4}-\d{2}$/.test(raw)) {
    return `${Number(raw.slice(5, 7))}月`
  }
  if (/^\d{4}$/.test(raw)) {
    return `${raw}年`
  }
  return raw
}

function clearRegionDrill() {
  regionDrill.value = 'all'
}

function initCharts() {
  charts.forEach(c => c.dispose())
  charts = []
  const isDark = appStore.theme === 'dark'
  const axisColor = isDark ? '#b8c0cc' : '#4f5b6b'
  const splitLineColor = isDark ? '#2a2f3a' : '#e7ebf0'
  
  if (heatmapRef.value) {
    const c = echarts.init(heatmapRef.value)
    charts.push(c)
    const bases = Array.from(new Set(salesItems.value.map(item => item.base)))
    const regions = Array.from(new Set(salesItems.value.map(item => item.region)))
    const matrixMap = new Map<string, { qty: number; amount: number; priceTotal: number; count: number }>()
    salesItems.value.forEach(item => {
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
      return {
        value: [regions.indexOf(region), bases.indexOf(base), +val.qty.toFixed(2)],
        base,
        region,
        amount: +val.amount.toFixed(2),
        avgPrice: +(val.priceTotal / Math.max(1, val.count)).toFixed(0),
      }
    })
    c.setOption({
      tooltip: {
        formatter: (p: any) => `${p.data.base} → ${p.data.region}<br/>销量：${p.value[2]} 万吨<br/>均价：${p.data.avgPrice} 元/吨<br/>金额：${p.data.amount} 万元`
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
        max: Math.max(1, ...matrix.map(row => row.value[2])),
        textStyle: { color: axisColor },
        inRange: { color: isDark ? ['#142240', '#1f4fa8', '#2b78ff'] : ['#e6f2ff', '#9ac8ff', '#2b78ff'] },
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
          formatter: (p: any) => p.value[2],
          color: (p: any) => (p.value[2] > Math.max(1, ...matrix.map(row => row.value[2])) * 0.55 ? '#ffffff' : (isDark ? '#d5e6ff' : '#1b3f7f')),
          fontWeight: 600
        },
        itemStyle: {
          borderColor: isDark ? '#1f2e4c' : '#ffffff',
          borderWidth: 1
        },
        emphasis: { itemStyle: { shadowBlur: 12, shadowColor: isDark ? 'rgba(43,120,255,0.55)' : 'rgba(43,120,255,0.35)' } }
      }]
    })
    c.off('click')
    c.on('click', (params: any) => {
      const regionName = params?.data?.region
      const baseName = params?.data?.base
      if (!regionName) return
      regionDrill.value = regionName
      selectedRegion.value = regionName
      if (baseName) selectedBase.value = baseName
    })
  }

  if (priceVolRef.value) {
    const c = echarts.init(priceVolRef.value)
    charts.push(c)
    c.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['出库量', '均价'], textStyle: { fontSize: 11 } },
      grid: { top: 35, right: 60, bottom: 30, left: 50 },
      xAxis: { type: 'category', data: (priceTrend.value.months || []).map(formatPeriodLabel) },
      yAxis: [
        { type: 'value', name: '万吨', axisLabel: { fontSize: 10 } },
        { type: 'value', name: '元/吨', axisLabel: { fontSize: 10 } }
      ],
      series: [
        { name: '出库量', type: 'bar', data: priceTrend.value.qty, itemStyle: { color: '#1677ff', borderRadius: [4, 4, 0, 0] } },
        { name: '均价', type: 'line', yAxisIndex: 1, data: priceTrend.value.avg_price, smooth: true, lineStyle: { color: '#faad14' }, itemStyle: { color: '#faad14' } }
      ]
    })
  }

  if (rankRef.value) {
    const c = echarts.init(rankRef.value)
    charts.push(c)
    const sorted = [...regionTotals.value].sort((a, b) => b.value - a.value)
    c.setOption({
      tooltip: { trigger: 'axis' },
      grid: { top: 10, right: 20, bottom: 30, left: 60 },
      xAxis: { type: 'value', name: '万吨' },
      yAxis: { type: 'category', data: sorted.map(r => compactRegionName(r.name)), axisLabel: { fontSize: 11 } },
      series: [{
        type: 'bar',
        data: sorted.map(r => ({
          value: r.value,
          itemStyle: { color: regionColors[r.name] || '#1f6fff', borderRadius: [0, 4, 4, 0] }
        }))
      }]
    })
    c.off('click')
    c.on('click', (params: any) => {
      const regionName = sorted[params?.dataIndex || 0]?.name
      if (!regionName) return
      regionDrill.value = regionName
      selectedRegion.value = regionName
    })
  }

  if (packageRef.value) {
    const c = echarts.init(packageRef.value)
    charts.push(c)
    const specMap = new Map<string, { qty: number; bagQty: number }>()
    salesItems.value.forEach(item => {
      const key = item.spec || '未分类'
      if (!specMap.has(key)) {
        specMap.set(key, { qty: 0, bagQty: 0 })
      }
      const hit = specMap.get(key)!
      hit.qty += Number(item.qty || 0)
      if (item.package === '袋装') {
        hit.bagQty += Number(item.qty || 0)
      }
    })
    const specs = Array.from(specMap.keys())
    const qtySeries = specs.map(name => +(specMap.get(name)?.qty || 0).toFixed(2))
    const bagRatioSeries = specs.map(name => {
      const hit = specMap.get(name)!
      return hit.qty ? +((hit.bagQty / hit.qty) * 100).toFixed(1) : 0
    })
    
    c.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['销量', '袋装占比'], bottom: 0, textStyle: { fontSize: 11 } },
      grid: { top: 22, right: 45, bottom: 42, left: 50 },
      xAxis: { type: 'category', data: specs, axisLabel: { fontSize: 10, rotate: 12 } },
      yAxis: [
        { type: 'value', name: '万吨' },
        { type: 'value', name: '%', min: 0, max: 100 }
      ],
      series: [
        {
          name: '销量',
          type: 'bar',
          data: qtySeries,
          barMaxWidth: 34,
          itemStyle: {
            color: isDark ? '#2b78ff' : '#3D5898',
            borderRadius: [6, 6, 0, 0],
            shadowBlur: isDark ? 8 : 0,
            shadowColor: isDark ? 'rgba(43,120,255,0.45)' : 'transparent'
          }
        },
        {
          name: '袋装占比',
          type: 'line',
          yAxisIndex: 1,
          smooth: true,
          data: bagRatioSeries,
          lineStyle: { color: isDark ? '#7fb6ff' : '#6B8FE8', width: 2 },
          itemStyle: { color: isDark ? '#7fb6ff' : '#6B8FE8' },
          areaStyle: { color: isDark ? 'rgba(127,182,255,0.14)' : 'rgba(107,143,232,0.12)' }
        },
      ]
    })
  }
}

const handleResize = () => charts.forEach(c => c.resize())
onMounted(() => { 
  fetchData()
  window.addEventListener('resize', handleResize) 
})
watch([() => appStore.queryNonce, () => appStore.timePoint], () => { fetchData() })
watch([() => appStore.timeMode, () => appStore.dateRange], () => { fetchData() }, { deep: true })
watch(() => appStore.theme, () => { initCharts() })
onUnmounted(() => { window.removeEventListener('resize', handleResize); charts.forEach(c => c.dispose()) })
</script>

<style scoped>
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
