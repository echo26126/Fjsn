<template>
  <div class="map-card" :style="{ background: 'var(--card-bg)', borderColor: 'var(--border-color)' }">
    <div class="map-card-header" :style="{ borderBottomColor: 'var(--border-color)' }">
      <span class="map-title" :style="{ color: 'var(--text-primary)' }">
        {{ title }}
      </span>
    </div>
    <div ref="chartRef" class="map-chart" :style="{ background: 'transparent' }"></div>

    <!-- 同城多区域选择弹层 -->
    <div v-if="regionSelector.visible" class="region-selector" 
         :style="{ left: regionSelector.x + 'px', top: regionSelector.y + 'px' }">
      <div class="selector-title">{{ regionSelector.city }}</div>
      <div class="selector-list">
        <div v-for="region in regionSelector.candidates" :key="region" 
             class="selector-item" @click="selectRegion(region)">
          {{ region }}
        </div>
      </div>
      <div class="selector-mask" @click="closeSelector"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick, PropType } from 'vue'
import * as echarts from 'echarts'
import { useAppStore } from '@/stores/app'
import { useECharts, getCssVar } from '@/composables/useECharts'

const props = defineProps({
  viewMode: {
    type: String as PropType<'production' | 'sales'>,
    default: 'production'
  },
  productionData: {
    type: Array as PropType<any[]>,
    default: () => []
  },
  salesData: {
    type: Array as PropType<any[]>,
    default: () => []
  },
  selectedSalesRegion: {
    type: String,
    default: 'all'
  },
  title: {
    type: String,
    default: '分布图'
  }
})
const emit = defineEmits<{
  (e: 'point-click', payload: { type: 'production' | 'sales'; name: string }): void
}>()

const chartRef = ref<HTMLElement>()
const appStore = useAppStore()
const isMapLoaded = ref(false)
const cityClickCursor = ref<Record<string, number>>({})

const regionSelector = ref({
  visible: false,
  x: 0,
  y: 0,
  city: '',
  candidates: [] as string[]
})

const regionColorMap = computed(() => {
  const map = new Map<string, string>()
  props.salesData.forEach(item => {
    map.set(item.displayName, item.color)
  })
  return map
})

// 初始化地图数据
onMounted(async () => {
  if (!echarts.getMap('fujian')) {
    try {
      const resp = await fetch('https://geo.datav.aliyun.com/areas_v3/bound/350000_full.json')
      const geoJson = await resp.json()
      echarts.registerMap('fujian', geoJson)
      isMapLoaded.value = true
    } catch {
      console.warn('GeoJSON 加载失败')
    }
  } else {
    isMapLoaded.value = true
  }
})

function parseSalesCities(cityText: string) {
  return cityText
    .split('、')
    .map(v => v.replace(/（.*?）/g, '').trim())
    .filter(Boolean)
}

const salesCityInfo = computed(() => {
  const cityInfo = new Map<string, { value: number; regions: string[]; color: string }>()
  props.salesData.forEach(region => {
    const cities = parseSalesCities(region.city || '')
    cities.forEach(city => {
      const hit = cityInfo.get(city)
      if (!hit) {
        cityInfo.set(city, { value: region.value, regions: [region.displayName], color: region.color })
      } else {
        const previous = hit.value
        hit.value += region.value
        hit.regions.push(region.displayName)
        if (region.value > previous) {
          hit.color = region.color
        }
      }
    })
  })
  return cityInfo
})

const regionNames = ['南平市', '宁德市', '福州市', '莆田市', '泉州市', '三明市', '厦门市', '漳州市', '龙岩市']

