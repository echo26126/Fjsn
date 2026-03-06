<template>
  <a-card class="trend-card" :bordered="false">
    <template #title>
      <span style="font-size: 14px; font-weight: 600">{{ panelTitle }}</span>
    </template>
    <div ref="chartRef" class="trend-chart"></div>
  </a-card>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import * as echarts from 'echarts'
import { useECharts, getCssVar } from '@/composables/useECharts'

const props = defineProps<{
  viewMode: 'production' | 'sales'
  selectedBase: string
  inventoryRows: Array<{ base: string; clinker: number; cement: number }>
  dailyInventory: { days: string[]; clinker_inventory: number[]; cement_inventory: number[] }
  salesTrend: { months: string[]; qty: number[]; avg_price: number[] }
}>()

const chartRef = ref<HTMLElement>()

const panelTitle = computed(() => {
  if (props.viewMode === 'sales') return '销售月度趋势'
  if (props.selectedBase !== 'all') return `${props.selectedBase}12月每日库存趋势`
  return '基地库存结构'
})

const formatMonthLabel = (raw: string) => {
  if (/^\d{4}-\d{2}$/.test(raw)) {
    return `${Number(raw.slice(5, 7))}月`
  }
  if (/^\d{4}$/.test(raw)) {
    return `${raw}年`
  }
  return raw
}

const getOption = (isDark: boolean): echarts.EChartsOption => {
  const textColor = getCssVar('--text-secondary')
  const borderColor = isDark ? 'rgba(0, 212, 255, 0.2)' : '#E5E6EB'
  const primaryColor = getCssVar('--primary-color')

  if (props.viewMode === 'production') {
    if (props.selectedBase !== 'all' && (props.dailyInventory?.days || []).length) {
      return {
        tooltip: { trigger: 'axis' },
        legend: { data: ['熟料库存', '水泥库存'], top: 0, textStyle: { color: textColor, fontSize: 11 } },
        grid: { top: 30, right: 15, bottom: 28, left: 46 },
        xAxis: {
          type: 'category',
          data: props.dailyInventory.days.map(day => day.replace('12月', '')),
          axisLabel: { color: textColor, fontSize: 10 },
          axisLine: { lineStyle: { color: borderColor } }
        },
        yAxis: {
          type: 'value',
          name: '万吨',
          nameTextStyle: { color: textColor, fontSize: 10 },
          axisLabel: { color: textColor, fontSize: 10 },
          splitLine: { lineStyle: { color: borderColor, type: 'dashed' } }
        },
        series: [
          {
            name: '熟料库存',
            type: 'line',
            smooth: true,
            data: props.dailyInventory.clinker_inventory,
            lineStyle: { color: isDark ? '#5B8FF9' : '#3D5898', width: 2 },
            itemStyle: { color: isDark ? '#5B8FF9' : '#3D5898' },
            areaStyle: { color: isDark ? 'rgba(91,143,249,0.20)' : 'rgba(61,88,152,0.14)' }
          },
          {
            name: '水泥库存',
            type: 'line',
            smooth: true,
            data: props.dailyInventory.cement_inventory,
            lineStyle: { color: isDark ? '#7fb6ff' : '#6B8FE8', width: 2 },
            itemStyle: { color: isDark ? '#7fb6ff' : '#6B8FE8' },
            areaStyle: { color: isDark ? 'rgba(127,182,255,0.18)' : 'rgba(107,143,232,0.12)' }
          }
        ]
      }
    }
    const rows = props.inventoryRows.length
      ? props.inventoryRows
      : [{ base: '暂无数据', clinker: 0, cement: 0 }]
    return {
      tooltip: { trigger: 'axis' },
      legend: { data: ['熟料库存', '水泥库存'], top: 0, textStyle: { color: textColor, fontSize: 11 } },
      grid: { top: 30, right: 15, bottom: 28, left: 46 },
      xAxis: {
        type: 'category',
        data: rows.map(row => row.base.replace('基地', '')),
        axisLabel: { color: textColor, fontSize: 10 },
        axisLine: { lineStyle: { color: borderColor } }
      },
      yAxis: {
        type: 'value',
        name: '万吨',
        nameTextStyle: { color: textColor, fontSize: 10 },
        axisLabel: { color: textColor, fontSize: 10 },
        splitLine: { lineStyle: { color: borderColor, type: 'dashed' } }
      },
      series: [
        {
          name: '熟料库存',
          type: 'bar',
          data: rows.map(row => row.clinker),
          barMaxWidth: 26,
          itemStyle: { color: isDark ? '#5B8FF9' : '#3D5898', borderRadius: [5, 5, 0, 0] }
        },
        {
          name: '水泥库存',
          type: 'bar',
          data: rows.map(row => row.cement),
          barMaxWidth: 26,
          itemStyle: { color: isDark ? '#7fb6ff' : '#6B8FE8', borderRadius: [5, 5, 0, 0] }
        }
      ]
    }
  }

  const months = (props.salesTrend?.months || []).map(formatMonthLabel)
  const qty = props.salesTrend?.qty || []
  const avgPrice = props.salesTrend?.avg_price || []
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['出库量', '均价'], top: 0, textStyle: { color: textColor, fontSize: 11 } },
    grid: { top: 30, right: 46, bottom: 28, left: 46 },
    xAxis: {
      type: 'category',
      data: months,
      axisLabel: { color: textColor, fontSize: 10 },
      axisLine: { lineStyle: { color: borderColor } }
    },
    yAxis: [
      {
        type: 'value',
        name: '万吨',
        nameTextStyle: { color: textColor, fontSize: 10 },
        axisLabel: { color: textColor, fontSize: 10 },
        splitLine: { lineStyle: { color: borderColor, type: 'dashed' } }
      },
      {
        type: 'value',
        name: '元/吨',
        nameTextStyle: { color: textColor, fontSize: 10 },
        axisLabel: { color: textColor, fontSize: 10 },
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: '出库量',
        type: 'bar',
        data: qty,
        barMaxWidth: 24,
        itemStyle: { color: primaryColor, borderRadius: [5, 5, 0, 0] }
      },
      {
        name: '均价',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        data: avgPrice,
        lineStyle: { color: '#faad14', width: 2 },
        itemStyle: { color: '#faad14' }
      }
    ]
  }
}

const dependencies = computed(() => [props.viewMode, props.selectedBase, props.inventoryRows, props.dailyInventory, props.salesTrend])
useECharts(chartRef, getOption, [dependencies])
</script>

<style scoped>
.trend-card :deep(.ant-card-body) {
  padding: 8px;
}

.trend-chart {
  width: 100%;
  height: 220px;
}
</style>
