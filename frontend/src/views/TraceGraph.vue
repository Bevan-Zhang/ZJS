<script setup lang="ts">
// 页面3 图谱解释：为什么给出这个 intent —— 局部图谱依据。
import { computed } from 'vue'
import { trace, current } from '../stores/trace'
import ThreatBar from '../components/trace/ThreatBar.vue'
import GraphView from '../components/trace/GraphView.vue'

const g = computed(() => trace.graph)
// 命中高亮：所有 CAPEC 节点 + stage 节点
const highlight = computed(() => {
  const ids: string[] = []
  for (const n of g.value?.nodes ?? []) {
    if (n.type === 'capec' || n.type === 'stage') ids.push(n.id)
  }
  return ids
})
const capecNodes = computed(() => (g.value?.nodes ?? []).filter((n) => n.type === 'capec'))
</script>

<template>
  <div>
    <h2 class="page-title">图谱解释</h2>
    <p class="page-desc">攻击意图解释 → 图谱依据展示：当前威胁命中的局部知识图谱。</p>

    <ThreatBar />

    <!-- threat 摘要 -->
    <div class="tech-panel summary" v-if="current()">
      <span>threat_id <b class="mono">{{ current()!.threat_id }}</b></span>
      <span>攻击类型 <b class="cyan">{{ g?.attack_type ?? current()!.attack_type ?? '—' }}</b></span>
      <span>阶段 <b>{{ g?.stage ?? '—' }}</b></span>
      <span>语义来源 <b class="cyan">{{ g?.source ?? '—' }}</b></span>
      <span>命中 CAPEC <b>{{ g?.capec_hit?.length ?? 0 }}</b></span>
    </div>

    <div class="grid">
      <!-- 图谱可视化 -->
      <div class="tech-panel">
        <div class="tech-h">局部图谱（threat · stage · CAPEC · tactic · technique）</div>
        <div class="graph-tip">拖动节点调整布局，滚轮缩放，拖动画布平移，点击节点聚焦邻接关系。</div>
        <GraphView
          v-if="g && g.nodes.length > 1"
          :nodes="g.nodes"
          :edges="g.edges"
          :highlight="highlight"
          height="480px"
        />
        <p v-else class="tech-sub" style="margin: 0" v-loading="trace.loadingDetail">
          {{ trace.loadingDetail ? '加载图谱中…' : '当前威胁暂无图谱依据。' }}
        </p>
      </div>

      <!-- 命中依据面板 -->
      <div class="tech-panel">
        <div class="tech-h">命中依据</div>
        <div v-if="g?.keywords?.length" class="kw">
          匹配关键词：<el-tag v-for="k in g.keywords" :key="k" size="small" effect="plain" class="kwtag">{{ k }}</el-tag>
        </div>
        <div class="capecs">
          <div v-for="n in capecNodes" :key="n.id" class="cap">
            <div class="cap-h">
              <el-tag size="small" effect="dark">{{ n.capec_id }}</el-tag>
              <b>{{ n.attack_pattern }}</b>
            </div>
            <div class="cap-row"><label>severity</label><span>{{ n.severity ?? '—' }}</span></div>
            <div class="cap-row"><label>命中关键词</label><span>{{ (n.matched_keywords ?? []).join(', ') || '—' }}</span></div>
            <div class="cap-row"><label>来源</label><span class="cyan">{{ n.source ?? '—' }}</span></div>
          </div>
          <p v-if="!capecNodes.length" class="tech-sub" style="margin: 0">暂无命中的 CAPEC。</p>
        </div>
      </div>
    </div>

    <div class="tech-panel legend">
      图例：
      <span class="dot threat" /> 威胁
      <span class="dot stage" /> 阶段
      <span class="dot capec" /> CAPEC
      <span class="dot tactic" /> Tactic
      <span class="dot technique" /> Technique
      <span class="hint">— 高亮（白边/辉光）= 当前命中节点</span>
    </div>
  </div>
</template>

<style scoped>
.page-title { margin: 0 0 6px; font-size: 26px; color: #eaf6ff; text-shadow: 0 0 16px var(--tech-glow); }
.page-desc { color: var(--tech-text-dim); margin: 0 0 18px; }
.summary { display: flex; gap: 26px; flex-wrap: wrap; margin-bottom: 18px; }
.summary span { color: var(--tech-text-dim); font-size: 14px; }
.summary b { color: #eaf6ff; }
.grid { display: grid; grid-template-columns: 1.6fr 1fr; gap: 18px; }
.graph-tip { color: var(--tech-text-dim); font-size: 12px; margin: -4px 0 8px; }
.cyan { color: var(--tech-cyan); }
.mono { font-family: 'Consolas', monospace; }
.kw { margin-bottom: 12px; color: var(--tech-text-dim); font-size: 13px; }
.kwtag { margin: 0 6px 6px 0; }
.capecs { display: flex; flex-direction: column; gap: 10px; max-height: 420px; overflow: auto; }
.cap { border: 1px solid var(--tech-border); border-radius: 8px; padding: 10px 12px; }
.cap-h { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.cap-h b { color: #eaf6ff; }
.cap-row { display: flex; font-size: 12px; padding: 1px 0; }
.cap-row label { width: 84px; color: var(--tech-text-dim); flex-shrink: 0; }
.cap-row span { color: #cfe6ff; word-break: break-all; }
.legend { margin-top: 18px; color: var(--tech-text-dim); font-size: 13px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.legend .dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-left: 10px; }
.dot.threat { background: #ff5c7a; }
.dot.stage { background: #ffb547; }
.dot.capec { background: #00e5ff; }
.dot.tactic { background: #7c8cff; }
.dot.technique { background: #5ad19a; }
.hint { margin-left: 14px; }
</style>
