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
    default: '品类结构'
  },
  data: {
    type: Array as PropType<any[]>,
    default: () => []
  }
})

const chartRef = ref<HTMLElement>()

const getOption = (isDark: boolean): echarts.EChartsOption => {
  const textColor = getCssVar('--text-secondary')

  return {
    tooltip: { 
      trigger: 'item', 
      formatter: '{b}: {c}万吨 ({d}%)',
      backgroundColor: isDark ? 'rgba(30, 41, 59, 0.8)' : 'rgba(255, 255, 255, 0.9)',
      borderColor: isDark ? '#00D4FF' : '#E5E6EB',
      textStyle: { color: getCssVar('--text-primary') }
    },
    legend: { 
      bottom: 0, 
      textStyle: { color: textColor, fontSize: 11 } 
    },
    series: [{
      type: 'pie', radius: ['42%', '68%'], center: ['50%', '45%'],
      label: { color: textColor, fontSize: 11 },
      itemStyle: { borderColor: getCssVar('--card-bg'), borderWidth: 2 },
      data: props.data
    }]
  }
}

// 依赖项：data 变化时重绘
const dependencies = computed(() => [props.data])

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
