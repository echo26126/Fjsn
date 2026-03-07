<template>
  <div class="dashboard">
    <!-- KPI 卡片带 -->
    <KpiStrip :list="kpiList" />

    <!-- 视图切换 -->
    <div class="view-switch">
      <a-radio-group v-model:value="viewMode" button-style="solid" size="small" class="mode-tabs">
        <a-radio-button value="production">生产</a-radio-button>
        <a-radio-button value="sales">销售</a-radio-button>
      </a-radio-group>
      <a-select v-model:value="category" style="width: 140px; margin-left: 12px" size="small">
        <a-select-option v-for="opt in categoryOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </a-select-option>
      </a-select>
    </div>

    <!-- 主体区域：地图 + 右侧面板 -->
    <div class="dashboard-body">
      <div class="map-area">
        <MapChart 
          :view-mode="viewMode" 
          :production-data="productionBaseData"
          :sales-data="salesRegionData"
          :selected-sales-region="selectedSalesRegion"
          :title="viewMode === 'production' ? '福建省生产分布' : '福建省销售分布'" 
          @point-click="handleMapPointClick"
        />
      </div>

      <div class="side-panels">
        <a-card v-if="isDetailMode" :bordered="false" class="detail-panel-card">
          <template #title>
            <div class="detail-header">
              <span>{{ detailPanel.title }}</span>
              <a-button size="small" @click="resetMapSelection">返回总览</a-button>
            </div>
          </template>
          <div class="detail-metrics">
            <div v-for="item in detailPanel.metrics" :key="item.label" class="detail-item">
              <div class="detail-label">{{ item.label }}</div>
              <div class="detail-value">{{ item.value }} {{ item.unit }}</div>
            </div>
          </div>
        </a-card>

        <RankList 
          v-else
          :title="viewMode === 'production' ? '基地产量排行' : '区域销售排行'" 
          :list="rankData"
          unit="万吨"
        />

        <OperationTrendPanel
          :view-mode="viewMode"
          :selected-base="appStore.selectedBase"
          :inventory-rows="productionInventoryRows"
          :daily-inventory="dailyInventoryData"
          :sales-trend="salesTrendData"
          :sales-items="currentSalesRows"
        />
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, markRaw, onMounted, watch } from 'vue'
import dayjs from 'dayjs'
import {
  BarChartOutlined,
  ShoppingCartOutlined,
  DatabaseOutlined,
  FundProjectionScreenOutlined
} from '@ant-design/icons-vue'
import { useAppStore } from '@/stores/app'
import { dashboardApi, queryApi } from '@/api'

import KpiStrip from '@/components/dashboard/KpiStrip.vue'
import MapChart from '@/components/dashboard/MapChart.vue'
import RankList from '@/components/dashboard/RankList.vue'
import OperationTrendPanel from '@/components/dashboard/OperationTrendPanel.vue'

const viewMode = ref<'production' | 'sales'>('production')
const category = ref('all')
const appStore = useAppStore()

// KPI Data
const kpiData = ref<any>({
  production: { value: 0, unit: '万吨', change: 0, percent: 0 },
  sales: { value: 0, unit: '万吨', change: 0, percent: 0 },
  inventory: { value: 0, unit: '万吨', change: 0, percent: 0 },
  balance_index: { value: 0, level: '-', percent: 0 }
})

// Production Data
interface ProductionBase {
  name: string
  coord: number[]
  plan: number
  capacity: number
  actual: number
  utilization: number
  inventory: number
}
const productionBaseData = ref<ProductionBase[]>([])

// Sales Data
interface SalesRegion {
  name: string
  displayName: string
  short: string
  city: string
  coord: number[]
  value: number
  avgPrice: number
  amount: number
  color: string
}
const salesRegionData = ref<SalesRegion[]>([])
const regionCityMap = ref<Record<string, string>>({})
const metricUnits = ref<Record<string, string>>({
  production: '万吨',
  sales: '万吨',
  inventory: '万吨',
  avg_price: '元/吨',
  amount: '万元'
})

