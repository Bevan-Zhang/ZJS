<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import type { NodeInfo } from '../api/client'

const props = withDefaults(
  defineProps<{
    nodes: NodeInfo[]
    probing?: boolean
    toggle?: boolean // 是否显示 2D/3D 切换（模块页固定 2D 时传 false）
    detection?: 'on' | 'off' // 传入则显示「模型检测已开启/已关闭」徽标（用字符串避免 boolean 被强制为 false）
    mode?: 'overview' | 'detection' // detection：隐藏能力浮标，s1 头上放 流量监听/流量检测 两图标
    linkFlow?: boolean // detection：host1-s1 链路数据流动动效（发送中）
    listenOn?: boolean // detection：流量监听图标变蓝
    detectOn?: boolean // detection：流量检测图标变绿
  }>(),
  { toggle: true, mode: 'overview' },
)
const emit = defineEmits<{ (e: 'probe'): void }>()

const view = ref<'2d' | '3d'>('2d')
const showToggle = computed(() => props.toggle !== false)

// 坐标系：1120 x 600
const W = 1120
const H = 600

type NType = 'switch' | 'host' | 'server' | 'cloud' | 'attack'
interface TNode {
  id: string; label: string; sub?: string; x: number; y: number; type: NType; backendId?: string
}
const NODES: TNode[] = [
  { id: 'host1', label: 'host1', sub: 'host', x: 70, y: 300, type: 'host', backendId: 'host1' },
  { id: 's1', label: 's1', sub: 'switch', x: 235, y: 300, type: 'switch', backendId: 'netunit1' },
  { id: 's3', label: 's3', sub: 'switch', x: 410, y: 300, type: 'switch', backendId: 'netunit3' },
  { id: 's4', label: 's4', sub: 'switch', x: 585, y: 300, type: 'switch', backendId: 'netunit4' },
  { id: 's7', label: 's7', sub: 'switch', x: 760, y: 300, type: 'switch', backendId: 'netunit7' },
  { id: 'server1', label: 'server1', sub: 'server', x: 920, y: 300, type: 'server', backendId: 'server1' },
  { id: 'internet', label: 'Internet', x: 1055, y: 300, type: 'cloud' },
  { id: 's2', label: 's2', sub: 'switch', x: 235, y: 440, type: 'switch' },
  { id: 's5', label: 's5', sub: 'switch', x: 410, y: 440, type: 'switch' },
  { id: 's6', label: 's6', sub: 'switch', x: 585, y: 440, type: 'switch' },
  { id: 's8', label: 's8', sub: 'switch', x: 760, y: 440, type: 'switch' },
  { id: 's9', label: 's9', sub: 'switch', x: 497, y: 555, type: 'switch' },
  { id: 'attack', label: '攻击源', x: 1000, y: 480, type: 'attack' },
]
const byId = Object.fromEntries(NODES.map((n) => [n.id, n]))

const TRUNK = ['host1', 's1', 's3', 's4', 's7', 'server1', 'internet']
const trunkSegs = TRUNK.slice(0, -1).map((a, i) => [a, TRUNK[i + 1]] as [string, string])
const MESH: [string, string][] = [
  ['s1', 's2'], ['s3', 's2'], ['s3', 's5'], ['s4', 's5'],
  ['s4', 's6'], ['s7', 's6'], ['s7', 's8'], ['s4', 's8'],
  ['s5', 's9'], ['s6', 's9'],
]
const ATTACK: [string, string][] = [['attack', 's1'], ['attack', 's3'], ['attack', 's4'], ['attack', 's7']]
const swPorts = [9, 17, 25, 33, 41, 49, 57]

interface Pin { id: string; label: string; en: string; icon: string; x: number; y: number; targets: string[]; cls: string }
const PINS: Pin[] = [
  { id: 'flow', label: '流量检测', en: 'TRAFFIC', icon: 'DataLine', x: 235, y: 140, targets: ['s1'], cls: 'p-green' },
  { id: 'trace', label: '溯源感知', en: 'TRACE', icon: 'Aim', x: 410, y: 140, targets: ['s3'], cls: 'p-gold' },
  { id: 'active', label: '主动防御', en: 'DEFENSE', icon: 'Lock', x: 672, y: 135, targets: ['s4', 's7'], cls: 'p-cyan' },
]

