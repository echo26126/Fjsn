<template>
  <div class="page-container">
    <div class="page-header">
      <span class="page-title">后台配置</span>
    </div>

    <a-tabs v-model:activeKey="activeTab">
      <!-- Excel 上传 -->
      <a-tab-pane key="upload" tab="数据上传">
        <a-card :bordered="false">
          <a-row :gutter="24">
            <a-col :span="10">
              <h4 style="margin-bottom: 12px">选择模板类型</h4>
              <a-radio-group v-model:value="templateType" style="width: 100%">
                <div class="template-list">
                  <div
                    v-for="t in templates"
                    :key="t.key"
                    class="template-item"
                    :class="{ active: templateType === t.key }"
                    @click="templateType = t.key"
                  >
                    <a-radio :value="t.key">
                      <span class="template-name">{{ t.name }}</span>
                    </a-radio>
                    <span class="template-desc">{{ t.desc }}</span>
                    <a-button type="link" size="small" @click.stop>下载模板</a-button>
                  </div>
                </div>
              </a-radio-group>
            </a-col>
            <a-col :span="14">
              <h4 style="margin-bottom: 12px">上传文件</h4>
              <a-upload-dragger
                :file-list="fileList"
                :before-upload="beforeUpload"
                @remove="handleRemove"
                accept=".xlsx,.xls"
              >
                <p class="ant-upload-drag-icon">
                  <InboxOutlined />
                </p>
                <p class="ant-upload-text">点击或拖拽 Excel 文件到此区域</p>
                <p class="ant-upload-hint">支持 .xlsx / .xls 格式，单次上传一个文件</p>
              </a-upload-dragger>

              <div v-if="uploadPreview" style="margin-top: 16px">
                <a-alert
                  :type="uploadPreview.errors > 0 ? 'warning' : 'success'"
                  :message="`校验完成：${uploadPreview.total}行数据，${uploadPreview.valid}行合法，${uploadPreview.errors}行异常`"
                  show-icon
                  style="margin-bottom: 12px"
                />
                <a-table
                  :columns="previewColumns"
                  :data-source="uploadPreview.rows"
                  size="small"
                  :pagination="{ pageSize: 5 }"
                  :row-class-name="(r: any) => r.hasError ? 'error-row' : ''"
                />
                <div style="margin-top: 12px; text-align: right">
                  <a-space>
                    <a-button @click="uploadPreview = null">取消</a-button>
                    <a-button type="primary" :disabled="uploadPreview.errors > 0">确认入库</a-button>
                  </a-space>
                </div>
              </div>
            </a-col>
          </a-row>
        </a-card>
      </a-tab-pane>

      <!-- 上传记录 -->
      <a-tab-pane key="records" tab="上传记录">
        <a-card :bordered="false">
          <a-table :columns="recordColumns" :data-source="uploadRecords" size="small">
            <template #bodyCell="{ column, record }">
              <template v-if="column.dataIndex === 'status'">
                <a-tag :color="record.status === '已入库' ? 'green' : record.status === '待审核' ? 'orange' : 'red'">
                  {{ record.status }}
                </a-tag>
              </template>
              <template v-if="column.dataIndex === 'action'">
                <a-space>
                  <a-button type="link" size="small">查看</a-button>
                  <a-popconfirm title="确定要撤回此批数据？" @confirm="() => {}">
                    <a-button type="link" size="small" danger>撤回</a-button>
                  </a-popconfirm>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-tab-pane>

      <!-- 模板管理 -->
      <a-tab-pane key="templates" tab="模板管理">
        <a-card :bordered="false">
          <a-table :columns="templateColumns" :data-source="templates" size="small" :pagination="false">
            <template #bodyCell="{ column }">
              <template v-if="column.dataIndex === 'action'">
                <a-button type="link" size="small">下载</a-button>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-tab-pane>

      <a-tab-pane key="brand-config" tab="企业品牌配置">
        <a-card :bordered="false">
          <a-form layout="vertical">
            <a-form-item label="企业名称">
              <a-input v-model:value="brandForm.companyName" placeholder="请输入企业名称" />
            </a-form-item>
            <a-form-item label="企业LOGO地址">
              <a-input v-model:value="brandForm.companyLogo" placeholder="请输入图片URL" />
            </a-form-item>
            <div class="config-actions">
              <a-space>
                <a-button @click="resetBrandForm">重置</a-button>
                <a-button type="primary" @click="saveBrandConfig">保存品牌配置</a-button>
              </a-space>
            </div>
          </a-form>
        </a-card>
      </a-tab-pane>

      <a-tab-pane key="region-config" tab="销售区域配置">
        <a-card :bordered="false">
          <a-form layout="vertical">
            <a-form-item label="区域-地市对照">
              <a-table :columns="regionMapColumns" :data-source="regionRows" size="small" :pagination="false">
                <template #bodyCell="{ column, record }">
                  <template v-if="column.dataIndex === 'region'">
                    <a-input v-model:value="record.region" :disabled="!canEditConfig" />
                  </template>
                  <template v-if="column.dataIndex === 'city'">
                    <a-input v-model:value="record.city" :disabled="!canEditConfig" />
                  </template>
                </template>
              </a-table>
              <div style="margin-top: 10px; text-align: right">
                <a-button size="small" :disabled="!canEditConfig" @click="addRegionRow">新增一行</a-button>
              </div>
            </a-form-item>
            <a-form-item label="指标单位">
              <a-row :gutter="10">
                <a-col :span="6"><a-input v-model:value="metricUnits.production" addon-before="生产" :disabled="!canEditConfig" /></a-col>
                <a-col :span="6"><a-input v-model:value="metricUnits.sales" addon-before="销售" :disabled="!canEditConfig" /></a-col>
                <a-col :span="6"><a-input v-model:value="metricUnits.inventory" addon-before="库存" :disabled="!canEditConfig" /></a-col>
                <a-col :span="6"><a-input v-model:value="metricUnits.avg_price" addon-before="均价" :disabled="!canEditConfig" /></a-col>
              </a-row>
            </a-form-item>
            <div class="config-actions">
              <a-space>
                <a-button :loading="loadingRegionConfig" @click="loadRegionConfig">刷新</a-button>
                <a-button type="primary" :disabled="!canEditConfig" :loading="savingRegionConfig" @click="saveRegionConfig">保存区域配置</a-button>
              </a-space>
            </div>
          </a-form>
        </a-card>
      </a-tab-pane>

      <a-tab-pane key="agent-config" tab="智能体配置">
        <a-card :bordered="false">
          <div class="auth-row">
            <span class="text-muted">当前操作人: {{ userStore.user?.username || '未登录' }}</span>
            <a-tag :color="canEditConfig ? 'green' : 'orange'">{{ canEditConfig ? '管理员可编辑' : '只读预览' }}</a-tag>
          </div>
          <a-form layout="vertical">
            <a-row :gutter="16">
              <a-col :span="8">
                <a-form-item label="模型供应商">
                  <a-select v-model:value="agentConfig.provider" :options="providerOptions" :disabled="!canEditConfig" />
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="模型名称">
                  <a-select v-model:value="agentConfig.model" :options="modelOptions" show-search :disabled="!canEditConfig" />
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="温度系数">
                  <a-slider v-model:value="agentConfig.temperature" :min="0" :max="1" :step="0.05" :disabled="!canEditConfig" />
                </a-form-item>
              </a-col>
            </a-row>

            <a-form-item label="API Base URL">
              <a-input v-model:value="agentConfig.base_url" placeholder="https://api.deepseek.com" :disabled="!canEditConfig" />
            </a-form-item>
            <a-form-item label="模型 KEY">
              <a-space style="width: 100%">
                <a-input :value="agentConfig.api_key" disabled />
                <a-input-password v-model:value="newApiKey" placeholder="输入新 KEY（可选）" :disabled="!canEditConfig" />
                <a-button type="primary" :disabled="!canEditConfig || !newApiKey" :loading="savingKey" @click="saveApiKey">更新KEY</a-button>
              </a-space>
            </a-form-item>

            <a-row :gutter="16">
              <a-col :span="12">
                <a-form-item label="SQL 生成提示词">
                  <a-textarea v-model:value="agentConfig.sql_prompt" :rows="7" :maxlength="3000" :disabled="!canEditConfig" />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="问答分析提示词">
                  <a-textarea v-model:value="agentConfig.analysis_prompt" :rows="7" :maxlength="3000" :disabled="!canEditConfig" />
                </a-form-item>
              </a-col>
            </a-row>

            <div class="config-actions">
              <a-space>
                <a-button :loading="loadingConfig" @click="loadAgentConfig">刷新</a-button>
                <a-button type="primary" :disabled="!canEditConfig" :loading="savingConfig" @click="saveAgentConfig">保存配置</a-button>
              </a-space>
            </div>
          </a-form>
          <a-divider />
          <a-table :columns="auditColumns" :data-source="auditLogs" size="small" :pagination="{ pageSize: 5 }" />
        </a-card>
      </a-tab-pane>

      <a-tab-pane key="permission-config" tab="用户权限配置">
        <a-card :bordered="false">
          <a-row :gutter="12" style="margin-bottom: 12px">
            <a-col :span="6">
              <a-input v-model:value="newUserForm.username" :disabled="!canEditConfig" placeholder="用户名称，如 sales01" />
            </a-col>
            <a-col :span="6">
              <a-input-password v-model:value="newUserForm.password" :disabled="!canEditConfig" placeholder="初始密码" />
            </a-col>
            <a-col :span="8">
              <a-select
                v-model:value="newUserForm.roles"
                mode="multiple"
                :disabled="!canEditConfig"
                :options="permissionRoleOptions"
                placeholder="选择角色"
              />
            </a-col>
            <a-col :span="4" style="text-align: right">
              <a-button type="primary" :disabled="!canEditConfig" @click="addPermissionUser">新增用户</a-button>
            </a-col>
          </a-row>
          <a-table :columns="permissionColumns" :data-source="permissionUsers" size="small" :pagination="false">
            <template #bodyCell="{ column, record }">
              <template v-if="column.dataIndex === 'roles'">
                <a-select
                  v-model:value="record.roles"
                  mode="multiple"
                  style="width: 260px"
                  :options="permissionRoleOptions"
                  :disabled="!canEditConfig"
                />
              </template>
              <template v-if="column.dataIndex === 'is_active'">
                <a-switch :checked="record.is_active" :disabled="!canEditConfig" @change="(v:boolean) => toggleUserEnabled(record, v)" />
              </template>
              <template v-if="column.dataIndex === 'action'">
                <a-space>
                  <a-button type="link" :disabled="!canEditConfig" @click="saveUserRoles(record)">保存</a-button>
                  <a-popconfirm title="确认删除该用户？" @confirm="() => deletePermissionUser(record)">
                    <a-button type="link" danger :disabled="!canEditConfig || record.username === 'admin'">删除</a-button>
                  </a-popconfirm>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import type { UploadProps } from 'ant-design-vue'
