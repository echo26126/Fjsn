<template>
  <div class="page-container">
    <div class="page-header">
      <span class="page-title">生产查询</span>
      <a-space>
        <a-button size="small"><DownloadOutlined /> 导出</a-button>
      </a-space>
    </div>

    <div class="query-switch-row">
      <a-space size="small" wrap>
        <a-tag color="blue">{{ layerPeriodLabel }}</a-tag>
        <span class="switch-label">基地</span>
        <a-select v-model:value="selectedBase" size="small" style="width: 150px">
          <a-select-option value="all">全部基地</a-select-option>
          <a-select-option v-for="item in appStore.baseOptions" :key="item" :value="item">{{ item }}</a-select-option>
        </a-select>
        <span class="switch-label">品类</span>
        <a-radio-group v-model:value="selectedCategory" size="small" button-style="solid">
          <a-radio-button value="all">全部</a-radio-button>
          <a-radio-button value="cement">水泥</a-radio-button>
          <a-radio-button value="clinker">熟料</a-radio-button>
        </a-radio-group>
      </a-space>
    </div>

    <div class="card-grid card-grid-2" style="margin-bottom: 16px">
      <a-card :bordered="false" title="主要设备运行情况一览">
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px">
          <a-radio-group v-model:value="equipmentViewMode" size="small" button-style="solid">
            <a-radio-button value="device">设备维度</a-radio-button>
            <a-radio-button value="base">基地维度</a-radio-button>
          </a-radio-group>
          <a-radio-group v-model:value="equipmentMetric" size="small" button-style="solid">
            <a-radio-button value="day">日</a-radio-button>
            <a-radio-button value="month">月</a-radio-button>
            <a-radio-button value="year">年</a-radio-button>
          </a-radio-group>
        </div>
        <div ref="equipmentRef" style="height: 220px"></div>
        <a-table
          :columns="equipmentColumns"
          :data-source="equipmentDetailTableData"
          size="small"
          :pagination="false"
          :scroll="{ y: 170 }"
          :row-class-name="equipmentRowClassName"
          style="margin-top: 8px"
        />
      </a-card>
      <a-card :bordered="false" title="停窑情况">
        <div style="display: flex; justify-content: flex-end; margin-bottom: 8px">
          <a-radio-group v-model:value="equipmentViewMode" size="small" button-style="solid">
            <a-radio-button value="base">按基地</a-radio-button>
            <a-radio-button value="device">按设备</a-radio-button>
          </a-radio-group>
        </div>
        <div ref="kilnRef" style="height: 210px"></div>
        <div ref="stopReasonRef" style="height: 130px; margin-top: 8px"></div>
      </a-card>
    </div>

    <a-card :bordered="false" title="生产一览" style="margin-bottom: 16px">
      <div style="display: flex; justify-content: flex-end; margin-bottom: 8px">
        <a-radio-group v-model:value="overviewMode" size="small" button-style="solid">
          <a-radio-button value="month">月</a-radio-button>
          <a-radio-button value="year">年</a-radio-button>
        </a-radio-group>
      </div>
      <div ref="reportRef" style="height: 320px; margin-bottom: 12px"></div>
      <a-table :columns="reportColumns" :data-source="reportTableData" size="small" :pagination="{ pageSize: 8, showTotal: (t: number) => `共 ${t} 条` }" />
    </a-card>

    <a-card :bordered="false" title="生产明细（到日）">
      <a-table :columns="columns" :data-source="tableData" size="small" :pagination="{ pageSize: 10, showTotal: (t: number) => `共 ${t} 条` }" />
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, h } from 'vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
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

const equipmentRef = ref<HTMLElement>()
const kilnRef = ref<HTMLElement>()
const stopReasonRef = ref<HTMLElement>()
const reportRef = ref<HTMLElement>()
let equipmentChart: echarts.ECharts
let kilnChart: echarts.ECharts
let stopReasonChart: echarts.ECharts
let reportChart: echarts.ECharts