// detection 模式：s1 头上的两个图标
interface DetIcon { id: string; label: string; en: string; icon: string; x: number; y: number }
const DETECT_ICONS: DetIcon[] = [
  { id: 'listen', label: '流量监听', en: 'LISTEN', icon: 'View', x: 175, y: 145 },
  { id: 'detect', label: '流量检测', en: 'DETECT', icon: 'DataLine', x: 295, y: 145 },
]
const isDetection = computed(() => props.mode === 'detection')
function detCls(id: string): string {
  if (id === 'listen') return props.listenOn ? 'di-blue' : 'di-off'
  return props.detectOn ? 'di-green' : 'di-off'
}

const onlineMap = computed(() => {
  const m: Record<string, boolean | undefined> = {}
  for (const n of props.nodes) m[n.id] = n.online
  return m
})
function statusCls(n: TNode): string {
  if (n.type === 'cloud') return 'st-cloud'
  if (n.type === 'attack') return 'st-attack'
  if (!n.backendId) return 'st-static'
  const on = onlineMap.value[n.backendId]
  if (on === undefined) return 'st-unknown'
  return on ? 'st-on' : 'st-off'
}
const posStyle = (n: { x: number; y: number }) => ({ left: `${(n.x / W) * 100}%`, top: `${(n.y / H) * 100}%` })

/* ===== 3D 交互：拖动旋转 / 滚轮缩放 / Shift 平移 / 复位 ===== */
const rotX = ref(56)
const rotZ = ref(0)
const scale = ref(0.82)
const panX = ref(0)
const panY = ref(0)
const dragging = ref(false)
let sx = 0
let sy = 0

const trans = computed(() => (dragging.value ? 'none' : 'transform .5s ease'))
const stageStyle = computed(() => {
  if (view.value !== '3d') return { transition: trans.value }
  return {
    transform: `translate(${panX.value}px, ${panY.value}px) rotateX(${rotX.value}deg) rotateZ(${rotZ.value}deg) scale(${scale.value})`,
    transition: trans.value,
  }
})
function billboard(lift: number) {
  if (view.value !== '3d') return 'translate(-50%, -50%)'
  return `translate(-50%, -50%) rotateZ(${-rotZ.value}deg) rotateX(${-rotX.value}deg) translateZ(${lift}px)`
}
const nodeStyle = (n: TNode) => ({ ...posStyle(n), transform: billboard(16), transition: trans.value })
const pinStyle = (p: { x: number; y: number }) => ({ ...posStyle(p), transform: billboard(70), transition: trans.value })

function onDown(e: MouseEvent) {
  if (view.value !== '3d') return
  dragging.value = true; sx = e.clientX; sy = e.clientY; e.preventDefault()
}
function onMove(e: MouseEvent) {
  if (!dragging.value) return
  const dx = e.clientX - sx; const dy = e.clientY - sy; sx = e.clientX; sy = e.clientY
  if (e.shiftKey) { panX.value += dx; panY.value += dy }
  else { rotZ.value += dx * 0.3; rotX.value = Math.min(85, Math.max(8, rotX.value - dy * 0.3)) }
}
function onUp() { dragging.value = false }
function onWheel(e: WheelEvent) {
  if (view.value !== '3d') return
  e.preventDefault()
  scale.value = Math.min(2, Math.max(0.4, scale.value * (1 - e.deltaY * 0.001)))
}
function resetView() { rotX.value = 56; rotZ.value = 0; scale.value = 0.82; panX.value = 0; panY.value = 0 }

onMounted(() => { window.addEventListener('mousemove', onMove); window.addEventListener('mouseup', onUp) })
onBeforeUnmount(() => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp) })
</script>

