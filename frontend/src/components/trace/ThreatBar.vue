<script setup lang="ts">
// 运行上下文 + threat 选择器：放在每页顶部，切换 threat 即驱动全局联动。
import { onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { trace, current, loadThreats, selectThreat, triggerDetect } from '../../stores/trace'

const props = defineProps<{ showDetect?: boolean }>()

onMounted(() => {
  if (!trace.threats.length) loadThreats()
})

async function onDetect() {
  const id = await triggerDetect()
  if (id) ElMessage.success(`检测完成，最新威胁 ${id}`)
  else ElMessage.warning(trace.error || '未解析到 threat_id，请看输出')
}
</script>

<template>
  <div class="tech-panel ctx">
    <div class="row">
      <div class="field">
        <label>当前威胁</label>
        <el-select
          :model-value="trace.currentId"
          filterable
          placeholder="选择 threat"
          size="default"
          style="width: 280px"
          :loading="trace.loadingThreats"
          @change="selectThreat"
        >
          <el-option
            v-for="t in trace.threats"
            :key="t.threat_id"
            :label="`${t.threat_id} · ${t.attack_type ?? '-'}`"
            :value="t.threat_id"
          />
        </el-select>
      </div>

      <div class="meta">
        <span>样本 <b>{{ current()?.file_name ?? '—' }}</b></span>
        <span>模态 <b>{{ current()?.modality ?? '—' }}</b></span>
        <span>提交 <b>{{ current()?.timestamp?.replace('T', ' ').slice(0, 19) ?? '—' }}</b></span>
        <span>
          API
          <b :class="trace.apiOnline ? 'ok' : 'bad'">
            {{ trace.apiOnline === null ? '…' : trace.apiOnline ? '在线' : '离线' }}
          </b>
        </span>
        <span v-if="trace.graph">语义来源 <b class="src">{{ trace.graph.source }}</b></span>
      </div>

      <span class="spacer" />
      <el-button v-if="props.showDetect" type="primary" :loading="trace.detecting" @click="onDetect">
        触发检测
      </el-button>
      <el-button text :loading="trace.loadingThreats" @click="loadThreats(false)">刷新</el-button>
    </div>
    <p v-if="trace.error" class="err">{{ trace.error }}</p>
  </div>
</template>

<style scoped>
.ctx { margin-bottom: 18px; }
.row { display: flex; align-items: center; gap: 18px; flex-wrap: wrap; }
.field { display: flex; align-items: center; gap: 8px; }
.field label { color: var(--tech-text-dim); font-size: 13px; }
.meta { display: flex; gap: 18px; flex-wrap: wrap; color: var(--tech-text-dim); font-size: 13px; }
.meta b { color: #eaf6ff; font-weight: 600; }
.meta b.ok { color: var(--tech-cyan); }
.meta b.bad { color: #ff8a80; }
.meta b.src { color: var(--tech-cyan); }
.spacer { flex: 1; }
.err { color: #ff8a80; margin: 10px 0 0; font-size: 13px; }
</style>