const productionList = ref<any[]>([])
const productionReportItems = ref<any[]>([])
const equipmentList = ref<any[]>([])
const equipmentDetailList = ref<any[]>([])
const stopReasonList = ref<any[]>([])
const baseCapacityMap = ref<Record<string, number>>({})
const overviewMode = ref<'month' | 'year'>('month')
const equipmentMetric = ref<'day' | 'month' | 'year'>('month')
const equipmentViewMode = ref<'device' | 'base'>('base')
const layerPeriodLabel = computed(() => {
  if (appStore.timeMode === 'year') return `${appStore.timePoint}年`
  if (appStore.timeMode === 'range') {
    const [start, end] = appStore.dateRange
    return `${dayjs(start).format('YYYY年M月D日')} - ${dayjs(end).format('M月D日')}`
  }
  return `${dayjs(`${appStore.timePoint}-01`).format('YYYY年M月')}`
})

const queryPeriod = computed(() => appStore.timeMode === 'year' ? 'month' : 'day')

const queryPoint = computed(() => {
  if (appStore.timeMode === 'year') return '2025-12-31'
  if (appStore.timeMode === 'range') return '2025-12-31'
  const monthText = dayjs(`${appStore.timePoint}-01`).format('YYYY-MM')
  return monthText === '2025-12' ? '2025-12-31' : '2025-12-31'
})

const equipmentQueryPoint = computed(() => {
  const p = queryPoint.value
  if (String(p).slice(5, 7) === '12') return p
  return '2025-12-31'
})

const fetchTopData = async () => {
  try {
    const equipmentRes = await queryApi.getProductionEquipment({
      base: selectedBase.value === 'all' ? undefined : selectedBase.value,
      point: equipmentQueryPoint.value,
    })
    equipmentList.value = equipmentRes?.items || []
    const equipmentDetailRes = await queryApi.getProductionEquipmentDetail({
      base: selectedBase.value === 'all' ? undefined : selectedBase.value,
      point: equipmentQueryPoint.value,
    })
    equipmentDetailList.value = equipmentDetailRes?.items || []
    const stopReasonRes = await queryApi.getProductionStopReasons({
      base: selectedBase.value === 'all' ? undefined : selectedBase.value,
      point: equipmentQueryPoint.value,
    })
    stopReasonList.value = stopReasonRes?.items || []
    initCharts()
  } catch (e) {
    loadFallbackData()
    initCharts()
  }
}

const fetchBottomData = async () => {
  try {
    const reportRes = await queryApi.getProductionReport({
      base: selectedBase.value === 'all' ? undefined : selectedBase.value,
      category: selectedCategory.value === 'all' ? undefined : selectedCategory.value,
      period: queryPeriod.value,
      point: queryPoint.value,
    })
    productionReportItems.value = reportRes?.items || []

    const detailRes = await queryApi.getProduction({
      base: selectedBase.value === 'all' ? undefined : selectedBase.value,
      category: selectedCategory.value === 'all' ? undefined : selectedCategory.value,
      period: queryPeriod.value,
      point: queryPoint.value,
    })
    productionList.value = detailRes?.items || []
    const inventoryRes = await queryApi.getInventory({
      period: appStore.timeMode,
      point: queryPoint.value,
      base: selectedBase.value === 'all' ? undefined : selectedBase.value,
      category: selectedCategory.value === 'all' ? undefined : selectedCategory.value,
    })
    const capacityMap: Record<string, number> = {}
    ;(inventoryRes?.items || []).forEach((item: any) => {
      const baseName = item.base
      if (!capacityMap[baseName]) capacityMap[baseName] = 0
      capacityMap[baseName] += Number(item.capacity || 0)
    })
    baseCapacityMap.value = capacityMap
    if (!productionReportItems.value.length && !productionList.value.length) {
      loadFallbackData()
    }
  } catch (e) {
    loadFallbackData()
  }
}

