<template>
  <div class="page-container">
    <div class="page-header">
      <span class="page-title">库存监控</span>
      <a-space>
        <a-button size="small"><DownloadOutlined /> 导出</a-button>
      </a-space>
    </div>

    <!-- 库存水位卡片 -->
    <div class="water-level-grid" style="margin-bottom: 16px">
      <div v-for="item in filteredInventory" :key="item.base" class="water-card" :class="{ 'water-card-active': activeBase === item.base }" @click="activeBase = item.base">
        <div class="water-card-title">{{ item.base }}</div>
        <div class="water-visual">
          <div class="water-tank">
            <div class="water-fill" :style="{ height: item.ratio + '%', background: getWaterColor(item.ratio) }"></div>
            <div class="water-safety-line" :style="{ bottom: item.safetyRatio + '%' }">
              <span class="safety-label">安全线</span>
            </div>
          </div>
          <div class="water-info">
            <div class="water-val">{{ item.current }}<span class="water-unit">万吨</span></div>
            <div class="water-meta">熟料库存: {{ item.clinkerQty }} 万吨</div>
            <div class="water-meta">水泥库存: {{ item.cementQty }} 万吨</div>
            <div class="water-meta">库容: {{ item.capacity }}万吨</div>
            <div class="water-meta">占比: {{ item.ratio }}%</div>
            <a-tag :color="item.ratio > 85 ? 'red' : item.ratio < 30 ? 'orange' : 'green'" style="margin-top: 4px">
              {{ item.ratio > 85 ? '高位预警' : item.ratio < 30 ? '低位预警' : '正常' }}
            </a-tag>
          </div>
        </div>
      </div>
    </div>

    <div class="card-grid card-grid-2" style="margin-bottom: 16px">
      <a-card :bordered="false" title="库存趋势">
        <div ref="trendRef" style="height: 320px"></div>
      </a-card>
      <a-card :bordered="false" title="熟料 / 水泥月度库存">
        <div ref="inOutRef" style="height: 320px"></div>
      </a-card>
    </div>

    <a-card :bordered="false" title="库存明细">
      <div v-if="drillMonth !== 'all'" class="drill-tip">
        <span>已按月份穿透：{{ formatPeriodLabel(drillMonth) }}</span>
        <a-button size="small" type="link" @click="drillMonth = 'all'">清除</a-button>
      </div>
      <div v-if="activeBase !== 'all'" class="drill-tip" style="margin-top: 6px">
        <span>已按基地联动：{{ activeBase }}</span>
        <a-button size="small" type="link" @click="activeBase = 'all'">清除</a-button>
      </div>
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
const selectedCategory = computed({
  get: () => appStore.selectedCategory,
  set: (val: string) => { appStore.selectedCategory = val }
})

// API Data
const inventoryList = ref<any[]>([])
const inventoryTrend = ref<any>({ months: [], total_inventory: [], safety_line: 0 })

const fetchData = async () => {
  try {
    const res = await queryApi.getInventory({
      base: selectedBase.value === 'all' ? undefined : selectedBase.value,
      category: selectedCategory.value === 'all' ? undefined : selectedCategory.value
    })
    if (res && res.items) {
      inventoryList.value = res.items
    }
    if (res && res.trend) {
      inventoryTrend.value = res.trend
    }
    initCharts()
  } catch (e) {
    console.error(e)
  }
}

const filteredInventory = computed(() => {
  const baseMap = new Map<string, { clinkerQty: number; cementQty: number; current: number; capacity: number; safetyQty: number }>()
  inventoryList.value.forEach(item => {
    if (!baseMap.has(item.base)) {
      baseMap.set(item.base, { clinkerQty: 0, cementQty: 0, current: 0, capacity: 0, safetyQty: 0 })
    }
    const baseData = baseMap.get(item.base)!
    const endQty = Number(item.end_qty || 0)
    const capacity = Number(item.capacity || 0)
    baseData.current += endQty
    baseData.capacity += capacity
    baseData.safetyQty += Number(item.safety_qty || 0)
    if (item.category === '熟料') {
      baseData.clinkerQty += endQty
    } else {
      baseData.cementQty += endQty
    }
  })

  return Array.from(baseMap.entries()).map(([base, info]) => {
    const ratio = info.capacity === 0 ? 0 : +(info.current / info.capacity * 100).toFixed(1)
    return {
      base,
      clinkerQty: +info.clinkerQty.toFixed(2),
      cementQty: +info.cementQty.toFixed(2),
      current: +info.current.toFixed(2),
      capacity: +info.capacity.toFixed(2),
      ratio,
      safetyRatio: info.capacity === 0 ? 20 : +(info.safetyQty / info.capacity * 100).toFixed(1)
    }
  })
})