import { InboxOutlined } from '@ant-design/icons-vue'
import { agentApi, dashboardApi, authApi } from '@/api'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'

const activeTab = ref('upload')
const appStore = useAppStore()
const userStore = useUserStore()

const templateType = ref('production_daily')
const fileList = ref<any[]>([])
const uploadPreview = ref<any>(null)
const loadingConfig = ref(false)
const savingConfig = ref(false)
const savingKey = ref(false)
const canEditConfig = computed(() => userStore.isAdmin)
const newApiKey = ref('')
const auditLogs = ref<any[]>([])
const loadingRegionConfig = ref(false)
const savingRegionConfig = ref(false)
const regionRows = ref<Array<{ key: number; region: string; city: string }>>([])
const regionCoords = ref<Record<string, number[]>>({})
const regionColors = ref<Record<string, string>>({})
const metricUnits = reactive({
  production: '万吨',
  sales: '万吨',
  inventory: '万吨',
  avg_price: '元/吨',
  amount: '万元',
})
const permissionUsers = ref<Array<{ key: number; id: number; username: string; roles: string[]; is_active: boolean }>>([])
const permissionRoleOptions = ref<Array<{ label: string; value: string }>>([
  { label: '管理员', value: 'admin' },
  { label: '分析员', value: 'analyst' },
  { label: '访客', value: 'viewer' },
])
const newUserForm = reactive({
  username: '',
  password: '',
  roles: [] as string[],
})
const brandForm = reactive({
  companyName: appStore.companyName,
  companyLogo: appStore.companyLogo,
})