const loadFallbackData = () => {
  const bases = selectedBase.value === 'all' ? appStore.baseOptions : [selectedBase.value]
  const synthetic = bases.map((base, idx) => {
    const plan = 6 + idx * 1.4
    const monthProd = +(plan * 0.9).toFixed(2)
    const util = +(monthProd / plan * 100).toFixed(1)
    return {
      base,
      category: '水泥',
      period: queryPoint.value,
      day: 30,
      plan_qty: plan,
      actual_qty: monthProd,
      variance_pct: +((monthProd - plan) / plan * 100).toFixed(1),
      utilization: util,
      daily_prod: +(monthProd / 30).toFixed(2),
      month_prod: monthProd,
      year_prod: +(monthProd * 10.8).toFixed(2),
      daily_out: +(monthProd / 30 * 0.96).toFixed(2),
      month_out: +(monthProd * 0.96).toFixed(2),
      year_out: +(monthProd * 10.2).toFixed(2),
      month_sale: +(monthProd * 0.96).toFixed(2),
      year_sale: +(monthProd * 10.2).toFixed(2),
      equipment_status: util >= 75 ? '正常' : '偏低',
      kiln_stop_hours: +(Math.max(0, (100 - util) / 100 * 24)).toFixed(1),
      kiln_stop_times: util < 80 ? 1 : 0,
    }
  })
  productionReportItems.value = synthetic
  productionList.value = synthetic
  equipmentList.value = synthetic.map(item => ({
    base: item.base,
    run_rate_day: +(item.utilization * 0.96).toFixed(2),
    run_rate_month: item.utilization,
    run_rate_year: +(item.utilization * 1.05).toFixed(2),
    runtime_day: +(24 * item.utilization / 100).toFixed(2),
    runtime_month: +(24 * 30 * item.utilization / 100 / 6).toFixed(2),
    runtime_year: +(24 * 365 * item.utilization / 100 / 6).toFixed(2),
    stop_hours_day: +(Math.max(0, 24 - 24 * item.utilization / 100)).toFixed(2),
    stop_hours_month: +(Math.max(0, 24 * 31 - 24 * 30 * item.utilization / 100 / 6)).toFixed(2),
    stop_hours_year: +(Math.max(0, 24 * 365 - 24 * 365 * item.utilization / 100 / 6)).toFixed(2),
    stop_count: item.kiln_stop_times,
    equipment_count: 6,
  }))
  equipmentDetailList.value = equipmentList.value.map(item => ({
    base: item.base,
    device: '主机组',
    run_rate_day: item.run_rate_day,
    run_rate_month: item.run_rate_month,
    run_rate_year: item.run_rate_year,
    runtime_day: item.runtime_day,
    runtime_month: item.runtime_month,
    runtime_year: item.runtime_year,
    stop_hours_day: item.stop_hours_day,
    stop_hours_month: item.stop_hours_month,
    stop_hours_year: item.stop_hours_year,
    stop_count: item.stop_count,
  }))
  stopReasonList.value = synthetic.map(item => ({
    base: item.base,
    续停: item.kiln_stop_times || 0,
    避峰: 0,
    检修: 0,
    故障: 0,
    其他: 0,
  }))
  baseCapacityMap.value = Object.fromEntries(synthetic.map(item => [item.base, 0]))
}

const columns = [
  { title: '基地', dataIndex: 'base', width: 100 },
  { title: '品类', dataIndex: 'category', width: 80 },
  { title: '周期', dataIndex: 'dayLabel', width: 100 },
  { title: '日产量(万吨)', dataIndex: 'dailyProd', width: 110 },
  { title: '日出厂(万吨)', dataIndex: 'dailyOut', width: 110 },
  { title: '月累计销售(万吨)', dataIndex: 'monthSale', width: 130 },
  { title: '年累计销售(万吨)', dataIndex: 'yearSale', width: 130 },
  { title: '计划产量(万吨)', dataIndex: 'plan', width: 130, sorter: (a: any, b: any) => a.plan - b.plan },
  { title: '月累计产量(万吨)', dataIndex: 'actual', width: 130, sorter: (a: any, b: any) => a.actual - b.actual },
  { title: '年累计产量(万吨)', dataIndex: 'yearProd', width: 130, sorter: (a: any, b: any) => a.yearProd - b.yearProd },
  { title: '偏差(%)', dataIndex: 'variance', width: 100, customRender: ({ text }: any) => {
    return `${text > 0 ? '+' : ''}${text}%`
  }},
  { title: '产能利用率', dataIndex: 'utilization', width: 110 },
]

const reportColumns = computed(() => {
  if (overviewMode.value === 'month') {
    return [
      { title: '基地', dataIndex: 'base', width: 100 },
      { title: '月计划(万吨)', dataIndex: 'plan', width: 120 },
      { title: '月累计产量(万吨)', dataIndex: 'monthProd', width: 140 },
      { title: '月出厂累计(万吨)', dataIndex: 'monthOut', width: 140 },
      { title: '库容(万吨)', dataIndex: 'capacity', width: 110 },
    ]
  }
  return [
    { title: '基地', dataIndex: 'base', width: 100 },
    { title: '年计划(万吨)', dataIndex: 'yearPlan', width: 120 },
    { title: '年累计产量(万吨)', dataIndex: 'yearProd', width: 140 },
    { title: '年出厂累计(万吨)', dataIndex: 'yearOut', width: 140 },
    { title: '库容(万吨)', dataIndex: 'capacity', width: 110 },
  ]
})

