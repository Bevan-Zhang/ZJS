<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { isRunning, pickMimetic } from '../../utils/defense'
import { useDashboard } from '../../composables/useDashboard'
import DefenseControl from '../../components/DefenseControl.vue'
import RawJson from '../../components/RawJson.vue'

const { dash, online, refresh } = useDashboard()
const STRATEGY = 'mimetic_adaptive_defense'
const running = computed(() => isRunning(pickMimetic(dash.value, STRATEGY)))

// ---- 异构执行体（后端控制上下线）----
interface Executor {
  id: number
  name: string
  type: 'traditional' | 'optimized'  // 传统 / 优化后
  online: boolean
  desc: string
}
const executors = ref<Executor[]>([
  { id: 1, name: 'REMI-AIA',         type: 'optimized',   online: true,  desc: '免疫优化代理 (s4:8080)' },
  { id: 2, name: 'Voting-5000',      type: 'traditional', online: true,  desc: '传统投票裁决器' },
  { id: 3, name: 'hetero_ubuntu',    type: 'traditional', online: true,  desc: 'Ubuntu + Apache' },
  { id: 4, name: 'hetero_centos',    type: 'traditional', online: true,  desc: 'CentOS + Nginx' },
  { id: 5, name: 'hetero_debian',    type: 'optimized',   online: false, desc: 'Debian + Tomcat (REMI 优化后)' },
  { id: 6, name: 'hetero_alpine',    type: 'traditional', online: true,  desc: 'Alpine + Lighttpd' },
  { id: 7, name: 'hetero_fedora',    type: 'optimized',   online: true,  desc: 'Fedora + Caddy (REMI 优化后)' },
])

const onlineExecutors = computed(() => executors.value.filter((e) => e.online))
const traditionalCount = computed(() => executors.value.filter((e) => e.type === 'traditional' && e.online).length)
const optimizedCount = computed(() => executors.value.filter((e) => e.type === 'optimized' && e.online).length)

// ---- 历史防御成功率（动态模拟）----
const successRate = ref(87.3)
const rateDelta = ref(2.1)
const rateHistory = ref<number[]>([82.4, 83.1, 79.8, 85.2, 86.7, 84.9, 87.3])
let rateTimer: number | undefined

function tickRate() {
  const delta = (Math.random() - 0.45) * 1.8
  successRate.value = Math.min(99.9, Math.max(75, +(successRate.value + delta).toFixed(1)))
  rateDelta.value = +(delta).toFixed(1)
  rateHistory.value.push(successRate.value)
  if (rateHistory.value.length > 15) rateHistory.value.shift()
}

onMounted(() => { rateTimer = window.setInterval(tickRate, 3000) })
onBeforeUnmount(() => { rateTimer && window.clearInterval(rateTimer) })

// 折线图坐标（viewBox: 0 0 220 110，含坐标轴边距）
const PLOT = { left: 30, right: 210, top: 8, bottom: 92 }
const Y_MIN = 75; const Y_MAX = 100

// 限制展示最近 N 个点，避免 X 轴挤
const MAX_PTS = 10
const visibleHistory = computed(() => rateHistory.value.slice(-MAX_PTS))

const chartPts = computed(() => {
  const data = visibleHistory.value
  if (data.length < 2) return []
  const w = PLOT.right - PLOT.left; const h = PLOT.bottom - PLOT.top
  return data.map((v, i) => ({
    x: PLOT.left + (i / Math.max(1, data.length - 1)) * w,
    y: PLOT.bottom - ((v - Y_MIN) / (Y_MAX - Y_MIN)) * h,
    v,
    idx: rateHistory.value.length - data.length + i + 1,  // 真实序号
  }))
})

const linePoints = computed(() => chartPts.value.map((p) => `${p.x},${p.y}`).join(' '))

const areaPath = computed(() => {
  const pts = chartPts.value
  if (pts.length < 2) return ''
  const upper = pts.map((p) => `${p.x},${p.y}`).join(' ')
  return `M${upper} L${pts[pts.length - 1].x},${PLOT.bottom} L${pts[0].x},${PLOT.bottom} Z`
})

