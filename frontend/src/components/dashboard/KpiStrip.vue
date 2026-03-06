<template>
  <div class="kpi-strip">
    <div v-for="kpi in list" :key="kpi.title" class="kpi-card" :style="{ background: 'var(--card-bg)', border: '1px solid var(--border-color)' }">
      <div class="kpi-icon" :style="{ background: kpi.iconBg }">
        <component :is="kpi.icon" style="font-size: 22px" />
      </div>
      <div class="kpi-info">
        <div class="kpi-label">{{ kpi.title }}</div>
        <div class="kpi-value">{{ kpi.value }}<span class="kpi-unit">{{ kpi.unit }}</span></div>
        <div class="kpi-change" :class="kpi.changeType">
          <ArrowUpOutlined v-if="kpi.changeType === 'up'" />
          <ArrowDownOutlined v-if="kpi.changeType === 'down'" />
          {{ kpi.change }}
        </div>
      </div>
      <div class="kpi-progress">
        <a-progress
          :percent="kpi.percent"
          :stroke-color="kpi.color"
          :show-info="false"
          size="small"
        />
        <span class="kpi-progress-text">{{ kpi.progressLabel }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { PropType } from 'vue'
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons-vue'

defineProps({
  list: {
    type: Array as PropType<any[]>,
    default: () => []
  }
})
</script>

<style scoped>
.kpi-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.kpi-card {
  border-radius: 8px;
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: var(--card-shadow);
  transition: all 0.2s;
}

.kpi-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.kpi-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.kpi-info {
  flex: 1;
  min-width: 0;
}

.kpi-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.kpi-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.3;
}

.kpi-unit {
  font-size: 13px;
  font-weight: 400;
  color: var(--text-secondary);
  margin-left: 2px;
}

.kpi-change {
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 2px;
}
.kpi-change.up { color: var(--success-color); }
.kpi-change.down { color: var(--danger-color); }

.kpi-progress {
  width: 80px;
  flex-shrink: 0;
}

.kpi-progress-text {
  font-size: 10px;
  color: var(--text-muted);
}
</style>
