import axios from 'axios'

// 生产由 nginx 反代 /api，开发由 vite proxy 转发 —— 统一相对路径
const http = axios.create({ baseURL: '/', timeout: 30000 })

export interface NodeInfo {
  id: string
  name: string
  role: string
  ssh_host?: string
  direct_ip?: string
  enabled: boolean
  online?: boolean
  detail?: string
}

export interface TaskInfo {
  id: number
  node_id: string
  kind: 'command' | 'script'
  command: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'error'
  exit_code?: number | null
  stdout: string
  stderr: string
  error?: string | null
  created_at?: string
  started_at?: string
  finished_at?: string
}

export interface PresetInfo {
  id: string
  name: string
  node_id: string
  command: string
  workdir?: string
  sudo: boolean
  desc?: string
}

export interface DetectionSample {
  name: string
  true: string
  pred: string
  correct: boolean
  confidence?: number | null
  modality?: string | null
}
export interface DetectionTypeStat {
  type: string
  correct: number
  wrong: number
}
export interface DetectionModalityStat {
  modality: string
  total: number
  correct: number
}
export interface DetectionFileStat {
  name: string
  total: number
  correct: number
  accuracy: number
  type_dist: DetectionTypeStat[]
  modality_dist: DetectionModalityStat[]
  samples: DetectionSample[]
}
export interface DetectionResult {
  total: number
  correct: number
  accuracy: number
  file_count: number
  files: DetectionFileStat[]
}

// ===== 溯源感知（trace）：控制面代理网元3 tactic-prediction 的视图 =====
export interface TraceThreat {
  threat_id: string
  attack_type?: string
  stage?: string
  severity?: string
  ml_confidence?: string
  ml_class?: string
  predicted_category?: string
  modality?: string
  file_name?: string
  timestamp?: string
  stage_source?: string
  stage_confidence?: number
  stage_evidence?: string[]
  stage_scores?: Record<string, number>
}
export interface TraceChainStage {
  stage?: string
  order?: number
  confidence?: number
  desc?: string
  modality?: string
  capec_id?: string
}
export interface TraceChain {
  chain_id: string
  theme?: string
  source?: string
  threat_id?: string
  total_stages?: number
  confidence?: number
  stages: TraceChainStage[]
}
export interface TraceIntentItem {
  attack_pattern?: string
  attack_id?: string
  severity?: string
  techniques?: string[]
  tactics?: string[]
  matched_keywords?: string[]
  source?: string
}
export interface TraceIntent {
  threat_id: string
  attack_type?: string
  modality?: string
  stage?: string
  related?: number
  keywords?: string[]
  intents?: TraceIntentItem[]
  local_intents?: TraceIntentItem[]
  neo4j_intents?: TraceIntentItem[]
  neo4j?: string
}
export interface GraphNode {
  id: string
  label: string
  type: 'threat' | 'stage' | 'capec' | 'tactic' | 'technique'
  [k: string]: any
}
export interface GraphEdge {
  source: string
  target: string
  label?: string
}
export interface IntentGraph {
  threat_id: string
  attack_type?: string
  modality?: string
  stage?: string
  capec_hit: string[]
  keywords: string[]
  source: string
  nodes: GraphNode[]
  edges: GraphEdge[]
}
export interface DetectTrigger {
  threat_id?: string | null
  output: string
}

export const traceApi = {
  listThreats: (limit = 500) =>
    http.get<{ total: number; threats: TraceThreat[] }>('/api/trace/threats', { params: { limit } }).then((r) => r.data),
  listChains: (threatId?: string) =>
    http.get<{ total: number; chains: TraceChain[] }>('/api/trace/chains', { params: threatId ? { threat_id: threatId } : {} }).then((r) => r.data),
  getIntent: (threatId: string) =>
    http.get<TraceIntent>(`/api/trace/intent/${threatId}`).then((r) => r.data),
  getIntentGraph: (threatId: string) =>
    http.get<IntentGraph>(`/api/trace/intent-graph/${threatId}`).then((r) => r.data),
  triggerDetect: () => http.post<DetectTrigger>('/api/trace/detect').then((r) => r.data),
}

// ===== 内生安全主动防御（代理 controller_server_v2.py:8000）=====
export const defenseApi = {
  health: () => http.get('/api/defense/health').then((r) => r.data),
  dashboard: () => http.get<any>('/api/defense/dashboard').then((r) => r.data),
  mimeticStatus: () => http.get<any>('/api/defense/mimetic/status').then((r) => r.data),
  netStatus: () => http.get<any>('/api/defense/status').then((r) => r.data),
  start: (strategy_name: string) =>
    http.post('/api/defense/mimetic/start', { strategy_name }).then((r) => r.data),
  stop: (strategy_name: string) =>
    http.post('/api/defense/mimetic/stop', { strategy_name }).then((r) => r.data),
  stopAll: () => http.post('/api/defense/mimetic/stop-all').then((r) => r.data),
  gameOptimal: (switch_ids?: number[]) =>
    http.post<any>('/api/defense/game-theory/optimal-strategy', switch_ids ? { switch_ids } : {}).then((r) => r.data),
  gameApply: (switch_ids: number[]) =>
    http.post<any>('/api/defense/game-theory/apply-optimal', { switch_ids }).then((r) => r.data),
}

export const api = {
  listNodes: () => http.get<NodeInfo[]>('/api/nodes').then((r) => r.data),
  listPresets: () => http.get<PresetInfo[]>('/api/presets').then((r) => r.data),
  runPreset: (id: string, args = '') =>
    http.post<TaskInfo>(`/api/presets/${id}/run`, { args }).then((r) => r.data),
  stopPreset: (id: string) => http.post<{ stopped: boolean }>(`/api/presets/${id}/stop`).then((r) => r.data),
  probeNode: (id: string) => http.get<NodeInfo>(`/api/nodes/${id}/probe`).then((r) => r.data),
  execCommand: (id: string, command: string) =>
    http.post<TaskInfo>(`/api/nodes/${id}/exec`, { command }).then((r) => r.data),
  execScript: (id: string, payload: { filename: string; content: string; remote_dir?: string; run_cmd?: string }) =>
    http.post<TaskInfo>(`/api/nodes/${id}/script`, payload).then((r) => r.data),
  getDetectionResults: (file?: string) =>
    http.get<DetectionResult>('/api/detection/results', { params: file ? { file } : {} }).then((r) => r.data),
  getDetectionRoll: () =>
    http.get<{ total: number; rows: DetectionSample[] }>('/api/detection/roll').then((r) => r.data),
  getTask: (taskId: number) => http.get<TaskInfo>(`/api/tasks/${taskId}`).then((r) => r.data),
  listTasks: (nodeId?: string) =>
    http.get<TaskInfo[]>('/api/tasks', { params: nodeId ? { node_id: nodeId } : {} }).then((r) => r.data),
}