// Y 轴刻度
const yTicks = [75, 80, 85, 90, 95, 100]
function yPos(v: number) { return PLOT.bottom - ((v - Y_MIN) / (Y_MAX - Y_MIN)) * (PLOT.bottom - PLOT.top) }

// X 轴标签：只显示每隔 N 个 + 最后一个
const xTickStep = computed(() => Math.max(1, Math.floor(visibleHistory.value.length / 5)))
const visibleXLabels = computed(() => {
  const step = xTickStep.value
  return chartPts.value.filter((_, i) => i % step === 0 || i === chartPts.value.length - 1)
})
</script>

<template>
  <div class="page">
    <h2 class="title">拟态自适应防御</h2>
    <DefenseControl name="拟态自适应防御 (REMI-AIA)" :strategy="STRATEGY" node="网元 s4（中间）" ip="192.168.4.2"
      :running="running" :online="online" @changed="refresh" />

    <div class="cols">
      <!-- 左：已上线执行体 -->
      <div class="tech-panel">
        <div class="tech-h">已上线执行体</div>
        <div class="exec-summary">
          <span class="es-tag traditional">传统 {{ traditionalCount }}</span>
          <span class="es-tag optimized">优化 {{ optimizedCount }}</span>
          <span class="es-total">共 {{ onlineExecutors.length }} 个在线</span>
        </div>
        <div class="exec-list">
          <div
            v-for="e in executors"
            :key="e.id"
            class="exec-item"
            :class="{ online: e.online, offline: !e.online }"
          >
            <span class="ei-dot" :class="e.online ? 'on' : 'off'" />
            <div class="ei-info">
              <span class="ei-name">{{ e.name }}</span>
              <span class="ei-desc">{{ e.desc }}</span>
            </div>
            <span class="ei-type" :class="e.type">
              {{ e.type === 'optimized' ? '优化后' : '传统' }}
            </span>
          </div>
        </div>
      </div>

      <!-- 右：历史防御成功率 -->
      <div class="tech-panel">
        <div class="tech-h">历史防御成功率</div>
        <div class="rate-main">
          <div class="rate-big">{{ successRate.toFixed(1) }}<span class="rate-pct">%</span></div>
          <div class="rate-change" :class="rateDelta >= 0 ? 'up' : 'down'">
            {{ rateDelta >= 0 ? '↑' : '↓' }}{{ Math.abs(rateDelta).toFixed(1) }}%
          </div>
        </div>
        <p class="rate-sub">近 7 次防御周期成功率变化</p>

        <!-- 折线图 -->
        <svg class="rate-chart" viewBox="0 0 220 110" preserveAspectRatio="xMidYMid meet">
          <defs>
            <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#36e3a3" stop-opacity=".25" />
              <stop offset="100%" stop-color="#36e3a3" stop-opacity="0" />
            </linearGradient>
          </defs>

          <!-- Y 轴网格线 -->
          <line v-for="t in yTicks" :key="'g'+t"
            :x1="PLOT.left" :x2="PLOT.right" :y1="yPos(t)" :y2="yPos(t)"
            stroke="rgba(255,255,255,.08)" stroke-width="0.4" stroke-dasharray="2,3" />

          <!-- Y 轴刻度 -->
          <text v-for="t in yTicks" :key="'y'+t"
            :x="PLOT.left - 4" :y="yPos(t) + 1.5" text-anchor="end" class="ax-label">{{ t }}</text>

          <!-- Y 轴标题 -->
          <text x="4" y="50" text-anchor="middle" class="ax-title" transform="rotate(-90, 4, 50)">成功率 %</text>

          <!-- 区域填充 -->
          <path :d="areaPath" fill="url(#areaGrad)" />

          <!-- 折线 -->
          <polyline :points="linePoints" fill="none" stroke="#36e3a3" stroke-width="1"
            stroke-linejoin="round" stroke-linecap="round" />

          <!-- 数据点 -->
          <circle v-for="(p, i) in chartPts" :key="'c'+i"
            :cx="p.x" :cy="p.y" r="1.5" fill="#36e3a3" stroke="#0a162c" stroke-width="0.5" />

          <!-- X 轴标签（间隔显示） -->
          <text v-for="p in visibleXLabels" :key="'x'+p.idx"
            :x="p.x" :y="PLOT.bottom + 9" text-anchor="middle" class="ax-label">
            #{{ p.idx }}
          </text>

          <!-- 坐标轴线 -->
          <line :x1="PLOT.left" :x2="PLOT.right" :y1="PLOT.bottom" :y2="PLOT.bottom"
            stroke="rgba(255,255,255,.18)" stroke-width="0.5" />
          <line :x1="PLOT.left" :x2="PLOT.left" :y1="PLOT.top" :y2="PLOT.bottom"
            stroke="rgba(255,255,255,.18)" stroke-width="0.5" />

          <!-- X 轴标题 -->
          <text :x="(PLOT.left + PLOT.right) / 2" :y="108" text-anchor="middle" class="ax-title">防御周期</text>
        </svg>
      </div>
    </div>

    <RawJson :data="dash" />
  </div>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: 18px; }
