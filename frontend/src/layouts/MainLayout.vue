<template>
  <a-layout class="main-layout">
    <a-layout-sider
      v-model:collapsed="appStore.collapsed"
      :trigger="null"
      collapsible
      :width="220"
      :collapsed-width="64"
      class="sidebar"
      :theme="appStore.theme === 'dark' ? 'dark' : 'light'"
    >
      <div class="logo" @click="$router.push('/')">
        <template v-if="appStore.companyLogo">
          <img :src="appStore.companyLogo" :class="appStore.collapsed ? 'logo-image-collapsed' : 'logo-image-full'" alt="logo" />
        </template>
        <template v-else>
          <svg viewBox="0 0 24 24" width="28" height="28" :fill="appStore.theme === 'dark' ? '#3dd9a8' : '#1b6b5a'">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
          </svg>
          <div v-show="!appStore.collapsed" class="logo-text-wrap">
            <span class="logo-text" :style="{ color: 'var(--text-primary)' }">{{ appStore.companyName }}</span>
            <span class="logo-subtext">产销平衡智能体</span>
          </div>
        </template>
      </div>

      <a-menu
        v-model:selectedKeys="selectedKeys"
        :theme="appStore.theme === 'dark' ? 'dark' : 'light'"
        mode="inline"
        @click="onMenuClick"
      >
        <a-menu-item key="/dashboard">
          <template #icon><DashboardOutlined /></template>
          <span>经营总览</span>
        </a-menu-item>

        <a-menu-item key="/decision-flow">
          <template #icon><DeploymentUnitOutlined /></template>
          <span>产销舆情</span>
        </a-menu-item>

        <a-menu-item key="/sales">
          <template #icon><ShoppingOutlined /></template>
          <span>销售分析</span>
        </a-menu-item>

        <a-menu-item key="/inventory">
          <template #icon><DatabaseOutlined /></template>
          <span>库存概览</span>
        </a-menu-item>

        <a-menu-item key="/production">
          <template #icon><BarChartOutlined /></template>
          <span>生产监控</span>
        </a-menu-item>

        <a-menu-item key="/decision-simulation">
          <template #icon><ExperimentOutlined /></template>
          <span>模拟建议</span>
        </a-menu-item>

        <a-menu-item key="/data">
          <template #icon><CloudUploadOutlined /></template>
          <span>后台配置</span>
        </a-menu-item>
      </a-menu>
    </a-layout-sider>

    <a-layout :style="{ marginLeft: appStore.collapsed ? '64px' : '220px', transition: 'margin-left 0.2s', minHeight: '100vh' }">
      <a-layout-header class="header" :style="{ background: 'var(--header-bg)', padding: '0 16px', borderBottom: '1px solid var(--border-color)', height: 'var(--header-height)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }">
        <div class="header-left" style="display: flex; alignItems: center; gap: 16px">
          <div class="trigger-wrapper" style="cursor: pointer; display: flex; alignItems: center">
            <MenuFoldOutlined
              v-if="!appStore.collapsed"
              class="trigger"
              @click="appStore.toggleCollapsed"
              :style="{ color: 'var(--text-primary)', fontSize: '18px' }"
            />
            <MenuUnfoldOutlined
              v-else
              class="trigger"
              @click="appStore.toggleCollapsed"
              :style="{ color: 'var(--text-primary)', fontSize: '18px' }"
            />
          </div>
          <span class="current-title">{{ currentTitle }}</span>
        </div>

        <div class="header-right" style="display: flex; alignItems: center; gap: 12px">
          <a-select
            v-model:value="appStore.timeMode"
            size="small"
            style="width: 80px"
          >
            <a-select-option value="year">按年</a-select-option>
            <a-select-option value="month">按月</a-select-option>
            <a-select-option value="range">区间</a-select-option>
          </a-select>
          <a-range-picker
            v-if="appStore.timeMode === 'range'"
            v-model:value="dateRangeValue"
            :locale="datePickerLocale"
            format="M月D日"
            size="small"
            style="width: 200px"
          />
          <a-date-picker
            v-else
            v-model:value="timePointValue"
            :picker="appStore.timeMode"
            :locale="datePickerLocale"
            :format="timePickerFormat"
            size="small"
            style="width: 120px"
          />
          <button class="theme-toggle" :class="{ dark: appStore.theme === 'dark' }" @click="appStore.toggleTheme">
            <svg v-if="appStore.theme === 'dark'" viewBox="0 0 24 24" width="16" height="16">
              <path fill="currentColor" d="M21 14.5A8.5 8.5 0 1 1 9.5 3a7 7 0 1 0 11.5 11.5z"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" width="16" height="16">
              <circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="1.8"/>
              <path d="M12 2.5v2.5M12 19v2.5M2.5 12H5M19 12h2.5M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M19.1 4.9l-1.8 1.8M6.7 17.3l-1.8 1.8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
            </svg>
          </button>
          
          <a-dropdown v-if="userStore.isLoggedIn">
            <span class="user-info" style="cursor: pointer; display: flex; alignItems: center; gap: 4px">
              <a-avatar size="small" :style="{ background: 'var(--primary-color)' }">{{ userStore.user?.username?.charAt(0).toUpperCase() || 'U' }}</a-avatar>
              <span :style="{ color: 'var(--text-primary)', fontSize: '14px' }">{{ userStore.user?.username || '用户' }}</span>
            </span>
            <template #overlay>
              <a-menu>
                <a-menu-item @click="handleLogout">退出登录</a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </a-layout-header>

      <a-layout-content class="content" :style="{ background: 'var(--content-bg)', padding: '24px', transition: 'all 0.3s ease' }">
        <router-view />
      </a-layout-content>
    </a-layout>

    <AiAssistant />
  </a-layout>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import dayjs from 'dayjs'