const getOption = (isDark: boolean): echarts.EChartsOption => {
  // 如果地图未加载完成，返回空配置或 loading 状态
  if (!isMapLoaded.value) return {}

  const textColor = getCssVar('--text-primary')
  const subTextColor = getCssVar('--text-secondary')
  const areaColor = getCssVar('--map-base-color')
  const borderColor = getCssVar('--map-border-color')
  const waterColor = getCssVar('--map-water-color')
  const primaryColor = getCssVar('--primary-color')
  const shadowColor = isDark ? 'rgba(108, 123, 255, 0.5)' : 'rgba(0, 0, 0, 0.08)'

  const productionScatter = props.productionData.map(b => ({
    name: b.name,
    value: [b.coord[0], b.coord[1], b.actual]
  }))
  const productionTopPoints = props.productionData.map(b => ({
    name: b.name,
    value: [b.coord[0], b.coord[1] + 0.34, b.actual]
  }))
  const productionBeamLines = props.productionData.map(b => ({
    name: b.name,
    coords: [[b.coord[0], b.coord[1] + 0.2], [b.coord[0], b.coord[1] + 0.03]], // 缩短光束高度
    value: b.actual
  }))

  const lightMapRegions = [
    { name: '南平市', itemStyle: { areaColor: '#54B4E3' } },
    { name: '宁德市', itemStyle: { areaColor: '#3D8FC8' } },
    { name: '三明市', itemStyle: { areaColor: '#D0E9F8' } },
    { name: '福州市', itemStyle: { areaColor: '#6ABBE8' } },
    { name: '龙岩市', itemStyle: { areaColor: '#E1F1FB' } },
    { name: '莆田市', itemStyle: { areaColor: '#8FCDEE' } },
    { name: '泉州市', itemStyle: { areaColor: '#ABD9F3' } },
    { name: '厦门市', itemStyle: { areaColor: '#C3E4F8' } },
    { name: '漳州市', itemStyle: { areaColor: '#B6DDF5' } },
  ]

  const getCityRegionColor = (cityName: string) => {
    const hit = salesCityInfo.value.get(cityName)
    if (!hit?.regions?.length) return isDark ? '#2a3450' : '#E1F1FB'
    const regions = [...new Set(hit.regions)]
    if (regions.length === 1) {
      return regionColorMap.value.get(regions[0]) || hit.color
    }
    if (props.selectedSalesRegion !== 'all' && regions.includes(props.selectedSalesRegion)) {
      return regionColorMap.value.get(props.selectedSalesRegion) || hit.color
    }
    // 多区域未选中特定区域时，返回该地市下第一个区域的颜色，确保颜色有区分
    // 或者可以返回一个混合色/特殊色，但这里优先显示主区域颜色
    return regionColorMap.value.get(regions[0]) || hit.color
  }

  const salesGeoRegions = regionNames.map(cityName => {
    const hit = salesCityInfo.value.get(cityName)
    const selected = props.selectedSalesRegion === 'all' || !!hit?.regions?.includes(props.selectedSalesRegion)
    return {
      name: cityName,
      itemStyle: {
        areaColor: getCityRegionColor(cityName),
        borderColor: isDark ? '#9aa8d4' : '#6BA8D8',
        opacity: props.selectedSalesRegion === 'all' ? 1 : (selected ? 1 : 0.26),
      },
    }
  })

  const salesMapData = regionNames.map(cityName => {
    const hit = salesCityInfo.value.get(cityName)
    const selected = props.selectedSalesRegion === 'all' || !!hit?.regions?.includes(props.selectedSalesRegion)
    return {
      name: cityName,
      value: hit?.value || 0,
      itemStyle: {
        areaColor: getCityRegionColor(cityName),
        opacity: props.selectedSalesRegion === 'all' ? 1 : (selected ? 1 : 0.3),
      },
      label: {
        color: selected ? (isDark ? '#f5f7ff' : '#1D2129') : (isDark ? '#6b789a' : '#9aa5b8')
      }
    }
  })

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: isDark ? 'rgba(30, 41, 59, 0.8)' : 'rgba(255, 255, 255, 0.95)',
      borderColor: isDark ? '#00D4FF' : '#E5E6EB',
      borderWidth: 1,
      textStyle: { color: textColor, fontSize: 12 },
      shadowBlur: isDark ? 8 : 10,
      shadowColor: shadowColor,
      padding: [10, 15],
      formatter: (p: any) => {
        if (props.viewMode === 'sales' && p.name) {
          const hit = salesCityInfo.value.get(p.name)
          if (hit) {
            return `<div style="font-weight:600;margin-bottom:4px;color:${isDark ? '#fff' : '#1f2329'}">${p.name}</div><div style="margin-bottom:2px">销量: <span style="font-weight:600;color:${isDark ? '#00D4FF' : '#1677FF'}">${hit.value.toFixed(2)} 万吨</span></div><div style="color:${isDark ? '#9fb2c8' : '#4b5f79'}">销售区域：${[...new Set(hit.regions)].join('、')}</div>`
          }
          return `<div style="font-weight:600;color:${isDark ? '#fff' : '#1f2329'}">${p.name}</div>`
        }
        if (p.seriesType === 'scatter' || p.seriesType === 'effectScatter') {
          if (props.viewMode === 'sales') {
            return `<div style="font-weight:600;margin-bottom:4px;color:${isDark ? '#fff' : '#1f2329'}">${p.data.fullName}</div><div style="margin-bottom:2px">销量: <span style="font-weight:600;color:${isDark ? '#00D4FF' : '#1677FF'}">${p.value[2]} 万吨</span></div><div style="color:${isDark ? '#9fb2c8' : '#4b5f79'}">对应地市：${p.data.city}</div>`
          }
          return `<div style="font-weight:600;margin-bottom:4px;color:${isDark ? '#fff' : '#1f2329'}">${p.name}</div><div>产量: <span style="font-weight:600;color:${isDark ? '#00D4FF' : '#1677FF'}">${p.value[2]} 万吨</span></div>`
        }
        return `<b>${p.name}</b>`
      }
    },
    geo: {
      map: 'fujian',
      roam: false,
      zoom: 1.15,
      center: [118.2, 25.8],
      itemStyle: {
        areaColor: isDark ? '#1a2238' : areaColor,
        borderColor: isDark ? '#5f6f98' : borderColor,
        borderWidth: isDark ? 1.8 : 1,
        shadowColor: shadowColor,
        shadowBlur: isDark ? 18 : 0,
      },
      emphasis: {
        itemStyle: {
          areaColor: isDark ? '#40558a' : '#7FC5EC',
          borderColor: isDark ? '#c5d2ff' : '#FFFFFF',
          borderWidth: 2,
          shadowBlur: isDark ? 22 : 8,
          shadowColor: isDark ? 'rgba(122, 140, 255, 0.9)' : 'rgba(61, 88, 152, 0.35)',
        },
        label: { 
          show: true, 
          color: isDark ? '#FFFFFF' : '#1D2129', 
          fontSize: 12, 
          fontWeight: 'bold' 
        }
      },
      label: {
        show: true,
        fontSize: 10,
        color: isDark ? subTextColor : 'rgba(36,58,86,0.72)',
      },
      regions: isDark ? [
        {
          name: 'water',
          itemStyle: {
            areaColor: waterColor,
            borderColor: isDark ? '#596a99' : '#4E5969',
          }
        }
      ] : lightMapRegions,
      ...(props.viewMode === 'sales' ? { regions: salesGeoRegions } : {})
    },
    series: props.viewMode === 'production'
      ? [
          {
            type: 'effectScatter',
            coordinateSystem: 'geo',
            data: productionScatter,
            symbolSize: (val: number[]) => Math.max(14, Math.min(24, val[2] * 1.2)),
            rippleEffect: {
              brushType: 'stroke',
              scale: 3.6,
              period: 3
            },
            itemStyle: {
              color: isDark ? 'rgba(111, 150, 239, 0.35)' : 'rgba(22,119,255,0.22)',
              opacity: appStore.selectedBase === 'all' ? 1 : 0.35,
            },
            z: 4,
          },
          {
            type: 'lines',
            coordinateSystem: 'geo',
            data: productionBeamLines,
            polyline: false,
            lineStyle: {
              width: 2,
              color: isDark ? '#d4deff' : '#4f9fff',
              opacity: 0.9
            },
            effect: {
              show: true,
              period: 2.4,
              trailLength: 0.4,
              symbolSize: 2.5,
              color: isDark ? '#ffffff' : '#1677FF'
            },
            z: 3
          },
          {
            type: 'scatter',
            coordinateSystem: 'geo',
            data: productionScatter,
            symbol: 'circle',
            symbolSize: (val: number[]) => Math.max(8, Math.min(14, val[2] * 0.8)),
            itemStyle: (p: any) => ({
              color: isDark ? '#7ea3ff' : '#1677FF',
              shadowBlur: isDark ? 16 : 10,
              shadowColor: isDark ? 'rgba(126,163,255,0.9)' : 'rgba(22,119,255,0.55)',
              borderWidth: 2,
              borderColor: '#ffffff',
              opacity: appStore.selectedBase === 'all' || p.name === appStore.selectedBase ? 1 : 0.35
            }),
            z: 5
          },
          {
            type: 'scatter',
            coordinateSystem: 'geo',
            data: productionTopPoints,
            symbol: 'circle',
            symbolSize: 6,
            itemStyle: (p: any) => ({
              color: '#ffffff',
              shadowBlur: 12,
              shadowColor: isDark ? 'rgba(255,255,255,0.95)' : 'rgba(22,119,255,0.45)',
              opacity: appStore.selectedBase === 'all' || p.name === appStore.selectedBase ? 1 : 0.35,
            }),
            label: {
              show: true,
              formatter: (p: any) => p.name.replace('基地', ''),
              position: 'top',
              fontSize: 10,
              fontWeight: 600,
              color: isDark ? '#dfe6ff' : '#243A56',
              distance: 5,
            },
            emphasis: { scale: 1.1 },
            z: 6
          }
        ]
      : [
          {
            type: 'map',
            map: 'fujian',
            geoIndex: 0,
            roam: false,
            data: salesMapData,
            selectedMode: false,
            label: {
              show: true,
              fontSize: 10,
              color: isDark ? '#f2f5ff' : '#1D2129'
            },
            itemStyle: {
              borderColor: isDark ? '#a7b4da' : '#6BA8D8',
              borderWidth: isDark ? 1.4 : 1
            },
            emphasis: {
              label: { color: '#ffffff', fontWeight: 700 },
              itemStyle: {
                borderColor: isDark ? '#ffffff' : '#1D2129',
                borderWidth: 2
              }
            },
            z: 2
          },
          {
            type: 'scatter',
            coordinateSystem: 'geo',
            data: [],
          },
        ]
  }
}

