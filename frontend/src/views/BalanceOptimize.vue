<template>
  <div class="page-container">
    <div class="page-header">
      <span class="page-title">产销平衡</span>
      <a-space>
        <a-button type="primary" size="small" :loading="optimizing" @click="runOptimize">
          <template #icon><ThunderboltOutlined /></template>
          运行优化
        </a-button>
        <a-button size="small"><DownloadOutlined /> 导出报告</a-button>
      </a-space>
    </div>

    <!-- 预警卡片 -->
    <div class="alert-section" style="margin-bottom: 16px">
      <a-card :bordered="false" title="预警概览" size="small">
        <div class="alert-grid">
          <div v-for="alert in alerts" :key="alert.id" class="alert-item" :class="alert.level">
            <div class="alert-icon">
              <WarningOutlined v-if="alert.level === 'danger'" />
              <ExclamationCircleOutlined v-else-if="alert.level === 'warning'" />
              <InfoCircleOutlined v-else />
            </div>
            <div class="alert-content">
              <div class="alert-title">{{ alert.title }}</div>
              <div class="alert-desc">{{ alert.description }}</div>
            </div>
            <a-tag :color="alert.level === 'danger' ? 'red' : alert.level === 'warning' ? 'orange' : 'blue'">
              {{ alert.level === 'danger' ? '严重' : alert.level === 'warning' ? '警告' : '提示' }}
            </a-tag>
          </div>
        </div>
      </a-card>
    </div>

    <!-- 优化结果 -->
    <div class="card-grid card-grid-2" style="margin-bottom: 16px">
      <a-card :bordered="false" title="供需缺口分析">
        <div ref="gapChartRef" style="height: 300px"></div>
      </a-card>
      <a-card :bordered="false" title="最优调配方案">
        <div ref="allocChartRef" style="height: 300px"></div>
      </a-card>
    </div>

    <!-- 建议列表 -->
    <a-card :bordered="false" style="margin-bottom: 16px">
      <template #title>
        <span style="font-size: 14px; font-weight: 600">优化建议</span>
        <a-tag color="green" style="margin-left: 8px">预计利润提升 +{{ profitIncrease }}万元</a-tag>
      </template>
      <a-table :columns="sugColumns" :data-source="suggestions" size="small" :pagination="false">
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'priority'">
            <a-tag :color="record.priority === '高' ? 'red' : record.priority === '中' ? 'orange' : 'blue'">{{ record.priority }}</a-tag>
          </template>
          <template v-if="column.dataIndex === 'impact'">
            <span :style="{ color: record.impact > 0 ? '#52c41a' : '#ff4d4f' }">
              {{ record.impact > 0 ? '+' : '' }}{{ record.impact }}万元
            </span>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- What-if 模拟 -->
    <a-card :bordered="false" title="What-if 模拟推演">
      <a-row :gutter="16">
        <a-col :span="8">
          <a-form layout="vertical" size="small">
            <a-form-item label="调整基地">
              <a-select v-model:value="whatifBase" placeholder="选择基地">
                <a-select-option v-for="b in baseList" :key="b" :value="b">{{ b }}</a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item label="产量变化(万吨)">
              <a-input-number v-model:value="whatifDelta" :min="-5" :max="5" :step="0.5" style="width: 100%" />
            </a-form-item>
            <a-button type="primary" block @click="runWhatif">模拟计算</a-button>
          </a-form>
        </a-col>
        <a-col :span="16">
          <div v-if="whatifResult" class="whatif-result">
            <a-descriptions :column="2" size="small" bordered>
              <a-descriptions-item label="利润变化">
                <span :style="{ color: whatifResult.profitDelta > 0 ? '#52c41a' : '#ff4d4f', fontWeight: 600 }">
                  {{ whatifResult.profitDelta > 0 ? '+' : '' }}{{ whatifResult.profitDelta }}万元
                </span>
              </a-descriptions-item>
              <a-descriptions-item label="库存影响">{{ whatifResult.inventoryImpact }}</a-descriptions-item>
              <a-descriptions-item label="运输成本变化">{{ whatifResult.transportDelta }}</a-descriptions-item>
              <a-descriptions-item label="综合评估">
                <a-tag :color="whatifResult.recommendation === '推荐' ? 'green' : 'orange'">{{ whatifResult.recommendation }}</a-tag>
              </a-descriptions-item>
            </a-descriptions>
            <div style="margin-top: 12px; color: #666; font-size: 13px">{{ whatifResult.explanation }}</div>
          </div>
          <a-empty v-else description="请设置参数并点击模拟计算" />
        </a-col>
      </a-row>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import {
  ThunderboltOutlined, DownloadOutlined,
  WarningOutlined, ExclamationCircleOutlined, InfoCircleOutlined,
} from '@ant-design/icons-vue'