const DEFAULT_REGION_COORDS: Record<string, number[]> = {
  "安砂销售部": [117.37, 25.98],
  "福州北销售区域": [119.30, 26.12],
  "福州南销售区域": [119.30, 25.98],
  "南平销售区域": [118.18, 26.64],
  "宁德销售区域": [119.53, 26.66],
  "莆田销售区域": [119.01, 25.43],
  "泉州销售区域": [118.58, 24.93],
  "三明销售区域": [117.63, 26.26],
  "厦漳销售区域": [117.95, 24.55],
}

const DEFAULT_REGION_COLORS: Record<string, string> = {
  "安砂销售部": '#2F54EB',    // 极客蓝-6
  "福州北销售区域": '#08979C', // 青色-7
  "福州南销售区域": '#13C2C2', // 青色-6 (稍亮，区分北)
  "南平销售区域": '#597EF7',   // 极客蓝-5 (比三明浅)
  "宁德销售区域": '#85A5FF',   // 极客蓝-4 (更浅)
  "莆田销售区域": '#006D75',   // 青色-8 (深青)
  "泉州销售区域": '#1890FF',   // 拂晓蓝-6 (标准蓝)
  "三明销售区域": '#2F54EB',   // 同安砂
  "厦漳销售区域": '#0050B3',   // 拂晓蓝-7 (深蓝)
  "厦漳区域": '#0050B3',       // 别名兼容
}

const DEFAULT_REGION_CITY_MAP: Record<string, string> = {
  "安砂销售部": "三明市",
  "福州北销售区域": "福州市",
  "福州南销售区域": "福州市",
  "南平销售区域": "南平市",
  "宁德销售区域": "宁德市",
  "莆田销售区域": "莆田市",
  "泉州销售区域": "泉州市",
  "三明销售区域": "三明市",
  "厦漳销售区域": "厦门市、漳州市",
  "厦漳区域": "厦门市、漳州市", // 别名兼容
}

const regionCoords = ref<Record<string, number[]>>(DEFAULT_REGION_COORDS)
const regionColors = ref<Record<string, string>>(DEFAULT_REGION_COLORS)
const BASE_COORDS: Record<string, number[]> = {
  '安砂建福': [117.47, 26.72],
  '永安建福': [117.37, 25.98],
  '顺昌炼石': [117.81, 26.8],
  '福州炼石': [119.31, 26.08],
  '宁德建福': [119.53, 26.66],
  '金银湖水泥': [117.99, 24.71],
}

const selectedSalesRegion = ref('all')
const inventoryCategoryRows = ref<any[]>([])
const productionReportRows = ref<any[]>([])
const salesDetailRows = ref<any[]>([])
const salesTrendData = ref<{ months: string[]; qty: number[]; avg_price: number[] }>({
  months: [],
  qty: [],
  avg_price: []
})
const dailyInventoryData = ref<{ days: string[]; clinker_inventory: number[]; cement_inventory: number[] }>({
  days: [],
  clinker_inventory: [],
  cement_inventory: []
})

const resolvedMonthPoint = computed(() => {
  if (appStore.timeMode === 'year') return `${appStore.timePoint}-12`
  if (appStore.timeMode === 'range') return appStore.dateRange[1].slice(0, 7)
  return dayjs(`${appStore.timePoint}-01`).format('YYYY-MM')
})

const currentSalesRows = computed(() => {
  if (category.value === 'all') return salesDetailRows.value
  const [model, pkg] = category.value.split('::')
  return salesDetailRows.value.filter((row: any) => {
    const modelPass = String(row.spec || '') === model
    const pkgPass = String(row.package || '') === pkg
    return modelPass && pkgPass
  })
})

