<script setup lang="ts">
import { computed } from 'vue'
import type { NodeInfo } from '../api/client'

// 受管节点的在线状态由父组件传入；其余节点为静态拓扑展示
const props = defineProps<{ nodes: NodeInfo[]; probing?: boolean }>()
const emit = defineEmits<{ (e: 'probe'): void }>()

type TopoType = 'hub' | 'managed' | 'static'
interface TopoNode {
  id: string
  label: string
  x: number
  y: number
  type: TopoType
  backendId?: string
}

// 布局参照真实拓扑图：controller 居上为枢纽，中间排为受管网元，下方为其余网元
const NODES: TopoNode[] = [
  { id: 'fangyu', label: '防御系统', x: 470, y: 70, type: 'static' },
  { id: 'controller', label: 'controller', x: 660, y: 120, type: 'hub' },
  { id: 'host1', label: 'host1', x: 70, y: 305, type: 'managed', backendId: 'host1' },
  { id: 'wy1', label: '多模态网元1', x: 300, y: 295, type: 'managed', backendId: 'netunit1' },
  { id: 'wy3', label: '多模态网元3', x: 540, y: 285, type: 'managed', backendId: 'netunit3' },
  { id: 'wy4', label: '多模态网元4', x: 770, y: 285, type: 'managed', backendId: 'netunit4' },
  { id: 'wy7', label: '多模态网元7', x: 1000, y: 285, type: 'managed', backendId: 'netunit7' },
  { id: 'server1', label: 'server1', x: 1250, y: 305, type: 'managed', backendId: 'server1' },
  { id: 'wy2', label: '多模态网元2', x: 300, y: 475, type: 'static' },
  { id: 'wy5', label: '多模态网元5', x: 540, y: 475, type: 'static' },
  { id: 'wy6', label: '多模态网元6', x: 770, y: 475, type: 'static' },
  { id: 'wy8', label: '多模态网元8', x: 1000, y: 475, type: 'static' },
  { id: 'wy9', label: '多模态网元9', x: 660, y: 635, type: 'static' },
  { id: 'server2', label: 'server2', x: 1250, y: 635, type: 'static' },
]

const EDGES: [string, string][] = [
  ['controller', 'fangyu'],
  ['controller', 'host1'], ['controller', 'wy1'], ['controller', 'wy3'],
  ['controller', 'wy4'], ['controller', 'wy7'], ['controller', 'server1'],
  ['controller', 'wy2'], ['controller', 'wy5'], ['controller', 'wy6'],
  ['controller', 'wy8'], ['controller', 'wy9'],
  ['host1', 'wy1'],
  ['wy1', 'wy3'], ['wy3', 'wy4'],   // 中间排相邻网元互联
  ['wy1', 'wy2'], ['wy1', 'wy5'],
  ['wy3', 'wy2'], ['wy3', 'wy5'], ['wy3', 'wy6'],
  ['wy4', 'wy5'], ['wy4', 'wy6'], ['wy4', 'wy7'],
  ['wy7', 'wy8'], ['wy7', 'server1'],
  ['server1', 'wy8'], ['server1', 'wy4'],
  ['wy2', 'wy5'], ['wy5', 'wy9'], ['wy6', 'wy9'], ['wy6', 'wy8'],
  ['wy9', 'server2'], ['wy8', 'server2'],
]

const byId = Object.fromEntries(NODES.map((n) => [n.id, n]))

// backendId -> online
const onlineMap = computed(() => {
  const m: Record<string, boolean | undefined> = {}
  for (const n of props.nodes) m[n.id] = n.online
  return m
})

function statusClass(n: TopoNode): string {
  if (n.type === 'hub') return 'hub'
  if (n.type === 'static') return 'static'
  const online = n.backendId ? onlineMap.value[n.backendId] : undefined
  if (online === undefined) return 'unknown'
  return online ? 'online' : 'offline'
}

function statusText(n: TopoNode): string {
  if (n.type === 'hub' || n.type === 'static') return '运行中'
  const online = n.backendId ? onlineMap.value[n.backendId] : undefined
  if (online === undefined) return '未探测'
  return online ? '在线' : '离线'
}

function edgeActive(a: string, b: string): boolean {
  if (a === 'controller' || b === 'controller') return true
  const na = byId[a]
  const nb = byId[b]
  const on = (n: TopoNode) => n.type === 'managed' && n.backendId && onlineMap.value[n.backendId]
  return Boolean(on(na) || on(nb))
}

