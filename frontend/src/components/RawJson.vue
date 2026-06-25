<script setup lang="ts">
defineProps<{ data: any; title?: string }>()
</script>

<template>
  <el-collapse class="raw-wrap">
    <el-collapse-item :title="title ?? '接口原始返回（调试用）'">
      <pre class="raw">{{ data ? JSON.stringify(data, null, 2) : '— 无数据 —' }}</pre>
    </el-collapse-item>
  </el-collapse>
</template>

<style scoped>
.raw-wrap { --el-collapse-border-color: var(--tech-border); background: transparent; border: none; }
.raw {
  margin: 0; max-height: 320px; overflow: auto; padding: 10px 12px;
  background: #02060f; border: 1px solid var(--tech-border); border-radius: 6px;
  color: #9fc4ec; font-family: 'JetBrains Mono', 'Consolas', monospace; font-size: 12px;
}
</style>