const rebuildSalesRegionData = () => {
  const regionMap = new Map<string, { qty: number; amount: number }>()
  currentSalesRows.value.forEach((row: any) => {
    const region = String(row.region || '').trim()
    if (!region) return
    const hit = regionMap.get(region) || { qty: 0, amount: 0 }
    hit.qty += Number(row.qty || 0)
    hit.amount += Number(row.amount || 0)
    regionMap.set(region, hit)
  })
  salesRegionData.value = Array.from(regionMap.entries()).map(([region, val]) => {
    const qty = +val.qty.toFixed(2)
    const amount = +val.amount.toFixed(2)
    const avgPrice = qty > 0 ? Math.round((amount * 10000) / (qty * 10000)) : 0
    return {
      name: region,
      displayName: region,
      short: region.replace('区域', ''),
      city: regionCityMap.value[region] || region.replace('区域', '市'),
      coord: regionCoords.value[region] || [118.0, 26.0],
      value: qty,
      avgPrice,
      amount,
      color: regionColors.value[region] || '#3498DB'
    }
  })
}

const fetchData = async () => {
  try {
    const configRes = await dashboardApi.getRegionConfig()
    if (configRes?.region_city_map) {
      regionCityMap.value = { ...DEFAULT_REGION_CITY_MAP, ...configRes.region_city_map }
    } else {
      regionCityMap.value = DEFAULT_REGION_CITY_MAP
    }
    if (configRes?.metric_units) {
      metricUnits.value = { ...metricUnits.value, ...configRes.metric_units }
    }
    if (configRes?.region_coords) {
      regionCoords.value = { ...DEFAULT_REGION_COORDS, ...configRes.region_coords }
    }
    if (configRes?.region_colors) {
      regionColors.value = { ...DEFAULT_REGION_COLORS, ...configRes.region_colors }
    }

    const productionRes = await queryApi.getProductionReport({
      period: 'month',
      point: resolvedMonthPoint.value
    })
    productionReportRows.value = productionRes?.items || []

    const inventoryRes = await queryApi.getInventory({
      period: appStore.timeMode,
      point: resolvedMonthPoint.value,
      category: viewMode.value === 'production' && category.value !== 'all' ? category.value : undefined
    })
    if (inventoryRes?.items) {
      inventoryCategoryRows.value = inventoryRes.items
    }

    const salesRes = await queryApi.getSales({
      period: appStore.timeMode,
      point: resolvedMonthPoint.value
    })
    salesDetailRows.value = salesRes?.items || []
    salesTrendData.value = salesRes?.price_trend || { months: [], qty: [], avg_price: [] }
    rebuildSalesRegionData()

    const inventoryByBase = new Map<string, { inventory: number; capacity: number }>()
    inventoryCategoryRows.value.forEach((row: any) => {
      const base = String(row.base || '')
      if (!base) return
      const hit = inventoryByBase.get(base) || { inventory: 0, capacity: 0 }
      hit.inventory += Number(row.end_qty || 0)
      hit.capacity += Number(row.capacity || 0)
      inventoryByBase.set(base, hit)
    })
    const productionByBase = new Map<string, { plan: number; actual: number }>()
    productionReportRows.value.forEach((row: any) => {
      const base = String(row.base || '')
      if (!base) return
      const hit = productionByBase.get(base) || { plan: 0, actual: 0 }
      hit.plan += Number(row.plan_qty || 0)
      hit.actual += Number(row.month_prod || row.actual_qty || 0)
      productionByBase.set(base, hit)
    })
    const baseNames = Array.from(new Set([
      ...Array.from(productionByBase.keys()),
      ...Array.from(inventoryByBase.keys()),
    ]))
    productionBaseData.value = baseNames.map(base => {
      const prod = productionByBase.get(base) || { plan: 0, actual: 0 }
      const inv = inventoryByBase.get(base) || { inventory: 0, capacity: 0 }
      return {
        name: base,
        coord: BASE_COORDS[base] || [118.0, 26.0],
        plan: +prod.plan.toFixed(2),
        capacity: +inv.capacity.toFixed(2),
        actual: +prod.actual.toFixed(2),
        utilization: inv.capacity > 0 ? +((prod.actual / inv.capacity) * 100).toFixed(1) : 0,
        inventory: +inv.inventory.toFixed(2)
      }
    })

    const productionValue = productionBaseData.value.reduce((sum, row) => sum + row.actual, 0)
    const productionPlan = productionBaseData.value.reduce((sum, row) => sum + row.plan, 0)
    const salesValue = salesDetailRows.value.reduce((sum, row: any) => sum + Number(row.qty || 0), 0)
    const inventoryValue = inventoryCategoryRows.value.reduce((sum, row: any) => sum + Number(row.end_qty || 0), 0)
    const inventoryCap = inventoryCategoryRows.value.reduce((sum, row: any) => sum + Number(row.capacity || 0), 0)
    const productionSalesRatio = salesValue > 0 ? Math.min(1, productionValue / salesValue) : 0
    const inventoryHealth = inventoryCap > 0 ? Math.max(0, 1 - Math.abs((inventoryValue / inventoryCap) - 0.62)) : 0
    const balanceScore = +(0.55 * productionSalesRatio + 0.45 * inventoryHealth).toFixed(2)
    const balanceLevel = balanceScore >= 0.9 ? '良好' : (balanceScore >= 0.8 ? '关注' : '偏低')
    kpiData.value = {
      production: {
        value: +productionValue.toFixed(2),
        unit: '万吨',
        change: 0,
        percent: productionPlan > 0 ? Math.min(100, Math.round((productionValue / productionPlan) * 100)) : 0,
      },
      sales: {
        value: +salesValue.toFixed(2),
        unit: '万吨',
        change: 0,
        percent: productionValue > 0 ? Math.min(100, Math.round((salesValue / productionValue) * 100)) : 0,
      },
      inventory: {
        value: +inventoryValue.toFixed(2),
        unit: '万吨',
        change: 0,
        percent: inventoryCap > 0 ? Math.min(100, Math.round((inventoryValue / inventoryCap) * 100)) : 0,
      },
      balance_index: {
        value: balanceScore,
        level: balanceLevel,
      }
    }
    await fetchDailyInventoryData()
  } catch (err) {
    console.error('Failed to fetch dashboard data:', err)
  }
}

