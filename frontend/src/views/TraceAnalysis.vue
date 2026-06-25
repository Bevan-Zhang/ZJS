<script setup lang="ts">
// 页面2 威胁溯源：从当前威胁回溯阶段链、传播路径与意图线索。
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { trace, current, selectThreat } from '../stores/trace'
import type { GraphNode, GraphEdge } from '../api/client'
import ThreatBar from '../components/trace/ThreatBar.vue'
import GraphView from '../components/trace/GraphView.vue'

// 由 chains 合成链图：threat 中心 → 各 chain 的 stage 路径
const chainGraph = computed<{ nodes: GraphNode[]; edges: GraphEdge[] }>(() => {
  const tid = trace.currentId
  if (!tid) return { nodes: [], edges: [] }
  const nodes: GraphNode[] = [{ id: tid, label: tid, type: 'threat' }]
  const edges: GraphEdge[] = []
  const seen = new Set([tid])
  for (const c of trace.chains) {
    let prev = tid
    const sorted = [...c.stages].sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
    sorted.forEach((s, i) => {
      const nid = `${c.chain_id}::${i}`
      nodes.push({ id: nid, label: `${s.stage}${s.confidence != null ? ` (${s.confidence})` : ''}`, type: 'stage', desc: s.desc })
      if (!seen.has(nid)) seen.add(nid)
      edges.push({ source: prev, target: nid, label: i === 0 ? c.theme : '' })
      prev = nid
    })
  }
  return { nodes, edges }
})

const intents = computed(() => trace.intent?.intents ?? trace.intent?.local_intents ?? [])
const lastSync = ref('')
let refreshTimer: number | undefined

const syncLabel = computed(() => lastSync.value || '等待同步')

async function refreshTraceDetail() {
  if (!trace.currentId) return
  await selectThreat(trace.currentId)
  lastSync.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
}

onMounted(() => {
  void refreshTraceDetail()
  refreshTimer = window.setInterval(refreshTraceDetail, 8000)
})

onBeforeUnmount(() => {
  if (refreshTimer) window.clearInterval(refreshTimer)
})

watch(() => trace.loadingDetail, (loading) => {
  if (!loading && trace.currentId) {
    lastSync.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  }
})
</script>