<template>
  <div class="tech-panel topo-panel">
    <div class="topo-head">
      <div class="tech-h" style="margin: 0">网络拓扑</div>
      <div class="head-right">
        <span v-if="detection" class="det-chip" :class="detection === 'on' ? 'on' : 'off'">
          <i class="d-dot" />{{ detection === 'on' ? '模型检测已开启' : '模型检测已关闭' }}
        </span>
        <el-button v-if="view === '3d' && showToggle" size="small" @click="resetView">复位</el-button>
        <el-button size="small" :loading="probing" @click="emit('probe')">探测全部</el-button>
        <div v-if="showToggle" class="view-toggle">
          <span :class="{ active: view === '3d' }" @click="view = '3d'">3D</span>
          <span :class="{ active: view === '2d' }" @click="view = '2d'">2D</span>
        </div>
      </div>
    </div>

    <div
      class="scene" :class="[view === '3d' ? 'is-3d' : 'is-2d', { grabbing: dragging }]"
      @mousedown="onDown" @wheel="onWheel"
    >
      <div class="stage" :style="stageStyle">
        <div class="floor" />
        <svg class="links" viewBox="0 0 1120 600" preserveAspectRatio="none">
          <defs>
            <linearGradient id="trunkGrad" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stop-color="#00e5ff" /><stop offset="100%" stop-color="#ffb648" />
            </linearGradient>
          </defs>
          <line v-for="([a, b], i) in MESH" :key="'m' + i" :x1="byId[a].x" :y1="byId[a].y" :x2="byId[b].x" :y2="byId[b].y" class="l-mesh" />
          <template v-for="([a, b], i) in trunkSegs" :key="'t' + i">
            <line :x1="byId[a].x" :y1="byId[a].y" :x2="byId[b].x" :y2="byId[b].y" class="l-trunk" />
            <line :x1="byId[a].x" :y1="byId[a].y" :x2="byId[b].x" :y2="byId[b].y" class="l-flow" />
          </template>
          <line v-for="([a, b], i) in ATTACK" :key="'a' + i" :x1="byId[a].x" :y1="byId[a].y" :x2="byId[b].x" :y2="byId[b].y" class="l-attack" />

          <!-- overview：能力浮标连接线 -->
          <template v-if="!isDetection">
            <template v-for="pin in PINS" :key="'pl' + pin.id">
              <line v-for="t in pin.targets" :key="pin.id + t" :x1="pin.x" :y1="pin.y + 28" :x2="byId[t].x" :y2="byId[t].y - 24" class="l-pin" />
            </template>
          </template>

          <!-- detection：检测图标到 s1 的连接线 + host1->s1 数据流动 -->
          <template v-if="isDetection">
            <line v-for="d in DETECT_ICONS" :key="'dl' + d.id" :x1="d.x" :y1="d.y + 28" :x2="byId['s1'].x" :y2="byId['s1'].y - 24" class="l-pin" />
            <!-- 数据流动效：host1 → s1 → s3 → s4 → s7 → server1 整条路径（均在 y=300 直线上） -->
            <template v-if="linkFlow">
              <line :x1="byId['host1'].x" :y1="byId['host1'].y" :x2="byId['server1'].x" :y2="byId['server1'].y" class="l-data" />
              <circle v-for="i in 7" :key="'pk' + i" r="4.5" :cy="byId['host1'].y" class="pkt">
                <animate attributeName="cx" :from="byId['host1'].x" :to="byId['server1'].x" dur="2.4s" :begin="`${(i - 1) * 0.34}s`" repeatCount="indefinite" />
              </circle>
            </template>
          </template>
        </svg>

        <!-- overview：三个能力浮标 -->
        <div v-for="pin in PINS" v-show="!isDetection" :key="pin.id" class="pin" :class="pin.cls" :style="pinStyle(pin)">
          <div class="pin-marker">
            <span class="pin-ring" />
            <svg viewBox="0 0 48 58" class="pin-shape">
              <path d="M24 3 C12 3 3 12 3 23 C3 35 24 55 24 55 C24 55 45 35 45 23 C45 12 36 3 24 3 Z" />
            </svg>
            <el-icon class="pin-icon"><component :is="pin.icon" /></el-icon>
          </div>
          <div class="pin-label">{{ pin.label }}<span class="pin-en">{{ pin.en }}</span></div>
        </div>

        <!-- detection：s1 头上 流量监听 / 流量检测 两图标 -->
        <div v-for="d in DETECT_ICONS" v-show="isDetection" :key="d.id" class="pin" :class="detCls(d.id)" :style="pinStyle(d)">
          <div class="pin-marker">
            <span class="pin-ring" />
            <svg viewBox="0 0 48 58" class="pin-shape">
              <path d="M24 3 C12 3 3 12 3 23 C3 35 24 55 24 55 C24 55 45 35 45 23 C45 12 36 3 24 3 Z" />
            </svg>
            <el-icon class="pin-icon"><component :is="d.icon" /></el-icon>
          </div>
          <div class="pin-label">{{ d.label }}<span class="pin-en">{{ d.en }}</span></div>
        </div>

        <div v-for="n in NODES" :key="n.id" class="node" :class="[statusCls(n), 'ty-' + n.type]" :style="nodeStyle(n)">
          <div class="node-body">
            <svg v-if="n.type === 'switch'" viewBox="0 0 76 40" class="sw">
              <rect x="3" y="6" width="70" height="28" rx="4" class="sw-body" />
              <rect v-for="px in swPorts" :key="px" :x="px" y="23" width="6" height="7" rx="1" class="sw-port" />
              <circle cx="65" cy="12" r="2.2" class="sw-led" />
            </svg>
            <div v-else-if="n.type === 'host' || n.type === 'server'" class="box">
              <span class="box-led" /><span class="box-led" /><span class="box-led" />
            </div>
            <svg v-else-if="n.type === 'cloud'" viewBox="0 0 64 40" class="cloud">
              <path d="M20 34 a11 11 0 0 1 1 -21 a15 15 0 0 1 28 3 a9 9 0 0 1 -1 18 z" />
            </svg>
            <svg v-else viewBox="0 0 48 48" class="atk">
              <polygon points="24,6 42,40 6,40" /><text x="24" y="36" text-anchor="middle">!</text>
            </svg>
            <span class="dot" />
          </div>
          <div class="node-label">{{ n.label }}<span v-if="n.sub" class="node-sub">{{ n.sub }}</span></div>
        </div>
      </div>
    </div>

    <div v-if="view === '3d' && showToggle" class="hint">拖动旋转 · 滚轮缩放 · Shift+拖动平移</div>
  </div>