const equipmentColumns = computed(() => {
  const isDay = equipmentMetric.value === 'day'
  const isMonth = equipmentMetric.value === 'month'
  const rateKey = isDay ? 'runRateDay' : (isMonth ? 'runRateMonth' : 'runRateYear')
  const runtimeKey = isDay ? 'runtimeDay' : (isMonth ? 'runtimeMonth' : 'runtimeYear')
  const stopKey = isDay ? 'stopHoursDay' : (isMonth ? 'stopHoursMonth' : 'stopHoursYear')
  const rateTitle = isDay ? '日运转率(%)' : (isMonth ? '月运转率(%)' : '年运转率(%)')
  const runtimeTitle = isDay ? '日运行(h)' : (isMonth ? '月运行(h)' : '年运行(h)')
  const stopTitle = isDay ? '日停窑(h)' : (isMonth ? '月停窑(h)' : '年停窑(h)')
  return [
    { title: '基地', dataIndex: 'base', width: 92 },
    { title: '设备', dataIndex: 'device', width: 130 },
    { title: rateTitle, dataIndex: rateKey, width: 110 },
    { title: runtimeTitle, dataIndex: runtimeKey, width: 110 },
    { title: stopTitle, dataIndex: stopKey, width: 100 },
  ]
})

const equipmentDetailTableData = computed(() =>
  equipmentDetailList.value.map((item, i) => ({
    key: item.device_key || `${item.base}-${item.device}-${i}`,
    base: item.base,
    device: item.device,
    deviceKey: item.device_key || `${item.base}|${item.device}`,
    runRateDay: Number(Number(item.run_rate_day || 0).toFixed(2)),
    runRateMonth: Number(Number(item.run_rate_month || 0).toFixed(2)),
    runRateYear: Number(Number(item.run_rate_year || 0).toFixed(2)),
    runtimeDay: Number(Number(item.runtime_day || 0).toFixed(2)),
    runtimeMonth: Number(Number(item.runtime_month || 0).toFixed(2)),
    runtimeYear: Number(Number(item.runtime_year || 0).toFixed(2)),
    stopHoursDay: Number(Number(item.stop_hours_day || 0).toFixed(2)),
    stopHoursMonth: Number(Number(item.stop_hours_month || 0).toFixed(2)),
    stopHoursYear: Number(Number(item.stop_hours_year || 0).toFixed(2)),
    stopCount: Number(item.stop_count || 0),
  }))
)

const equipmentRowClassName = (record: any) => {
  const isDay = equipmentMetric.value === 'day'
  const isMonth = equipmentMetric.value === 'month'
  const stopKey = isDay ? 'stopHoursDay' : (isMonth ? 'stopHoursMonth' : 'stopHoursYear')
  const stopped = Number(record?.[stopKey] || 0) > 0
  return stopped ? 'equipment-child-row equipment-stop-row' : 'equipment-child-row'
}

const reportTableData = computed(() =>
  productionReportItems.value.map((item, i) => ({
    key: i,
    base: item.base,
    plan: item.plan_qty,
    yearPlan: +(Number(item.plan_qty || 0) * 12).toFixed(2),
    dailyProd: item.daily_prod,
    monthProd: item.month_prod,
    yearProd: item.year_prod,
    dailyOut: item.daily_out,
    monthSale: item.month_sale,
    yearSale: item.year_sale,
    monthOut: item.month_out,
    yearOut: item.year_out,
    capacity: +(baseCapacityMap.value[item.base] || 0).toFixed(2),
  }))
)

const tableData = computed(() => {
  return productionList.value.map((item, i) => ({
    key: i,
    base: item.base,
    category: item.category,
    dayLabel: queryPeriod.value === 'day' ? `${String(item.period || queryPoint.value).slice(5, 10)}` : String(item.period || queryPoint.value),
    dailyProd: item.daily_prod,
    dailyOut: item.daily_out,
    monthSale: item.month_sale,
    yearSale: item.year_sale,
    plan: item.plan_qty,
    actual: item.actual_qty,
    yearProd: item.year_prod,
    variance: item.variance_pct,
    utilization: `${item.utilization}%`
  }))
})

