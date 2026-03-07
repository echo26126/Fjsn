<template>
  <div class="ai-bubble" v-show="!appStore.aiVisible" @click="appStore.toggleAi">
    <RobotOutlined style="font-size: 24px" />
  </div>

  <div
    v-show="appStore.aiVisible"
    class="ai-window"
    :style="windowStyle"
  >
    <div class="ai-header" @mousedown="startDrag">
      <span class="ai-title"><RobotOutlined /> 建福智衡</span>
      <div class="ai-header-actions">
        <span class="header-btn" @click.stop="toggleMaximize">{{ maximized ? '🗗' : '🗖' }}</span>
        <MinusOutlined @click="appStore.toggleAi" />
        <CloseOutlined @click="appStore.toggleAi" />
      </div>
    </div>

    <div class="ai-body" ref="bodyRef">
      <!-- 常见问题已移除 -->

      <div v-for="(msg, i) in appStore.aiMessages" :key="i" class="msg-row" :class="msg.role">
        <div class="msg-bubble" :class="msg.role">
          {{ msg.content }}
          <div v-if="msg.role === 'ai' && msg.data && msg.data.length" class="rich-block">
            <div
              v-if="msg.chartType && msg.chartType !== 'kpi'"
              class="msg-chart"
              :ref="(el) => setChartRef(el, i)"
            ></div>
            <a-table
              size="small"
              :columns="getDataColumns(msg.data)"
              :data-source="formatTableData(msg.data)"
              :pagination="false"
              :scroll="{ x: true }"
            />
          </div>
        </div>
      </div>

      <div v-if="loading" class="msg-row ai">
        <div class="msg-bubble ai typing">
          <span class="dot"></span><span class="dot"></span><span class="dot"></span>
        </div>
      </div>
    </div>

    <div class="ai-footer">
      <div class="input-wrapper">
        <a-textarea
          v-model:value="inputText"
          placeholder="请输入问题..."
          :auto-size="{ minRows: 2, maxRows: 6 }"
          @keydown.enter="handleEnterKey"
          class="chat-input"
        />
        <div v-if="loading" class="stop-btn-wrapper" @click="stopGeneration">
          <div class="stop-icon"></div>
        </div>
        <SendOutlined
          v-else
          class="send-btn"
          :style="{ color: inputText ? '#1677ff' : '#ccc', cursor: inputText ? 'pointer' : 'default' }"
          @click="onSend"
        />
      </div>
    </div>

    <div class="resize-handle" @mousedown.stop="startResize"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, reactive, onUnmounted } from 'vue'
import { RobotOutlined, MinusOutlined, CloseOutlined, SendOutlined } from '@ant-design/icons-vue'
import * as echarts from 'echarts'
import { useAppStore } from '@/stores/app'
import { agentApi } from '@/api'

const appStore = useAppStore()
const inputText = ref('')
const loading = ref(false)
const abortController = ref<AbortController | null>(null)
const bodyRef = ref<HTMLElement>()
const maximized = ref(false)
const chartEls = reactive<Record<number, HTMLElement | null>>({})
const chartInstances = new Map<number, echarts.ECharts>()
const previousPos = reactive({ x: 0, y: 0, w: 0, h: 0 })
const pos = reactive({
  x: Math.max(20, window.innerWidth - 700),
  y: 64,
  w: Math.min(660, window.innerWidth - 40),
  h: Math.min(760, window.innerHeight - 80),
})

const windowStyle = ref({})
function updateWindowStyle() {
  windowStyle.value = {
    left: pos.x + 'px',
    top: pos.y + 'px',
    width: pos.w + 'px',
    height: pos.h + 'px',
  }
}
updateWindowStyle()

