<script setup lang="ts">
import { computed } from 'vue'
import { isRunning, pickMimetic } from '../../utils/defense'
import { useDashboard } from '../../composables/useDashboard'
import DefenseControl from '../../components/DefenseControl.vue'
import RawJson from '../../components/RawJson.vue'

const { dash, online, refresh } = useDashboard()
const STRATEGY = 'mimetic_honeypot'
const running = computed(() => isRunning(pickMimetic(dash.value, STRATEGY)))

// ---- 诱捕率（从 dashboard 读取）----
const trapRate = computed(() => dash.value?.honeypot?.trap_rate ?? 0)

// 环形仪表盘 SVG 参数
const RING_R = 32; const RING_C = 2 * Math.PI * RING_R
const ringOffset = computed(() => RING_C * (1 - trapRate.value / 100))

// ---- 攻击类型捕获次数（从 dashboard 读取）----
const attackStats = computed(() => (dash.value?.honeypot?.attack_stats as any[]) ?? [])

const maxCount = computed(() => Math.max(...attackStats.value.map((a: any) => a.count), 1))
const totalAttacks = computed(() => attackStats.value.reduce((s: number, a: any) => s + a.count, 0))
function barWidth(c: number) { return `${(c / maxCount.value) * 100}%` }
</script>

<template>
  <div class="page">
    <h2 class="title">跨膜态诱捕蜜罐</h2>
    <DefenseControl name="跨膜态诱捕蜜罐" :strategy="STRATEGY" node="网元 s7（出口）" ip="192.168.7.2"
      :running="running" :online="online" @changed="refresh" />

    <div class="cols">
      <!-- 左：诱捕率 -->
      <div class="tech-panel">
        <div class="tech-h">诱捕率</div>
        <p class="tech-sub">攻击流量命中蜜罐并被成功诱捕的比例</p>

        <!-- 环形仪表 -->
        <div class="ring-wrap">
          <svg class="ring" viewBox="0 0 80 80">
            <!-- 背景环 -->
            <circle cx="40" cy="40" :r="RING_R" fill="none"
              stroke="rgba(255,255,255,.06)" stroke-width="5" />
            <!-- 进度环 -->
            <circle cx="40" cy="40" :r="RING_R" fill="none"
              stroke="#36e3a3" stroke-width="5" stroke-linecap="round"
              :stroke-dasharray="RING_C" :stroke-dashoffset="ringOffset"
              transform="rotate(-90, 40, 40)"
              style="transition: stroke-dashoffset .8s ease" />
            <!-- 中心数值 -->
            <text x="40" y="38" text-anchor="middle" class="ring-val">{{ trapRate.toFixed(1) }}%</text>
            <text x="40" y="50" text-anchor="middle" class="ring-sub">诱捕率</text>
          </svg>
        </div>

        <!-- 摘要行 -->
        <div class="trap-summary">
          <div class="ts-item">
            <div class="ts-num" style="color:#36e3a3">{{ totalAttacks }}</div>
            <div class="ts-label">总攻击次数</div>
          </div>
          <div class="ts-item">
            <div class="ts-num" style="color:#ffb648">{{ Math.round(totalAttacks * trapRate / 100) }}</div>
            <div class="ts-label">成功诱捕</div>
          </div>
        </div>
      </div>

      <!-- 右：攻击类型捕获次数 -->
      <div class="tech-panel">
        <div class="tech-h">攻击类型捕获次数</div>
        <p class="tech-sub">各类型攻击被蜜罐捕获的累计次数</p>

        <div class="bar-list">
          <div v-for="a in attackStats" :key="a.type" class="bar-row">
            <span class="bar-label">{{ a.type }}</span>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: barWidth(a.count) }" />
            </div>
            <span class="bar-cnt">{{ a.count }}</span>
          </div>
        </div>
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

/* ===== 环形仪表 ===== */
.ring-wrap { display: flex; justify-content: center; margin: 12px 0; }
.ring { width: 180px; height: 180px; }
.ring-val { font-size: 14px; font-weight: 700; fill: #eaf6ff; font-family: 'JetBrains Mono', monospace; }
.ring-sub { font-size: 4.5px; fill: #6b7a90; }

/* ===== 诱捕摘要 ===== */
.trap-summary { display: flex; gap: 12px; }
.ts-item { flex: 1; text-align: center; padding: 12px 8px; border-radius: 8px; background: rgba(255,255,255,.02); border: 1px solid var(--tech-border); }
.ts-num { font-size: 22px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
.ts-label { font-size: 11px; color: var(--tech-text-dim); margin-top: 2px; }

/* ===== 条形图 ===== */
.bar-list { display: flex; flex-direction: column; gap: 8px; margin-top: 10px; }
.bar-row { display: flex; align-items: center; gap: 10px; }
.bar-label { font-size: 12px; color: #cfe3fb; width: 110px; flex-shrink: 0; text-align: right; }
.bar-track { flex: 1; height: 18px; background: rgba(255,255,255,.03); border-radius: 4px; overflow: hidden; border: 1px solid rgba(255,255,255,.06); }
.bar-fill {
  height: 100%; border-radius: 4px;
  background: linear-gradient(90deg, rgba(255,122,122,.5), rgba(255,182,72,.6));
  transition: width .6s ease;
}
.bar-cnt { font-size: 13px; font-weight: 700; color: #ff9a8b; font-family: 'JetBrains Mono', monospace; width: 36px; text-align: left; }

.tech-sub { color: var(--tech-text-dim); font-size: 12px; margin-bottom: 4px; line-height: 1.6; }
</style>