const chartData = computed(() => {
  return productionReportItems.value.map(item => ({
    base: item.base,
    plan: item.plan_qty,
    actual: item.actual_qty,
    utilization: item.utilization,
    kilnStopHours: item.kiln_stop_hours || 0,
    kilnStopTimes: item.kiln_stop_times || 0,
    dailyProd: item.daily_prod || 0,
    monthProd: item.month_prod || 0,
    yearProd: item.year_prod || 0,
    dailyOut: item.daily_out || 0,
    monthOut: item.month_out || 0,
    yearOut: item.year_out || 0,
    monthSale: item.month_sale || item.month_out || 0,
    yearSale: item.year_sale || item.year_out || 0,
  }))
})

const equipmentChartSource = computed(() => {
  if (equipmentViewMode.value === 'device') {
    if (selectedBase.value === 'all') {
      return equipmentDetailList.value.map(item => ({
        name: `${item.base}-${item.device}`,
        base: item.base,
        run_rate_day: Number(item.run_rate_day || 0),
        run_rate_month: Number(item.run_rate_month || 0),
        run_rate_year: Number(item.run_rate_year || 0),
        runtime_day: Number(item.runtime_day || 0),
        runtime_month: Number(item.runtime_month || 0),
        runtime_year: Number(item.runtime_year || 0),
      }))
    }
    return equipmentDetailList.value
      .filter(item => String(item.base) === selectedBase.value)
      .map(item => ({
        name: item.device,
        base: item.base,
        run_rate_day: Number(item.run_rate_day || 0),
        run_rate_month: Number(item.run_rate_month || 0),
        run_rate_year: Number(item.run_rate_year || 0),
        runtime_day: Number(item.runtime_day || 0),
        runtime_month: Number(item.runtime_month || 0),
        runtime_year: Number(item.runtime_year || 0),
      }))
  }
  return equipmentList.value.map(item => ({
    name: String(item.base).replace('基地', ''),
    base: item.base,
    run_rate_day: Number(item.run_rate_day || 0),
    run_rate_month: Number(item.run_rate_month || 0),
    run_rate_year: Number(item.run_rate_year || 0),
    runtime_day: Number(item.runtime_day || 0),
    runtime_month: Number(item.runtime_month || 0),
    runtime_year: Number(item.runtime_year || 0),
  }))
})

const stopChartSource = computed(() => {
  const period = equipmentMetric.value
  const periodKey = period === 'day' ? 'day' : (period === 'month' ? 'month' : 'year')
  const detailRows = selectedBase.value !== 'all'
    ? equipmentDetailList.value.filter(item => String(item.base) === selectedBase.value)
    : equipmentDetailList.value
  if (equipmentViewMode.value === 'device') {
    return detailRows.map(item => {
      const hours = Number(item[`stop_hours_${periodKey}`] || 0)
      const rate = Number(item[`run_rate_${periodKey}`] || 0)
      return {
        name: selectedBase.value === 'all' ? `${item.base}-${item.device}` : item.device,
        stop_hours: Number(hours.toFixed(2)),
        stop_count: rate <= 0 || hours > 0 ? 1 : 0,
        base: item.base,
      }
    })
  }
  const grouped = new Map<string, { stop_hours: number; stop_count: number }>()
  detailRows.forEach((item: any) => {
    const key = String(item.base)
    if (!grouped.has(key)) grouped.set(key, { stop_hours: 0, stop_count: 0 })
    const agg = grouped.get(key)!
    const hours = Number(item[`stop_hours_${periodKey}`] || 0)
    const rate = Number(item[`run_rate_${periodKey}`] || 0)
    agg.stop_hours += hours
    if (rate <= 0 || hours > 0) agg.stop_count += 1
  })
  return Array.from(grouped.entries()).map(([base, agg]) => ({
    name: base.replace('基地', ''),
    stop_hours: Number(agg.stop_hours.toFixed(2)),
    stop_count: agg.stop_count,
    base,
  }))
})

const stopReasonLegend = ['续停', '避峰', '检修', '故障', '其他']

