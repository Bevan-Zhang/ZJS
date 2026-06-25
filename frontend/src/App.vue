<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { menu } from './config/menu'
import { api } from './api/client'

const route = useRoute()
const activePath = computed(() => route.path)

// 顶栏在线网元统计
const onlineCount = ref(0)
const totalCount = ref(0)
onMounted(async () => {
  try {
    const nodes = await api.listNodes()
    totalCount.value = nodes.filter((n) => n.enabled).length
  } catch {
    /* 后端未起时忽略 */
  }
})
</script>

<template>
  <el-container class="app-shell" style="height: 100vh">
    <el-header class="app-header">
      <span class="app-title"><span class="dot" />多模态网络主动防御系统</span>
      <span class="header-spacer" />
      <span class="header-stat">纳管网元 <b>{{ totalCount }}</b></span>
      <span class="header-stat">在线 <b>{{ onlineCount }}</b></span>
    </el-header>
    <el-container>
      <el-aside class="app-aside">
        <el-menu :default-active="activePath" router unique-opened :default-openeds="[menu[0].key]">
          <template v-for="group in menu" :key="group.key">
            <!-- 单子项的组（首页）直接平铺 -->
            <el-menu-item v-if="group.children.length === 1" :index="group.children[0].path">
              <el-icon><component :is="group.icon" /></el-icon>
              <span>{{ group.title }}</span>
            </el-menu-item>
            <!-- 多子项折叠 -->
            <el-sub-menu v-else :index="group.key">
              <template #title>
                <el-icon><component :is="group.icon" /></el-icon>
                <span>{{ group.title }}</span>
              </template>
              <el-menu-item v-for="child in group.children" :key="child.path" :index="child.path">
                {{ child.title }}
              </el-menu-item>
            </el-sub-menu>
          </template>
        </el-menu>
      </el-aside>
      <el-main style="padding: 24px; overflow-y: auto">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