const providerOptions = [
  { label: 'DeepSeek', value: 'deepseek' },
  { label: 'OpenAI兼容', value: 'openai-compatible' },
]
const providerPresets: Record<string, { baseUrl: string; defaultModel: string }> = {
  deepseek: { baseUrl: 'https://api.deepseek.com', defaultModel: 'deepseek-chat' },
  'openai-compatible': { baseUrl: 'https://api.openai.com/v1', defaultModel: 'gpt-4o-mini' },
}

const deepseekModelOptions = [
  { label: 'deepseek-chat', value: 'deepseek-chat' },
  { label: 'deepseek-reasoner', value: 'deepseek-reasoner' },
]
const openaiModelOptions = [
  { label: 'gpt-4o-mini', value: 'gpt-4o-mini' },
  { label: 'gpt-4.1', value: 'gpt-4.1' },
]

const agentConfig = reactive({
  provider: 'deepseek',
  model: 'deepseek-chat',
  base_url: 'https://api.deepseek.com',
  api_key: '',
  temperature: 0.5,
  sql_prompt: '',
  analysis_prompt: '',
})
const modelOptions = computed(() => agentConfig.provider === 'deepseek' ? deepseekModelOptions : openaiModelOptions)

const templates = [
  { key: 'production_daily', name: '生产日报模板', desc: '基地/品类/日期/产量' },
  { key: 'monthly_plan', name: '月度计划模板', desc: '基地/品类/月份/计划产量' },
  { key: 'yearly_plan', name: '年度计划模板', desc: '基地或区域/品类/年份/计划量' },
  { key: 'sales_target', name: '销售目标模板', desc: '区域/型号/袋散/月份/目标量' },
  { key: 'cost_data', name: '成本数据模板', desc: '基地/品类/月份/单位成本' },
  { key: 'logistics_cost', name: '物流成本模板', desc: '起点基地/终点区域/距离/单位成本' },
  { key: 'inventory_params', name: '库存参数模板', desc: '基地/品类/安全库存/仓容上限' },
]

