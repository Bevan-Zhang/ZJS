<script setup lang="ts">
import { computed } from 'vue'
import type { NodeInfo } from '../api/client'

const props = withDefaults(
  defineProps<{
    nodes: NodeInfo[]
    probing?: boolean
    mode?: 'overview' | 'detection'
    linkFlow?: boolean
    listenOn?: boolean
    detectOn?: boolean
  }>(),
  { mode: 'overview' },
)
const emit = defineEmits<{ (e: 'probe'): void }>()

type FabricNode = {
  id: string
  backendId?: string
  x: number
  y: number
  role: string
  edge?: boolean
}

const fabricNodes: FabricNode[] = [
  { id: 's1', backendId: 'netunit1', x: 454, y: 224, role: '接入边缘', edge: true },
  { id: 's3', backendId: 'netunit3', x: 578, y: 322, role: 'Spine' },
  { id: 's4', backendId: 'netunit4', x: 758, y: 322, role: 'Spine' },
  { id: 's7', backendId: 'netunit7', x: 882, y: 224, role: '服务边缘', edge: true },
  { id: 's2', x: 454, y: 546, role: '接入边缘', edge: true },
  { id: 's5', x: 578, y: 454, role: 'Spine' },
  { id: 's6', x: 758, y: 454, role: 'Spine' },
  { id: 's8', x: 882, y: 546, role: '服务边缘', edge: true },
]

const nodeById = Object.fromEntries(fabricNodes.map((node) => [node.id, node]))
const fabricEdges: [string, string][] = [
  ['s1', 's3'], ['s1', 's5'], ['s2', 's3'], ['s2', 's5'],
  ['s3', 's4'], ['s3', 's5'], ['s4', 's6'], ['s5', 's6'],
  ['s4', 's7'], ['s6', 's7'], ['s4', 's8'], ['s6', 's8'],
]
const backbone: [string, string][] = [['s1', 's3'], ['s3', 's4'], ['s4', 's7']]

const onlineMap = computed(() => {
  const result: Record<string, boolean | undefined> = {}
  for (const node of props.nodes) result[node.id] = node.online
  return result
})

function nodeState(node: FabricNode) {
  if (!node.backendId) return 'static'
  const online = onlineMap.value[node.backendId]
  if (online === undefined) return 'unknown'
  return online ? 'online' : 'offline'
}

function edgePath([from, to]: [string, string]) {
  const a = nodeById[from]
  const b = nodeById[to]
  return `M ${a.x} ${a.y} L ${b.x} ${b.y}`
}

const terminals = [
  { y: 236, type: 'phone', label: '移动终端', target: 's1' },
  { y: 392, type: 'laptop', label: '办公终端', target: 's1' },
  { y: 550, type: 'desktop', label: '工作站', target: 's2' },
]

const overviewCapabilities = [
  { id: 'traffic', x: 430, y: 72, label: '流量检测', en: 'TRAFFIC', color: '#36f29a', target: 's1', active: true },
  { id: 'trace', x: 675, y: 58, label: '溯源感知', en: 'TRACE', color: '#ffbf4d', target: 's3', active: true },
  { id: 'defense', x: 930, y: 72, label: '主动防御', en: 'DEFENSE', color: '#20d8ff', target: 's7', active: true },
]

const capabilities = computed(() => {
  if (props.mode !== 'detection') return overviewCapabilities
  return [
    {
      id: 'listen', x: 408, y: 72, label: '流量监听', en: 'LISTEN',
      color: props.listenOn ? '#4ea3ff' : '#60738d', target: 's1', active: props.listenOn,
    },
    {
      id: 'detect', x: 510, y: 72, label: '流量检测', en: 'DETECT',
      color: props.detectOn ? '#36f29a' : '#60738d', target: 's1', active: props.detectOn,
    },
  ]
})

const detectionFlowPath =
  'M 278 392 C 335 392 376 250 454 224 L 578 322 L 758 322 L 882 224 C 968 224 1022 282 1080 282'

const apps = [
  { id: 'chat', x: 1234, y: 292, label: '智能对话', color: '#20d8ff' },
  { id: 'video', x: 1330, y: 292, label: '视频请求', color: '#9b7cff' },
  { id: 'web', x: 1234, y: 452, label: '网页请求', color: '#36f29a' },
  { id: 'capture', x: 1330, y: 452, label: '抓包请求', color: '#ffbf4d' },
]
</script>