function initCharts() {
  if (equipmentRef.value) {
    if (equipmentChart) equipmentChart.dispose()
    equipmentChart = echarts.init(equipmentRef.value)
    const equipData = equipmentChartSource.value
    const names = equipData.map(item => item.name)
    const rateField = equipmentMetric.value === 'day' ? 'run_rate_day' : (equipmentMetric.value === 'month' ? 'run_rate_month' : 'run_rate_year')
    const runtimeField = equipmentMetric.value === 'day' ? 'runtime_day' : (equipmentMetric.value === 'month' ? 'runtime_month' : 'runtime_year')
    equipmentChart.setOption({
      tooltip: { 
        trigger: 'axis',
        formatter: (params: any) => {
          const idx = params?.[0]?.dataIndex ?? 0
          const row = equipData[idx]
          if (!row) return ''
          const isDay = equipmentMetric.value === 'day'
          const isMonth = equipmentMetric.value === 'month'
          const label = isDay ? '日' : (isMonth ? '月' : '年')
          const rate = isDay ? row.run_rate_day : (isMonth ? row.run_rate_month : row.run_rate_year)
          const runtime = isDay ? row.runtime_day : (isMonth ? row.runtime_month : row.runtime_year)
          return [
            `<b>${row.name}</b>`,
            `${label}运转率：${rate}%`,
            `${label}运行时间：${runtime} h`,
          ].join('<br/>')
        }
      },
      legend: { data: ['运转率', '运行时间'], textStyle: { fontSize: 11 } },
      grid: { top: 36, right: 42, bottom: 30, left: 50 },
      xAxis: { type: 'category', data: names, axisLabel: { fontSize: 10 } },
      yAxis: [
        { type: 'value', name: '%', max: 120, axisLabel: { fontSize: 10 } },
        { type: 'value', name: 'h', axisLabel: { fontSize: 10 } }
      ],
      series: [
        { name: '运转率', type: 'line', smooth: true, data: equipData.map((b: any) => Number(b[rateField] || 0)), lineStyle: { color: '#1f6fff' }, itemStyle: { color: '#1f6fff' } },
        { name: '运行时间', type: 'bar', yAxisIndex: 1, data: equipData.map((b: any) => Number(b[runtimeField] || 0)), itemStyle: { color: '#52c41a', borderRadius: [4, 4, 0, 0] } },
      ]
    })
    equipmentChart.off('click')
    equipmentChart.on('click', (params: any) => {
      if (selectedBase.value === 'all' && equipmentViewMode.value === 'base') {
        const hit = equipmentList.value.find(item => String(item.base).replace('基地', '') === params.name)
        if (hit?.base) selectedBase.value = hit.base
      }
    })
  }
  if (kilnRef.value) {
    if (kilnChart) kilnChart.dispose()
    kilnChart = echarts.init(kilnRef.value)
    const stopData = stopChartSource.value
    const names = stopData.map(item => item.name)
    kilnChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['停窑时长', '停窑次数'], textStyle: { fontSize: 11 } },
      grid: { top: 36, right: 42, bottom: 30, left: 50 },
      xAxis: { type: 'category', data: names, axisLabel: { fontSize: 10 } },
      yAxis: [
        { type: 'value', name: '小时', axisLabel: { fontSize: 10 } },
        { type: 'value', name: '次', axisLabel: { fontSize: 10 }, minInterval: 1 }
      ],
      series: [
        { name: '停窑时长', type: 'bar', data: stopData.map(item => item.stop_hours), itemStyle: { color: '#faad14', borderRadius: [4, 4, 0, 0] } },
        { name: '停窑次数', type: 'line', yAxisIndex: 1, smooth: true, data: stopData.map(item => item.stop_count), lineStyle: { color: '#ff4d4f' }, itemStyle: { color: '#ff4d4f' } }
      ]
    })
    kilnChart.off('click')
    kilnChart.on('click', (params: any) => {
      if (equipmentViewMode.value === 'base' && selectedBase.value === 'all') {
        const hit = equipmentList.value.find(item => String(item.base).replace('基地', '') === params.name)
        if (hit?.base) selectedBase.value = hit.base
      }
    })
  }
  if (stopReasonRef.value) {
    if (stopReasonChart) stopReasonChart.dispose()
    stopReasonChart = echarts.init(stopReasonRef.value)
    if (selectedBase.value !== 'all') {
      const row = stopReasonList.value.find(item => item.base === selectedBase.value) || { 续停: 0, 避峰: 0, 检修: 0, 故障: 0, 其他: 0 }
      stopReasonChart.setOption({
        tooltip: { trigger: 'item' },
        legend: { orient: 'vertical', right: 4, top: 'center', textStyle: { fontSize: 11 } },
        series: [
          {
            type: 'pie',
            radius: ['38%', '68%'],
            center: ['35%', '50%'],
            data: stopReasonLegend.map(name => ({ name, value: Number(row[name] || 0) })),
            label: { fontSize: 10, formatter: '{b}:{c}' }
          }
        ]
      })
    } else {
      const names = stopReasonList.value.map(item => String(item.base).replace('基地', ''))
      stopReasonChart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: stopReasonLegend, textStyle: { fontSize: 10 } },
        grid: { top: 22, right: 10, bottom: 26, left: 38 },
        xAxis: { type: 'category', data: names, axisLabel: { fontSize: 10 } },
        yAxis: { type: 'value', axisLabel: { fontSize: 10 }, minInterval: 1 },
        series: stopReasonLegend.map(name => ({
          name,
          type: 'bar',
          stack: 'reason',
          data: stopReasonList.value.map(item => Number(item[name] || 0)),
        })),
      })
    }
  }
  if (reportRef.value) {
    if (reportChart) reportChart.dispose()
    reportChart = echarts.init(reportRef.value)
    const names = chartData.value.map(item => item.base.replace('基地', ''))
    const isMonth = overviewMode.value === 'month'
    reportChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: isMonth ? ['月计划', '月累计产量', '月出厂累计'] : ['年计划', '年累计产量', '年出厂累计'], textStyle: { fontSize: 11 } },
      grid: { top: 44, right: 22, bottom: 30, left: 50 },
      xAxis: { type: 'category', data: names, axisLabel: { fontSize: 10 } },
      yAxis: [{ type: 'value', name: '万吨', axisLabel: { fontSize: 10 } }],
      series: [
        { name: isMonth ? '月计划' : '年计划', type: 'bar', barMaxWidth: 26, data: chartData.value.map(item => isMonth ? item.plan : +(item.plan * 12).toFixed(2)), itemStyle: { color: '#7aa7ff' } },
        { name: isMonth ? '月累计产量' : '年累计产量', type: 'bar', barMaxWidth: 26, data: chartData.value.map(item => isMonth ? item.monthProd : item.yearProd), itemStyle: { color: '#1f6fff' } },
        { name: isMonth ? '月出厂累计' : '年出厂累计', type: 'bar', barMaxWidth: 26, data: chartData.value.map(item => isMonth ? item.monthOut : item.yearOut), itemStyle: { color: '#52c41a' } },
      ]
    })
  }
}

