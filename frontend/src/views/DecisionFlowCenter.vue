<template>
  <div class="page-container">
    <div class="page-header">
      <span class="page-title">产销舆情中心</span>
    </div>

    <!-- 舆情概览卡片 -->
    <div class="overview-grid">
      <div 
        class="overview-card total" 
        :class="{ active: overviewFocus === 'all' }" 
        @click="overviewFocus = 'all'"
      >
        <div class="card-content">
          <div class="card-label">舆情总数</div>
          <div class="card-value">{{ overviewTotalCount }}</div>
        </div>
        <div class="card-icon">
          <MessageOutlined />
        </div>
      </div>

      <div 
        class="overview-card pending" 
        :class="{ active: overviewFocus === 'pending' }" 
        @click="overviewFocus = 'pending'"
      >
        <div class="card-content">
          <div class="card-label">待处理</div>
          <div class="card-value">{{ pendingCount }}</div>
        </div>
        <div class="card-icon">
          <ClockCircleOutlined />
        </div>
      </div>

      <div 
        class="overview-card processing" 
        :class="{ active: overviewFocus === 'processing' }" 
        @click="overviewFocus = 'processing'"
      >
        <div class="card-content">
          <div class="card-label">跟进中</div>
          <div class="card-value">{{ processingCount }}</div>
        </div>
        <div class="card-icon">
          <SyncOutlined />
        </div>
      </div>

      <div 
        class="overview-card feedback" 
        :class="{ active: overviewFocus === 'feedback' }" 
        @click="overviewFocus = 'feedback'"
      >
        <div class="card-content">
          <div class="card-label">已反馈</div>
          <div class="card-value">{{ feedbackCount }}</div>
        </div>
        <div class="card-icon">
          <MessageOutlined />
        </div>
      </div>

      <div 
        class="overview-card overdue" 
        :class="{ active: overviewFocus === 'overdue' }" 
        @click="overviewFocus = 'overdue'"
      >
        <div class="card-content">
          <div class="card-label">已超时</div>
          <div class="card-value">{{ overdueCount }}</div>
        </div>
        <div class="card-icon">
          <WarningOutlined />
        </div>
      </div>

      <div 
        class="overview-card closed" 
        :class="{ active: overviewFocus === 'closed' }" 
        @click="overviewFocus = 'closed'"
      >
        <div class="card-content">
          <div class="card-label">已关闭</div>
          <div class="card-value">{{ closedCount }}</div>
        </div>
        <div class="card-icon">
          <CheckCircleOutlined />
        </div>
      </div>
    </div>

    <a-card :bordered="false" title="预警事件流" style="margin-bottom: 16px">
      <a-space wrap style="margin-bottom: 12px">
        <a-select v-model:value="queryType" style="width: 120px">
          <a-select-option value="全部">全部类型</a-select-option>
          <a-select-option value="履约风险">履约风险</a-select-option>
          <a-select-option value="库存异常">库存异常</a-select-option>
          <a-select-option value="价格异常">价格异常</a-select-option>
          <a-select-option value="订单异常">订单异常</a-select-option>
          <a-select-option value="生产异常">生产异常</a-select-option>
        </a-select>
        <a-select v-model:value="queryLevel" style="width: 100px">
          <a-select-option value="全部">全部级别</a-select-option>
          <a-select-option value="P1">P1</a-select-option>
          <a-select-option value="P2">P2</a-select-option>
          <a-select-option value="P3">P3</a-select-option>
        </a-select>
        <a-select v-model:value="queryStatus" style="width: 110px">
          <a-select-option value="全部">全部状态</a-select-option>
          <a-select-option value="未处理">未处理</a-select-option>
          <a-select-option value="已指派">已指派</a-select-option>
          <a-select-option value="处理中">处理中</a-select-option>
          <a-select-option value="超时">超时</a-select-option>
          <a-select-option value="已关闭">已关闭</a-select-option>
        </a-select>
        <a-input v-model:value="queryKeyword" placeholder="搜索标题/描述/组织" style="width: 220px" allow-clear />
        <a-button @click="resetFilters">重置筛选</a-button>
        <a-button type="primary" @click="openManualModal">手工提交预警</a-button>
        <a-button @click="handleCreateAutoAlert">模拟</a-button>
      </a-space>

      <div class="alert-list">
        <div
          v-for="item in visibleAlertRows"
          :key="item.alert_id"
          class="alert-item"
          :class="[severityClass(item), topicClass(item.alert_type)]"
        >
          <div class="alert-item-head">
            <div class="alert-title-wrap">
              <span class="alert-icon">{{ levelIcon(item.alert_level) }}</span>
              <span class="alert-title">{{ item.alert_title || `${item.affected_org_name || '区域'}${item.alert_type}` }}</span>
            </div>
            <a-space>
              <a-tag :color="item.alert_level === 'P1' ? 'red' : item.alert_level === 'P2' ? 'orange' : 'blue'">{{ item.alert_level }}</a-tag>
              <a-tag>{{ item.severity_tag || '警告' }}</a-tag>
              <a-tag :color="topicTagColor(item.alert_type)">{{ topicLabel(item.alert_type) }}</a-tag>
              <a-tag :color="statusColor(item)">{{ statusLabel(item) }}</a-tag>
            </a-space>
          </div>
          <div class="alert-content">{{ item.alert_content || fallbackContent(item) }}</div>
          <div class="alert-meta">
            <span>来源：{{ item.source_type === 'ticket' ? '舆情工单' : '自动监控' }}</span>
            <span>状态：{{ statusLabel(item) }}</span>
            <span>负责人：{{ item.owner_user || '未设置' }}</span>
            <span>处理人：{{ item.assignee_user || '未指派' }}</span>
            <span>预警时间：{{ displayAlertTime(item) }}</span>
            <span>完成时间：{{ item.action_deadline || '-' }}</span>
          </div>
          <div class="suggestion-box">
            <div class="suggestion-main">
              <div class="suggestion-main-content">
                <span class="suggestion-label">AI建议：</span>
                <span class="suggestion-text">{{ suggestionForAlert(item) }}</span>
              </div>
              <div class="suggestion-actions">
                <a-tag class="suggestion-type-tag" color="blue">{{ suggestionTagForAlert(item) }}</a-tag>
                <a-button
                  size="small"
                  type="text"
                  class="vote-btn vote-up"
                  @click="handleSuggestionVote(item, '已采纳')"
                >
                  <template #icon><LikeOutlined /></template>
                </a-button>
                <a-button
                  size="small"
                  type="text"
                  danger
                  class="vote-btn vote-down"
                  @click="handleSuggestionVote(item, '已驳回')"
                >
                  <template #icon><DislikeOutlined /></template>
                </a-button>
              </div>
            </div>
            <div class="suggestion-footer">
              <a-button size="small" type="link" @click="openAIDetailsByAlert(item)">AI思路说明</a-button>
              <a-button size="small" type="primary" @click="openProcessDrawer(item)">去处理</a-button>
            </div>
          </div>
        </div>
      </div>
    </a-card>

    <!-- AI 思路说明弹窗 -->
    <a-modal
      v-model:open="aiDetailsVisible"
      title="AI 决策思路说明"
      width="600px"
      :footer="null"
    >
      <div v-if="currentAIDetail" class="ai-detail-content">
        <div class="detail-section">
          <div class="detail-title">建议核心</div>
          <div class="detail-text">{{ currentAIDetail.recommendation_summary }}</div>
        </div>
        <div class="detail-section">
          <div class="detail-title">决策依据</div>
          <div class="detail-text">
            {{ currentAIDetail.reasoning_logic || '基于当前库存安全水位、历史销量趋势及物流成本优化模型，系统识别出该区域存在潜在供需缺口。通过运筹算法模拟，建议采取上述调配动作以最大化整体收益并规避履约风险。' }}
          </div>
        </div>
        <div class="detail-section">
          <div class="detail-title">执行细节</div>
          <a-descriptions bordered size="small" :column="2">
            <a-descriptions-item label="建议动作">{{ currentAIDetail.action_type }}</a-descriptions-item>
            <a-descriptions-item label="建议数量">{{ currentAIDetail.action_qty_ton }} 吨</a-descriptions-item>
            <a-descriptions-item label="置信度">94.2%</a-descriptions-item>
          </a-descriptions>
        </div>
      </div>
    </a-modal>

    <a-modal
      v-model:open="manualVisible"
      title="手工提交预警"
      width="520px"
      ok-text="提交"
      cancel-text="取消"
      @ok="handleCreateTicketAlert"
    >
      <a-space direction="vertical" style="width: 100%">
        <a-space style="width: 100%">
          <a-select v-model:value="manualForm.alert_level" style="width: 90px">
            <a-select-option value="P1">P1</a-select-option>
            <a-select-option value="P2">P2</a-select-option>
            <a-select-option value="P3">P3</a-select-option>
          </a-select>
          <a-select v-model:value="manualForm.alert_type" style="width: 150px">
            <a-select-option value="履约风险">履约风险</a-select-option>
            <a-select-option value="库存异常">库存异常</a-select-option>
            <a-select-option value="价格异常">价格异常</a-select-option>
            <a-select-option value="订单异常">订单异常</a-select-option>
            <a-select-option value="生产异常">生产异常</a-select-option>
          </a-select>
          <a-input v-model:value="manualForm.event_time" placeholder="预警时间(默认当前)" style="flex: 1" />
        </a-space>
        <a-input v-model:value="manualForm.alert_title" placeholder="舆情标题" />
        <a-textarea v-model:value="manualForm.alert_content" :rows="4" placeholder="舆情描述/上下文" />
      </a-space>
    </a-modal>

    <a-modal
      v-model:open="processVisible"
      :title="`处置台 · ${processAlertTitle}`"
      width="620px"
      ok-text="提交处置"
      cancel-text="取消"
      @ok="submitProcess"
    >
      <a-space direction="vertical" style="width: 100%">
        <div class="process-target-card">
          <div class="process-target-label">本次处理对象</div>
          <div class="process-target-title">{{ processAlertTitle || '-' }}</div>
          <div class="process-target-content">{{ processAlertContent || '-' }}</div>
        </div>
        <a-radio-group v-model:value="processMode">
          <a-radio-button value="assign">指派</a-radio-button>
          <a-radio-button value="process">处理</a-radio-button>
        </a-radio-group>
        <template v-if="processMode === 'assign'">
          <div class="field-hint">指派人：仅在指派模式填写</div>
          <a-input v-model:value="processForm.assignee_user" size="large" placeholder="指派处理人" />
          <div class="field-hint">指派动作：例如加急、跨区协同、升级处理</div>
          <a-select v-model:value="processForm.assign_action" size="large" class="wide-select" placeholder="选择指派动作">
            <a-select-option v-for="action in assignActionOptions" :key="action" :value="action">{{ action }}</a-select-option>
          </a-select>
          <div class="field-hint">指派说明：记录本次指派依据与要求</div>
          <a-textarea v-model:value="processForm.assign_note" :rows="3" placeholder="填写指派说明" />
          <a-input v-model:value="processForm.action_deadline" size="large" placeholder="完成时间(YYYY-MM-DD HH:mm，可选)" />
        </template>
        <template v-else>
          <div class="field-hint">处理动作：用于标记你当前的处置动作</div>
          <a-select v-model:value="processForm.process_action" size="large" class="wide-select" placeholder="选择处理动作">
            <a-select-option v-for="action in processActionOptions" :key="action" :value="action">{{ action }}</a-select-option>
          </a-select>
          <div class="field-hint">处理意见：用于记录你本人的处理结果</div>
          <a-textarea v-model:value="processForm.process_result" :rows="4" placeholder="填写处理意见/回执结果" />
        </template>
      </a-space>
    </a-modal>

    <a-modal
      v-model:open="aiSuggestVisible"
      :title="`AI分析 · ${aiSuggestTitle}`"
      width="900px"
      ok-text="写入建议"
      cancel-text="关闭"
      :confirm-loading="aiSuggestSubmitting"
      @ok="confirmAiSuggestion"
    >
      <a-space direction="vertical" style="width: 100%">
        <a-tabs v-model:activeKey="aiSuggestTab">
          <a-tab-pane key="analysis" tab="AI思路">
            <a-alert type="info" show-icon message="当前为模拟效果：下一阶段将接入AGENT接口返回意见" />
            <div class="ai-analysis-list">
              <div v-for="block in aiAnalysisBlocks" :key="block.title" class="ai-analysis-box">
                <div class="ai-analysis-title">{{ block.title }}</div>
                <div class="ai-analysis-content">{{ block.content }}</div>
              </div>
            </div>
          </a-tab-pane>
          <a-tab-pane key="base" tab="基础参数（V2）">
            <a-spin :spinning="optimizerParamsLoading">
              <a-row :gutter="12">
                <a-col :span="12">
                  <a-card size="small" title="产能参数">
                    <a-table :data-source="capacityRowsV2" :columns="capacityCols" :pagination="false" size="small" row-key="base" />
                  </a-card>
                </a-col>
                <a-col :span="12">
                  <a-card size="small" title="需求参数">
                    <a-table :data-source="demandRowsV2" :columns="demandCols" :pagination="false" size="small" row-key="region" />
                  </a-card>
                </a-col>
              </a-row>
              <a-row :gutter="12" style="margin-top: 12px">
                <a-col :span="12">
                  <a-card size="small" title="售价参数">
                    <a-table :data-source="priceRowsV2" :columns="priceCols" :pagination="false" size="small" row-key="region" />
                  </a-card>
                </a-col>
                <a-col :span="12">
                  <a-card size="small" title="成品成本参数">
                    <a-table :data-source="prodCostRowsV2" :columns="prodCostCols" :pagination="false" size="small" row-key="base" />
                  </a-card>
                </a-col>
              </a-row>
            </a-spin>
          </a-tab-pane>
          <a-tab-pane key="factor" tab="变化因子模拟">
            <a-row :gutter="12">
              <a-col :span="8">
                <a-card size="small" title="变化因子">
                  <a-space direction="vertical" style="width: 100%">
                    <a-select v-model:value="factorForm.type" @change="onFactorTypeChange">
                      <a-select-option value="capacity">产能</a-select-option>
                      <a-select-option value="price">售价</a-select-option>
                      <a-select-option value="demand">需求</a-select-option>
                      <a-select-option value="prod_cost">成品成本</a-select-option>
                      <a-select-option value="transport">运输成本</a-select-option>
                    </a-select>
                    <a-select v-model:value="factorForm.mode">
                      <a-select-option value="pct">百分比</a-select-option>
                      <a-select-option value="abs">绝对值</a-select-option>
                    </a-select>
                    <a-input-number v-model:value="factorForm.value" style="width: 100%" :addon-after="factorForm.mode === 'pct' ? '%' : factorValueUnit" />
                    <a-select v-if="factorNeedsBase" v-model:value="factorForm.bases" mode="multiple" allow-clear placeholder="选择基地（可多选）">
                      <a-select-option v-for="base in optimizerBases" :key="base" :value="base">{{ base }}</a-select-option>
                    </a-select>
                    <a-select v-if="factorNeedsRegion" v-model:value="factorForm.regions" mode="multiple" allow-clear placeholder="选择区域（可多选）">
                      <a-select-option v-for="region in optimizerRegions" :key="region" :value="region">{{ region }}</a-select-option>
                    </a-select>
                    <a-select v-if="factorNeedsProduct" v-model:value="factorForm.products" mode="multiple" allow-clear placeholder="选择品种（可多选）">
                      <a-select-option v-for="product in optimizerProducts" :key="product" :value="product">{{ product }}</a-select-option>
                    </a-select>
                    <a-button type="primary" @click="addFactorAdjustments">加入调整项</a-button>
                  </a-space>
                </a-card>
              </a-col>
              <a-col :span="16">
                <a-card size="small" title="调整项（支持多项叠加）">
                  <a-empty v-if="whatifAdjustments.length === 0" description="请先添加调整项" />
                  <div v-for="(adj, idx) in whatifAdjustments" :key="`${adj.type}-${idx}`" class="adj-line">
                    <span>{{ renderAdjustment(adj) }}</span>
                    <a-button size="small" danger @click="removeWhatifAdjustment(idx)">删除</a-button>
                  </div>
                  <a-space style="margin-top: 10px">
                    <a-button @click="clearWhatifAdjustments">清空</a-button>
                    <a-button type="primary" :loading="whatifRunning" @click="runWhatifSimulation">运行模拟并刷新建议</a-button>
                  </a-space>
                  <div v-if="whatifResult" class="whatif-result">
                    <div>利润变化：{{ whatifResult.profit_delta >= 0 ? '+' : '' }}{{ whatifResult.profit_delta }} 万元（{{ whatifResult.profit_delta_pct }}%）</div>
                    <div>结论：{{ whatifResult.recommendation }}</div>
                  </div>
                </a-card>
              </a-col>
            </a-row>
          </a-tab-pane>
        </a-tabs>
      </a-space>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import {
  DislikeOutlined,
  LikeOutlined,
  MessageOutlined,
  ClockCircleOutlined,
  SyncOutlined,
  WarningOutlined,
  CheckCircleOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { computed, onMounted, ref } from 'vue'
import { authApi, decisionFlowApi, optimizerApi, queryApi } from '@/api'

const alertRows = ref<any[]>([])
const recommendationRows = ref<any[]>([])
const selectedAlertId = ref('')
const activeView = ref('handle')
const currentUser = ref('')
const processVisible = ref(false)
const manualVisible = ref(false)
const aiSuggestVisible = ref(false)
const aiSuggestSubmitting = ref(false)
const aiSuggestTab = ref('analysis')
const processAlertTitle = ref('')
const processAlertContent = ref('')
const aiSuggestTitle = ref('')
const aiAnalysisBlocks = ref<Array<{ title: string; content: string }>>([])
const aiSuggestionDraft = ref<any>(null)
const aiSuggestAlertId = ref('')
const optimizerParamsLoading = ref(false)
const whatifRunning = ref(false)
const optimizerBases = ref<string[]>([])
const optimizerRegions = ref<string[]>([])
const optimizerProducts = ref<string[]>([])
const capacityRowsV2 = ref<any[]>([])
const demandRowsV2 = ref<any[]>([])
const priceRowsV2 = ref<any[]>([])
const prodCostRowsV2 = ref<any[]>([])
const whatifAdjustments = ref<any[]>([])
const whatifResult = ref<any>(null)
const queryType = ref('全部')
const queryLevel = ref('全部')
const queryStatus = ref('全部')
const queryKeyword = ref('')
const overviewFocus = ref('all')
const aiDetailsVisible = ref(false)
const currentAIDetail = ref<any>(null)
const processMode = ref('assign')
const suggestionLoadingMap = ref<Record<string, boolean>>({})
const assignActionOptions = ref<string[]>([])
const processActionOptions = ref<string[]>([])

const manualForm = ref({
  alert_level: 'P2',
  alert_type: '履约风险',
  alert_title: '',
  alert_content: '',
  event_time: '',
})

const processForm = ref({
  assignee_user: '',
  assign_action: '',
  assign_note: '',
  action_deadline: '',
  process_action: '',
  process_result: '',
})
const factorForm = ref({
  type: 'capacity',
  mode: 'pct',
  value: 0,
  bases: [] as string[],
  regions: [] as string[],
  products: ['散装'] as string[],
})

const capacityCols = [
  { title: '基地', dataIndex: 'base' },
  { title: '散装', dataIndex: 'bulk' },
  { title: '袋装', dataIndex: 'bag' },
]
const demandCols = [
  { title: '区域', dataIndex: 'region' },
  { title: '散装', dataIndex: 'bulk' },
  { title: '袋装', dataIndex: 'bag' },
]
const priceCols = [
  { title: '区域', dataIndex: 'region' },
  { title: '散装', dataIndex: 'bulk' },
  { title: '袋装', dataIndex: 'bag' },
]
const prodCostCols = [
  { title: '基地', dataIndex: 'base' },
  { title: '散装', dataIndex: 'bulk' },
  { title: '袋装', dataIndex: 'bag' },
]

const loadData = async () => {
  const [alerts, recs] = await Promise.all([
    decisionFlowApi.listAlerts({ limit: 300 }),
    decisionFlowApi.listRecommendations({ limit: 300 }),
  ])
  alertRows.value = alerts?.items || []
  recommendationRows.value = recs?.items || []
  if (!selectedAlertId.value && alertRows.value.length) {
    selectedAlertId.value = alertRows.value[0].alert_id
  }
}

const loadCurrentUser = async () => {
  try {
    const me = await authApi.getMe()
    currentUser.value = me?.username || ''
  } catch {
    currentUser.value = ''
  }
}

const loadActionConfig = async () => {
  try {
    const cfg = await decisionFlowApi.getActionConfig()
    assignActionOptions.value = Array.isArray(cfg?.assign_actions) ? cfg.assign_actions : []
    processActionOptions.value = Array.isArray(cfg?.process_actions) ? cfg.process_actions : []
  } catch {
    assignActionOptions.value = []
    processActionOptions.value = []
  }
}

const loadOptimizerParams = async () => {
  optimizerParamsLoading.value = true
  try {
    const params = await optimizerApi.getParams()
    optimizerBases.value = params?.bases || []
    optimizerRegions.value = params?.regions || []
    optimizerProducts.value = params?.products || ['散装', '袋装']
    capacityRowsV2.value = optimizerBases.value.map((base: string) => ({
      base,
      bulk: Number(params?.capacity?.[base]?.['散装'] || 0),
      bag: Number(params?.capacity?.[base]?.['袋装'] || 0),
    }))
    demandRowsV2.value = optimizerRegions.value.map((region: string) => ({
      region,
      bulk: Number(params?.demand?.[region]?.['散装'] || 0),
      bag: Number(params?.demand?.[region]?.['袋装'] || 0),
    }))
    priceRowsV2.value = optimizerRegions.value.map((region: string) => ({
      region,
      bulk: Number(params?.price?.[region]?.['散装'] || 0),
      bag: Number(params?.price?.[region]?.['袋装'] || 0),
    }))
    prodCostRowsV2.value = optimizerBases.value.map((base: string) => ({
      base,
      bulk: Number(params?.prod_cost?.[base]?.['散装'] || 0),
      bag: Number(params?.prod_cost?.[base]?.['袋装'] || 0),
    }))
  } finally {
    optimizerParamsLoading.value = false
  }
}

const factorNeedsBase = computed(() => ['capacity', 'prod_cost', 'transport'].includes(factorForm.value.type))
const factorNeedsRegion = computed(() => ['price', 'demand', 'transport'].includes(factorForm.value.type))
const factorNeedsProduct = computed(() => ['capacity', 'price', 'demand', 'prod_cost'].includes(factorForm.value.type))
const factorValueUnit = computed(() => {
  if (factorForm.value.type === 'capacity' || factorForm.value.type === 'demand') return '万吨'
  return '元/吨'
})

const onFactorTypeChange = () => {
  factorForm.value.bases = []
  factorForm.value.regions = []
  factorForm.value.products = ['散装']
}

const addFactorAdjustments = () => {
  const t = factorForm.value.type
  const mode = factorForm.value.mode
  const value = Number(factorForm.value.value || 0)
  const bases = factorForm.value.bases.length ? factorForm.value.bases : ['']
  const regions = factorForm.value.regions.length ? factorForm.value.regions : ['']
  const products = factorForm.value.products.length ? factorForm.value.products : ['']
  if ((t === 'capacity' || t === 'prod_cost') && !factorForm.value.bases.length) {
    message.warning('请至少选择一个基地')
    return
  }
  if ((t === 'price' || t === 'demand') && !factorForm.value.regions.length) {
    message.warning('请至少选择一个区域')
    return
  }
  if (t === 'transport' && (!factorForm.value.bases.length || !factorForm.value.regions.length)) {
    message.warning('运输成本请至少选择基地与区域')
    return
  }
  const newItems: any[] = []
  for (const b of bases) {
    for (const r of regions) {
      for (const p of products) {
        const item: any = { type: t, mode, value }
        if (b) item.base = b
        if (r) item.region = r
        if (factorNeedsProduct.value && p) item.product = p
        if (t === 'transport') delete item.product
        newItems.push(item)
      }
    }
  }
  whatifAdjustments.value = [...whatifAdjustments.value, ...newItems]
}

const renderAdjustment = (adj: any) => {
  const unit = adj.mode === 'pct' ? '%' : (adj.type === 'capacity' || adj.type === 'demand' ? '万吨' : '元/吨')
  const target = [adj.base, adj.region, adj.product].filter(Boolean).join(' / ') || '全局'
  return `${adj.type} | ${target} | ${adj.mode} ${adj.value}${unit}`
}

const removeWhatifAdjustment = (idx: number) => {
  whatifAdjustments.value.splice(idx, 1)
}
const clearWhatifAdjustments = () => {
  whatifAdjustments.value = []
}

const runWhatifSimulation = async () => {
  if (!whatifAdjustments.value.length) {
    message.warning('请先添加调整项')
    return
  }
  whatifRunning.value = true
  try {
    const res = await optimizerApi.runWhatIf({
      adjustments: whatifAdjustments.value,
      decompose: true,
    })
    whatifResult.value = res
    const top = Array.isArray(res?.decomposition) && res.decomposition.length ? res.decomposition[0] : null
    const qtyTon = top && Number.isFinite(Number(top.profit_delta))
      ? Math.max(Math.round(Math.abs(Number(top.profit_delta)) * 10), 30)
      : 50
    aiSuggestionDraft.value = {
      summary: res?.recommendation || '建议按模拟结果优先执行高收益调整项。',
      actionType: top?.label || '综合优化',
      qtyTon,
      estNetGain: Number(res?.profit_delta || 0),
    }
    aiAnalysisBlocks.value = [
      { title: '模拟口径', content: `调整项数量：${whatifAdjustments.value.length}；求解状态：${res?.new_solve_status || '-'}；用时：${res?.total_time_ms || 0}ms` },
      { title: '利润变化', content: `${res?.profit_delta >= 0 ? '+' : ''}${res?.profit_delta || 0} 万元（${res?.profit_delta_pct || 0}%）` },
      { title: '建议结论', content: res?.recommendation || '暂无建议结论' },
    ]
    aiSuggestTab.value = 'analysis'
    message.success('变化因子模拟已完成，建议草稿已更新')
  } finally {
    whatifRunning.value = false
  }
}

const suggestionMap = computed(() => {
  const map: Record<string, any> = {}
  recommendationRows.value.forEach((row: any) => {
    if (!map[row.alert_id] || row.recommendation_role === 'PRIMARY') {
      map[row.alert_id] = row
    }
  })
  return map
})
const queryFilteredRows = computed(() => {
  return alertRows.value.filter((item: any) => {
    if (queryType.value !== '全部' && item.alert_type !== queryType.value) return false
    if (queryLevel.value !== '全部' && item.alert_level !== queryLevel.value) return false
    if (queryStatus.value !== '全部') {
      if (statusLabel(item) !== queryStatus.value) return false
    }
    const keyword = queryKeyword.value.trim().toLowerCase()
    if (!keyword) return true
    const text = `${item.alert_title || ''} ${item.alert_content || ''} ${item.affected_org_name || ''}`.toLowerCase()
    return text.includes(keyword)
  })
})
const overviewTotalCount = computed(() => queryFilteredRows.value.length)
const pendingCount = computed(() => queryFilteredRows.value.filter(item => statusLabel(item) === '未处理').length)
const processingCount = computed(() => queryFilteredRows.value.filter(item => statusLabel(item) === '已指派').length)
const feedbackCount = computed(() => queryFilteredRows.value.filter(item => statusLabel(item) === '处理中').length)
const closedCount = computed(() => queryFilteredRows.value.filter(item => statusLabel(item) === '已关闭').length)
const overdueCount = computed(() => queryFilteredRows.value.filter(item => isOverdue(item)).length)
const visibleAlertRows = computed(() => {
  if (overviewFocus.value === 'pending') {
    return queryFilteredRows.value.filter(item => statusLabel(item) === '未处理')
  }
  if (overviewFocus.value === 'processing') {
    return queryFilteredRows.value.filter(item => statusLabel(item) === '已指派')
  }
  if (overviewFocus.value === 'feedback') {
    return queryFilteredRows.value.filter(item => statusLabel(item) === '处理中')
  }
  if (overviewFocus.value === 'overdue') {
    return queryFilteredRows.value.filter(item => isOverdue(item))
  }
  if (overviewFocus.value === 'closed') {
    return queryFilteredRows.value.filter(item => statusLabel(item) === '已关闭')
  }
  return queryFilteredRows.value
})

const topicLabel = (alertType: string) => {
  if (alertType === '库存异常') return '库存'
  if (alertType === '订单异常' || alertType === '履约风险' || alertType === '价格异常') return '销售'
  return '生产'
}

const topicTagColor = (alertType: string) => {
  if (alertType === '库存异常') return 'gold'
  if (alertType === '订单异常' || alertType === '履约风险') return 'purple'
  if (alertType === '价格异常') return 'magenta'
  return 'cyan'
}

const topicClass = (alertType: string) => {
  if (alertType === '库存异常') return 'topic-inventory'
  if (alertType === '订单异常' || alertType === '履约风险' || alertType === '价格异常') return 'topic-sales'
  return 'topic-production'
}

const severityClass = (item: any) => {
  if (item.alert_level === 'P1') return 'alert-p1'
  if (item.alert_level === 'P2') return 'alert-p2'
  return 'alert-p3'
}

const levelIcon = (level: string) => {
  if (level === 'P1') return '🚨'
  if (level === 'P2') return '⚠️'
  return '🔔'
}

const isOverdue = (item: any) => {
  if (['已关闭', '已处理'].includes(item.process_status)) return false
  if (!item.action_deadline) return false
  const deadline = new Date(item.action_deadline.replace(' ', 'T'))
  if (Number.isNaN(deadline.getTime())) return false
  return deadline.getTime() < Date.now()
}

const fallbackContent = (item: any) => {
  const org = item.affected_org_name || '区域'
  const sku = item.sku_name || '产品'
  return `${org}出现${sku}相关异常，请及时跟进处理。`
}

const primarySuggestion = (alertId: string) => suggestionMap.value[alertId] || null
const suggestionTagForAlert = (item: any) => {
  const rec = primarySuggestion(item.alert_id)
  if (rec?.action_type) return rec.action_type
  if (item.alert_type === '库存异常') {
    return String(item.alert_title || '').includes('偏高') ? '压库去化' : '补库调拨'
  }
  if (item.alert_type === '生产异常') return '排产调整'
  if (item.alert_type === '订单异常' || item.alert_type === '履约风险') return '履约保障'
  if (item.alert_type === '价格异常') return '价格修正'
  return '综合处置'
}
const suggestionForAlert = (item: any) => {
  const rec = primarySuggestion(item.alert_id)
  if (rec?.recommendation_summary) return rec.recommendation_summary
  const org = item.affected_org_name || '该组织'
  if (item.alert_type === '库存异常') {
    return String(item.alert_title || '').includes('偏高')
      ? `建议优先对${org}执行库存去化，降低库存占压。`
      : `建议优先对${org}执行跨组织补库，保障安全库存。`
  }
  if (item.alert_type === '生产异常') return `建议对${org}调整排产并预留应急产能。`
  if (item.alert_type === '订单异常' || item.alert_type === '履约风险') return '建议按客户优先级重排订单并保障高优先级履约。'
  if (item.alert_type === '价格异常') return '建议执行区域分层调价并同步重点客户沟通。'
  return '建议先复核异常根因，再按履约优先级执行综合调度。'
}
const formatDateTime = (val: any) => {
  if (!val) return '-'
  const d = new Date(val)
  if (Number.isNaN(d.getTime())) return String(val)
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}
const SIMULATION_MONTH = '2025-12'
const BASES = ['安砂建福', '永安建福', '顺昌炼石', '福州炼石', '宁德建福', '金银湖水泥']
const simulationTime = (day = 31, hhmm = '09:30') => `${SIMULATION_MONTH}-${String(day).padStart(2, '0')} ${hhmm}`
const nowText = () => simulationTime()
const buildAutoAlertBatchFromDecemberData = async () => {
  const inventoryRes = await queryApi.getInventory({ period: 'month', point: SIMULATION_MONTH })
  const inventoryRows = (inventoryRes?.items || []) as any[]
  const rows = inventoryRows.filter((it: any) => it?.category === '水泥' && BASES.includes(it?.base))
  const sorted = [...rows].sort((a: any, b: any) => Math.abs(Number(b?.ratio_pct || 0) - 55) - Math.abs(Number(a?.ratio_pct || 0) - 55))
  const picked = sorted.slice(0, 4)
  const payloads: any[] = []
  for (let i = 0; i < picked.length; i += 1) {
    const row = picked[i]
    const base = row?.base || BASES[i % BASES.length]
    const dayMatch = String(row?.date || '').match(/(\d+)日/)
    const eventDay = dayMatch ? Number(dayMatch[1]) : 31
    const endQty = Number(row?.end_qty || 0)
    const safetyQty = Number(row?.safety_qty || 0)
    const ratio = Number(row?.ratio_pct || 0)
    const salesRes = await queryApi.getSales({ period: 'month', point: SIMULATION_MONTH, base })
    const salesItems = (salesRes?.items || []) as any[]
    const topSku = [...salesItems].sort((a: any, b: any) => Number(b?.qty || 0) - Number(a?.qty || 0))[0]
    const skuName = [topSku?.material_name, topSku?.spec].filter(Boolean).join(' ').trim() || 'P.O42.5'
    const qtyWan = Number.isFinite(endQty) ? endQty.toFixed(2) : '0.00'
    const safetyWan = Number.isFinite(safetyQty) ? safetyQty.toFixed(2) : '0.00'
    const ratioPct = Number.isFinite(ratio) ? ratio.toFixed(1) : '0.0'
    const lowRisk = ratio <= 35
    const highRisk = ratio >= 85
    const gapQtyTon = lowRisk
      ? Math.max(0, Math.round((safetyQty - endQty) * 10000))
      : Math.max(0, Math.round((endQty - safetyQty) * 10000))
    payloads.push({
      alert_level: lowRisk ? 'P1' : 'P2',
      alert_type: '库存异常',
      source_type: 'auto',
      alert_title: lowRisk ? `自动监控触发：${base}${skuName}库存偏低` : (highRisk ? `自动监控触发：${base}${skuName}库存偏高` : `自动监控触发：${base}${skuName}库存波动`),
      alert_content: `2025年12月监测显示，${base}${skuName}库存${qtyWan}万吨，安全线${safetyWan}万吨（库存占比${ratioPct}%）。${lowRisk ? '存在履约风险，建议优先补库。' : (highRisk ? '存在压库风险，建议加快去化。' : '建议持续跟踪库存波动并优化发运节奏。')}`,
      affected_org_name: base,
      sku_name: skuName,
      gap_qty_ton: gapQtyTon,
      owner_user: `${base}负责人`,
      process_status: '待跟进',
      severity_tag: lowRisk ? '严重' : '警告',
      note: `event_time:${simulationTime(eventDay, i % 2 === 0 ? '09:30' : '14:20')}`,
    })
  }
  return payloads
}
const parseEventTime = (item: any) => {
  const note = item?.note || ''
  if (note.startsWith('event_time:')) return note.replace('event_time:', '').trim()
  return ''
}
const displayAlertTime = (item: any) => parseEventTime(item) || formatDateTime(item.created_at)
const statusLabel = (item: any) => {
  if (item.process_status === '已关闭') return '已关闭'
  if (isOverdue(item)) return '超时'
  if ((item.process_result || '').trim()) return '处理中'
  if ((item.assignee_user || '').trim()) return '已指派'
  return '未处理'
}
const statusColor = (item: any) => {
  const status = statusLabel(item)
  if (status === '已关闭') return 'green'
  if (status === '超时') return 'red'
  if (status === '已指派') return 'gold'
  if (status === '处理中') return 'orange'
  return 'blue'
}
const resetFilters = () => {
  queryType.value = '全部'
  queryLevel.value = '全部'
  queryStatus.value = '全部'
  queryKeyword.value = ''
  overviewFocus.value = 'all'
}
const openManualModal = () => {
  manualForm.value.alert_level = 'P2'
  manualForm.value.alert_type = '履约风险'
  manualForm.value.alert_title = ''
  manualForm.value.alert_content = ''
  manualForm.value.event_time = nowText()
  manualVisible.value = true
}
const upsertRecommendation = (row: any) => {
  if (!row?.recommendation_id) return
  const idx = recommendationRows.value.findIndex((it: any) => it.recommendation_id === row.recommendation_id)
  if (idx >= 0) {
    recommendationRows.value.splice(idx, 1, row)
  } else {
    recommendationRows.value = [row, ...recommendationRows.value]
  }
}

const handleCreateTicketAlert = async () => {
  if (!manualForm.value.alert_title || !manualForm.value.alert_content) {
    message.warning('请填写工单标题和内容')
    return
  }
  await decisionFlowApi.createAlert({
    alert_level: manualForm.value.alert_level,
    alert_type: manualForm.value.alert_type,
    alert_title: manualForm.value.alert_title,
    alert_content: manualForm.value.alert_content,
    source_type: 'ticket',
    owner_user: currentUser.value || '值班负责人',
    severity_tag: manualForm.value.alert_level === 'P1' ? '严重' : '警告',
    process_status: '待跟进',
    note: `event_time:${manualForm.value.event_time || nowText()}`,
  })
  manualVisible.value = false
  await loadData()
  message.success('事件工单已提交')
}

const handleCreateModelSuggestionForAlert = async (alertId: string) => {
  if (suggestionLoadingMap.value[alertId]) return
  
  try {
    selectedAlertId.value = alertId
    suggestionLoadingMap.value = { ...suggestionLoadingMap.value, [alertId]: true }
    
    const res = await decisionFlowApi.createModelSuggestion(alertId)
    if (res?.item) {
      upsertRecommendation(res.item)
      message.success('已结合运筹/模型能力生成建议')
    } else {
      message.warning('模型未能生成有效建议，请稍后再试')
    }
  } catch (err: any) {
    console.error('Create suggestion failed:', err)
    message.error(`生成建议失败: ${err.message || '未知错误'}`)
  } finally {
    suggestionLoadingMap.value = { ...suggestionLoadingMap.value, [alertId]: false }
  }
}

const handleCreateAutoAlert = async () => {
  try {
    const res = await decisionFlowApi.regenerateSimulatedAlerts()
    await loadData()
    message.success(`已重建${Number(res?.count || 0)}条模拟预警（按2025-12真实数据）`)
    return
  } catch (_) {
  }
  let payloads: any[] = []
  try {
    payloads = await buildAutoAlertBatchFromDecemberData()
  } catch (_) {
    payloads = [
      {
        alert_level: 'P1',
        alert_type: '库存异常',
        source_type: 'auto',
        alert_title: '自动监控触发：安砂建福库存偏低',
        alert_content: '2025年12月监测显示，安砂建福水泥库存低于安全线，存在履约风险。',
        affected_org_name: '安砂建福',
        sku_name: 'P.O42.5',
        owner_user: '安砂建福负责人',
        process_status: '待跟进',
        severity_tag: '严重',
        note: `event_time:${simulationTime(31, '09:30')}`,
      },
      {
        alert_level: 'P2',
        alert_type: '库存异常',
        source_type: 'auto',
        alert_title: '自动监控触发：宁德建福库存偏高',
        alert_content: '2025年12月监测显示，宁德建福水泥库存高于安全线，存在压库风险。',
        affected_org_name: '宁德建福',
        sku_name: 'P.C42.5',
        owner_user: '宁德建福负责人',
        process_status: '待跟进',
        severity_tag: '警告',
        note: `event_time:${simulationTime(31, '14:20')}`,
      },
    ]
  }
  for (const payload of payloads) {
    await decisionFlowApi.createAlert(payload)
  }
  await loadData()
  message.success(`已基于2025年12月真实数据生成${payloads.length}条模拟预警`)
}

const openProcessDrawer = (item: any) => {
  selectedAlertId.value = item.alert_id
  processAlertTitle.value = item.alert_title || `${item.affected_org_name || ''}${item.alert_type || ''}`
  processAlertContent.value = item.alert_content || fallbackContent(item)
  processMode.value = (item.process_result || '').trim() ? 'process' : ((item.assignee_user || '').trim() ? 'assign' : 'assign')
  processForm.value.assignee_user = item.assignee_user || ''
  processForm.value.assign_action = ''
  processForm.value.assign_note = ''
  processForm.value.action_deadline = item.action_deadline || ''
  processForm.value.process_action = ''
  processForm.value.process_result = item.process_result || ''
  processVisible.value = true
}

const submitProcess = async () => {
  if (!selectedAlertId.value) return
  let nextStatus = '未处理'
  let actionType = '跟进'
  let content = '更新处置信息'
  if (processMode.value === 'assign') {
    if (!processForm.value.assignee_user.trim()) {
      message.warning('请填写指派人')
      return
    }
    if (!processForm.value.assign_action) {
      message.warning('请先选择指派动作')
      return
    }
    if (!processForm.value.assign_note.trim()) {
      message.warning('请填写指派说明')
      return
    }
    nextStatus = '已指派'
    actionType = processForm.value.assign_action
    content = `${processForm.value.assign_action}：${processForm.value.assignee_user}；说明：${processForm.value.assign_note}`
    await decisionFlowApi.updateAlert(selectedAlertId.value, {
      assignee_user: processForm.value.assignee_user,
      action_deadline: processForm.value.action_deadline,
      process_status: nextStatus,
    })
  } else {
    if (!processForm.value.process_action) {
      message.warning('请先选择处理动作')
      return
    }
    if (!processForm.value.process_result.trim()) {
      message.warning('请填写处理意见')
      return
    }
    nextStatus = '处理中'
    actionType = processForm.value.process_action
    content = processForm.value.process_result
    await decisionFlowApi.updateAlert(selectedAlertId.value, {
      process_status: nextStatus,
      process_result: processForm.value.process_result,
    })
  }
  await decisionFlowApi.createAlertFollowup(selectedAlertId.value, {
    action_type: actionType,
    content,
    result_status: nextStatus,
  })
  await loadData()
  processVisible.value = false
  message.success('处置已提交')
}

const buildAiSuggestionDraft = async (item: any) => {
  const alertId = item?.alert_id || ''
  const res = await decisionFlowApi.getAiAnalysis(alertId)
  const suggestion = res?.suggestion || {}
  const analysisBlocks = [
    { title: '风险判断', content: res?.risk || '' },
    { title: '根因分析', content: res?.root_cause || '' },
    { title: '处置方案', content: res?.plan || '' },
    { title: '预期影响', content: res?.impact || '' },
  ]
  return {
    summary: suggestion?.summary || '',
    actionType: suggestion?.action_type || '',
    qtyTon: Number(suggestion?.action_qty_ton || 0),
    estNetGain: Number(suggestion?.est_net_gain || 0),
    analysisBlocks,
  }
}

const openAiSuggestModal = async (item: any) => {
  aiSuggestAlertId.value = item?.alert_id || ''
  aiSuggestTitle.value = item?.alert_title || `${item?.affected_org_name || ''}${item?.alert_type || ''}`
  aiSuggestTab.value = 'analysis'
  aiAnalysisBlocks.value = [{ title: '分析中', content: '正在生成AI模拟分析，请稍候...' }]
  aiSuggestionDraft.value = null
  whatifAdjustments.value = []
  whatifResult.value = null
  aiSuggestVisible.value = true
  try {
    if (!optimizerBases.value.length || !optimizerRegions.value.length) {
      await loadOptimizerParams()
    }
    const draft = await buildAiSuggestionDraft(item)
    aiSuggestionDraft.value = draft
    aiAnalysisBlocks.value = draft.analysisBlocks
  } catch (_) {
    aiSuggestionDraft.value = {
      summary: '建议优先保障高优先级订单履约，并跟踪库存变化执行滚动处置。',
      actionType: '履约保障',
      qtyTon: 50,
      estNetGain: 5.0,
    }
    aiAnalysisBlocks.value = [
      { title: '风险判断', content: '当前无法完整读取模拟数据，已回退默认分析。' },
      { title: '根因分析', content: `数据口径${SIMULATION_MONTH}暂不可用，建议稍后重试。` },
      { title: '处置方案', content: '建议优先保障高优先级订单履约，并跟踪库存变化执行滚动处置。' },
      { title: '预期影响', content: '预计可降低异常扩散风险并稳定履约表现。' },
    ]
  }
}

const confirmAiSuggestion = async () => {
  if (!aiSuggestAlertId.value) return
  const draft = aiSuggestionDraft.value || {}
  aiSuggestSubmitting.value = true
  try {
    const res = await decisionFlowApi.createRecommendation({
      alert_id: aiSuggestAlertId.value,
      recommendation_role: 'PRIMARY',
      recommendation_summary: draft.summary || '建议优先保障高优先级订单履约，并跟踪库存变化执行滚动处置。',
      action_type: draft.actionType || '履约保障',
      action_qty_ton: Number(draft.qtyTon || 0),
      est_net_gain: Number(draft.estNetGain || 0),
      decision_status: '待确认',
      decision_user: currentUser.value || 'AI模拟',
    })
    upsertRecommendation(res?.item)
    aiSuggestVisible.value = false
    message.success('AI模拟建议已写入')
  } finally {
    aiSuggestSubmitting.value = false
  }
}

const openAIDetailsByAlert = (item: any) => {
  const rec = primarySuggestion(item.alert_id)
  currentAIDetail.value = rec || {
    recommendation_summary: suggestionForAlert(item),
    action_type: suggestionTagForAlert(item),
    action_qty_ton: Number(item.gap_qty_ton || 0),
    reasoning_logic: `基于当前预警类型、状态与上下文信息，系统对${item.affected_org_name || '目标组织'}生成了处置建议，建议优先执行并结合现场反馈滚动调整。`,
  }
  aiDetailsVisible.value = true
}

const handleSuggestionVote = async (item: any, status: string) => {
  let rec = primarySuggestion(item.alert_id)
  if (!rec) {
    const res = await decisionFlowApi.createModelSuggestion(item.alert_id)
    if (!res?.item) {
      message.warning('当前预警暂无法生成可投票建议')
      return
    }
    upsertRecommendation(res.item)
    rec = res.item
  }
  await handleDecision(rec, status)
}

const handleDecision = async (record: any, status: string) => {
  await decisionFlowApi.decideRecommendation(record.recommendation_id, {
    decision_status: status,
    decision_reason: status === '已驳回' ? '人工驳回' : '人工采纳',
  })
  await loadData()
  message.success(`已${status}`)
}

onMounted(async () => {
  await Promise.all([loadCurrentUser(), loadData(), loadActionConfig(), loadOptimizerParams()])
})
</script>

<style scoped>
.ant-card {
  border-radius: 10px;
}

.alert-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 舆情概览网格布局 */
.overview-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.overview-card {
  background: #fff;
  border-radius: 8px;
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid #f0f0f0;
  position: relative;
  overflow: hidden;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
}

.overview-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08);
}

