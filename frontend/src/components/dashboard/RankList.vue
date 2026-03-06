<template>
  <a-card class="rank-card" :bordered="false">
    <template #title>
      <div style="display: flex; align-items: baseline; gap: 8px">
        <span style="font-size: 14px; font-weight: 600">
          {{ title }}
        </span>
        <span style="font-size: 12px; color: var(--text-secondary)">单位：{{ unit }}</span>
      </div>
    </template>
    <div class="rank-list">
      <div v-for="(item, idx) in list" :key="item.name" class="rank-item">
        <span class="rank-no" :class="{
          top1: idx === 0,
          top2: idx === 1,
          top3: idx === 2,
          other: idx > 2
        }">{{ idx + 1 }}</span>
        <span class="rank-name" :style="{ color: 'var(--text-primary)' }">{{ item.name }}</span>
        <div class="rank-bar-wrap">
          <div class="rank-bar" :style="{ width: (item.value / maxValue * 100) + '%', background: 'var(--primary-color)' }"></div>
        </div>
        <span class="rank-val" :style="{ color: 'var(--text-primary)' }">{{ item.value.toFixed(1) }}</span>
      </div>
    </div>
  </a-card>
</template>

<script setup lang="ts">
import { computed, PropType } from 'vue'

const props = defineProps({
  title: {
    type: String,
    default: '排行榜'
  },
  list: {
    type: Array as PropType<{ name: string; value: number }[]>,
    default: () => []
  },
  unit: {
    type: String,
    default: '万吨'
  }
})

const maxValue = computed(() => {
  if (!props.list.length) return 1
  return Math.max(...props.list.map(item => item.value)) || 1
})
</script>

<style scoped>
.rank-card :deep(.ant-card-body) {
  padding: 12px 16px;
}

.rank-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rank-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  position: relative;
  height: 24px;
}

.rank-no {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  background: #eaf3ff;
  text-align: center;
  line-height: 20px;
  font-size: 11px;
  color: #5b7a99;
  flex-shrink: 0;
}

.rank-no.top1 {
  background: linear-gradient(135deg, #ff9f1a, #ffc53d);
  color: #fff;
}

.rank-no.top2 {
  background: linear-gradient(135deg, #2f8cff, #67b4ff);
  color: #fff;
}

.rank-no.top3 {
  background: linear-gradient(135deg, #22b8b0, #5fd3cd);
  color: #fff;
}

.rank-no.other {
  background: #eef5ff;
  color: #6b86a3;
}

.rank-name {
  width: 70px;
  flex-shrink: 0;
  color: var(--text-primary);
}

.rank-bar-wrap {
  flex: 1;
  height: 8px;
  background: color-mix(in srgb, var(--border-color) 55%, transparent);
  border-radius: 4px;
  overflow: hidden;
}

.rank-bar {
  height: 100%;
  background: var(--primary-color);
  border-radius: 4px;
  transition: width 0.6s ease;
}

.rank-val {
  width: 40px;
  text-align: right;
  color: var(--text-primary);
  font-weight: 500;
  flex-shrink: 0;
}
</style>