async function onSend() {
  const text = inputText.value.trim()
  if (!text || loading.value) return

  appStore.addAiMessage({ role: 'user', content: text })
  appStore.addAiMessage({ role: 'ai', content: '' })
  const aiIndex = appStore.aiMessages.length - 1
  inputText.value = ''
  loading.value = true
  const controller = new AbortController()
  abortController.value = controller

  await nextTick()
  scrollToBottom()

  try {
    const response = await agentApi.chatStream(text, undefined, controller.signal)
    if (!response.ok || !response.body) {
      throw new Error('stream_failed')
    }
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''
    while (true) {
      if (controller.signal.aborted) {
        reader.cancel()
        break
      }
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''
      for (const block of parts) {
        const line = block.split('\n').find(item => item.startsWith('data:'))
        if (!line) continue
        const payload = line.slice(5).trim()
        if (!payload) continue
        const event = JSON.parse(payload)
        const current = appStore.aiMessages[aiIndex]
        if (!current) continue
        if (event.type === 'delta') {
          current.content = `${current.content}${event.content || ''}`
        } else if (event.type === 'done') {
          current.sql = event.sql ?? null
          current.data = Array.isArray(event.data) ? event.data : []
          current.chartType = event.chart_type || 'kpi'
          await nextTick()
          renderMessageChart(aiIndex, current)
        } else if (event.type === 'error') {
          current.content = event.message || '抱歉，处理您的问题时出现错误。'
        }
      }
      await nextTick()
      scrollToBottom()
    }
    if (!appStore.aiMessages[aiIndex]?.content) {
      appStore.aiMessages[aiIndex].content = '未返回文本结果。'
    }
  } catch (error: any) {
    if (error.name === 'AbortError' || controller.signal.aborted) {
      const current = appStore.aiMessages[aiIndex]
      if (current) {
        current.content += ' [已停止生成]'
      }
      return
    }
    try {
      if (!controller.signal.aborted) {
        const res: any = await agentApi.chat(text)
        const current = appStore.aiMessages[aiIndex]
        if (res && res.answer && current) {
          current.content = res.answer
          current.sql = res.sql ?? null
          current.data = Array.isArray(res.data) ? res.data : []
          current.chartType = res.chart_type || 'kpi'
          await nextTick()
          renderMessageChart(aiIndex, current)
        } else if (current) {
          current.content = '未拿到有效回答。'
        }
      }
    } catch {
      appStore.aiMessages[aiIndex].content = '抱歉，连接服务失败，请稍后重试。'
    }
  } finally {
    loading.value = false
    abortController.value = null
    await nextTick()
    scrollToBottom()
  }
}

function stopGeneration() {
  if (abortController.value) {
    abortController.value.abort()
    abortController.value = null
    loading.value = false
  }
}

function handleEnterKey(e: KeyboardEvent) {
  if (!e.shiftKey) {
    e.preventDefault()
    onSend()
  }
}

function scrollToBottom() {
  if (bodyRef.value) {
    bodyRef.value.scrollTop = bodyRef.value.scrollHeight
  }
}

function getDataColumns(data: Array<Record<string, any>>) {
  if (!data.length) return []
  return Object.keys(data[0]).map((key) => ({
    title: key,
    dataIndex: key,
    key,
    width: 120,
  }))
}

function formatTableData(data: Array<Record<string, any>>) {
  return data.map((row, idx) => ({ key: idx, ...row }))
}

function setChartRef(el: any, idx: number) {
  chartEls[idx] = el as HTMLElement | null
}

function renderMessageChart(idx: number, msg: any) {
  if (!msg?.data?.length || !chartEls[idx] || msg.chartType === 'kpi') return
  const data = msg.data as Array<Record<string, any>>
  const first = data[0] || {}
  const dimKey = Object.keys(first).find((k) => typeof first[k] !== 'number') || Object.keys(first)[0]
  const valKey = Object.keys(first).find((k) => typeof first[k] === 'number')
  if (!dimKey || !valKey) return
  const labels = data.map((row) => String(row[dimKey] ?? ''))
  const values = data.map((row) => Number(row[valKey] ?? 0))
  let chart = chartInstances.get(idx)
  if (!chart) {
    chart = echarts.init(chartEls[idx] as HTMLElement)
    chartInstances.set(idx, chart)
  }
  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { top: 22, right: 12, bottom: 30, left: 42 },
    xAxis: { type: 'category', data: labels, axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', axisLabel: { fontSize: 10 } },
    series: [{
      type: 'bar',
      data: values,
      itemStyle: { color: '#1677ff', borderRadius: [4, 4, 0, 0] },
      barMaxWidth: 24,
    }]
  })
}

let dragStart = { x: 0, y: 0, px: 0, py: 0 }
function startDrag(e: MouseEvent) {
  if (maximized.value) return
  dragStart = { x: e.clientX, y: e.clientY, px: pos.x, py: pos.y }
  const onMove = (ev: MouseEvent) => {
    pos.x = Math.max(0, Math.min(window.innerWidth - pos.w, dragStart.px + (ev.clientX - dragStart.x)))
    pos.y = Math.max(0, Math.min(window.innerHeight - pos.h, dragStart.py + (ev.clientY - dragStart.y)))
    updateWindowStyle()
  }
  const onUp = () => {
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onUp)
  }
  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
}