const beforeUpload: UploadProps['beforeUpload'] = (file) => {
  fileList.value = [file]
  simulatePreview()
  return false
}

const handleRemove = () => {
  fileList.value = []
  uploadPreview.value = null
}

function simulatePreview() {
  setTimeout(() => {
    uploadPreview.value = {
      total: 18,
      valid: 16,
      errors: 2,
      rows: Array.from({ length: 8 }, (_, i) => ({
        key: i,
        base: ['龙岩基地', '三明基地', '南平基地', '泉州基地'][i % 4],
        category: i % 2 === 0 ? '水泥' : '熟料',
        date: '2026-02-' + String(i + 1).padStart(2, '0'),
        value: +(5 + Math.random() * 8).toFixed(2),
        hasError: i === 3 || i === 6,
        errorMsg: i === 3 ? '产量超出产能上限' : i === 6 ? '日期格式错误' : '',
      }))
    }
  }, 500)
}

const previewColumns = [
  { title: '基地', dataIndex: 'base', width: 100 },
  { title: '品类', dataIndex: 'category', width: 80 },
  { title: '日期', dataIndex: 'date', width: 110 },
  { title: '值(万吨)', dataIndex: 'value', width: 100 },
  { title: '异常', dataIndex: 'errorMsg', width: 160, customRender: ({ text }: any) => text || '-' },
]

const recordColumns = [
  { title: '上传时间', dataIndex: 'time', width: 170 },
  { title: '模板类型', dataIndex: 'template', width: 120 },
  { title: '文件名', dataIndex: 'filename', width: 200 },
  { title: '数据行数', dataIndex: 'rows', width: 90 },
  { title: '操作人', dataIndex: 'operator', width: 90 },
  { title: '状态', dataIndex: 'status', width: 90 },
  { title: '操作', dataIndex: 'action', width: 130 },
]

const uploadRecords = ref([
  { key: 1, time: '2026-03-01 14:30', template: '生产日报', filename: '龙岩基地2月生产日报.xlsx', rows: 56, operator: '张三', status: '已入库' },
  { key: 2, time: '2026-03-01 10:15', template: '月度计划', filename: '3月月度生产计划.xlsx', rows: 27, operator: '李四', status: '已入库' },
  { key: 3, time: '2026-02-28 16:45', template: '成本数据', filename: '2月成本数据.xlsx', rows: 18, operator: '王五', status: '待审核' },
  { key: 4, time: '2026-02-27 09:20', template: '物流成本', filename: '运输成本矩阵更新.xlsx', rows: 81, operator: '张三', status: '已入库' },
])

const templateColumns = [
  { title: '模板名称', dataIndex: 'name', width: 160 },
  { title: '模板标识', dataIndex: 'key', width: 160 },
  { title: '说明', dataIndex: 'desc' },
  { title: '操作', dataIndex: 'action', width: 100 },
]
const regionMapColumns = [
  { title: '销售区域/部门', dataIndex: 'region', width: 240 },
  { title: '对应地市', dataIndex: 'city' },
]
const permissionColumns = [
  { title: 'ID', dataIndex: 'id', width: 60 },
  { title: '用户名称', dataIndex: 'username', width: 140 },
  { title: '角色', dataIndex: 'roles', width: 300 },
  { title: '启用', dataIndex: 'is_active', width: 90 },
  { title: '操作', dataIndex: 'action', width: 150 },
]