const fetchDailyInventoryData = async () => {
  if (appStore.selectedBase === 'all') {
    dailyInventoryData.value = { days: [], clinker_inventory: [], cement_inventory: [] }
    return
  }
  try {
    const res = await queryApi.getInventoryDaily({ base: appStore.selectedBase, month: '2025-12' })
    if (res?.days) {
      dailyInventoryData.value = {
        days: res.days,
        clinker_inventory: res.clinker_inventory || [],
        cement_inventory: res.cement_inventory || []
      }
    }
  } catch {
    dailyInventoryData.value = { days: [], clinker_inventory: [], cement_inventory: [] }
  }
}

onMounted(() => {
  fetchData()
})

const categoryOptions = computed(() => {
  if (viewMode.value === 'sales') {
    const keys = Array.from(new Set(
      salesDetailRows.value
        .map((row: any) => `${String(row.spec || '').trim()}::${String(row.package || '').trim()}`)
        .filter((item: string) => item.split('::')[0])
    ))
    return [
      { value: 'all', label: '全部型号规格' },
      ...keys.map(item => {
        const [model, pkg] = item.split('::')
        return { value: item, label: `${model}${pkg ? ` ${pkg}` : ''}` }
      })
    ]
  }
  return [
    { value: 'all', label: '全部品类' },
    { value: 'cement', label: '水泥' },
    { value: 'clinker', label: '熟料' },
  ]
})

const filteredProduction = computed(() => {
  if (appStore.selectedBase === 'all') return productionBaseData.value
  return productionBaseData.value.filter(b => b.name === appStore.selectedBase)
})