const optimizing = ref(false)
const profitIncrease = ref(286)

const baseList = ['龙岩基地', '三明基地', '南平基地', '泉州基地', '漳州基地', '福州基地', '厦门基地', '宁德基地', '莆田基地']

const alerts = ref([
  { id: 1, level: 'danger', title: '宁德区域缺货风险', description: '库存1.2万吨，低于安全库存2.0万吨，本月需求预测3.5万吨，缺口约2.3万吨' },
  { id: 2, level: 'danger', title: '厦门基地库存高位', description: '当前库存4.5万吨，库容占比90%，建议增加外发或减产' },
  { id: 3, level: 'warning', title: '南平基地产销偏差', description: '本月实际产量偏离计划-8.2%，连续两月低于计划' },
  { id: 4, level: 'warning', title: '泉州区域价格波动', description: '本月均价环比下降3.2%，利润贡献度下降' },
  { id: 5, level: 'info', title: '龙岩基地产能利用高', description: '产能利用率92%，接近上限，排产空间有限' },
])

const sugColumns = [
  { title: '序号', dataIndex: 'id', width: 60 },
  { title: '建议类型', dataIndex: 'type', width: 100 },
  { title: '建议内容', dataIndex: 'content', ellipsis: true },
  { title: '优先级', dataIndex: 'priority', width: 80 },
  { title: '预计利润影响', dataIndex: 'impact', width: 130 },
]

const suggestions = ref([
  { id: 1, type: '调配建议', content: '将厦门基地多余库存1.5万吨调往宁德区域，解决宁德缺货风险', priority: '高', impact: 120 },
  { id: 2, type: '排产建议', content: '南平基地水泥产量提升至计划的95%，补充区域供应缺口', priority: '高', impact: 85 },
  { id: 3, type: '减产建议', content: '厦门基地减产5%，降低库存压力，节省库存持有成本', priority: '中', impact: 45 },
  { id: 4, type: '定价建议', content: '泉州区域散装水泥价格可适当上调2%，提升利润贡献', priority: '中', impact: 36 },
])

const gapChartRef = ref<HTMLElement>()
const allocChartRef = ref<HTMLElement>()
let chart1: echarts.ECharts
let chart2: echarts.ECharts

const whatifBase = ref<string>()
const whatifDelta = ref(0)
const whatifResult = ref<any>(null)

function runOptimize() {
  optimizing.value = true
  setTimeout(() => { optimizing.value = false }, 2000)
}

function runWhatif() {
  whatifResult.value = {
    profitDelta: whatifDelta.value > 0 ? +(whatifDelta.value * 60).toFixed(0) : +(whatifDelta.value * 45).toFixed(0),
    inventoryImpact: whatifDelta.value > 0 ? `库存增加约${(whatifDelta.value * 0.3).toFixed(1)}万吨` : `库存减少约${(Math.abs(whatifDelta.value) * 0.3).toFixed(1)}万吨`,
    transportDelta: whatifDelta.value > 0 ? `+${(whatifDelta.value * 8).toFixed(0)}万元` : `${(whatifDelta.value * 8).toFixed(0)}万元`,
    recommendation: whatifDelta.value > 0 && whatifDelta.value <= 2 ? '推荐' : '需谨慎',
    explanation: `模拟${whatifBase.value || '该基地'}产量${whatifDelta.value > 0 ? '增加' : '减少'}${Math.abs(whatifDelta.value)}万吨后，综合评估利润、库存和运输三项指标得出以上结论。（当前为演示模拟结果）`
  }
}

