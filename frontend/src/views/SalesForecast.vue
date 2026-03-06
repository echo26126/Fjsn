<template>
  <div class="page-container">
    <div class="page-header">
      <span class="page-title">销售预测</span>
      <a-space>
        <a-button type="primary" @click="saveForecast">保存预测</a-button>
        <a-button>导出 Excel</a-button>
      </a-space>
    </div>

    <div class="ag-theme-alpine" :class="{ 'ag-theme-alpine-dark': isDark }" style="height: calc(100vh - 140px); width: 100%;">
      <ag-grid-vue
        style="width: 100%; height: 100%;"
        :class="themeClass"
        :columnDefs="columnDefs"
        :rowData="rowData"
        :defaultColDef="defaultColDef"
        :enableRangeSelection="true"
        :rowSelection="'multiple'"
        @grid-ready="onGridReady"
      >
      </ag-grid-vue>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { useAppStore } from '@/stores/app'
import "ag-grid-community/styles/ag-grid.css"
import "ag-grid-community/styles/ag-theme-alpine.css"

const appStore = useAppStore()
const isDark = computed(() => appStore.theme === 'dark')
const themeClass = computed(() => isDark.value ? 'ag-theme-alpine-dark' : 'ag-theme-alpine')

const columnDefs = ref([
  { field: 'region', headerName: '区域', rowGroup: true, hide: true },
  { field: 'customer', headerName: '客户', width: 150, pinned: 'left' },
  { field: 'product', headerName: '产品', width: 120, pinned: 'left' },
  { field: 'm1', headerName: '1月预测', editable: true, type: 'numericColumn' },
  { field: 'm2', headerName: '2月预测', editable: true, type: 'numericColumn' },
  { field: 'm3', headerName: '3月预测', editable: true, type: 'numericColumn' },
  { field: 'm4', headerName: '4月预测', editable: true, type: 'numericColumn' },
  { field: 'm5', headerName: '5月预测', editable: true, type: 'numericColumn' },
  { field: 'm6', headerName: '6月预测', editable: true, type: 'numericColumn' },
  { field: 'total', headerName: '上半年合计', valueGetter: 'Number(data.m1 || 0) + Number(data.m2 || 0) + Number(data.m3 || 0) + Number(data.m4 || 0) + Number(data.m5 || 0) + Number(data.m6 || 0)' }
])

const defaultColDef = {
  flex: 1,
  minWidth: 100,
  sortable: true,
  filter: true,
  resizable: true,
}

const rowData = ref([
  { region: '福州北销售区域', customer: '鼓楼建材', product: 'P.O 42.5', m1: 500, m2: 520, m3: 600, m4: 580, m5: 620, m6: 650 },
  { region: '福州北销售区域', customer: '晋安商砼', product: 'P.O 42.5', m1: 800, m2: 850, m3: 900, m4: 880, m5: 920, m6: 950 },
  { region: '福州南销售区域', customer: '仓山建材', product: 'P.O 42.5', m1: 400, m2: 420, m3: 450, m4: 460, m5: 480, m6: 500 },
  { region: '福州南销售区域', customer: '长乐港务', product: 'P.O 52.5', m1: 1200, m2: 1300, m3: 1400, m4: 1350, m5: 1450, m6: 1500 },
  { region: '泉州销售区域', customer: '泉港水泥', product: 'P.O 42.5', m1: 600, m2: 650, m3: 700, m4: 720, m5: 750, m6: 800 },
  { region: '泉州销售区域', customer: '晋江建材', product: 'P.O 42.5', m1: 900, m2: 950, m3: 1000, m4: 980, m5: 1050, m6: 1100 },
  { region: '厦漳销售区域', customer: '厦门港务', product: 'P.O 52.5', m1: 1500, m2: 1600, m3: 1700, m4: 1650, m5: 1750, m6: 1800 },
  { region: '厦漳销售区域', customer: '鹭岛建材', product: 'P.O 42.5', m1: 300, m2: 320, m3: 350, m4: 360, m5: 380, m6: 400 },
])

const gridApi = ref(null)

function onGridReady(params: any) {
  gridApi.value = params.api
}

function saveForecast() {
  console.log('Saving data...')
  alert('预测数据已保存')
}
</script>

<style scoped>
.ag-theme-alpine-dark {
  --ag-background-color: #0e203c;
  --ag-foreground-color: #e6eefc;
  --ag-border-color: #1d365a;
  --ag-header-background-color: #0b1d39;
  --ag-row-hover-color: #1d365a;
  --ag-odd-row-background-color: #0e203c;
  --ag-header-column-separator-color: #1d365a;
}
</style>