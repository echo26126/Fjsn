<template>
  <a-card class="trend-card" :bordered="false">
    <template #title>
      <span style="font-size: 14px; font-weight: 600">{{ title }}</span>
    </template>
    <div ref="chartRef" class="trend-chart"></div>
  </a-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import { useAppStore } from '@/stores/app'
import { useECharts, getCssVar } from '@/composables/useECharts'

const props = defineProps({
  title: {
    type: String,
    default: '月度趋势'
  },
  timePoint: {
    type: String,
    default: ''
  }
})

const chartRef = ref<HTMLElement>()
const appStore = useAppStore()

const getOption = (isDark: boolean): echarts.EChartsOption => {
  const textColor = getCssVar('--text-secondary')
  const primaryColor = getCssVar('--primary-color')
  const borderColor = isDark ? 'rgba(0, 212, 255, 0.2)' : '#E5E6EB'

  const months = Array.from({ length: 12 }, (_, i) => 
    dayjs(props.timePoint || appStore.timePoint).subtract(11 - i, 'month').format('M月')
  )

  return {
    tooltip: { 
      trigger: 'axis',
      backgroundColor: isDark ? 'rgba(30, 41, 59, 0.8)' : 'rgba(255, 255, 255, 0.9)',
      borderColor: isDark ? '#00D4FF' : '#E5E6EB',
      textStyle: { color: getCssVar('--text-primary') }
    },
    legend: { 
      data: ['产量', '销量'], 
      top: 0, 
      textStyle: { color: textColor, fontSize: 11 } 
    },
    grid: { top: 30, right: 15, bottom: 24, left: 40 },
    xAxis: { 
      type: 'category', 
      data: months, 
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
        name: '产量', type: 'line', smooth: true,
        data: [58, 52, 61, 64, 59, 68, 72, 70, 65, 68, 71, 68],
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: isDark ? 'rgba(0, 212, 255, 0.3)' : 'rgba(22, 119, 255, 0.2)' }, { offset: 1, color: 'transparent' }]) },
        lineStyle: { color: primaryColor, width: 2 }, 
        itemStyle: { color: primaryColor }
      },
      {
        name: '销量', type: 'line', smooth: true,
        data: [55, 50, 58, 60, 56, 65, 69, 67, 62, 64, 68, 62],
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(54, 207, 201, 0.3)' }, { offset: 1, color: 'transparent' }]) },
        lineStyle: { color: '#36CFC9', width: 2 }, 
        itemStyle: { color: '#36CFC9' }
      }
    ]
  }
}

// 依赖项：timePoint 变化时重绘
const dependencies = computed(() => [props.timePoint])

useECharts(chartRef, getOption, [dependencies])
</script>

<style scoped>
.trend-card :deep(.ant-card-body) {
  padding: 8px;
}

.trend-chart {
  width: 100%;
  height: 200px;
}
</style>
