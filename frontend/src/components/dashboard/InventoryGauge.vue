<template>
  <a-card :bordered="false" class="bottom-chart-card">
    <template #title>
      <span style="font-size: 14px; font-weight: 600">{{ title }}</span>
    </template>
    <div ref="chartRef" class="bottom-chart"></div>
  </a-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import * as echarts from 'echarts'
import { useECharts, getCssVar } from '@/composables/useECharts'

const props = defineProps({
  title: {
    type: String,
    default: '库容占比'
  },
  percent: {
    type: Number,
    default: 0
  }
})

const chartRef = ref<HTMLElement>()

const getOption = (isDark: boolean): echarts.EChartsOption => {
  const textColor = getCssVar('--text-secondary')

  return {
    series: [
      {
        type: 'gauge',
        startAngle: 210,
        endAngle: -30,
        min: 0,
        max: 100,
        pointer: { show: false },
        progress: { show: true, overlap: false, roundCap: true, clip: false },
        axisLine: { lineStyle: { width: 16, color: [[1, isDark ? '#1f3148' : '#E8EEF5']] } },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        detail: {
          fontSize: 24,
          fontWeight: 700,
          formatter: '{value}%',
          color: isDark ? '#FFFFFF' : '#1677FF',
          offsetCenter: [0, '38%']
        },
        title: {
          fontSize: 12,
          offsetCenter: [0, '65%'],
          color: textColor
        },
        data: [
          {
            value: props.percent,
            name: '总库容占比',
            itemStyle: {
              color: isDark
                ? new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#00A8FF' }, { offset: 1, color: '#00D4FF' }])
                : new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#4F9BFF' }, { offset: 1, color: '#7EC3FF' }])
            }
          }
        ]
      }
    ]
  }
}

// 依赖项
const dependencies = computed(() => [props.percent])

useECharts(chartRef, getOption, [dependencies])
</script>

<style scoped>
.bottom-chart-card {
  flex: 1;
}
.bottom-chart {
  width: 100%;
  height: 240px;
}
</style>
