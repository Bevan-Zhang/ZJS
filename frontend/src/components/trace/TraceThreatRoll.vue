<script setup lang="ts">
import { computed } from 'vue'
import type { TraceThreat } from '../../api/client'
import { modClass, modLabel, sampleLabel } from '../../utils/detect'

const props = defineProps<{
  rows: TraceThreat[]
  currentId?: string
}>()

const emit = defineEmits<{ (e: 'select', id: string): void }>()

const dur = computed(() => Math.max(20, props.rows.length * 0.9))

function confPct(value?: string) {
  const n = Number(value)
  if (!Number.isFinite(n)) return '-'
  return `${(n * 100).toFixed(1)}%`
}

function shortId(id?: string) {
  return id?.replace(/^threat_/, '') ?? '-'
}
</script>

<template>
  <div class="ticker">
    <div class="t-head">
      <div class="t-title"><span class="live" />威胁检测流</div>
      <div class="t-meta">已检 <b>{{ rows.length.toLocaleString() }}</b></div>
    </div>

    <div class="t-cols">
      <span class="c-sample">样本</span>
      <span class="c-mod">模态</span>
      <span class="c-verdict">攻击 → 阶段</span>
      <span class="c-conf">置信</span>
      <span class="c-res">ID</span>
    </div>

    <div class="t-body">
      <div v-if="!rows.length" class="t-empty">等待威胁检测结果</div>
      <div v-else class="t-track" :style="{ animationDuration: dur + 's' }">
        <div v-for="copy in 2" :key="copy" class="t-list">
          <div
            v-for="(r, i) in rows"
            :key="copy + '-' + i"
            class="t-row"
            :class="{ active: r.threat_id === currentId }"
            @click="emit('select', r.threat_id)"
          >
            <span class="c-sample" :title="r.file_name || r.threat_id">{{ sampleLabel(r.file_name || r.threat_id) }}</span>
            <span class="c-mod"><span :class="modClass(r.modality)">{{ modLabel(r.modality) }}</span></span>
            <span class="c-verdict">
              <span class="vtrue">{{ r.attack_type || '-' }}</span>
              <span class="arrow">›</span>
              <span class="vpred ok">{{ r.stage || '-' }}</span>
            </span>
            <span class="c-conf">
              <span class="bar"><i :style="{ width: confPct(r.ml_confidence) }" /></span>
              <em>{{ confPct(r.ml_confidence) }}</em>
            </span>
            <span class="c-res"><span class="vd vd-hit">{{ shortId(r.threat_id) }}</span></span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ticker {
  height: 560px; display: flex; flex-direction: column;
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
  grid-template-columns: 1.7fr 64px 1.85fr 1.1fr 76px;
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
  cursor: pointer;
}
.t-row:hover,
.t-row.active { background: rgba(0, 229, 255, 0.09); }
.c-sample { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #a9c6e8; }
.c-verdict { display: flex; align-items: center; gap: 6px; white-space: nowrap; overflow: hidden; }
.vtrue { color: #cfe3fb; overflow: hidden; text-overflow: ellipsis; }
.arrow { color: var(--tech-text-dim); }
.vpred.ok { color: #36e3a3; overflow: hidden; text-overflow: ellipsis; }
.c-conf { display: flex; align-items: center; gap: 6px; }
.c-conf .bar { flex: 1; height: 4px; border-radius: 2px; background: rgba(125, 148, 184, 0.2); overflow: hidden; }
.c-conf .bar i { display: block; height: 100%; background: linear-gradient(90deg, #1f8fff, #00e5ff); }
.c-conf em { font-style: normal; font-size: 11px; color: #8fb4dd; min-width: 42px; text-align: right; }
.vd { white-space: nowrap; font-weight: 700; }
.vd-hit { color: #36e3a3; }
</style>
