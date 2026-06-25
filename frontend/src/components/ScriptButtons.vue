<script setup lang="ts">
import { reactive } from 'vue'

// 纯展示控制：按钮不真正跑代码，只切换状态驱动拓扑动效（真实脚本走命令行手动跑）
const props = defineProps<{ only?: string[] }>()
const emit = defineEmits<{ (e: 'change', active: Record<string, boolean>): void }>()

interface ScriptDef { key: string; name: string; node: string }
const ALL: ScriptDef[] = [
  { key: 'host1_sender', name: '流量发送 (sender.py)', node: 'host1' },
  { key: 'netunit1_listener', name: '流量监听 (host1_listener.py)', node: '网元1' },
  { key: 'netunit1_main', name: '检测模型 (main.py)', node: '网元1' },
]
const scripts = props.only?.length
  ? (props.only.map((k) => ALL.find((s) => s.key === k)).filter(Boolean) as ScriptDef[])
  : ALL

const active = reactive<Record<string, boolean>>({})
function run(k: string) { active[k] = true; emit('change', { ...active }) }
function stop(k: string) { active[k] = false; emit('change', { ...active }) }
</script>

<template>
  <div class="tech-panel">
    <div class="tech-h">脚本控制台</div>
    <div class="cards">
      <div v-for="s in scripts" :key="s.key" class="sc-card" :class="{ on: active[s.key] }">
        <div class="card-head">
          <div class="title">{{ s.name }}</div>
          <span class="node">{{ s.node }}</span>
        </div>
        <div class="btns">
          <el-button type="primary" :disabled="active[s.key]" @click="run(s.key)">
            <span v-if="active[s.key]">● 运行中</span>
            <span v-else>▶ 运行</span>
          </el-button>
          <el-button class="stop-btn" :disabled="!active[s.key]" @click="stop(s.key)">■ 结束运行</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cards { display: flex; flex-wrap: wrap; gap: 16px; }
.sc-card {
  flex: 1 1 320px; min-width: 280px;
  background: linear-gradient(180deg, rgba(20, 38, 70, 0.5), rgba(12, 22, 44, 0.5));
  border: 1px solid var(--tech-border); border-radius: 12px; padding: 16px 18px;
  transition: border-color .25s, box-shadow .25s;
}
.sc-card.on { border-color: var(--tech-cyan); box-shadow: 0 0 18px rgba(0, 229, 255, 0.18); }
.card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.title { font-weight: 600; font-size: 15px; color: #e9f4ff; }
.node {
  font-size: 12px; color: var(--tech-cyan); padding: 1px 8px;
  border: 1px solid rgba(0, 229, 255, 0.35); border-radius: 6px; background: rgba(0, 229, 255, 0.06);
}
.btns { display: flex; gap: 10px; }
.stop-btn { color: #ff9a9a; background: rgba(245, 108, 108, 0.08); border-color: rgba(245, 108, 108, 0.4); }
.stop-btn:hover:not(.is-disabled) { color: #fff; background: rgba(245, 108, 108, 0.85); border-color: transparent; }
</style>