function initCharts() {
  if (gapChartRef.value) {
    chart1 = echarts.init(gapChartRef.value)
    const regions = ['福州', '厦门', '泉州', '漳州', '龙岩', '三明', '南平', '宁德', '莆田']
    chart1.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['需求', '可供应', '缺口'], textStyle: { fontSize: 11 } },
      grid: { top: 35, right: 20, bottom: 30, left: 50 },
      xAxis: { type: 'category', data: regions, axisLabel: { fontSize: 10 } },
      yAxis: { type: 'value', name: '万吨' },
      series: [
        { name: '需求', type: 'bar', stack: 'demand', data: [10.5, 9.8, 11.2, 7.6, 6.4, 5.9, 4.8, 3.5, 2.4], itemStyle: { color: '#91caff' } },
        { name: '可供应', type: 'bar', stack: 'supply', data: [10.2, 10.5, 10.8, 7.2, 6.8, 6.1, 4.5, 1.2, 2.6], itemStyle: { color: '#52c41a' } },
        { name: '缺口', type: 'bar', data: [0.3, -0.7, 0.4, 0.4, -0.4, -0.2, 0.3, 2.3, -0.2].map(v => v > 0 ? v : 0), itemStyle: { color: '#ff4d4f', borderRadius: [4, 4, 0, 0] } },
      ]
    })
  }
  if (allocChartRef.value) {
    chart2 = echarts.init(allocChartRef.value)
    chart2.setOption({
      tooltip: { trigger: 'item' },
      series: [{
        type: 'sankey',
        layout: 'none',
        emphasis: { focus: 'adjacency' },
        nodeAlign: 'left',
        data: [
          { name: '龙岩基地' }, { name: '三明基地' }, { name: '厦门基地' }, { name: '南平基地' },
          { name: '福州区域' }, { name: '泉州区域' }, { name: '厦漳区域' }, { name: '宁德区域' },
        ],
        links: [
          { source: '龙岩基地', target: '泉州区域', value: 4.2 },
          { source: '龙岩基地', target: '厦漳区域', value: 3.5 },
          { source: '龙岩基地', target: '宁德区域', value: 1.5 },
          { source: '三明基地', target: '福州区域', value: 4.8 },
          { source: '三明基地', target: '宁德区域', value: 2.0 },
          { source: '厦门基地', target: '厦漳区域', value: 3.0 },
          { source: '厦门基地', target: '宁德区域', value: 1.5 },
          { source: '南平基地', target: '福州区域', value: 3.2 },
          { source: '南平基地', target: '宁德区域', value: 1.8 },
        ],
        lineStyle: { color: 'gradient', curveness: 0.5 },
        itemStyle: { borderWidth: 1, borderColor: '#aaa' },
        label: { fontSize: 11 }
      }]
    })
  }
}

const handleResize = () => { chart1?.resize(); chart2?.resize() }
onMounted(() => { initCharts(); window.addEventListener('resize', handleResize) })
onUnmounted(() => { window.removeEventListener('resize', handleResize); chart1?.dispose(); chart2?.dispose() })
</script>

<style scoped>
.alert-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.alert-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 6px;
  border-left: 3px solid;
}
.alert-item.danger { background: #fff2f0; border-color: #ff4d4f; }
.alert-item.warning { background: #fffbe6; border-color: #faad14; }
.alert-item.info { background: #e6f4ff; border-color: #1677ff; }

.alert-icon { font-size: 18px; flex-shrink: 0; }
.alert-item.danger .alert-icon { color: #ff4d4f; }
.alert-item.warning .alert-icon { color: #faad14; }
.alert-item.info .alert-icon { color: #1677ff; }

.alert-content { flex: 1; }
.alert-title { font-weight: 600; font-size: 13px; color: var(--text-primary); }
.alert-desc { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }

.whatif-result {
  padding: 12px;
  background: #fafafa;
  border-radius: 6px;
}
</style>
