<script setup lang="ts">
// 模态流量分布：把各结果文件的 modality_dist（后端按全量行聚合）汇总，
// 环形饼图展示每个模态的流量数量与占比，配色复用全站模态色板。
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { PieChart } from 'echarts/charts'
import { TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { DetectionFileStat } from '../api/client'
import { modLabel } from '../utils/detect'

echarts.use([PieChart, TooltipComponent, CanvasRenderer])

const props = defineProps<{
  files: DetectionFileStat[]
  height?: string
}>()

// 模态 -> 主题色（与 theme.css 的 .mod-* 一致）
const MOD_COLOR: Record<string, string> = {
  ipv4: '#2ad1ff', ipv6: '#b79cff', mpls: '#ffc05c', geo: '#36e3a3', scion: '#ff79b0',
}
function modColor(m: string): string {
  const k = (m || '').toLowerCase()
  for (const key in MOD_COLOR) if (k.includes(key)) return MOD_COLOR[key]
  return '#7d94b8'
}

// 汇总各文件的模态分布
const rows = computed(() => {
  const m = new Map<string, { total: number; correct: number }>()
  for (const f of props.files) {
    for (const d of f.modality_dist ?? []) {
      const cur = m.get(d.modality) ?? { total: 0, correct: 0 }
      cur.total += d.total
      cur.correct += d.correct
      m.set(d.modality, cur)
    }
  }
  return [...m.entries()]
    .map(([modality, v]) => ({ modality, ...v, color: modColor(modality) }))
    .sort((a, b) => b.total - a.total)
})
const grandTotal = computed(() => rows.value.reduce((s, r) => s + r.total, 0))
const hasData = computed(() => rows.value.length > 0)
function pct(n: number): string {
  return grandTotal.value ? ((n / grandTotal.value) * 100).toFixed(1) : '0.0'
}

const el = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

function render() {
  if (!chart || !hasData.value) return
  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      formatter: (p: any) => {
        const acc = p.value ? ((p.data.correct / p.value) * 100).toFixed(1) : '0.0'
        return `${p.marker}${p.name}<br/>数量: <b>${p.value.toLocaleString()}</b>（${p.percent}%）<br/>准确率: <b>${acc}%</b>`
      },
    },
    series: [
      {
        type: 'pie',
        radius: ['58%', '82%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: { borderColor: '#0a1428', borderWidth: 2 },
        label: { show: false },
        emphasis: { scale: true, scaleSize: 6, itemStyle: { shadowBlur: 16, shadowColor: 'rgba(0,229,255,.35)' } },
        data: rows.value.map((r) => ({
          name: modLabel(r.modality), value: r.total, correct: r.correct,
          itemStyle: { color: r.color },
        })),
      },
    ],
  })
  chart.resize()
}

function init() {
  if (el.value) {
    chart = echarts.init(el.value)
    render()
  }
}
const onResize = () => chart?.resize()

onMounted(() => {
  init()
  window.addEventListener('resize', onResize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  chart?.dispose()
})
watch(() => props.files, render, { deep: true })
</script>

<template>
  <div class="pie-card">
    <div class="pc-head">
      <span class="pc-bar" />
      <div class="pc-title">模态流量分布</div>
      <div class="pc-sub">各模态承载流量的数量与占比</div>
    </div>

    <div v-if="hasData" class="pc-body">
      <div class="pc-chart" :style="{ height: props.height ?? '240px' }">
        <div ref="el" class="pc-canvas" />
        <div class="pc-center">
          <div class="pc-total">{{ grandTotal.toLocaleString() }}</div>
          <div class="pc-total-cap">流量样本</div>
        </div>
      </div>

      <ul class="pc-legend">
        <li v-for="r in rows" :key="r.modality">
          <span class="lg-dot" :style="{ background: r.color }" />
          <span class="lg-name">{{ modLabel(r.modality) }}</span>
          <span class="lg-count">{{ r.total.toLocaleString() }}</span>
          <span class="lg-pct">{{ pct(r.total) }}%</span>
          <span class="lg-bar"><i :style="{ width: pct(r.total) + '%', background: r.color }" /></span>
        </li>
      </ul>
    </div>
    <div v-else class="pc-empty">暂无模态数据。</div>
  </div>
</template>

<style scoped>
.pie-card {
  background: linear-gradient(180deg, rgba(14, 28, 54, 0.5), rgba(8, 16, 32, 0.5));
  border: 1px solid var(--tech-border); border-radius: 14px; padding: 16px 18px;
}
.pc-head { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; flex-wrap: wrap; }
.pc-bar {
  width: 10px; height: 16px; border-radius: 2px;
  background: linear-gradient(180deg, var(--tech-cyan), #1f6fff); box-shadow: 0 0 10px rgba(0, 229, 255, .5);
}
.pc-title { font-size: 15px; font-weight: 600; color: #e9f4ff; }
.pc-sub { color: var(--tech-text-dim); font-size: 12px; }

.pc-body { display: flex; align-items: center; gap: 26px; }
.pc-chart { position: relative; width: 240px; flex: none; }
.pc-canvas { width: 100%; height: 100%; }
.pc-center {
  position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center; pointer-events: none;
}
.pc-total { font-size: 26px; font-weight: 700; color: #eaf6ff; font-family: 'JetBrains Mono', monospace; text-shadow: 0 0 16px var(--tech-glow); }
.pc-total-cap { font-size: 11px; color: var(--tech-text-dim); letter-spacing: 2px; margin-top: 2px; }

.pc-legend { flex: 1; min-width: 0; list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 11px; }
.pc-legend li {
  display: grid;
  grid-template-columns: 12px 1fr auto auto;
  grid-template-areas: 'dot name count pct' 'bar bar bar bar';
  align-items: center; column-gap: 10px; row-gap: 6px;
}
.lg-dot { grid-area: dot; width: 10px; height: 10px; border-radius: 3px; box-shadow: 0 0 8px currentColor; }
.lg-name { grid-area: name; color: #cfe3fb; font-size: 13px; font-weight: 600; }
.lg-count { grid-area: count; color: #9fc4ec; font-family: 'JetBrains Mono', monospace; font-size: 13px; }
.lg-pct { grid-area: pct; color: var(--tech-cyan); font-family: 'JetBrains Mono', monospace; font-size: 13px; min-width: 50px; text-align: right; }
.lg-bar { grid-area: bar; height: 4px; border-radius: 2px; background: rgba(125, 148, 184, .18); overflow: hidden; }
.lg-bar i { display: block; height: 100%; border-radius: 2px; }

.pc-empty { color: var(--tech-text-dim); font-size: 13px; padding: 24px 0; text-align: center; }

@media (max-width: 760px) {
  .pc-body { flex-direction: column; align-items: stretch; }
  .pc-chart { width: 100%; }
}
</style>