<template>
  <div>
    <div class="title-row">
      <div>
        <h2 class="page-title">威胁溯源</h2>
        <p class="page-desc">基于当前 threat 持续回溯攻击阶段、传播路径与证据链。</p>
      </div>
      <div class="live-pill">
        <span class="pulse" />
        <span>{{ trace.loadingDetail ? '同步中' : '实时联动' }}</span>
        <b>{{ syncLabel }}</b>
      </div>
    </div>

    <ThreatBar />

    <!-- threat 摘要 -->
    <div class="tech-panel summary" v-if="current()">
      <span>threat_id <b class="mono">{{ current()!.threat_id }}</b></span>
      <span>攻击类型 <b class="cyan">{{ current()!.attack_type ?? '—' }}</b></span>
      <span>当前阶段 <b>{{ trace.intent?.stage ?? current()!.stage ?? '—' }}</b></span>
      <span>模态 <b>{{ current()!.modality ?? '—' }}</b></span>
    </div>

    <div class="grid">
      <!-- chain 列表 -->
      <div class="tech-panel">
        <div class="tech-h">溯源路径 <span class="cnt">{{ trace.chains.length }} 条候选链</span></div>
        <el-table :data="trace.chains" size="small" v-loading="trace.loadingDetail" style="background: transparent">
          <el-table-column type="expand">
            <template #default="{ row }">
              <div class="stages">
                <div v-for="(s, i) in row.stages" :key="i" class="stage">
                  <span class="ord">{{ s.order ?? i + 1 }}</span>
                  <b>{{ s.stage }}</b>
                  <span class="dim">{{ s.desc }} · conf {{ s.confidence }} · {{ s.modality }}</span>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="theme" label="路径主题" width="160" />
          <el-table-column prop="source" label="来源" width="90" />
          <el-table-column prop="total_stages" label="阶段数" width="80" align="center" />
          <el-table-column prop="confidence" label="置信度" width="90" align="center" />
        </el-table>
      </div>

      <!-- chain 图 -->
      <div class="tech-panel">
        <div class="tech-h">溯源链路图</div>
        <div class="graph-tip">当前 threat 到各阶段节点的实时联动路径。</div>
        <GraphView v-if="chainGraph.nodes.length > 1" :nodes="chainGraph.nodes" :edges="chainGraph.edges" height="360px" />
        <p v-else class="tech-sub" style="margin: 0">当前威胁暂无可视化链路。</p>
      </div>
    </div>

    <!-- 源头意图线索 -->
    <div class="tech-panel" style="margin-top: 18px">
      <div class="tech-h">
        源头意图线索
        <span class="cnt" v-if="trace.intent">
          来源 <b class="cyan">{{ intents[0]?.source ?? (trace.intent.neo4j === 'degraded' ? 'local_subgraph' : '-') }}</b>
          · related {{ trace.intent.related ?? 0 }}
        </span>
      </div>
      <div v-if="trace.intent?.keywords?.length" class="kw">
        触发证据：<el-tag v-for="k in trace.intent.keywords" :key="k" size="small" effect="plain" class="kwtag">{{ k }}</el-tag>
      </div>
      <div class="intents">
        <div v-for="(it, i) in intents" :key="i" class="intent-card">
          <div class="ic-h">
            <b>{{ it.attack_pattern }}</b>
            <el-tag size="small" effect="dark" class="capec">{{ it.attack_id }}</el-tag>
          </div>
          <div class="ic-row"><label>severity</label><span>{{ it.severity ?? '—' }}</span></div>
          <div class="ic-row"><label>tactics</label><span>{{ it.tactics?.length ? it.tactics.join(', ') : '—' }}</span></div>
          <div class="ic-row"><label>techniques</label><span>{{ it.techniques?.length ? it.techniques.join(', ') : '—' }}</span></div>
          <div class="ic-row"><label>matched</label><span>{{ it.matched_keywords?.join(', ') ?? '—' }}</span></div>
          <div class="ic-row"><label>source</label><span class="cyan">{{ it.source }}</span></div>
        </div>
        <p v-if="!intents.length" class="tech-sub" style="margin: 0">当前威胁暂无意图结果。</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-title { margin: 0 0 6px; font-size: 26px; color: #eaf6ff; text-shadow: 0 0 16px var(--tech-glow); }
.page-desc { color: var(--tech-text-dim); margin: 0 0 18px; }
.title-row { display: flex; justify-content: space-between; align-items: flex-start; gap: 18px; }
.live-pill { display: inline-flex; align-items: center; gap: 8px; border: 1px solid rgba(0,229,255,0.35); border-radius: 999px; padding: 7px 12px; color: var(--tech-text-dim); background: rgba(0,229,255,0.07); font-size: 13px; }
.live-pill b { color: #eaf6ff; font-family: 'Consolas', monospace; }
.pulse { width: 8px; height: 8px; border-radius: 50%; background: var(--tech-cyan); box-shadow: 0 0 12px var(--tech-cyan); animation: pulse 1.3s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: .45; transform: scale(.9); } 50% { opacity: 1; transform: scale(1.25); } }
.summary { display: flex; gap: 26px; flex-wrap: wrap; margin-bottom: 18px; }
.summary span { color: var(--tech-text-dim); font-size: 14px; }
.summary b { color: #eaf6ff; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
.graph-tip { color: var(--tech-text-dim); font-size: 12px; margin: -4px 0 8px; }
.cnt { color: var(--tech-text-dim); font-size: 13px; font-weight: 400; margin-left: 8px; }
.cyan { color: var(--tech-cyan); }
.mono { font-family: 'Consolas', monospace; }
.stages { padding: 6px 12px; }
.stage { display: flex; align-items: center; gap: 10px; padding: 4px 0; }
.stage .ord { width: 20px; height: 20px; line-height: 20px; text-align: center; border-radius: 50%; background: rgba(0,229,255,0.18); color: var(--tech-cyan); font-size: 12px; }
.stage .dim { color: var(--tech-text-dim); font-size: 12px; }
.kw { margin-bottom: 12px; color: var(--tech-text-dim); font-size: 13px; }
.kwtag { margin: 0 6px 6px 0; }
.intents { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 12px; }
.intent-card { border: 1px solid var(--tech-border); border-radius: 8px; padding: 12px; background: rgba(0,229,255,0.03); }
.ic-h { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.ic-h b { color: #eaf6ff; }
.capec { background: rgba(0,229,255,0.15); }
.ic-row { display: flex; font-size: 12px; padding: 2px 0; }
.ic-row label { width: 84px; color: var(--tech-text-dim); flex-shrink: 0; }
.ic-row span { color: #cfe6ff; word-break: break-all; }
</style>