import datePickerLocale from 'ant-design-vue/es/date-picker/locale/zh_CN'
import {
  DashboardOutlined,
  BarChartOutlined,
  ShoppingOutlined,
  CloudUploadOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  ExperimentOutlined,
  DatabaseOutlined,
  LineChartOutlined,
  DeploymentUnitOutlined,
  FundProjectionScreenOutlined,
} from '@ant-design/icons-vue'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/api'
import AiAssistant from '@/components/AiAssistant.vue'

const appStore = useAppStore()
const userStore = useUserStore()
const route = useRoute()
const router = useRouter()

onMounted(async () => {
  if (userStore.isLoggedIn && !userStore.user) {
    try {
      const user = await authApi.getMe()
      userStore.setUser(user)
    } catch {
      userStore.logout()
      router.push('/login')
    }
  }
})

function handleLogout() {
  userStore.logout()
  router.push('/login')
}

const selectedKeys = ref<string[]>([route.path])
const currentTitle = computed(() => (route.meta?.title as string) || '')
const isQueryPage = computed(() => ['/production', '/inventory', '/sales'].includes(route.path))

function getQueryMemoryKey(path: string) {
  return `query_memory_${path}`
}

function restoreQueryState(path: string) {
  if (!isQueryPage.value) return
  try {
    const raw = localStorage.getItem(getQueryMemoryKey(path))
    if (!raw) {
      appStore.selectedBase = 'all'
      appStore.selectedRegion = 'all'
      appStore.selectedCategory = 'all'
      return
    }
    const parsed = JSON.parse(raw)
    appStore.selectedBase = parsed.selectedBase || 'all'
    appStore.selectedRegion = parsed.selectedRegion || 'all'
    appStore.selectedCategory = parsed.selectedCategory || 'all'
  } catch {
    appStore.selectedBase = 'all'
    appStore.selectedRegion = 'all'
    appStore.selectedCategory = 'all'
  }
}

function saveQueryState(path: string) {
  if (!isQueryPage.value) return
  localStorage.setItem(
    getQueryMemoryKey(path),
    JSON.stringify({
      selectedBase: appStore.selectedBase,
      selectedRegion: appStore.selectedRegion,
      selectedCategory: appStore.selectedCategory,
    })
  )
}

const timePointValue = computed({
  get: () => {
    const format = appStore.timeMode === 'year' ? 'YYYY' : 'YYYY-MM'
    return dayjs(appStore.timePoint, format)
  },
  set: (val: any) => {
    if (!val) return
    const format = appStore.timeMode === 'year' ? 'YYYY' : 'YYYY-MM'
    appStore.timePoint = val.format(format)
  }
})