const handleResize = () => { equipmentChart?.resize(); kilnChart?.resize(); stopReasonChart?.resize(); reportChart?.resize() }

onMounted(() => {
  fetchTopData()
  fetchBottomData()
  window.addEventListener('resize', handleResize)
})
watch([() => appStore.queryNonce, () => appStore.timeMode, () => appStore.timePoint, () => appStore.dateRange, () => selectedBase.value, () => selectedCategory.value], () => {
  fetchTopData()
  fetchBottomData()
}, { deep: true })
watch(() => overviewMode.value, () => {
  initCharts()
})
watch(() => equipmentMetric.value, () => {
  initCharts()
})
watch(() => equipmentViewMode.value, () => {
  initCharts()
})
watch(() => selectedBase.value, (base) => {
  equipmentViewMode.value = base === 'all' ? 'base' : equipmentViewMode.value
  initCharts()
})
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  equipmentChart?.dispose()
  kilnChart?.dispose()
  stopReasonChart?.dispose()
  reportChart?.dispose()
})
</script>

<style scoped>
:deep(.equipment-child-row > td) {
  padding-top: 4px !important;
  padding-bottom: 4px !important;
  font-size: 12px;
}

:deep(.equipment-stop-row > td) {
  background: #fff7f7;
}

.stop-flag {
  display: inline-block;
  min-width: 40px;
  text-align: center;
  border-radius: 10px;
  padding: 0 8px;
  line-height: 20px;
  font-size: 12px;
}

.stop-flag-danger {
  background: #fff1f0;
  color: #cf1322;
}

.stop-flag-normal {
  background: #f6ffed;
  color: #389e0d;
}

.query-switch-row {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 10px;
}

.switch-label {
  font-size: 12px;
  color: var(--text-secondary);
}
</style>