.title { margin: 0; font-size: 26px; color: #eaf6ff; text-shadow: 0 0 16px var(--tech-glow); }
.cols { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
@media (max-width: 960px) { .cols { grid-template-columns: 1fr; } }

/* ===== 执行体摘要 ===== */
.exec-summary { display: flex; gap: 10px; align-items: center; margin-bottom: 12px; }
.es-tag {
  font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 5px;
}
.es-tag.traditional { background: rgba(255,182,72,.12); color: #ffb648; border: 1px solid rgba(255,182,72,.25); }
.es-tag.optimized { background: rgba(54,227,163,.10); color: #36e3a3; border: 1px solid rgba(54,227,163,.25); }
.es-total { font-size: 11px; color: var(--tech-text-dim); margin-left: auto; }

/* ===== 执行体列表 ===== */
.exec-list { display: flex; flex-direction: column; gap: 6px; }
.exec-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px; border-radius: 8px;
  border: 1px solid var(--tech-border); background: rgba(255,255,255,.02);
  transition: all .3s;
}
.exec-item.online { border-color: rgba(0,229,255,.18); }
.exec-item.offline { opacity: .4; border-style: dashed; }
.ei-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.ei-dot.on { background: #36e3a3; box-shadow: 0 0 8px #36e3a3; }
.ei-dot.off { background: #6b7a90; }
.ei-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.ei-name { font-size: 13px; font-weight: 600; color: #eaf6ff; font-family: 'JetBrains Mono', monospace; }
.ei-desc { font-size: 11px; color: var(--tech-text-dim); }
.ei-type {
  font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 4px; flex-shrink: 0;
}
.ei-type.traditional { background: rgba(255,182,72,.12); color: #ffb648; }
.ei-type.optimized { background: rgba(54,227,163,.10); color: #36e3a3; }

/* ===== 成功率 ===== */
.rate-main { display: flex; align-items: baseline; gap: 14px; margin: 8px 0 4px; }
.rate-big { font-size: 48px; font-weight: 700; color: #36e3a3; font-family: 'JetBrains Mono', monospace; line-height: 1; }
.rate-pct { font-size: 24px; color: #36e3a3; }
.rate-change { font-size: 16px; font-weight: 700; padding: 4px 10px; border-radius: 6px; }
.rate-change.up { color: #36e3a3; background: rgba(54,227,163,.08); }
.rate-change.down { color: #ff7a7a; background: rgba(255,122,122,.08); }
.rate-sub { color: var(--tech-text-dim); font-size: 12px; margin-bottom: 16px; }

/* ===== 折线图 ===== */
.rate-chart {
  width: 100%; height: auto; margin-top: 8px;
}
.ax-label { font-size: 5px; fill: #7a8fa0; font-family: 'JetBrains Mono', monospace; }
.ax-title { font-size: 4.5px; fill: #5a6a7e; font-weight: 600; }
</style>