async function loadAgentConfig() {
  loadingConfig.value = true
  try {
    const res = await agentApi.getConfig()
    Object.assign(agentConfig, res || {})
    await loadAuditLogs()
  } catch (error) {
    if ((error as any)?.response?.status === 403) {
      // 这里的403可能是因为token过期，或者用户权限不足
      // 但拦截器通常会处理401，403则需要提示
      const readonly = await agentApi.getConfig().catch(() => null)
      if (readonly) Object.assign(agentConfig, readonly || {})
      message.warning('您没有编辑权限')
    } else {
      message.error('读取智能体配置失败')
    }
  } finally {
    loadingConfig.value = false
  }
}

async function loadAuditLogs() {
  if (!userStore.isAdmin) {
    auditLogs.value = []
    return
  }
  try {
    const res = await agentApi.getAuditLogs(30)
    auditLogs.value = (res?.items || []).map((item: any, idx: number) => ({
      key: idx,
      time: item.timestamp,
      action: item.action,
      operator: item.operator,
      details: JSON.stringify(item.details || {})
    }))
  } catch {
    auditLogs.value = []
  }
}

async function loadRegionConfig() {
  loadingRegionConfig.value = true
  try {
    const res = await dashboardApi.getRegionConfig()
    const cityMap = res?.region_city_map || {}
    regionRows.value = Object.entries(cityMap).map(([region, city], idx) => ({
      key: idx + 1,
      region: String(region),
      city: String(city),
    }))
    Object.assign(metricUnits, res?.metric_units || {})
    regionCoords.value = res?.region_coords || {}
    regionColors.value = res?.region_colors || {}
  } catch {
    message.error('读取区域配置失败')
  } finally {
    loadingRegionConfig.value = false
  }
}

function validateConfig() {
  if (!/^https?:\/\/.+/.test(agentConfig.base_url)) {
    message.error('API Base URL 格式不正确')
    return false
  }
  if (!(agentConfig.temperature >= 0 && agentConfig.temperature <= 1)) {
    message.error('温度系数必须在 0 到 1 之间')
    return false
  }
  if (!agentConfig.model?.trim()) {
    message.error('模型名称不能为空')
    return false
  }
  const modelValue = String(agentConfig.model || '').trim()
  if (!modelOptions.value.some(item => item.value.toLowerCase() === modelValue.toLowerCase())) {
    message.error('模型与供应商不匹配，请重新选择')
    return false
  }
  const normalized = modelOptions.value.find(item => item.value.toLowerCase() === modelValue.toLowerCase())?.value
  if (normalized) {
    agentConfig.model = normalized
  }
  if ((agentConfig.sql_prompt || '').length > 3000 || (agentConfig.analysis_prompt || '').length > 3000) {
    message.error('提示词长度不能超过 3000')
    return false
  }
  return true
}

function resetBrandForm() {
  brandForm.companyName = appStore.companyName
  brandForm.companyLogo = appStore.companyLogo
}

function saveBrandConfig() {
  if (!brandForm.companyName.trim()) {
    message.error('企业名称不能为空')
    return
  }
  appStore.setCompanyBrand(brandForm.companyName.trim(), brandForm.companyLogo.trim())
  message.success('品牌配置已保存')
}

async function saveApiKey() {
  if (!newApiKey.value.trim()) return
  savingKey.value = true
  try {
    await agentApi.updateApiKey(newApiKey.value.trim())
    newApiKey.value = ''
    await loadAgentConfig()
    message.success('模型KEY已更新')
  } catch {
    message.error('更新KEY失败，请检查权限')
  } finally {
    savingKey.value = false
  }
}

async function saveRegionConfig() {
  savingRegionConfig.value = true
  try {
    const regionCityMap = regionRows.value.reduce((acc, cur) => {
      const region = cur.region.trim()
      const city = cur.city.trim()
      if (region && city) acc[region] = city
      return acc
    }, {} as Record<string, string>)
    const payload = {
      region_city_map: regionCityMap,
      metric_units: { ...metricUnits },
      region_coords: { ...regionCoords.value },
      region_colors: { ...regionColors.value },
    }
    await dashboardApi.saveRegionConfig(payload)
    message.success('区域配置已保存')
    await loadRegionConfig()
  } catch {
    message.error('保存失败，请检查JSON格式与权限')
  } finally {
    savingRegionConfig.value = false
  }
}