function getWaterColor(ratio: number) {
  if (ratio > 85) return 'linear-gradient(to top, #ff4d4f, #ff7875)'
  if (ratio < 30) return 'linear-gradient(to top, #faad14, #ffd666)'
  return 'linear-gradient(to top, #1f6fff, #69b1ff)'
}

const trendRef = ref<HTMLElement>()
const inOutRef = ref<HTMLElement>()
let chart1: echarts.ECharts
let chart2: echarts.ECharts
const drillMonth = ref('all')
const activeBase = ref<string>('all')
const effectiveBase = computed(() => activeBase.value === 'all' ? selectedBase.value : activeBase.value)

const columns = [
  { title: '基地', dataIndex: 'base', width: 100 },
  { title: '品类', dataIndex: 'category', width: 80 },
  { title: '期初库存(万吨)', dataIndex: 'begin', width: 130 },
  { title: '期末库存(万吨)', dataIndex: 'end', width: 130 },
  { title: '可用库存(万吨)', dataIndex: 'available', width: 130 },
  { title: '仓容上限(万吨)', dataIndex: 'capacity', width: 130 },
  { title: '库容占比', dataIndex: 'ratio', width: 100 },
  { title: '状态', dataIndex: 'status', width: 90 },
]

const formatPeriodLabel = (raw: string) => {
  if (/^\d{4}-\d{2}$/.test(raw)) {
    return `${Number(raw.slice(5, 7))}月`
  }
  if (/^\d{4}$/.test(raw)) {
    return `${raw}年`
  }
  return raw
}

const tableData = computed(() => {
  const list = inventoryList.value.map((item, i) => ({
    key: i,
    base: item.base,
    category: item.category || '水泥',
    begin: item.begin_qty,
    end: item.end_qty,
    available: item.available_qty,
    capacity: item.capacity,
    ratio: item.ratio_pct + '%',
    status: item.status,
  }))
  const monthFiltered = drillMonth.value === 'all' ? list : list.filter(item => {
    const period = String((inventoryList.value[item.key]?.month ?? inventoryList.value[item.key]?.period ?? inventoryList.value[item.key]?.date ?? ''))
    return period.includes(drillMonth.value)
  })
  if (activeBase.value === 'all') return monthFiltered
  return monthFiltered.filter(item => item.base === activeBase.value)
})

