<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { api, type PresetInfo } from '../api/client'
import ScriptRunnerCard from './ScriptRunnerCard.vue'

// only：仅展示这些 preset id，并按该顺序排列（左→右）；不传则展示全部
const props = defineProps<{ only?: string[] }>()
const emit = defineEmits<{ (e: 'running-map', map: Record<string, boolean>): void }>()

const presets = ref<PresetInfo[]>([])
const runningMap = reactive<Record<string, boolean>>({})

function onCardRunning(p: { id: string; running: boolean }) {
  runningMap[p.id] = p.running
  emit('running-map', { ...runningMap })
}

async function load() {
  try {
    const all = await api.listPresets()
    if (props.only?.length) {
      const map = new Map(all.map((p) => [p.id, p]))
      presets.value = props.only.map((id) => map.get(id)).filter(Boolean) as PresetInfo[]
    } else {
      presets.value = all
    }
  } catch {
    /* 后端未起 */
  }
}

onMounted(load)
</script>

<template>
  <div class="tech-panel">
    <div class="tech-h">脚本控制台</div>
    <div class="tech-sub">每个脚本独立运行，可同时启动；各窗口实时回显输出，旁边的「结束运行」可随时停止</div>

    <div class="cards">
      <ScriptRunnerCard v-for="p in presets" :key="p.id" :preset="p" @running="onCardRunning" />
      <span v-if="!presets.length" class="tech-sub" style="margin: 0">暂无预设（在 presets.yaml 中配置）</span>
    </div>
  </div>
</template>

<style scoped>
.cards { display: flex; flex-wrap: wrap; gap: 16px; }
</style>
