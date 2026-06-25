<script setup lang="ts">
// 通用图谱渲染（ECharts graph）：传 nodes/edges + 命中高亮集，按节点类型上色。
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { GraphChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { GraphNode, GraphEdge } from '../../api/client'

echarts.use([GraphChart, TooltipComponent, LegendComponent, TitleComponent, CanvasRenderer])

const props = defineProps<{
  nodes: GraphNode[]
  edges: GraphEdge[]
  highlight?: string[] // 命中并需要高亮的节点 id
  height?: string
}>()

const el = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

const TYPE_COLOR: Record<string, string> = {
  threat: '#ff5c7a',
  stage: '#ffb547',
  capec: '#00e5ff',
  tactic: '#7c8cff',
  technique: '#5ad19a',
}
const TYPE_NAME: Record<string, string> = {
  threat: '威胁', stage: '阶段', capec: 'CAPEC', tactic: 'Tactic', technique: 'Technique',
}

function render() {
  if (!chart) return
  const hl = new Set(props.highlight ?? [])
  const categories = Object.keys(TYPE_COLOR).map((k) => ({ name: TYPE_NAME[k], itemStyle: { color: TYPE_COLOR[k] } }))
  const catIndex: Record<string, number> = {}
  Object.keys(TYPE_COLOR).forEach((k, i) => (catIndex[k] = i))

  const nodes = props.nodes.map((n) => {
    const hit = hl.has(n.id)
    return {
      id: n.id,
      name: n.label,
      category: catIndex[n.type] ?? 0,
      symbolSize: n.type === 'threat' ? 56 : n.type === 'stage' ? 42 : hit ? 40 : 32,
      itemStyle: hit ? { borderColor: '#fff', borderWidth: 2, shadowBlur: 18, shadowColor: TYPE_COLOR[n.type] } : {},
      label: { show: true },
      _raw: n,
    }
  })
  const links = props.edges.map((e) => ({
    source: e.source,
    target: e.target,
    label: { show: !!e.label, formatter: e.label ?? '' },
    lineStyle: { color: 'rgba(120,180,255,0.45)', curveness: 0.12 },
  }))

  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      formatter: (p: any) => {
        if (p.dataType === 'edge') return p.data.label?.formatter ?? ''
        const r = p.data._raw as GraphNode
        const extra: string[] = []
        if (r.severity) extra.push(`severity: ${r.severity}`)
        if (r.matched_keywords?.length) extra.push(`命中: ${r.matched_keywords.join(', ')}`)
        if (r.source) extra.push(`source: ${r.source}`)
        return `<b>${r.label}</b><br/>类型: ${TYPE_NAME[r.type]}${extra.length ? '<br/>' + extra.join('<br/>') : ''}`
      },
    },
    legend: [{ data: categories.map((c) => c.name), textStyle: { color: '#7d94b8' }, top: 6 }],
    series: [
      {
        type: 'graph',
        layout: 'force',
        roam: true,
        draggable: true,
        categories,
        force: { repulsion: 280, edgeLength: [60, 140], gravity: 0.08 },
        label: { color: '#dff1ff', fontSize: 11, position: 'right' },
        edgeSymbol: ['none', 'arrow'],
        edgeSymbolSize: 7,
        emphasis: { focus: 'adjacency' },
        data: nodes,
        links,
      },
    ],
  })
  chart.resize()
}

function init() {
  if (el.value) {
    chart = echarts.init(el.value)
    chart.on('click', (params: any) => {
      if (params.dataType !== 'node') return
      chart?.dispatchAction({ type: 'downplay', seriesIndex: 0 })
      chart?.dispatchAction({ type: 'highlight', seriesIndex: 0, dataIndex: params.dataIndex })
      chart?.dispatchAction({ type: 'showTip', seriesIndex: 0, dataIndex: params.dataIndex })
    })
    chart.getZr().on('click', (event) => {
      if (event.target) return
      chart?.dispatchAction({ type: 'downplay', seriesIndex: 0 })
      chart?.dispatchAction({ type: 'hideTip' })
    })
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
watch(() => [props.nodes, props.edges, props.highlight], render, { deep: true })
</script>

<template>
  <div ref="el" :style="{ width: '100%', height: props.height ?? '420px' }" />
</template>
