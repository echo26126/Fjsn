<template>
  <a-card :bordered="false" class="bottom-chart-card">
    <template #title>
      <span style="font-size: 14px; font-weight: 600">{{ title }}</span>
    </template>
    <div ref="chartRef" class="bottom-chart"></div>
  </a-card>
</template>

<script setup lang="ts">
import { ref, computed, PropType } from 'vue'
import * as echarts from 'echarts'
import { useECharts, getCssVar } from '@/composables/useECharts'

const props = defineProps({
  title: {
    type: String,
    default: '计划 vs 实际'
  },
  planData: {
    type: Array as PropType<number[]>,
    default: () => []
  },
  actualData: {
    type: Array as PropType<number[]>,
    default: () => []
  },
  categories: {
    type: Array as PropType<string[]>,
    default: () => []
  }
})

const chartRef = ref<HTMLElement>()

const getOption = (isDark: boolean): echarts.EChartsOption => {
  const textColor = getCssVar('--text-secondary')
  const primaryColor = getCssVar('--primary-color')
  const borderColor = isDark ? 'rgba(0, 212, 255, 0.2)' : '#E5E6EB'

  return {
    tooltip: { 
      trigger: 'axis',
      backgroundColor: isDark ? 'rgba(30, 41, 59, 0.8)' : 'rgba(255, 255, 255, 0.9)',
      borderColor: isDark ? '#00D4FF' : '#E5E6EB',
      textStyle: { color: getCssVar('--text-primary') }
    },
    legend: { 
      data: ['计划', '实际'], 
      top: 0, 
      textStyle: { color: textColor, fontSize: 11 } 
    },
    grid: { top: 30, right: 15, bottom: 24, left: 40 },
    xAxis: { 
      type: 'category', 
      data: props.categories, 
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
        name: '计划', type: 'bar', 
        data: props.planData, 
        itemStyle: { 
          color: isDark ? 'rgba(0, 212, 255, 0.32)' : '#97B6D6',
          borderRadius: [3, 3, 0, 0] 
        } 
      },
      { 
        name: '实际', type: 'bar', 
        data: props.actualData, 
        itemStyle: { color: primaryColor, borderRadius: [3, 3, 0, 0] } 
      },
    ]
  }
}

// 依赖项
const dependencies = computed(() => [props.planData, props.actualData, props.categories])

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