const productionInventoryRows = computed(() => {
  const baseMap = new Map<string, { clinker: number; cement: number }>()
  inventoryCategoryRows.value.forEach((item: any) => {
    const baseName = item.base
    if (appStore.selectedBase !== 'all' && baseName !== appStore.selectedBase) return
    if (!baseMap.has(baseName)) {
      baseMap.set(baseName, { clinker: 0, cement: 0 })
    }
    const hit = baseMap.get(baseName)!
    if (item.category === '熟料') {
      hit.clinker += Number(item.end_qty || 0)
    } else {
      hit.cement += Number(item.end_qty || 0)
    }
  })
  return Array.from(baseMap.entries()).map(([base, data]) => ({
    base,
    clinker: +data.clinker.toFixed(2),
    cement: +data.cement.toFixed(2)
  }))
})

const filteredSales = computed(() => {
  if (selectedSalesRegion.value === 'all') return salesRegionData.value
  return salesRegionData.value.filter(r => r.displayName === selectedSalesRegion.value)
})

const compactSalesName = (name: string) =>
  name.replace('销售区域', '').replace('区域', '').replace('销售部', '').replace('销售', '').trim()

const rankData = computed(() =>
  viewMode.value === 'production'
    ? filteredProduction.value.map(b => ({ name: b.name, value: b.actual }))
    : filteredSales.value.map(r => ({ name: compactSalesName(r.displayName), value: r.value }))
)

function handleMapPointClick(payload: { type: 'production' | 'sales'; name: string }) {
  if (payload.type === 'production') {
    appStore.selectedBase = appStore.selectedBase === payload.name ? 'all' : payload.name
    return
  }
  selectedSalesRegion.value = selectedSalesRegion.value === payload.name ? 'all' : payload.name
}

function resetMapSelection() {
  if (viewMode.value === 'production') {
    appStore.selectedBase = 'all'
    return
  }
  selectedSalesRegion.value = 'all'
}

watch(() => viewMode.value, () => {
  selectedSalesRegion.value = 'all'
  category.value = 'all'
  rebuildSalesRegionData()
})

watch(() => appStore.selectedBase, () => {
  fetchDailyInventoryData()
})

watch(() => category.value, () => {
  if (viewMode.value === 'sales') {
    rebuildSalesRegionData()
    selectedSalesRegion.value = 'all'
    return
  }
  fetchData()
})

watch([() => appStore.queryNonce, () => appStore.timePoint, () => appStore.timeMode, () => appStore.dateRange], () => {
  fetchData()
}, { deep: true })

const isDetailMode = computed(() => {
  if (viewMode.value === 'production') return appStore.selectedBase !== 'all'
  return selectedSalesRegion.value !== 'all'
})

const detailPanel = computed(() => {
  if (viewMode.value === 'production') {
    const base = productionBaseData.value.find(item => item.name === appStore.selectedBase)
    if (!base) {
      return { title: '基地详情', metrics: [] as Array<{ label: string; value: string; unit: string }> }
    }
    const salesAmount = salesRegionData.value.reduce((sum, item) => sum + item.value, 0)
    return {
      title: `${base.name}经营详情`,
      metrics: [
        { label: '生产', value: base.actual.toFixed(2), unit: metricUnits.value.production },
        { label: '库存', value: base.inventory.toFixed(2), unit: metricUnits.value.inventory },
        { label: '销售', value: salesAmount.toFixed(2), unit: metricUnits.value.sales },
      ]
    }
  }
  const region = salesRegionData.value.find(item => item.displayName === selectedSalesRegion.value)
  return {
    title: `${selectedSalesRegion.value}经营详情`,
    metrics: [
      { label: '销量', value: (region?.value || 0).toFixed(2), unit: metricUnits.value.sales },
      { label: '均价', value: String(Math.round(region?.avgPrice || 0)), unit: metricUnits.value.avg_price },
      { label: '金额', value: String(Math.round(region?.amount || 0)), unit: metricUnits.value.amount },
    ]
  }
})

const inventoryTotal = computed(() =>
  filteredProduction.value.reduce((sum, b) => sum + b.inventory, 0)
)