const radius = (t: TopoType) => (t === 'hub' ? 30 : 22)
</script>

<template>
  <div class="tech-panel">
    <div class="topo-head">
      <div class="tech-h" style="margin: 0">网络拓扑</div>
      <el-button size="small" :loading="probing" @click="emit('probe')">探测全部</el-button>
    </div>

    <svg viewBox="0 0 1320 710" class="topo" preserveAspectRatio="xMidYMid meet">
      <defs>
        <filter id="glow" x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="4" result="b" />
          <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
        <radialGradient id="hubFill" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="#0ff" stop-opacity="0.55" />
          <stop offset="100%" stop-color="#0a3a55" stop-opacity="0.25" />
        </radialGradient>
        <radialGradient id="nodeFill" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="#13325c" stop-opacity="0.9" />
          <stop offset="100%" stop-color="#0a1530" stop-opacity="0.9" />
        </radialGradient>
      </defs>

      <!-- 连线 -->
      <g>
        <template v-for="([a, b], i) in EDGES" :key="i">
          <line
            :x1="byId[a].x" :y1="byId[a].y" :x2="byId[b].x" :y2="byId[b].y"
            :class="['edge', { active: edgeActive(a, b) }]"
          />
          <line
            v-if="edgeActive(a, b)"
            :x1="byId[a].x" :y1="byId[a].y" :x2="byId[b].x" :y2="byId[b].y"
            class="edge-flow"
          />
        </template>
      </g>

      <!-- 节点 -->
      <g v-for="n in NODES" :key="n.id">
        <circle
          :cx="n.x" :cy="n.y" :r="radius(n.type) + 6"
          :class="['ring', statusClass(n)]"
        />
        <circle
          :cx="n.x" :cy="n.y" :r="radius(n.type)"
          :class="['node', statusClass(n)]"
          :fill="n.type === 'hub' ? 'url(#hubFill)' : 'url(#nodeFill)'"
          filter="url(#glow)"
        />
        <!-- 设备小标识 -->
        <rect :x="n.x - 9" :y="n.y - 6" width="18" height="12" rx="2" class="dev" />
        <text :x="n.x" :y="n.y + radius(n.type) + 20" class="label">{{ n.label }}</text>
        <text :x="n.x" :y="n.y + radius(n.type) + 36" :class="['status', statusClass(n)]">
          ({{ statusText(n) }})
        </text>
      </g>
    </svg>
  </div>
</template>

<style scoped>
.topo-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.topo { width: 100%; height: auto; display: block; }

/* 连线 */
.edge { stroke: rgba(90, 120, 170, 0.28); stroke-width: 1.4; }
.edge.active { stroke: rgba(0, 229, 255, 0.45); stroke-width: 1.8; }
.edge-flow {
  stroke: #00e5ff;
  stroke-width: 2;
  stroke-dasharray: 6 16;
  filter: drop-shadow(0 0 4px #00e5ff);
  animation: flow 1.2s linear infinite;
}
@keyframes flow { to { stroke-dashoffset: -22; } }

/* 节点外环 */
.ring { fill: none; stroke-width: 1.5; opacity: 0.7; }
.ring.hub { stroke: #00e5ff; animation: ringPulse 2s ease-in-out infinite; }
.ring.online { stroke: #00e5ff; animation: ringPulse 2.4s ease-in-out infinite; }
.ring.offline { stroke: #f56c6c; }
.ring.unknown { stroke: #6b86b0; }
.ring.static { stroke: #3fa7ff; opacity: 0.45; }
@keyframes ringPulse { 0%,100% { transform: scale(1); opacity: 0.7; } 50% { transform: scale(1.12); opacity: 0.2; } }
.ring { transform-box: fill-box; transform-origin: center; }

/* 节点主体 */
.node { stroke-width: 2.5; }
.node.hub { stroke: #00e5ff; }
.node.online { stroke: #00e5ff; }
.node.offline { stroke: #f56c6c; }
.node.unknown { stroke: #6b86b0; }
.node.static { stroke: #3fa7ff; }

.dev { fill: rgba(255, 255, 255, 0.85); }

.label { fill: #cfe6ff; font-size: 14px; text-anchor: middle; font-weight: 500; }
.status { font-size: 12px; text-anchor: middle; }
.status.hub, .status.online { fill: #4be3ff; }
.status.offline { fill: #f78989; }
.status.unknown { fill: #8aa1c4; }
.status.static { fill: #6fae6f; }
</style>