.overview-card.active {
  border-color: #1677ff;
  background: #f0f7ff;
  box-shadow: 0 4px 10px rgba(22, 119, 255, 0.1);
}

.overview-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: transparent;
  transition: all 0.3s;
}

.overview-card.total::before    { background: #1677ff; }
.overview-card.pending::before  { background: #faad14; }
.overview-card.processing::before { background: #1890ff; }
.overview-card.feedback::before  { background: #722ed1; }
.overview-card.overdue::before  { background: #ff4d4f; }
.overview-card.closed::before   { background: #52c41a; }

.card-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.card-label {
  font-size: 12px;
  color: #8c8c8c;
  font-weight: 500;
}

.card-value {
  font-size: 22px;
  font-weight: 700;
  color: #262626;
  font-family: 'DIN Alternate', 'Roboto', sans-serif;
}

.card-icon {
  font-size: 24px;
  opacity: 0.12;
  transition: all 0.3s;
}

.overview-card:hover .card-icon {
  opacity: 0.3;
  transform: scale(1.1);
}

.overview-card.active .card-icon {
  opacity: 0.4;
  color: #1677ff;
}

.overview-card.total:hover { border-color: #1677ff; }
.overview-card.pending:hover { border-color: #faad14; }
.overview-card.processing:hover { border-color: #1890ff; }
.overview-card.feedback:hover { border-color: #722ed1; }
.overview-card.overdue:hover { border-color: #ff4d4f; }
.overview-card.closed:hover { border-color: #52c41a; }

.field-hint {
  color: var(--text-secondary);
  font-size: 12px;
}

.wide-select {
  width: 100%;
}

.alert-item {
  border: 1px solid var(--border-color);
  border-left: 4px solid #d9d9d9;
  border-radius: 8px;
  padding: 10px 12px;
  transition: all 0.2s ease;
}

.alert-item:hover {
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.06);
}

.alert-p1 {
  border-left-color: #ff4d4f;
  background: #fff2f0;
}

.alert-p2 {
  border-left-color: #faad14;
  background: #fffbe6;
}

.alert-p3 {
  border-left-color: #1677ff;
  background: #e6f4ff;
}

.topic-inventory {
  box-shadow: inset 0 0 0 1px rgba(250, 173, 20, 0.18);
}

.topic-sales {
  box-shadow: inset 0 0 0 1px rgba(114, 46, 209, 0.18);
}

.topic-production {
  box-shadow: inset 0 0 0 1px rgba(19, 194, 194, 0.18);
}

.alert-item-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.alert-title-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
}

.alert-title {
  font-weight: 600;
  color: var(--text-primary);
}

.alert-content {
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.alert-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  color: var(--text-secondary);
  font-size: 12px;
}

.alert-actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}

.suggestion-box {
  margin-top: 12px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
}

.suggestion-main {
  padding: 12px 16px 8px 16px;
  margin-bottom: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  background: transparent;
  border: none;
}

.suggestion-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.suggestion-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
  padding: 8px 16px 12px 16px;
  background: transparent;
  border: none;
  margin: 0;
}

.vote-btn {
  width: 28px;
  height: 28px;
  padding: 0;
  border-radius: 999px;
  border: 1px solid #d9d9d9;
  background: #fff;
}

.vote-up:hover {
  border-color: #4096ff;
  color: #1677ff;
}

.vote-down:hover {
  border-color: #ff7875;
  color: #ff4d4f;
}

.ai-detail-content {
  padding: 12px 0;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f1f1f;
  margin-bottom: 8px;
  padding-left: 8px;
  border-left: 3px solid #1677ff;
}

.detail-text {
  color: #595959;
  line-height: 1.6;
  background: #f5f5f5;
  padding: 12px;
  border-radius: 6px;
}

.process-target-card {
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  padding: 10px 12px;
  background: #fafcff;
}

.process-target-label {
  color: #4e5969;
  font-size: 12px;
  margin-bottom: 4px;
}

.process-target-title {
  color: #1d2129;
  font-weight: 600;
  margin-bottom: 4px;
}

.process-target-content {
  color: #4e5969;
  line-height: 1.6;
}

.ai-analysis-box {
  border: 1px solid #e5e6eb;
  background: #fafafa;
  border-radius: 8px;
  padding: 10px 12px;
}

.ai-analysis-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ai-analysis-title {
  font-size: 13px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 4px;
}

.ai-analysis-content {
  white-space: pre-line;
  color: #4e5969;
  line-height: 1.7;
}

.adj-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px dashed #f0f0f0;
}

.whatif-result {
  margin-top: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  color: #135200;
}
</style>
