// 溯源感知共享状态：当前选中的 threat_id 驱动所有下游模块联动刷新。
// 不引 Pinia，用一个 reactive 单例即可（需求第 6 节：联动是核心）。
import { reactive } from 'vue'
import {
  traceApi,
  type TraceThreat,
  type TraceChain,
  type TraceIntent,
  type IntentGraph,
} from '../api/client'

interface TraceState {
  threats: TraceThreat[]
  total: number
  currentId: string
  chains: TraceChain[]
  intent: TraceIntent | null
  graph: IntentGraph | null
  loadingThreats: boolean
  loadingDetail: boolean
  detecting: boolean
  error: string
  apiOnline: boolean | null
}

export const trace = reactive<TraceState>({
  threats: [],
  total: 0,
  currentId: '',
  chains: [],
  intent: null,
  graph: null,
  loadingThreats: false,
  loadingDetail: false,
  detecting: false,
  error: '',
  apiOnline: null,
})

export const current = () => trace.threats.find((t) => t.threat_id === trace.currentId) || null

export async function loadThreats(autoSelect = true) {
  trace.loadingThreats = true
  trace.error = ''
  try {
    const data = await traceApi.listThreats()
    trace.threats = data.threats
    trace.total = data.total
    trace.apiOnline = true
    if (autoSelect && trace.threats.length && !trace.currentId) {
      await selectThreat(trace.threats[0].threat_id)
    }
  } catch (e: any) {
    trace.apiOnline = false
    trace.error = e?.response?.data?.detail ?? '加载 threat 列表失败'
  } finally {
    trace.loadingThreats = false
  }
}

// 选中某 threat → 同步拉取 chain / intent / graph（联动核心）
export async function selectThreat(id: string) {
  if (!id) return
  trace.currentId = id
  trace.loadingDetail = true
  trace.chains = []
  trace.intent = null
  trace.graph = null
  try {
    const [chains, intent, graph] = await Promise.allSettled([
      traceApi.listChains(id),
      traceApi.getIntent(id),
      traceApi.getIntentGraph(id),
    ])
    if (chains.status === 'fulfilled') trace.chains = chains.value.chains
    if (intent.status === 'fulfilled') trace.intent = intent.value
    if (graph.status === 'fulfilled') trace.graph = graph.value
  } finally {
    trace.loadingDetail = false
  }
}

export async function triggerDetect(): Promise<string | null> {
  trace.detecting = true
  trace.error = ''
  try {
    const res = await traceApi.triggerDetect()
    await loadThreats(false)
    if (res.threat_id) await selectThreat(res.threat_id)
    return res.threat_id ?? null
  } catch (e: any) {
    trace.error = e?.response?.data?.detail ?? '触发检测失败'
    return null
  } finally {
    trace.detecting = false
  }
}