<template>
  <section class="tech-panel fabric-panel">
    <div class="fabric-head">
      <div>
        <div class="tech-h">多模态网络拓扑</div>
        <div class="fabric-sub">USER DOMAIN · SPINE–LEAF FABRIC · SERVICE DOMAIN</div>
      </div>
      <el-button size="small" :loading="probing" @click="emit('probe')">探测全部</el-button>
    </div>

    <div class="canvas-wrap">
      <svg class="fabric-svg" viewBox="0 0 1440 720" role="img" aria-label="多模态网络拓扑">
        <defs>
          <linearGradient id="fabric-bg" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#03101f" />
            <stop offset=".62" stop-color="#061426" />
            <stop offset="1" stop-color="#11091c" />
          </linearGradient>
          <linearGradient id="cloud-fill" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#1c7898" stop-opacity=".58" />
            <stop offset=".55" stop-color="#164c68" stop-opacity=".66" />
            <stop offset="1" stop-color="#10213e" stop-opacity=".82" />
          </linearGradient>
          <linearGradient id="backbone" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stop-color="#13d9ff" />
            <stop offset=".55" stop-color="#79efff" />
            <stop offset="1" stop-color="#26d3ff" />
          </linearGradient>
          <filter id="cyan-glow" x="-80%" y="-80%" width="260%" height="260%">
            <feGaussianBlur stdDeviation="5" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
          <filter id="soft-shadow" x="-80%" y="-80%" width="260%" height="260%">
            <feDropShadow dx="0" dy="14" stdDeviation="10" flood-color="#000814" flood-opacity=".72" />
          </filter>
          <filter id="attack-glow" x="-80%" y="-80%" width="260%" height="260%">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
          <pattern id="micro-grid" width="46" height="46" patternUnits="userSpaceOnUse">
            <path d="M 46 0 L 0 0 0 46" fill="none" stroke="#20d8ff" stroke-opacity=".035" />
          </pattern>
        </defs>

        <rect width="1440" height="720" fill="url(#fabric-bg)" />
        <rect width="1440" height="720" fill="url(#micro-grid)" />
        <g class="stars">
          <circle v-for="i in 66" :key="i" :cx="36 + ((i * 97) % 1360)" :cy="24 + ((i * 53) % 660)" :r="i % 7 === 0 ? 1.4 : .75" />
        </g>

        <!-- Three visual domains -->
        <g class="zones">
          <rect x="30" y="18" width="270" height="676" rx="14" />
          <rect x="318" y="18" width="750" height="676" rx="14" />
          <rect x="1086" y="18" width="324" height="676" rx="14" />
          <line x1="308" y1="32" x2="308" y2="680" />
          <line x1="1077" y1="32" x2="1077" y2="680" />
          <text x="52" y="49" class="zone-title">用户侧</text>
          <text x="52" y="70" class="zone-en">USER DOMAIN</text>
          <text x="342" y="49" class="zone-title">多模态网络侧</text>
          <text x="342" y="70" class="zone-en">SPINE–LEAF FABRIC</text>
          <text x="1108" y="49" class="zone-title">服务侧</text>
          <text x="1108" y="70" class="zone-en">SERVICE DOMAIN</text>
        </g>

        <!-- Capability pins -->
        <g
          v-for="cap in capabilities" :key="cap.id" class="capability"
          :class="[{ inactive: mode === 'detection' && !cap.active }, `cap-${cap.id}`]"
          :style="{ '--cap': cap.color }"
        >
          <path :d="`M ${cap.x} ${cap.y + 54} Q ${cap.x} ${cap.y + 92} ${nodeById[cap.target].x} ${nodeById[cap.target].y - 48}`" class="cap-line" />
          <circle :cx="cap.x" :cy="cap.y" r="31" class="cap-ring" />
          <path :d="`M ${cap.x} ${cap.y - 29} C ${cap.x - 22} ${cap.y - 29} ${cap.x - 31} ${cap.y - 12} ${cap.x - 27} ${cap.y + 5} C ${cap.x - 22} ${cap.y + 24} ${cap.x} ${cap.y + 42} ${cap.x} ${cap.y + 42} C ${cap.x} ${cap.y + 42} ${cap.x + 22} ${cap.y + 24} ${cap.x + 27} ${cap.y + 5} C ${cap.x + 31} ${cap.y - 12} ${cap.x + 22} ${cap.y - 29} ${cap.x} ${cap.y - 29} Z`" class="cap-pin" />
          <g v-if="cap.id === 'traffic' || cap.id === 'detect'" class="cap-glyph">
            <rect :x="cap.x - 13" :y="cap.y - 10" width="26" height="19" rx="2" />
            <path :d="`M ${cap.x - 8} ${cap.y + 3} l6 -6 l5 4 l7 -8`" />
          </g>
          <g v-else-if="cap.id === 'listen'" class="cap-glyph">
            <path :d="`M ${cap.x - 17} ${cap.y} Q ${cap.x} ${cap.y - 15} ${cap.x + 17} ${cap.y} Q ${cap.x} ${cap.y + 15} ${cap.x - 17} ${cap.y} Z`" />
            <circle :cx="cap.x" :cy="cap.y" r="5" />
          </g>
          <g v-else-if="cap.id === 'trace'" class="cap-glyph">
            <circle :cx="cap.x" :cy="cap.y" r="12" />
            <path :d="`M ${cap.x - 16} ${cap.y} H ${cap.x + 16} M ${cap.x} ${cap.y - 16} V ${cap.y + 16}`" />
          </g>
          <g v-else class="cap-glyph">
            <rect :x="cap.x - 11" :y="cap.y - 7" width="22" height="20" rx="3" />
            <path :d="`M ${cap.x - 7} ${cap.y - 7} V ${cap.y - 13} A 7 7 0 0 1 ${cap.x + 7} ${cap.y - 13} V ${cap.y - 7}`" />
          </g>
          <text :x="cap.x" :y="cap.y + 70" class="cap-label">{{ cap.label }}</text>
          <text :x="cap.x" :y="cap.y + 86" class="cap-en">{{ cap.en }}</text>
        </g>

        <!-- User terminals and access gateways -->
        <g class="terminals">
          <path d="M 286 236 V 550" class="terminal-bus" />
          <g v-for="terminal in terminals" :key="terminal.type">
            <path :d="`M 150 ${terminal.y} H 214`" class="terminal-link" />
            <path :d="`M 278 ${terminal.y} C 330 ${terminal.y}, 356 ${nodeById[terminal.target].y}, ${nodeById[terminal.target].x - 44} ${nodeById[terminal.target].y}`" class="gateway-uplink" />
            <g v-if="terminal.type === 'phone'">
              <rect x="86" :y="terminal.y - 38" width="48" height="74" rx="10" class="terminal-body" />
              <rect x="95" :y="terminal.y - 27" width="30" height="47" rx="4" class="terminal-screen" />
              <circle cx="110" :cy="terminal.y + 28" r="2.5" class="terminal-led" />
            </g>
            <g v-else-if="terminal.type === 'laptop'">
              <rect x="72" :y="terminal.y - 34" width="82" height="50" rx="6" class="terminal-body" />
              <rect x="82" :y="terminal.y - 23" width="62" height="30" rx="3" class="terminal-screen" />
              <path :d="`M 61 ${terminal.y + 20} H 166 L 150 ${terminal.y + 38} H 78 Z`" class="terminal-base" />
            </g>
            <g v-else>
              <rect x="80" :y="terminal.y - 34" width="66" height="52" rx="6" class="terminal-body" />
              <rect x="91" :y="terminal.y - 23" width="44" height="28" rx="3" class="terminal-screen" />
              <rect x="108" :y="terminal.y + 20" width="12" height="22" rx="2" class="terminal-base" />
            </g>
            <text x="110" :y="terminal.y + 60" class="terminal-label">{{ terminal.label }}</text>

            <g class="access-gateway" :transform="`translate(246 ${terminal.y})`">
              <ellipse cy="25" rx="34" ry="10" class="gateway-platform" />
              <rect x="-36" y="-16" width="72" height="30" rx="8" class="gateway-body" />
              <ellipse cy="-16" rx="36" ry="15" class="gateway-top" />
              <path d="M -16 -20 H 16 M 7 -27 L 17 -20 L 7 -13 M 16 -6 H -16 M -7 -13 L -17 -6 L -7 1" class="gateway-glyph" />
              <text y="48" class="gateway-label">用户侧网关</text>
            </g>
          </g>
        </g>

        <!-- Network fabric cloud and links -->
        <g class="network-cloud">
          <path d="M 370 356 C 384 258 470 184 556 213 C 615 142 739 142 800 213 C 878 185 976 253 986 348 C 1038 399 1005 520 920 557 C 846 621 746 578 680 542 C 605 615 478 599 418 536 C 354 518 333 412 370 356 Z" class="cloud-shadow" />
          <path d="M 370 356 C 384 258 470 184 556 213 C 615 142 739 142 800 213 C 878 185 976 253 986 348 C 1038 399 1005 520 920 557 C 846 621 746 578 680 542 C 605 615 478 599 418 536 C 354 518 333 412 370 356 Z" class="cloud-body" />
          <path d="M 424 368 C 455 294 520 264 588 278 C 642 236 731 237 784 280 C 852 260 925 302 942 368 C 969 425 914 493 844 510 C 755 533 592 527 499 501 C 443 485 398 427 424 368 Z" class="cloud-core" />
          <text x="680" y="226" class="fabric-label">Spine Fabric</text>
          <text x="680" y="514" class="fabric-label">Leaf Fabric</text>
        </g>

        <g class="fabric-links">
          <path v-for="edge in fabricEdges" :key="edge.join('-')" :d="edgePath(edge)" class="mesh-link" />
          <g v-for="edge in backbone" :key="`main-${edge.join('-')}`">
            <path :d="edgePath(edge)" class="backbone-shadow" />
            <path :d="edgePath(edge)" class="backbone-line" />
            <path :d="edgePath(edge)" class="backbone-stream" />
          </g>
          <g v-if="mode === 'detection' && linkFlow" class="detection-flow-layer">
            <path :d="detectionFlowPath" class="detection-flow-shadow" />
            <path :d="detectionFlowPath" class="detection-flow-line" />
            <circle v-for="i in 7" :key="`packet-${i}`" r="4" class="detection-packet">
              <animateMotion :path="detectionFlowPath" dur="2.8s" :begin="`${(i - 1) * 0.38}s`" repeatCount="indefinite" />
            </circle>
          </g>
        </g>

        <!-- Fabric devices -->
        <g v-for="node in fabricNodes" :key="node.id" class="router" :class="nodeState(node)" :transform="`translate(${node.x} ${node.y})`">
          <ellipse cy="42" :rx="node.edge ? 42 : 46" ry="14" class="router-ring" />
          <ellipse cy="16" :rx="node.edge ? 38 : 42" ry="18" class="router-side" />
          <rect :x="node.edge ? -38 : -42" y="-14" :width="node.edge ? 76 : 84" height="30" class="router-body" />
          <ellipse cy="-14" :rx="node.edge ? 38 : 42" ry="19" class="router-top" />
          <ellipse cy="-14" :rx="node.edge ? 27 : 31" ry="12" class="router-inner" />
          <path d="M -19 -18 H 19 M 8 -26 L 19 -18 L 8 -10 M 19 -3 H -19 M -8 -11 L -19 -3 L -8 5" class="router-arrows" />
          <g class="router-ports">
            <rect v-for="i in 7" :key="i" :x="-31 + (i - 1) * 10" y="22" width="5" height="4" rx="1" />
          </g>
          <circle cx="23" cy="20" r="3" class="router-led" />
          <text y="-58" class="router-role">{{ node.role }}</text>
          <text y="-37" class="router-name">{{ node.id }}</text>
        </g>

        <!-- Service gateways and application cluster -->
        <g class="services">
          <rect x="1190" y="185" width="205" height="385" rx="18" class="service-frame" />
          <text x="1292" y="150" class="service-role">服务侧</text>
          <text x="1292" y="176" class="service-title">应用服务集群</text>
          <path d="M 924 224 C 1000 224 1035 282 1080 282 M 924 224 C 1000 260 1035 382 1080 382 M 924 546 C 1000 546 1035 482 1080 482" class="service-bus" />
          <g v-for="(y, i) in [282, 382, 482]" :key="y" :transform="`translate(1118 ${y})`" class="service-gateway">
            <ellipse cy="25" rx="36" ry="10" class="service-platform" />
            <rect x="-39" y="-18" width="78" height="32" rx="8" class="service-gateway-body" />
            <ellipse cy="-18" rx="39" ry="16" class="service-gateway-top" />
            <path d="M -17 -22 H 17 M 7 -29 L 18 -22 L 7 -15 M 17 -7 H -17 M -7 -14 L -18 -7 L -7 0" class="service-glyph" />
            <text y="51" class="service-gateway-label">服务侧网关</text>
            <path :d="`M 40 -6 C 62 ${i === 1 ? -6 : i === 0 ? 8 : -18}, 66 ${i === 1 ? 0 : i === 0 ? 24 : -8}, 76 ${i === 1 ? 0 : i === 0 ? 24 : -8}`" class="service-ingress" />
          </g>

          <g v-for="app in apps" :key="app.id" class="app-node" :style="{ '--app': app.color }" :transform="`translate(${app.x} ${app.y})`">
            <ellipse cy="50" rx="40" ry="12" class="app-platform" />
            <polygon points="-28,-35 17,-35 31,-45 -14,-45" class="app-top" />
            <polygon points="17,-35 31,-45 31,24 17,34" class="app-side" />
            <rect x="-28" y="-35" width="45" height="69" rx="2" class="app-body" />
            <g class="app-icon">
              <g v-if="app.id === 'chat'">
                <rect x="-12" y="-14" width="38" height="28" rx="5" />
                <path d="M -2 14 L -9 22 L -7 13" />
                <circle v-for="dx in [0, 8, 16]" :key="dx" :cx="dx" cy="0" r="2" class="icon-dot" />
              </g>
              <g v-else-if="app.id === 'video'">
                <rect x="-12" y="-15" width="38" height="30" rx="4" />
                <path d="M 2 -9 L 19 0 L 2 9 Z" />
              </g>
              <g v-else-if="app.id === 'web'">
                <circle cx="7" cy="0" r="20" />
                <path d="M -13 0 H 27 M 7 -20 C -3 -9 -3 9 7 20 M 7 -20 C 17 -9 17 9 7 20" />
              </g>
              <g v-else>
                <rect x="-12" y="-15" width="38" height="30" />
                <path d="M -4 -7 H 16 M -4 0 H 19 M -4 7 H 11 M 15 -23 V -8 M 9 -14 L 15 -8 L 21 -14" />
              </g>
            </g>
            <text x="4" y="58" class="app-label">{{ app.label }}</text>
          </g>
        </g>

        <!-- Attack source -->
        <g class="attack">
          <path d="M 1006 581 C 978 545 950 506 910 477 M 1006 581 C 955 552 878 514 798 478 M 1006 581 C 930 584 786 558 646 496" class="attack-rays" />
          <ellipse cx="1006" cy="646" rx="62" ry="20" class="attack-platform" />
          <polygon points="1006,548 1054,574 1042,626 1006,650 970,626 958,574" class="attack-body" />
          <polygon points="1006,530 1038,558 974,558" class="attack-warning" />
          <path d="M 1006 537 V 548 M 1006 552 V 554" class="attack-mark" />
          <path d="M 987 587 H 1025 M 996 573 L 1016 603 M 1016 573 L 996 603" class="attack-circuit" />
          <circle cx="1036" cy="574" r="4" class="attack-dot" />
          <text x="1006" y="516" class="attack-label">攻击源</text>
        </g>
      </svg>
    </div>
  </section>
