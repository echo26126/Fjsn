import { defineStore } from 'pinia'
import { ref } from 'vue'
import dayjs from 'dayjs'

export const useAppStore = defineStore('app', () => {
  const collapsed = ref(false)
  const baseOptions = [
    '安砂建福',
    '永安建福',
    '顺昌炼石',
    '福州炼石',
    '宁德建福',
    '金银湖水泥',
  ]
  const selectedBase = ref('all')
  const selectedRegion = ref('all')
  const selectedCategory = ref('all')
  const queryNonce = ref(0)
  const regionOptions = [
    '安砂销售部',
    '福州北销售区域',
    '福州南销售区域',
    '南平销售区域',
    '宁德销售区域',
    '莆田销售区域',
    '泉州销售区域',
    '三明销售区域',
    '厦漳销售区域',
  ]
  const timeMode = ref<'year' | 'month' | 'range'>('month')
  const timePoint = ref('2025-12')
  const dateRange = ref<[string, string]>([
    '2025-12-01',
    '2025-12-31'
  ])
  const dataScope = ref<'shipment' | 'outbound'>('outbound')
  const aiVisible = ref(false)
  const aiMessages = ref<Array<{
    role: 'user' | 'ai'
    content: string
    chart?: any
    chartType?: string
    data?: Array<Record<string, any>>
    sql?: string | null
  }>>([])
  const theme = ref<'light' | 'dark'>('light')
  const companyName = ref(localStorage.getItem('company_name') || '福建水泥')
  const companyLogo = ref(localStorage.getItem('company_logo') || '/logo_fjcement.png')

  function initTheme() {
    document.documentElement.setAttribute('data-theme', theme.value)
  }

  function toggleCollapsed() {
    collapsed.value = !collapsed.value
  }

  function toggleAi() {
    aiVisible.value = !aiVisible.value
  }

  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
    document.documentElement.setAttribute('data-theme', theme.value)
  }

  function addAiMessage(msg: {
    role: 'user' | 'ai'
    content: string
    chart?: any
    chartType?: string
    data?: Array<Record<string, any>>
    sql?: string | null
  }) {
    aiMessages.value.push(msg)
  }

  function triggerQuery() {
    queryNonce.value += 1
  }

  function setCompanyBrand(name: string, logo: string) {
    companyName.value = name
    companyLogo.value = logo
    localStorage.setItem('company_name', name)
    localStorage.setItem('company_logo', logo)
  }

  return {
    collapsed,
    baseOptions,
    regionOptions,
    selectedBase,
    selectedRegion,
    selectedCategory,
    queryNonce,
    timeMode,
    timePoint,
    dateRange,
    dataScope,
    aiVisible,
    aiMessages,
    theme,
    companyName,
    companyLogo,
    initTheme,
    toggleCollapsed,
    toggleAi,
    toggleTheme,
    addAiMessage,
    triggerQuery,
    setCompanyBrand
  }
})
