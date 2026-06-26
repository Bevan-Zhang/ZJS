<script setup lang="ts">
// 检测结果统计图：把各结果文件的逐样本按「真实攻击类型」聚合，
// 堆叠出每类的命中/误判条形，给检测页一个全局可视化概览。
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { DetectionFileStat } from '../api/client'

echarts.use([BarChart, TooltipComponent, LegendComponent, GridComponent, CanvasRenderer])

const props = defineProps<{
  files: DetectionFileStat[]
  height?: string
}>()

const HIT = '#00e5ff'
const MISS = '#ff5c7a'
const TYPE_CAP = 12 // 类型过多时只展示样本量最大的前 N 类，避免拥挤

// 聚合：真实攻击类型 -> { correct, wrong }（取后端按全量行算好的 type_dist，避免只看截断样本失真）
const byType = computed(() => {
  const m = new Map<string, { correct: number; wrong: number }>()
  for (const f of props.files) {
    for (const t of f.type_dist ?? []) {
      const cur = m.get(t.type) ?? { correct: 0, wrong: 0 }
      cur.correct += t.correct
      cur.wrong += t.wrong
      m.set(t.type, cur)
    }
  }
  return [...m.entries()]
    .map(([type, v]) => ({ type, ...v, total: v.correct + v.wrong }))
    .sort((a, b) => b.total - a.total)
    .slice(0, TYPE_CAP)
})

const hasData = computed(() => byType.value.length > 0)

const el = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

function render() {
  if (!chart || !hasData.value) return
  const rows = byType.value
  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (ps: any[]) => {
        const name = ps[0]?.axisValue ?? ''
        const total = ps.reduce((s, p) => s + (p.value || 0), 0)
        const acc = total ? ((ps.find((p) => p.seriesName === '命中')?.value ?? 0) / total * 100).toFixed(1) : '0.0'
        const lines = ps.map((p) => `${p.marker}${p.seriesName}: <b>${p.value}</b>`).join('<br/>')
        return `<b>${name}</b><br/>${lines}<br/>准确率: <b>${acc}%</b>`
      },
    },
    legend: { data: ['命中', '误判'], textStyle: { color: '#7d94b8' }, top: 4 },
    grid: { left: 10, right: 16, top: 38, bottom: 8, containLabel: true },
    xAxis: {
      type: 'category',
      data: rows.map((r) => r.type),
      axisLabel: { color: '#9db4d6', interval: 0, rotate: rows.length > 6 ? 28 : 0, fontSize: 11 },
      axisLine: { lineStyle: { color: 'rgba(125,148,184,.35)' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#7d94b8' },
      splitLine: { lineStyle: { color: 'rgba(125,148,184,.12)' } },
    },
    series: [
      {
        name: '命中', type: 'bar', stack: 'cnt', barMaxWidth: 38,
        itemStyle: { color: HIT },
        data: rows.map((r) => r.correct),
      },
      {
        name: '误判', type: 'bar', stack: 'cnt', barMaxWidth: 38,
        itemStyle: { color: MISS },
        data: rows.map((r) => r.wrong),
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
  <div class="stats-card">
    <div class="sc-head">
      <span class="sc-bar" />
      <div class="sc-title">攻击类型检出分布</div>
      <div class="sc-sub">按真实攻击类型对全量样本聚合，堆叠展示命中 / 误判</div>
    </div>
    <div v-if="hasData" ref="el" :style="{ width: '100%', height: props.height ?? '300px' }" />
    <div v-else class="sc-empty">暂无样本数据，先点「查看结果」拉取检测结果。</div>
  </div>
</template>

<style scoped>
.stats-card {
  background: linear-gradient(180deg, rgba(14, 28, 54, 0.5), rgba(8, 16, 32, 0.5));
  border: 1px solid var(--tech-border); border-radius: 14px; padding: 16px 18px;
}
.sc-head { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; flex-wrap: wrap; }
.sc-bar {
  width: 10px; height: 16px; border-radius: 2px;
  background: linear-gradient(180deg, var(--tech-cyan), #1f6fff); box-shadow: 0 0 10px rgba(0, 229, 255, .5);
}
.sc-title { font-size: 15px; font-weight: 600; color: #e9f4ff; }
.sc-sub { color: var(--tech-text-dim); font-size: 12px; }
.sc-empty { color: var(--tech-text-dim); font-size: 13px; padding: 24px 0; text-align: center; }
</style>
