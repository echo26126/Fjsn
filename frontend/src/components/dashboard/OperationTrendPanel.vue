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
  salesItems: Array<{ spec: string; package: string; qty: number }>
}>()

const chartRef = ref<HTMLElement>()

const panelTitle = computed(() => {
  if (props.viewMode === 'sales') return '销售品类结构（型号×规格）'
  if (props.selectedBase !== 'all') return `${props.selectedBase}12月每日库存趋势`
  return '基地库存结构'
})

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

  const sourceRows = (props.salesItems || []).map(row => ({
    model: String(row.spec || '').trim() || '未分类',
    pkg: String(row.package || '').trim() || '未标注',
    qty: Number(row.qty || 0),
  }))
  const modelList = Array.from(new Set(sourceRows.map(item => item.model)))
  const packageOrder = ['熟料', '散', '袋', '未标注']
  const packageList = Array.from(new Set(sourceRows.map(item => item.pkg))).sort((a, b) => {
    const ia = packageOrder.indexOf(a)
    const ib = packageOrder.indexOf(b)
    return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib)
  })
  const modelPackageMap = new Map<string, number>()
  sourceRows.forEach(item => {
    const key = `${item.model}__${item.pkg}`
    modelPackageMap.set(key, (modelPackageMap.get(key) || 0) + item.qty)
  })
  const colorMap: Record<string, string> = {
    '熟料': isDark ? '#8E7CFF' : '#6f5ef9',
    '散': isDark ? '#00D4FF' : '#2F8CFF',
    '袋': isDark ? '#2ECFD1' : '#15b9bb',
    '未标注': '#94a3b8',
  }
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: packageList, top: 0, textStyle: { color: textColor, fontSize: 11 } },
    grid: { top: 30, right: 16, bottom: 28, left: 46 },
    xAxis: {
      type: 'category',
      data: modelList,
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
    series: packageList.map((pkg, idx) => ({
      name: pkg,
      type: 'bar',
      stack: 'qty',
      barMaxWidth: 24,
      data: modelList.map(model => +(modelPackageMap.get(`${model}__${pkg}`) || 0).toFixed(2)),
      itemStyle: {
        color: colorMap[pkg] || primaryColor,
        borderRadius: idx === packageList.length - 1 ? [4, 4, 0, 0] : [0, 0, 0, 0]
      }
    }))
  }
}

const dependencies = computed(() => [props.viewMode, props.selectedBase, props.inventoryRows, props.dailyInventory, props.salesTrend, props.salesItems])
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