const inventoryCapacity = computed(() =>
  filteredProduction.value.reduce((sum, b) => sum + b.capacity, 0)
)

const kpiList = computed(() => {
  const kpi = kpiData.value
  return [
    {
      title: '本月产量',
      value: kpi.production?.value || 0,
      unit: kpi.production?.unit || '万吨',
      change: `环比${kpi.production?.change > 0 ? '+' : ''}${kpi.production?.change || 0}%`,
      changeType: (kpi.production?.change || 0) >= 0 ? 'up' : 'down',
      percent: kpi.production?.percent || 0,
      color: appTheme.value === 'dark' ? '#3dd9a8' : '#1b6b5a',
      progressLabel: `计划完成 ${kpi.production?.percent || 0}%`,
      icon: markRaw(BarChartOutlined),
      iconBg: appTheme.value === 'dark' ? 'linear-gradient(135deg, #22b88b, #3dd9a8)' : 'linear-gradient(135deg, #1b6b5a, #2f8a76)'
    },
    {
      title: '本月销售',
      value: kpi.sales?.value || 0,
      unit: kpi.sales?.unit || '万吨',
      change: `环比${kpi.sales?.change > 0 ? '+' : ''}${kpi.sales?.change || 0}%`,
      changeType: (kpi.sales?.change || 0) >= 0 ? 'up' : 'down',
      percent: kpi.sales?.percent || 0,
      color: '#e8853b',
      progressLabel: `目标达成 ${kpi.sales?.percent || 0}%`,
      icon: markRaw(ShoppingCartOutlined),
      iconBg: 'linear-gradient(135deg, #d9722e, #e8853b)'
    },
    {
      title: '当前库存',
      value: +inventoryTotal.value.toFixed(2),
      unit: kpi.inventory?.unit || '万吨',
      change: `环比${kpi.inventory?.change > 0 ? '+' : ''}${kpi.inventory?.change || 0}%`,
      changeType: (kpi.inventory?.change || 0) >= 0 ? 'up' : 'down',
      percent: inventoryPercent.value,
      color: '#3b82c4',
      progressLabel: `总库容 ${inventoryCapacity.value.toFixed(2)} 万吨`,
      icon: markRaw(DatabaseOutlined),
      iconBg: 'linear-gradient(135deg, #2f6ea8, #3b82c4)'
    },
    {
      title: '产销平衡指数',
      value: kpi.balance_index?.value || 0,
      unit: '',
      change: kpi.balance_index?.level || '-',
      changeType: 'up',
      percent: Math.min(100, (kpi.balance_index?.value || 0) * 100),
      color: '#8b6cc1',
      progressLabel: `综合评分 ${Math.round((kpi.balance_index?.value || 0) * 100)}`,
      icon: markRaw(FundProjectionScreenOutlined),
      iconBg: 'linear-gradient(135deg, #7655b1, #8b6cc1)'
    },
  ]
})

const appTheme = computed(() => appStore.theme)

const inventoryPercent = computed(() => {
  return inventoryCapacity.value === 0 ? 0 : Math.min(100, Math.round((inventoryTotal.value / inventoryCapacity.value) * 100))
})
</script>

<style scoped>
.dashboard {
  padding: 16px;
}

.view-switch {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  padding: 8px 10px;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  background: color-mix(in srgb, var(--card-bg) 92%, var(--primary-color));
}

.mode-tabs :deep(.ant-radio-button-wrapper) {
  min-width: 68px;
  text-align: center;
}

.dashboard-body {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.map-area {
  flex: 3;
}

.side-panels {
  flex: 2;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-panel-card :deep(.ant-card-body) {
  padding: 14px 16px;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.detail-metrics {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}

.detail-item {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 10px 12px;
  background: color-mix(in srgb, var(--card-bg) 88%, var(--primary-color));
}

.detail-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.detail-value {
  margin-top: 4px;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

@media (max-width: 1400px) {
  .dashboard-body { flex-direction: column; }
}
</style>