const dateRangeValue = computed({
  get: () => [dayjs(appStore.dateRange[0]), dayjs(appStore.dateRange[1])] as any,
  set: (val: any) => {
    if (val && val.length === 2) {
      appStore.dateRange = [val[0].format('YYYY-MM-DD'), val[1].format('YYYY-MM-DD')]
    }
  }
})

const timePickerFormat = computed(() => appStore.timeMode === 'year' ? 'YYYY年' : 'M月')

watch(() => appStore.timeMode, (mode) => {
  if (mode === 'year') {
    appStore.timePoint = dayjs().format('YYYY')
  } else if (mode === 'month') {
    appStore.timePoint = dayjs().format('YYYY-MM')
  }
})

watch(() => route.path, (path) => {
  selectedKeys.value = [path]
  restoreQueryState(path)
}, { immediate: true })

watch(
  () => [appStore.selectedBase, appStore.selectedRegion, appStore.selectedCategory, route.path],
  ([, , , path]) => {
    saveQueryState(path as string)
  },
  { deep: true }
)

function onMenuClick({ key }: { key: string }) {
  router.push(key)
}
</script>

<style scoped>
.main-layout {
  min-height: 100vh;
}

.sidebar {
  background: var(--sidebar-bg);
  overflow-y: auto;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 100;
}

.sidebar :deep(.ant-layout-sider-children) {
  display: flex;
  flex-direction: column;
}

.logo {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
}

.logo-text {
  font-size: 15px;
  font-weight: 600;
  white-space: nowrap;
  line-height: 1.2;
}

.logo-subtext {
  font-size: 11px;
  color: var(--text-secondary);
  line-height: 1.1;
}

.logo-text-wrap {
  display: flex;
  flex-direction: column;
}

.logo-image-full {
  width: 100%;
  height: 44px;
  padding: 0 12px;
  object-fit: contain;
}

.logo-image-collapsed {
  width: 32px;
  height: 32px;
  object-fit: contain;
}

.header {
  background: #fff;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--header-height);
  line-height: var(--header-height);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  position: sticky;
  top: 0;
  z-index: 50;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.trigger {
  font-size: 18px;
  cursor: pointer;
  padding: 4px;
  color: var(--text-primary);
  transition: color 0.2s;
}

.trigger:hover {
  color: var(--primary-color);
}

.current-title {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
}

.query-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-right: -6px;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-size: 14px;
}

.theme-toggle {
  width: 36px;
  height: 32px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background: #ffffff;
  color: #6b7a90;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.theme-toggle.dark {
  background: #191f2d;
  color: #a6b3ce;
  border-color: #2f3a52;
}

.content {
  background: var(--content-bg);
  min-height: calc(100vh - var(--header-height));
  overflow-y: auto;
}

/* 优化后的菜单样式 */
.sidebar :deep(.ant-menu) {
  background: transparent;
  padding: 8px;
  border-inline-end: none !important;
}

.sidebar :deep(.ant-menu-item) {
  margin: 4px 0;
  border-radius: 8px;
  height: 44px;
  line-height: 44px;
  font-size: 15px; /* 字号加大 */
  color: var(--text-secondary);
  transition: all 0.2s ease;
}

.sidebar :deep(.ant-menu-item:hover) {
  color: var(--primary-color);
  background: rgba(0, 0, 0, 0.03);
}

.sidebar :deep(.ant-menu-item-selected) {
  background: var(--primary-color-light) !important;
  color: var(--primary-color) !important;
  font-weight: 500;
}

/* 适配暗色模式 */
.sidebar[theme='dark'] :deep(.ant-menu-item:hover) {
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
}

.sidebar[theme='dark'] :deep(.ant-menu-item-selected) {
  background: var(--primary-color) !important;
  color: #fff !important;
}

/* 调整图标大小与间距 */
.sidebar :deep(.ant-menu-item .anticon) {
  font-size: 18px;
  margin-right: 12px;
}

/* 折叠状态适配 */
.sidebar.ant-layout-sider-collapsed :deep(.ant-menu-item) {
  padding: 0 calc(50% - 18px / 2);
}

</style>