</template>

<style scoped>
.topo-panel { padding-bottom: 8px; }
.topo-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.head-right { display: flex; gap: 12px; align-items: center; }
.view-toggle { display: flex; border: 1px solid var(--tech-border); border-radius: 6px; overflow: hidden; }
.view-toggle span { padding: 4px 14px; font-size: 13px; cursor: pointer; color: var(--tech-text-dim); background: rgba(255, 255, 255, 0.03); }
.view-toggle span.active { background: var(--tech-cyan); color: #022; font-weight: 600; }

.det-chip {
  display: inline-flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 600;
  padding: 3px 12px; border-radius: 14px; border: 1px solid;
}
.det-chip .d-dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; box-shadow: 0 0 6px currentColor; }
.det-chip.on { color: #2ee6a0; background: rgba(46, 230, 160, 0.10); border-color: rgba(46, 230, 160, 0.5); }
.det-chip.off { color: #8aa1c4; background: rgba(138, 161, 196, 0.08); border-color: rgba(138, 161, 196, 0.35); }

.scene { perspective: 1300px; }
.scene.is-3d { cursor: grab; }
.scene.is-3d.grabbing { cursor: grabbing; }
.stage { position: relative; width: 100%; aspect-ratio: 1120 / 600; transform-style: preserve-3d; }

.floor {
  position: absolute; inset: 0;
  background-image:
    linear-gradient(rgba(64, 158, 255, 0.10) 1px, transparent 1px),
    linear-gradient(90deg, rgba(64, 158, 255, 0.10) 1px, transparent 1px);
  background-size: 46px 46px; opacity: 0; transition: opacity 0.6s ease;
}
.is-3d .floor { opacity: 1; box-shadow: inset 0 0 120px rgba(0, 229, 255, 0.12); }

.links { position: absolute; inset: 0; width: 100%; height: 100%; overflow: visible; }
.l-mesh { stroke: rgba(120, 150, 200, 0.30); stroke-width: 2; }
.l-trunk { stroke: url(#trunkGrad); stroke-width: 3.5; opacity: 0.5; }
.l-flow { stroke: #fff; stroke-width: 2; stroke-dasharray: 5 16; filter: drop-shadow(0 0 4px #00e5ff); animation: flow 1s linear infinite; }
@keyframes flow { to { stroke-dashoffset: -21; } }
.l-attack { stroke: #ff7a3c; stroke-width: 2.2; stroke-dasharray: 7 7; animation: flow 1.4s linear infinite; }
.l-pin { stroke: rgba(0, 229, 255, 0.5); stroke-width: 1.4; stroke-dasharray: 3 5; }

.node, .pin { position: absolute; transform-style: preserve-3d; }
.node-body { position: relative; display: flex; justify-content: center; }
.sw { width: 74px; height: 40px; }
.sw-body { fill: rgba(13, 40, 70, 0.9); stroke-width: 2.4; }
.sw-port { fill: rgba(200, 220, 255, 0.55); }
.sw-led { fill: #28c840; }
.box { width: 60px; height: 42px; border-radius: 6px; border-width: 2.2px; border-style: solid; background: rgba(13, 40, 70, 0.85); display: flex; gap: 4px; align-items: center; justify-content: center; padding-top: 4px; }
.box-led { width: 5px; height: 5px; border-radius: 50%; background: currentColor; opacity: 0.8; }
.cloud { width: 64px; height: 40px; }
.atk { width: 46px; height: 46px; }
.atk text { fill: #fff; font-size: 20px; font-weight: 700; }
.dot { position: absolute; top: -2px; right: 6px; width: 8px; height: 8px; border-radius: 50%; }
.node-label { margin-top: 4px; text-align: center; font-size: 13px; color: #dcebff; font-weight: 600; white-space: nowrap; }
.node-sub { display: block; font-size: 10px; color: var(--tech-text-dim); font-weight: 400; }

/* 状态配色 */
.st-on .sw-body, .st-on .box { stroke: #00e5ff; border-color: #00e5ff; }
.st-on { color: #00e5ff; filter: drop-shadow(0 0 8px rgba(0, 229, 255, 0.5)); }
.st-on .dot { background: #28c840; box-shadow: 0 0 6px #28c840; }
.st-off .sw-body, .st-off .box { stroke: #f56c6c; border-color: #f56c6c; }
.st-off { color: #f56c6c; }
.st-off .dot { background: #f56c6c; box-shadow: 0 0 6px #f56c6c; }
.st-unknown .sw-body, .st-unknown .box { stroke: #6b86b0; border-color: #6b86b0; }
.st-unknown .dot { background: #6b86b0; }
.st-static .sw-body, .st-static .box { stroke: #2fa8e0; border-color: #2fa8e0; }
.st-static { color: #2fa8e0; }
.st-static .dot { background: #28c840; box-shadow: 0 0 6px #28c840; }
.st-cloud .cloud path { fill: rgba(150, 170, 200, 0.5); stroke: #aab8d0; stroke-width: 1.5; }
.st-cloud .dot { display: none; }
.st-attack .atk polygon { fill: rgba(255, 122, 60, 0.85); stroke: #ff7a3c; stroke-width: 2; }
.st-attack .dot { display: none; }
.st-attack .node-label { color: #ff9a5c; }

/* 能力浮标 */
.pin { width: 64px; }
.pin-marker { position: relative; width: 64px; height: 64px; }
.pin-ring { position: absolute; top: 0; left: 8px; width: 48px; height: 48px; border-radius: 50%; border: 2px dashed currentColor; opacity: 0.6; animation: spin 6s linear infinite; }
.pin-shape { position: absolute; top: 1px; left: 8px; width: 48px; height: 58px; filter: drop-shadow(0 0 9px currentColor); }
.pin-shape path { fill: rgba(10, 25, 45, 0.92); stroke: currentColor; stroke-width: 2.5; }
.pin-icon { position: absolute; top: 13px; left: 0; width: 64px; justify-content: center; font-size: 22px; color: currentColor; }
.pin-label { margin-top: 6px; text-align: center; font-size: 14px; font-weight: 600; color: #eaf6ff; white-space: nowrap; }
.pin-en { display: block; font-size: 9px; letter-spacing: 1px; color: currentColor; opacity: 0.8; }
@keyframes spin { to { transform: rotate(360deg); } }
.p-green { color: #2ee6a0; }
.p-gold { color: #ffc24b; }
.p-cyan { color: #38d6ff; }

/* detection 图标三态：无色 / 蓝(监听) / 绿(检测) */
.di-off { color: #6b86b0; }
.di-off .pin-shape { filter: none; }
.di-off .pin-shape path { fill: rgba(20, 30, 50, 0.85); stroke: #6b86b0; }
.di-off .pin-ring { opacity: 0.35; }
.di-blue { color: #29b6ff; }
.di-green { color: #2ee6a0; }

/* host1->s1 数据流动效 */
.l-data {
  stroke: #00e5ff; stroke-width: 3; stroke-dasharray: 10 10;
  filter: drop-shadow(0 0 6px #00e5ff); animation: flow 0.6s linear infinite;
}
.pkt { fill: #aef6ff; filter: drop-shadow(0 0 6px #00e5ff); }

.hint { text-align: center; color: var(--tech-text-dim); font-size: 12px; margin-top: 8px; }
</style>
