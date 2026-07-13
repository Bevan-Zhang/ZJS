<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api, type NodeInfo } from '../api/client'
import HomeFabricTopo from '../components/HomeFabricTopo.vue'

const nodes = ref<NodeInfo[]>([])
const probing = ref(false)
const enabledNodes = computed(() => nodes.value.filter((n) => n.enabled))

async function load() {
  try {
    nodes.value = await api.listNodes()
    probeAll() // 进入首页自动探测一次，拓扑直接出在线状态
  } catch {
    /* 后端未连接 */
  }
}

async function probeAll() {
  probing.value = true
  try {
    await Promise.all(
      enabledNodes.value.map(async (n) => {
        try {
          const r = await api.probeNode(n.id)
          n.online = r.online
          n.detail = r.detail
        } catch {
          n.online = false
        }
      }),
    )
  } finally {
    probing.value = false
  }
}

onMounted(load)
</script>

<template>
  <!-- 首页使用多模态 Spine–Leaf 拓扑；检测页仍保留原 HomeTopo 联动视图 -->
  <HomeFabricTopo :nodes="nodes" :probing="probing" @probe="probeAll" />
</template>