let resizeStart = { x: 0, y: 0, w: 0, h: 0 }
function startResize(e: MouseEvent) {
  if (maximized.value) return
  resizeStart = { x: e.clientX, y: e.clientY, w: pos.w, h: pos.h }
  const onMove = (ev: MouseEvent) => {
    pos.w = Math.max(480, Math.min(window.innerWidth * 0.94, resizeStart.w + (ev.clientX - resizeStart.x)))
    pos.h = Math.max(560, Math.min(window.innerHeight * 0.94, resizeStart.h + (ev.clientY - resizeStart.y)))
    updateWindowStyle()
  }
  const onUp = () => {
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onUp)
  }
  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
}

function toggleMaximize() {
  if (!maximized.value) {
    previousPos.x = pos.x
    previousPos.y = pos.y
    previousPos.w = pos.w
    previousPos.h = pos.h
    pos.x = 12
    pos.y = 12
    pos.w = window.innerWidth - 24
    pos.h = window.innerHeight - 24
    maximized.value = true
  } else {
    pos.x = previousPos.x || Math.max(20, window.innerWidth - 700)
    pos.y = previousPos.y || 64
    pos.w = previousPos.w || Math.min(660, window.innerWidth - 40)
    pos.h = previousPos.h || Math.min(760, window.innerHeight - 80)
    maximized.value = false
  }
  updateWindowStyle()
  nextTick(() => {
    chartInstances.forEach((item) => item.resize())
  })
}

onUnmounted(() => {
  chartInstances.forEach((item) => item.dispose())
  chartInstances.clear()
})
</script>

<style scoped>
.ai-bubble {
  position: fixed;
  left: 24px;
  bottom: 24px;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1677ff, #4096ff);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(22, 119, 255, 0.4);
  z-index: 1000;
  transition: transform 0.2s;
}
.ai-bubble:hover {
  transform: scale(1.1);
}

.ai-window {
  position: fixed;
  z-index: 1001;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.ai-header {
  background: linear-gradient(135deg, #001529, #003a70);
  color: #fff;
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: move;
  user-select: none;
  flex-shrink: 0;
}

.ai-title {
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
}

.ai-header-actions {
  display: flex;
  gap: 10px;
}
.ai-header-actions span {
  cursor: pointer;
  opacity: 0.7;
  transition: opacity 0.2s;
}
.ai-header-actions span:hover {
  opacity: 1;
}

.header-btn {
  font-size: 12px;
  line-height: 1;
}

.ai-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #f9f9f9;
}

/* 常见问题样式已移除 */

.msg-row {
  margin-bottom: 12px;
  display: flex;
}
.msg-row.user {
  justify-content: flex-end;
}
.msg-row.ai {
  justify-content: flex-start;
}

.msg-bubble {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
}
.msg-bubble.user {
  background: #1677ff;
  color: #fff;
  border-bottom-right-radius: 2px;
}
.msg-bubble.ai {
  background: #f4f6f8;
  color: #333;
  border-bottom-left-radius: 2px;
}

.rich-block {
  margin-top: 8px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e8edf2;
  padding: 8px;
}

.msg-chart {
  height: 180px;
  margin-bottom: 8px;
}

.typing {
  display: flex;
  gap: 4px;
  padding: 12px 18px;
}
.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #999;
  animation: blink 1.2s infinite;
}
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink {
  0%, 60%, 100% { opacity: 0.3; }
  30% { opacity: 1; }
}

.ai-footer {
  padding: 24px 20px;
  border-top: 1px solid #e8e8e8;
  background: #fff;
  flex-shrink: 0;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: flex-end;
}

.chat-input {
  min-height: 64px; /* 初始高度 */
  border-radius: 8px;
  font-size: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  padding-right: 48px;
  padding-top: 12px;
  padding-bottom: 12px;
  resize: none;
}

.chat-input:hover, .chat-input:focus {
  box-shadow: 0 4px 12px rgba(22, 119, 255, 0.1);
}

.send-btn {
  position: absolute;
  right: 12px;
  bottom: 12px;
  font-size: 26px;
  margin-right: 0;
  transition: all 0.2s;
  z-index: 10;
}

.stop-btn-wrapper {
  position: absolute;
  right: 12px;
  bottom: 12px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  background: #ff4d4f;
  border-radius: 50%;
  transition: all 0.2s;
}

.stop-icon {
  width: 12px;
  height: 12px;
  background: #fff;
  border-radius: 2px;
}

.stop-btn-wrapper:hover {
  background: #ff7875;
  transform: scale(1.1);
}

.send-btn:hover {
  transform: scale(1.1);
}

.resize-handle {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 16px;
  height: 16px;
  cursor: nwse-resize;
  background: linear-gradient(135deg, transparent 50%, #ccc 50%);
  border-radius: 0 0 12px 0;
}
</style>