function initCharts() {
  if (trendRef.value) {
    if (chart1) chart1.dispose()
    chart1 = echarts.init(trendRef.value)
    const months = inventoryTrend.value.months || []
    const baseTrendMap = inventoryTrend.value.base_category_trend || {}
    const selectedBaseTrendClinker = baseTrendMap[`${effectiveBase.value}|熟料`]
    const selectedBaseTrendCement = baseTrendMap[`${effectiveBase.value}|水泥`]
    const clinkerSeries = effectiveBase.value !== 'all' && selectedBaseTrendClinker ? selectedBaseTrendClinker : (inventoryTrend.value.clinker_inventory || [])
    const cementSeries = effectiveBase.value !== 'all' && selectedBaseTrendCement ? selectedBaseTrendCement : (inventoryTrend.value.cement_inventory || [])
    const totalSeries = months.map((_: string, idx: number) => Number(clinkerSeries[idx] || 0) + Number(cementSeries[idx] || 0))
    const safetyLine = Number(inventoryTrend.value.safety_line || 0)
    chart1.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['库存总量', '安全线'], textStyle: { fontSize: 11 } },
      grid: { top: 35, right: 20, bottom: 30, left: 50 },
      xAxis: { type: 'category', data: months.map(formatPeriodLabel), axisLabel: { fontSize: 10 } },
      yAxis: { type: 'value', name: '万吨' },
      series: [
        {
          name: '库存总量',
          type: 'line',
          smooth: true,
          data: totalSeries,
          areaStyle: { color: 'rgba(31,111,255,0.12)' },
          lineStyle: { color: '#1f6fff', width: 2 },
          itemStyle: { color: '#1f6fff' }
        },
        {
          name: '安全线',
          type: 'line',
          smooth: false,
          symbol: 'none',
          data: months.map(() => safetyLine),
          lineStyle: { color: '#ff7875', width: 1.6, type: 'dashed' }
        },
      ]
    })
  }
  if (inOutRef.value) {
    if (chart2) chart2.dispose()
    chart2 = echarts.init(inOutRef.value)
    const months = inventoryTrend.value.months || []
    const baseTrendMap = inventoryTrend.value.base_category_trend || {}
    const clinkerSeries = inventoryTrend.value.clinker_inventory || []
    const cementSeries = inventoryTrend.value.cement_inventory || []
    const selectedBaseTrendClinker = baseTrendMap[`${effectiveBase.value}|熟料`]
    const selectedBaseTrendCement = baseTrendMap[`${effectiveBase.value}|水泥`]
    chart2.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['熟料库存', '水泥库存'], textStyle: { fontSize: 11 } },
      grid: { top: 35, right: 20, bottom: 30, left: 50 },
      xAxis: { type: 'category', data: months.map(formatPeriodLabel), axisLabel: { fontSize: 10 } },
      yAxis: { type: 'value', name: '万吨' },
      series: [
        {
          name: '熟料库存',
          type: 'bar',
          data: effectiveBase.value !== 'all' && selectedBaseTrendClinker ? selectedBaseTrendClinker : clinkerSeries,
          itemStyle: { color: '#3D5898', borderRadius: [3, 3, 0, 0] },
          barMaxWidth: 24
        },
        {
          name: '水泥库存',
          type: 'bar',
          data: effectiveBase.value !== 'all' && selectedBaseTrendCement ? selectedBaseTrendCement : cementSeries,
          itemStyle: { color: '#6B8FE8', borderRadius: [3, 3, 0, 0] },
          barMaxWidth: 24
        },
      ]
    })
    chart2.off('click')
    chart2.on('click', (params: any) => {
      const month = params?.name
      if (!month) return
      drillMonth.value = String(month)
    })
  }
}

const handleResize = () => { chart1?.resize(); chart2?.resize() }
onMounted(() => { initCharts(); fetchData(); window.addEventListener('resize', handleResize) })
watch([() => appStore.queryNonce, () => appStore.timePoint], () => { fetchData() })
watch([() => appStore.timeMode, () => appStore.dateRange], () => { fetchData() }, { deep: true })
watch(() => selectedBase.value, (base) => {
  activeBase.value = base === 'all' ? 'all' : base
  initCharts()
})
watch(() => activeBase.value, () => {
  initCharts()
})
onUnmounted(() => { window.removeEventListener('resize', handleResize); chart1?.dispose(); chart2?.dispose() })
</script>

<style scoped>
.water-level-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 14px;
}

.water-card {
  background: var(--card-bg);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 14px;
  box-shadow: var(--card-shadow);
  cursor: pointer;
}

.water-card-active {
  border-color: #1677ff;
  box-shadow: 0 0 0 2px rgba(22, 119, 255, 0.15);
}

.water-card-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 10px;
  text-align: center;
  color: var(--text-primary);
}

.water-visual {
  display: flex;
  gap: 10px;
  align-items: flex-end;
}

.water-tank {
  width: 44px;
  height: 96px;
  border: 2px solid var(--border-color);
  border-radius: 4px;
  position: relative;
  overflow: hidden;
  flex-shrink: 0;
}

.water-fill {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  transition: height 0.8s ease;
  border-radius: 0 0 2px 2px;
}

.water-safety-line {
  position: absolute;
  left: -4px;
  right: -4px;
  border-top: 1.5px dashed #ff4d4f;
}

.safety-label {
  position: absolute;
  right: -40px;
  top: -8px;
  font-size: 8px;
  color: #ff4d4f;
  white-space: nowrap;
}

.water-info {
  flex: 1;
}

.water-val {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
}

.water-unit {
  font-size: 11px;
  color: var(--text-muted);
  margin-left: 2px;
}

.water-meta {
  font-size: 12px;
  color: var(--text-secondary);
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