</template>

<style scoped>
.fabric-panel { padding: 14px 14px 10px; overflow: hidden; }
.fabric-head { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin: 0 2px 10px; }
.fabric-head .tech-h { margin: 0; }
.fabric-sub { color: #6685aa; font: 10px/1.4 'Consolas', monospace; letter-spacing: 1.4px; margin-top: 4px; }
.canvas-wrap { overflow: hidden; border: 1px solid rgba(32, 216, 255, .16); border-radius: 8px; background: #03101f; box-shadow: inset 0 0 50px rgba(32, 216, 255, .035); }
.fabric-svg { display: block; width: 100%; height: auto; min-height: 510px; font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif; }
.stars circle { fill: #a5efff; opacity: .22; }
.zones rect { fill: rgba(5, 18, 35, .13); stroke: rgba(54, 119, 162, .13); }
.zones line { stroke: rgba(91, 143, 184, .32); stroke-dasharray: 10 9; }
.zone-title { fill: #c8f7ff; font-size: 20px; font-weight: 900; filter: url(#cyan-glow); }
.zone-en { fill: #7f9fc7; font-size: 10px; font-weight: 800; letter-spacing: .5px; }

.capability { color: var(--cap); }
.capability.inactive { opacity: .64; }
.capability.inactive .cap-ring { filter: none; animation: none; }
.cap-line { fill: none; stroke: var(--cap); stroke-opacity: .52; stroke-width: 1.5; stroke-dasharray: 6 9; }
.cap-ring { fill: rgba(7, 20, 38, .9); stroke: var(--cap); stroke-width: 2; stroke-dasharray: 7 5; filter: url(#cyan-glow); animation: ring-spin 8s linear infinite; transform-box: fill-box; transform-origin: center; }
.cap-pin { fill: rgba(5, 22, 38, .94); stroke: var(--cap); stroke-width: 2.3; filter: url(#cyan-glow); }
.cap-glyph * { fill: none; stroke: #d8fbff; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.cap-label { fill: #e8f1ff; text-anchor: middle; font-size: 15px; font-weight: 900; }
.cap-en { fill: var(--cap); text-anchor: middle; font-size: 9px; font-weight: 900; letter-spacing: 1.4px; }
@keyframes ring-spin { to { transform: rotate(360deg); } }

.terminal-bus, .terminal-link { fill: none; stroke: rgba(32, 216, 255, .32); stroke-width: 1.6; }
.gateway-uplink { fill: none; stroke: #20d8ff; stroke-width: 2; stroke-dasharray: 9 7; filter: url(#cyan-glow); animation: dash 5s linear infinite; }
.terminal-body { fill: rgba(10, 37, 62, .92); stroke: rgba(32, 216, 255, .74); stroke-width: 1.4; filter: url(#cyan-glow); }
.terminal-screen { fill: rgba(56, 197, 220, .24); stroke: rgba(216, 251, 255, .34); }
.terminal-base { fill: rgba(132, 190, 255, .18); stroke: rgba(216, 251, 255, .38); }
.terminal-led { fill: #36f29a; filter: url(#cyan-glow); }
.terminal-label { fill: #a8bdd8; text-anchor: middle; font-size: 11px; font-weight: 800; }
.access-gateway, .service-gateway { filter: url(#soft-shadow); }
.gateway-platform, .service-platform { fill: rgba(32, 216, 255, .09); stroke: rgba(32, 216, 255, .5); }
.gateway-body, .service-gateway-body { fill: rgba(3, 16, 31, .94); stroke: rgba(32, 216, 255, .76); stroke-width: 1.3; }
.gateway-top, .service-gateway-top { fill: rgba(14, 48, 78, .95); stroke: rgba(32, 216, 255, .92); stroke-width: 1.4; filter: url(#cyan-glow); }
.gateway-glyph, .service-glyph { fill: none; stroke: #d8fbff; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.gateway-label, .service-gateway-label { fill: #d8fbff; font-size: 10px; font-weight: 900; text-anchor: middle; }

.cloud-shadow { fill: #000713; opacity: .75; transform: translateY(18px); filter: blur(7px); }
.cloud-body { fill: url(#cloud-fill); stroke: #20d8ff; stroke-width: 1.8; filter: url(#cyan-glow); }
.cloud-core { fill: rgba(10, 28, 56, .6); stroke: rgba(94, 216, 255, .18); }
.fabric-label { fill: #a7c7df; font-size: 12px; font-weight: 800; text-anchor: middle; }
.mesh-link { fill: none; stroke: rgba(142, 208, 233, .38); stroke-width: 1.7; }
.backbone-shadow { fill: none; stroke: #20d8ff; stroke-width: 15; opacity: .18; filter: url(#cyan-glow); }
.backbone-line { fill: none; stroke: url(#backbone); stroke-width: 6; stroke-linecap: round; filter: url(#cyan-glow); }
.backbone-stream { fill: none; stroke: #e8fcff; stroke-width: 2; stroke-linecap: round; stroke-dasharray: 2 18; animation: dash 1.2s linear infinite; }
.detection-flow-shadow { fill: none; stroke: #20d8ff; stroke-width: 16; opacity: .2; filter: url(#cyan-glow); }
.detection-flow-line { fill: none; stroke: #d8fbff; stroke-width: 2.4; stroke-linecap: round; stroke-dasharray: 3 15; filter: url(#cyan-glow); animation: dash .95s linear infinite; }
.detection-packet { fill: #eaffff; stroke: #20d8ff; stroke-width: 1.5; filter: url(#cyan-glow); }
@keyframes dash { to { stroke-dashoffset: -180; } }

.router { filter: url(#soft-shadow); }
.router-ring { fill: rgba(32, 216, 255, .07); stroke: #20d8ff; stroke-opacity: .58; filter: url(#cyan-glow); }
.router-side { fill: rgba(3, 11, 24, .98); stroke: #20d8ff; stroke-opacity: .58; }
.router-body { fill: rgba(5, 15, 29, .98); stroke: #20d8ff; stroke-opacity: .7; }
.router-top { fill: rgba(16, 44, 70, .98); stroke: #20d8ff; stroke-width: 1.5; filter: url(#cyan-glow); }
.router-inner { fill: rgba(4, 14, 28, .94); stroke: rgba(216, 251, 255, .3); }
.router-arrows { fill: none; stroke: #d8fbff; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.router-ports rect { fill: rgba(216, 251, 255, .55); }
.router-led { fill: #36f29a; filter: url(#cyan-glow); }
.router-role { fill: #9fb4d4; font-size: 12px; font-weight: 800; text-anchor: middle; }
.router-name { fill: #e8f1ff; font-size: 22px; font-weight: 900; text-anchor: middle; filter: url(#cyan-glow); }
.router.offline .router-top, .router.offline .router-body, .router.offline .router-side { stroke: #ff5a67; }
.router.offline .router-led { fill: #ff5a67; }
.router.unknown { opacity: .78; }

.service-frame { fill: rgba(7, 35, 56, .5); stroke: rgba(32, 216, 255, .3); stroke-dasharray: 10 10; filter: url(#cyan-glow); }
.service-role { fill: #9fb4d4; font-size: 13px; font-weight: 800; text-anchor: middle; }
.service-title { fill: #e8f1ff; font-size: 21px; font-weight: 900; text-anchor: middle; filter: url(#cyan-glow); }
.service-bus, .service-ingress { fill: none; stroke: rgba(32, 216, 255, .78); stroke-width: 2; stroke-dasharray: 8 8; animation: dash 5s linear infinite; }
.app-node { color: var(--app); filter: url(#soft-shadow); }
.app-platform { fill: rgba(32, 216, 255, .08); stroke: var(--app); stroke-opacity: .7; }
.app-body { fill: rgba(8, 25, 43, .97); stroke: var(--app); stroke-width: 1.4; }
.app-side { fill: rgba(3, 10, 22, .95); stroke: var(--app); }
.app-top { fill: rgba(25, 57, 81, .95); stroke: var(--app); filter: url(#cyan-glow); }
.app-icon * { fill: none; stroke: #d8fbff; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.app-icon .icon-dot { fill: #d8fbff; }
.app-label { fill: #dce8ff; font-size: 11px; font-weight: 800; text-anchor: middle; }

.attack-rays { fill: none; stroke: #ff743c; stroke-width: 2.2; stroke-dasharray: 8 8; opacity: .72; animation: dash 3.6s linear infinite; }
.attack-platform { fill: rgba(255, 107, 53, .1); stroke: #ff9866; filter: url(#attack-glow); }
.attack-body { fill: rgba(255, 107, 53, .34); stroke: #ffb58a; stroke-width: 2; filter: url(#attack-glow); }
.attack-warning { fill: rgba(255, 90, 103, .78); stroke: #ffe2da; stroke-width: 1.5; filter: url(#attack-glow); }
.attack-mark, .attack-circuit { fill: none; stroke: #fff5eb; stroke-width: 3; stroke-linecap: round; }
.attack-dot { fill: #ffdcbf; filter: url(#attack-glow); }
.attack-label { fill: #fff2e8; font-size: 19px; font-weight: 900; text-anchor: middle; filter: url(#attack-glow); }

@media (max-width: 1100px) {
  .fabric-svg { min-height: 430px; }
}
@media (max-width: 760px) {
  .fabric-head { align-items: flex-start; }
  .fabric-sub { display: none; }
  .canvas-wrap { overflow-x: auto; }
  .fabric-svg { width: 1060px; max-width: none; min-height: 530px; }
}
</style>
