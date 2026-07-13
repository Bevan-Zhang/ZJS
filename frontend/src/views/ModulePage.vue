<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api, type NodeInfo } from '../api/client'
import DispatchPanel from '../components/DispatchPanel.vue'
import ScriptButtons from '../components/ScriptButtons.vue'
import PresetRunner from '../components/PresetRunner.vue'
import HomeFabricTopo from '../components/HomeFabricTopo.vue'
import DetectionResultPanel from '../components/DetectionResultPanel.vue'
import RollTicker from '../components/RollTicker.vue'

const route = useRoute()
const title = computed(() => (route.meta.title as string) ?? '功能')
const desc = computed(() => (route.meta.desc as string) ?? '')
const group = computed(() => (route.meta.group as string) ?? '')
const presets = computed(() => (route.meta.presets as string[]) ?? [])
const realRun = computed(() => route.meta.realRun === true) // 真跑代码+控制台
const bindMain = computed(() => route.meta.bindMain === true) // 所有动效绑定到 模型检测

// 脚本运行状态（PresetRunner 真跑 / ScriptButtons 纯展示，都给一个 map）
const active = ref<Record<string, boolean>>({})
const mainActive = computed(() => !!active.value['netunit1_main'])
// 动效：bindMain 时全部跟随 模型检测；否则按各脚本
const linkFlow = computed(() => (bindMain.value ? mainActive.value : !!active.value['host1_sender']))
const listenOn = computed(() => (bindMain.value ? mainActive.value : !!active.value['netunit1_listener']))
const detectOn = computed(() => mainActive.value)

// 拓扑节点 + 在线探测
const nodes = ref<NodeInfo[]>([])
const probing = ref(false)
async function loadNodes() {
  try {
    nodes.value = await api.listNodes()
    probeAll()
  } catch {
    /* 后端未连接 */
  }
}
async function probeAll() {
  probing.value = true
  try {
    await Promise.all(
      nodes.value.filter((n) => n.enabled).map(async (n) => {
        try {
          const r = await api.probeNode(n.id)
          n.online = r.online
        } catch {
          n.online = false
        }
      }),
    )
  } finally {
    probing.value = false
  }
}

function maybeLoad() {
  active.value = {}
  if (presets.value.length) loadNodes()
}
onMounted(maybeLoad)
watch(() => route.path, maybeLoad)
</script>

<template>
  <div>
    <!-- 检测页：展示态 -->
    <template v-if="presets.length">
      <h2 class="page-title only-title">{{ title }}</h2>

      <!-- realRun：左半=模型检测控制台，右半=实时检测流 -->
      <div v-if="realRun" class="split">
        <div class="split-cell"><PresetRunner :only="presets" @running-map="(m) => (active = m)" /></div>
        <div class="split-cell"><RollTicker /></div>
      </div>
      <div v-else style="margin-bottom: 20px">
        <ScriptButtons :only="presets" @change="(m) => (active = m)" />
      </div>

      <HomeFabricTopo
        :nodes="nodes" :probing="probing" mode="detection"
        :link-flow="linkFlow" :listen-on="listenOn" :detect-on="detectOn"
        @probe="probeAll"
      />

      <div style="margin-top: 20px">
        <DetectionResultPanel />
      </div>
    </template>

    <!-- 其它页面：保留说明 + 通用下发入口 -->
    <template v-else>
      <div class="page-head">
        <div class="crumb">{{ group }}</div>
        <h2 class="page-title">{{ title }}</h2>
        <p class="page-desc">{{ desc }}</p>
      </div>
      <div class="tech-panel" style="margin-bottom: 20px">
        <div class="tech-h">功能说明</div>
        <p class="tech-sub" style="margin: 0">「{{ title }}」模块。下方可向网元下发命令或脚本。</p>
      </div>
      <DispatchPanel :title="`${title} · 网元下发`" />
    </template>
  </div>
</template>

<style scoped>
.page-head { margin-bottom: 20px; }
.crumb { color: var(--tech-text-dim); font-size: 13px; letter-spacing: 1px; }
.page-title { margin: 4px 0 6px; font-size: 26px; color: #eaf6ff; text-shadow: 0 0 16px var(--tech-glow); }
.page-desc { color: var(--tech-text-dim); margin: 0; }
.only-title { margin: 0 0 20px; }
.split { display: flex; gap: 18px; align-items: stretch; margin-bottom: 20px; }
.split-cell { flex: 1 1 0; min-width: 0; }
@media (max-width: 1000px) { .split { flex-direction: column; } }
</style>
