<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { DetectionSample } from '../api/client'
import { confPct, modClass, modLabel, sampleLabel } from '../utils/detect'

// 右侧聚光：依次走过该文件的每条样本
const props = defineProps<{ samples: DetectionSample[] }>()
const idx = ref(0)
let timer: number | undefined

const cur = computed<DetectionSample | null>(() => props.samples[idx.value] ?? null)

function start() {
  stop()
  if (props.samples.length > 1) {
    timer = window.setInterval(() => {
      idx.value = (idx.value + 1) % props.samples.length
    }, 1600)
  }
}
function stop() { if (timer) { window.clearInterval(timer); timer = undefined } }

watch(() => props.samples, () => { idx.value = 0; start() })
onMounted(start)
onBeforeUnmount(stop)
</script>

<template>
  <div class="spot" @mouseenter="stop" @mouseleave="start">
    <div class="spot-head">
      <span class="lbl">样本</span>
      <span class="counter" v-if="samples.length">{{ (idx + 1).toLocaleString() }} / {{ samples.length.toLocaleString() }}</span>
    </div>

    <transition name="swap" mode="out-in">
      <div v-if="cur" :key="idx" class="spot-body">
        <div class="sname" :title="cur.name">
          {{ sampleLabel(cur.name) }}
          <span v-if="cur.modality" :class="modClass(cur.modality)">{{ modLabel(cur.modality) }}</span>
        </div>

        <div class="duo">
          <div class="cell">
            <div class="k">真实攻击类型</div>
            <div class="v">{{ cur.true }}</div>
          </div>
          <div class="sep">›</div>
          <div class="cell">
            <div class="k">预测攻击类型</div>
            <div class="v" :class="cur.correct ? 'ok' : 'bad'">{{ cur.pred }}</div>
          </div>
        </div>

        <div class="foot">
          <div class="judge" :class="cur.correct ? 'hit' : 'miss'">
            <i class="dot" />{{ cur.correct ? '预测正确' : '预测错误' }}
          </div>
          <div class="conf">
            <span class="ck">置信度</span>
            <span class="cbar"><i :style="{ width: (cur.confidence ?? 0) * 100 + '%' }" /></span>
            <span class="cv">{{ confPct(cur.confidence) }}</span>
          </div>
        </div>
      </div>
      <div v-else class="spot-empty">无样本</div>
    </transition>
  </div>
</template>

<style scoped>
.spot {
  width: 300px; flex: none; align-self: stretch;
  background: radial-gradient(120% 90% at 50% 0%, rgba(0, 229, 255, 0.07), transparent 60%),
    linear-gradient(180deg, rgba(9, 20, 40, 0.6), rgba(6, 12, 26, 0.6));
  border: 1px solid var(--tech-border); border-radius: 12px;
  padding: 14px 16px; display: flex; flex-direction: column;
}
.spot-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 12px; }
.lbl { font-size: 16px; font-weight: 700; color: #e9f4ff; letter-spacing: 4px; }
.counter { font-size: 12px; color: var(--tech-text-dim); font-family: 'JetBrains Mono', monospace; }
.spot-body { display: flex; flex-direction: column; flex: 1; }
.sname {
  font-family: 'JetBrains Mono', monospace; font-size: 13px; color: var(--tech-cyan);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 14px;
  display: flex; align-items: center; gap: 8px;
}
.duo { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; }
.cell { flex: 1; }
.k { font-size: 11px; color: var(--tech-text-dim); margin-bottom: 4px; }
.v { font-size: 19px; font-weight: 700; color: #eaf6ff; }
.v.ok { color: #36e3a3; }
.v.bad { color: #ff7a7a; }
.sep { color: var(--tech-text-dim); font-size: 18px; }
.foot { margin-top: auto; display: flex; flex-direction: column; gap: 10px; }
.judge { display: inline-flex; align-items: center; gap: 7px; font-weight: 700; font-size: 14px; }
.judge .dot { width: 9px; height: 9px; border-radius: 50%; background: currentColor; box-shadow: 0 0 8px currentColor; }
.judge.hit { color: #36e3a3; }
.judge.miss { color: #ff7a7a; }
.conf { display: flex; align-items: center; gap: 8px; }
.ck { font-size: 12px; color: var(--tech-text-dim); }
.cbar { flex: 1; height: 5px; border-radius: 3px; background: rgba(125, 148, 184, 0.2); overflow: hidden; }
.cbar i { display: block; height: 100%; background: linear-gradient(90deg, #1f8fff, #00e5ff); }
.cv { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #9fc4ec; min-width: 48px; text-align: right; }
.spot-empty { color: var(--tech-text-dim); font-size: 13px; padding: 30px 0; }

.swap-enter-active, .swap-leave-active { transition: opacity .25s ease, transform .25s ease; }
.swap-enter-from { opacity: 0; transform: translateY(6px); }
.swap-leave-to { opacity: 0; transform: translateY(-6px); }
</style>