function addRegionRow() {
  regionRows.value.push({
    key: Date.now(),
    region: '',
    city: '',
  })
}

async function loadPermissionConfig() {
  try {
    const res = await authApi.getUsers()
    permissionUsers.value = (res || []).map((item: any) => ({
      key: item.id,
      ...item,
      roles: [...(item.roles || [])],
    }))
  } catch {
    permissionUsers.value = []
  }
}

async function saveUserRoles(record: any) {
  try {
    await authApi.updateUser(record.id, { roles: record.roles || [] })
    message.success('用户权限已更新')
    await loadPermissionConfig()
  } catch {
    message.error('保存权限失败')
  }
}

async function addPermissionUser() {
  const username = newUserForm.username.trim()
  const password = newUserForm.password.trim()
  if (!username || !password) {
    message.error('用户名和初始密码不能为空')
    return
  }
  if (!newUserForm.roles.length) {
    message.error('请至少选择一个角色')
    return
  }
  try {
    await authApi.createUser({
      username: username,
      password: password,
      roles: [...newUserForm.roles]
    })
    message.success('用户新增成功')
    newUserForm.username = ''
    newUserForm.password = ''
    newUserForm.roles = []
    await loadPermissionConfig()
  } catch (error: any) {
    const status = error?.response?.status
    if (status === 400) { // Backend returns 400 for duplicate username
      message.error('用户名已存在')
      return
    }
    message.error('新增用户失败')
  }
}

async function toggleUserEnabled(record: any, isActive: boolean) {
  try {
    await authApi.updateUser(record.id, { is_active: isActive })
    message.success('用户状态已更新')
    await loadPermissionConfig()
  } catch {
    message.error('更新用户状态失败')
  }
}

async function deletePermissionUser(record: any) {
  try {
    await authApi.deleteUser(record.id)
    message.success('用户已删除')
    await loadPermissionConfig()
  } catch (error: any) {
    message.error('删除用户失败')
  }
}

async function saveAgentConfig() {
  if (!validateConfig()) return
  savingConfig.value = true
  try {
    const payload = { ...agentConfig, api_key: '' }
    await agentApi.saveConfig(payload)
    await loadAgentConfig()
    message.success('智能体配置已保存')
  } catch (error) {
    message.error('保存失败，请检查配置内容')
  } finally {
    savingConfig.value = false
  }
}

const auditColumns = [
  { title: '时间', dataIndex: 'time', width: 170 },
  { title: '动作', dataIndex: 'action', width: 220 },
  { title: '操作人', dataIndex: 'operator', width: 100 },
  { title: '详情', dataIndex: 'details' },
]

onMounted(() => {
  loadAgentConfig()
  loadRegionConfig()
  loadPermissionConfig()
})

watch(() => agentConfig.provider, (provider) => {
  const preset = providerPresets[provider] || providerPresets.deepseek
  const shouldResetBaseUrl = !agentConfig.base_url
    || (provider === 'deepseek' && agentConfig.base_url.includes('openai.com'))
    || (provider !== 'deepseek' && !agentConfig.base_url.includes('/v1'))
  if (shouldResetBaseUrl) {
    agentConfig.base_url = preset.baseUrl
  }
  const currentModel = String(agentConfig.model || '').trim().toLowerCase()
  if (provider === 'deepseek' && !deepseekModelOptions.some(item => item.value.toLowerCase() === currentModel)) {
    agentConfig.model = 'deepseek-chat'
  }
  if (provider !== 'deepseek' && !openaiModelOptions.some(item => item.value.toLowerCase() === currentModel)) {
    agentConfig.model = preset.defaultModel
  }
})
</script>

<style scoped>
.template-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.template-item {
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.template-item:hover {
  border-color: var(--primary-color);
}

.template-item.active {
  border-color: var(--primary-color);
  background: color-mix(in srgb, var(--primary-color) 12%, transparent);
}

.template-name {
  font-weight: 500;
}

.template-desc {
  font-size: 12px;
  color: var(--text-muted);
  flex: 1;
}

:deep(.error-row) {
  background: #fff2f0 !important;
}

.config-actions {
  display: flex;
  justify-content: flex-end;
}

.auth-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
</style>