// 依赖项：增加 isMapLoaded
const dependencies = computed(() => [props.viewMode, props.productionData, props.salesData, props.selectedSalesRegion, appStore.selectedBase, isMapLoaded.value])

useECharts(chartRef, getOption, [dependencies])

function closeSelector() {
  regionSelector.value.visible = false
}

function selectRegion(region: string) {
  emit('point-click', { type: 'sales', name: region })
  closeSelector()
}

function bindMapClick() {
  if (!chartRef.value) return
  const chart = echarts.getInstanceByDom(chartRef.value)
  if (!chart) return
  chart.off('click')
  chart.on('click', (p: any) => {
    // 阻止事件冒泡，防止触发下面的 ZR click 关闭弹层
    if (p.event && p.event.event) {
      p.event.event.stopPropagation?.()
      // 标记点击事件，防止 ZR click 误判
      ;(chart as any)._isClickingMap = true
      setTimeout(() => {
        ;(chart as any)._isClickingMap = false
      }, 100)
    }

    if (props.viewMode === 'production' && (p.seriesType === 'scatter' || p.seriesType === 'effectScatter') && p.name) {
      emit('point-click', { type: 'production', name: p.name })
      return
    }
    if (props.viewMode === 'sales' && p.name) {
      const hit = salesCityInfo.value.get(p.name)
      if (hit?.regions?.length) {
        const candidates = [...new Set(hit.regions)]
        if (candidates.length > 1) {
          // 弹出选择框
          const e = p.event.event
          regionSelector.value = {
            visible: true,
            x: e.clientX + 10,
            y: e.clientY + 10,
            city: p.name,
            candidates: candidates
          }
        } else {
          // 单个区域直接选中
          emit('point-click', { type: 'sales', name: candidates[0] })
        }
      }
    }
  })
  
  // 点击空白处关闭弹层
  chart.getZr().on('click', (params) => {
    // 如果刚刚触发了 map click，不要关闭
    if ((chart as any)._isClickingMap) return
    
    if (!params.target) {
      closeSelector()
    }
  })
}

watch(dependencies, () => {
  nextTick(() => bindMapClick())
}, { deep: true })
</script>

<style scoped>
.map-card {
  background: var(--card-bg);
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--border-color);
  box-shadow: var(--card-shadow);
  position: relative;
}

.map-card-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
}

.map-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  position: relative;
  padding-left: 10px;
}

.map-title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 14px;
  background: var(--primary-color);
  border-radius: 2px;
  box-shadow: none;
}

.map-chart {
  width: 100%;
  height: 480px;
  background: transparent;
}

.region-selector {
  position: fixed; /* 改为 fixed 定位，确保不被父容器遮挡 */
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border-radius: 4px;
  z-index: 9999; /* 提高层级 */
  min-width: 120px;
  padding: 4px 0;
}

.selector-title {
  padding: 6px 12px;
  font-size: 12px;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-color);
  background: rgba(0, 0, 0, 0.02);
}

.selector-item {
  padding: 8px 12px;
  font-size: 13px;
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s;
}

.selector-item:hover {
  background: var(--primary-color);
  color: #fff;
}

.selector-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: -1;
}
</style>
