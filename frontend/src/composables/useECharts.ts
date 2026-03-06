import { ref, onMounted, onUnmounted, nextTick, watch, Ref } from 'vue'
import * as echarts from 'echarts'
import { useAppStore } from '@/stores/app'

/**
 * ECharts 通用 Hook
 * @param chartRef 图表 DOM 容器的引用
 * @param optionFactory 获取 Option 的工厂函数，支持根据是否深色模式动态生成
 * @param dependencies 触发图表重绘的依赖项数组
 */
export function useECharts(
  chartRef: Ref<HTMLElement | undefined>,
  optionFactory: (isDark: boolean) => echarts.EChartsOption,
  dependencies: Ref<any>[] = []
) {
  let chartInstance: echarts.ECharts | null = null
  const appStore = useAppStore()

  // 初始化图表
  const initChart = () => {
    if (!chartRef.value) return
    if (!chartInstance) {
      chartInstance = echarts.init(chartRef.value)
    }
    updateChart()
  }

  // 更新图表配置
  const updateChart = () => {
    if (!chartInstance) return
    const isDark = appStore.theme === 'dark'
    const option = optionFactory(isDark)
    chartInstance.setOption(option, true)
  }

  // 处理窗口大小变化
  const handleResize = () => {
    chartInstance?.resize()
  }

  // 监听依赖变化
  watch(
    [() => appStore.theme, ...dependencies],
    () => {
      nextTick(() => {
        // 如果实例不存在（可能还没挂载），尝试初始化
        if (!chartInstance) {
          initChart()
        } else {
          updateChart()
        }
      })
    },
    { deep: true }
  )

  onMounted(() => {
    nextTick(() => {
      initChart()
      window.addEventListener('resize', handleResize)
    })
  })

  onUnmounted(() => {
    window.removeEventListener('resize', handleResize)
    chartInstance?.dispose()
    chartInstance = null
  })

  return {
    chartInstance,
    updateChart,
    resize: handleResize
  }
}

/**
 * 获取 CSS 变量值的辅助函数
 */
export function getCssVar(name: string) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}
