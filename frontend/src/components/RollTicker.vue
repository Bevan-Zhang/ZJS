<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api, type DetectionSample } from '../api/client'
import { confPct, modClass, modLabel, sampleLabel } from '../utils/detect'

const rows = ref<DetectionSample[]>([])
const total = ref(0)

async function load() {
  try {
    const r = await api.getDetectionRoll()
    rows.value = r.rows
    total.value = r.total
  } catch {
    rows.value = []
  }
}

// 无缝循环：列表复制两份，整体 translateY -50%；时长随条数走，保证恒定行速
const dur = computed(() => Math.max(20, rows.value.length * 0.9))
const hitRate = computed(() => {
  if (!rows.value.length) return 0
  const hit = rows.value.filter((r) => r.correct).length
  return Math.round((hit / rows.value.length) * 100)
})

onMounted(load)
</script>

<template>
  <div class="ticker">
    <div class="t-head">
      <div class="t-title"><span class="live" />历史检测流</div>
      <div class="t-meta">已检 <b>{{ total.toLocaleString() }}</b> · 命中 <b>{{ hitRate }}%</b></div>
    </div>

    <div class="t-cols">
      <span class="c-sample">样本</span>
      <span class="c-mod">模态</span>
      <span class="c-verdict">真实 → 预测</span>
      <span class="c-conf">置信</span>
      <span class="c-res">判定</span>
    </div>

    <div class="t-body">
      <div v-if="!rows.length" class="t-empty">等待检测流（results/roll.csv）…</div>
      <div v-else class="t-track" :style="{ animationDuration: dur + 's' }">
        <div v-for="copy in 2" :key="copy" class="t-list">
          <div v-for="(r, i) in rows" :key="copy + '-' + i" class="t-row" :class="{ miss: !r.correct }">
            <span class="c-sample" :title="r.name">{{ sampleLabel(r.name) }}</span>
            <span class="c-mod"><span :class="modClass(r.modality)">{{ modLabel(r.modality) }}</span></span>
            <span class="c-verdict">
              <span class="vtrue">{{ r.true }}</span>
              <span class="arrow">›</span>
              <span :class="r.correct ? 'vpred ok' : 'vpred bad'">{{ r.pred }}</span>
            </span>
            <span class="c-conf">
              <span class="bar"><i :style="{ width: (r.confidence ?? 0) * 100 + '%' }" /></span>
              <em>{{ confPct(r.confidence) }}</em>
            </span>
            <span class="c-res"><span class="vd" :class="r.correct ? 'vd-hit' : 'vd-miss'">{{ r.correct ? '命中' : '误判' }}</span></span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ticker {
  height: 100%; display: flex; flex-direction: column;
  background: linear-gradient(180deg, rgba(10, 22, 44, 0.7), rgba(6, 14, 30, 0.7));
  border: 1px solid var(--tech-border); border-radius: 12px; overflow: hidden;
  box-shadow: inset 0 0 30px rgba(0, 229, 255, 0.05);
}
.t-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px; border-bottom: 1px solid var(--tech-border);
}
.t-title { display: flex; align-items: center; gap: 8px; font-weight: 600; color: #e6f3ff; font-size: 15px; }
.live { width: 8px; height: 8px; border-radius: 50%; background: var(--tech-cyan); box-shadow: 0 0 8px var(--tech-cyan); }
.t-meta { font-size: 12px; color: var(--tech-text-dim); }
.t-meta b { color: var(--tech-cyan); font-family: 'JetBrains Mono', monospace; }

.t-cols, .t-row {
  display: grid;
  grid-template-columns: 1.6fr 64px 1.8fr 1.1fr 56px;
  gap: 10px; align-items: center;
}
.t-cols {
  padding: 8px 16px; font-size: 11px; letter-spacing: 1px; color: var(--tech-text-dim);
  border-bottom: 1px solid rgba(64, 158, 255, 0.12); background: rgba(255, 255, 255, 0.02);
}
.t-body { position: relative; flex: 1; min-height: 0; overflow: hidden; }
.t-empty { padding: 30px 16px; color: var(--tech-text-dim); font-size: 13px; }
.t-track { position: absolute; left: 0; right: 0; top: 0; animation: roll linear infinite; will-change: transform; }
.ticker:hover .t-track { animation-play-state: paused; }
@keyframes roll { from { transform: translateY(0); } to { transform: translateY(-50%); } }

.t-row {
  padding: 7px 16px; font-size: 12.5px; color: #c7ddf5;
  border-bottom: 1px solid rgba(64, 158, 255, 0.06);
  font-family: 'JetBrains Mono', 'Consolas', monospace;
}
.t-row.miss { background: rgba(255, 122, 122, 0.06); }
.c-sample { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #a9c6e8; }
.c-verdict { display: flex; align-items: center; gap: 6px; white-space: nowrap; overflow: hidden; }
.vtrue { color: #cfe3fb; }
.arrow { color: var(--tech-text-dim); }
.vpred.ok { color: #36e3a3; }
.vpred.bad { color: #ff7a7a; font-weight: 700; }
.c-conf { display: flex; align-items: center; gap: 6px; }
.c-conf .bar { flex: 1; height: 4px; border-radius: 2px; background: rgba(125, 148, 184, 0.2); overflow: hidden; }
.c-conf .bar i { display: block; height: 100%; background: linear-gradient(90deg, #1f8fff, #00e5ff); }
.c-conf em { font-style: normal; font-size: 11px; color: #8fb4dd; min-width: 42px; text-align: right; }
</style>
