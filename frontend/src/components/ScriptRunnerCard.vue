<script setup lang="ts">
import { nextTick, onUnmounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { api, type PresetInfo, type TaskInfo } from '../api/client'

// 单个脚本的独立控制台：运行 + 结束 + 实时输出（固定高度、内部滚动）
const props = defineProps<{ preset: PresetInfo }>()
const emit = defineEmits<{ (e: 'running', payload: { id: string; running: boolean }): void }>()

const task = ref<TaskInfo | null>(null)
const running = ref(false)
const stopping = ref(false)
const args = ref('') // 可选追加参数，如 --exp variant
const termRef = ref<HTMLElement | null>(null)
let timer: number | undefined

const statusType: Record<string, string> = {
  pending: 'info', running: 'warning', success: 'success', failed: 'danger', error: 'danger',
}
const statusText: Record<string, string> = {
  pending: '待运行', running: '运行中', success: '已完成', failed: '失败', error: '异常',
}

function isTerminal(s: string) {
  return ['success', 'failed', 'error'].includes(s)
}

// 仅当用户已在底部附近时才自动滚到底，方便向上回看历史
async function maybeAutoScroll() {
  const el = termRef.value
  if (!el) return
  const atBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 40
  await nextTick()
  if (atBottom) el.scrollTop = el.scrollHeight
}

async function run() {
  if (running.value) return
  running.value = true
  task.value = null
  try {
    const t = await api.runPreset(props.preset.id, args.value.trim())
    task.value = t
    timer = window.setInterval(async () => {
      const cur = await api.getTask(t.id)
      task.value = cur
      maybeAutoScroll()
      if (isTerminal(cur.status)) {
        window.clearInterval(timer)
        running.value = false
      }
    }, 800)
  } catch (e: any) {
    running.value = false
    ElMessage.error(e?.response?.data?.detail ?? '启动失败')
  }
}

async function stop() {
  stopping.value = true
  try {
    await api.stopPreset(props.preset.id)
    ElMessage.success(`已发送结束指令：${props.preset.name}`)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail ?? '结束失败')
  } finally {
    stopping.value = false
  }
}

watch(running, (v) => emit('running', { id: props.preset.id, running: v }))

onUnmounted(() => timer && window.clearInterval(timer))
</script>

<template>
  <div class="card">
    <div class="card-head">
      <div class="title">{{ preset.name }}</div>
      <span class="node">{{ preset.node_id }}</span>
    </div>
    <div class="meta" :title="preset.desc">{{ preset.desc }}</div>

    <div class="args">
      <span class="args-pre">参数</span>
      <el-input v-model="args" :disabled="running" size="small" placeholder="可选，如 --exp variant" clearable />
    </div>

    <div class="btns">
      <el-button type="primary" :loading="running" @click="run">
        <span class="ico">▶</span>&nbsp;运行
      </el-button>
      <el-button class="stop-btn" :loading="stopping" :disabled="!running" @click="stop">
        <span class="ico">■</span>&nbsp;结束运行
      </el-button>
    </div>

    <!-- 终端窗口 -->
    <div class="console">
      <div class="console-bar">
        <span class="dot d1" /><span class="dot d2" /><span class="dot d3" />
        <span class="console-title">{{ preset.command }}</span>
        <span class="bar-spacer" />
        <span v-if="task" class="exit" v-show="task.exit_code !== null && task.exit_code !== undefined">
          exit {{ task.exit_code }}
        </span>
        <el-tag v-if="task" size="small" effect="dark" :type="(statusType[task.status] as any)">
          {{ statusText[task.status] }}
        </el-tag>
      </div>
      <pre ref="termRef" class="console-body">{{ task ? (task.stdout || (task.status === 'running' ? '⏳ 启动中…' : '')) : '— 尚未运行 —' }}<span v-if="task && task.error" class="err">{{ task.error }}</span></pre>
    </div>
  </div>
</template>

<style scoped>
.card {
  flex: 1 1 340px;
  min-width: 300px;
  background: linear-gradient(180deg, rgba(20, 38, 70, 0.5), rgba(12, 22, 44, 0.5));
  border: 1px solid var(--tech-border);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: inset 0 0 26px rgba(0, 229, 255, 0.05);
}
.card-head { display: flex; justify-content: space-between; align-items: center; }
.title { font-weight: 600; font-size: 15px; color: #e9f4ff; }
.node {
  font-size: 12px; color: var(--tech-cyan);
  border: 1px solid rgba(0, 229, 255, 0.35); border-radius: 6px; padding: 1px 8px;
  background: rgba(0, 229, 255, 0.06);
}
.meta {
  color: var(--tech-text-dim); font-size: 12px; margin: 6px 0 12px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.args { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.args-pre { font-size: 12px; color: var(--tech-text-dim); white-space: nowrap; }
.btns { display: flex; gap: 10px; margin-bottom: 12px; }
.ico { font-size: 11px; }
.stop-btn {
  color: #ff9a9a;
  background: rgba(245, 108, 108, 0.08);
  border-color: rgba(245, 108, 108, 0.4);
}
.stop-btn:hover:not(.is-disabled) { color: #fff; background: rgba(245, 108, 108, 0.85); border-color: transparent; }

/* 终端窗口 */
.console {
  border: 1px solid rgba(120, 160, 220, 0.22);
  border-radius: 10px;
  overflow: hidden;
  background: #0b1426;
}
.console-bar {
  display: flex; align-items: center; gap: 6px;
  height: 30px; padding: 0 12px;
  background: rgba(255, 255, 255, 0.04);
  border-bottom: 1px solid rgba(120, 160, 220, 0.18);
}
.dot { width: 9px; height: 9px; border-radius: 50%; }
.dot.d1 { background: #ff5f57; }
.dot.d2 { background: #febc2e; }
.dot.d3 { background: #28c840; }
.console-title {
  margin-left: 8px; font-size: 12px; color: #7e96bd;
  font-family: 'Consolas', monospace;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 150px;
}
.bar-spacer { flex: 1; }
.exit { font-size: 11px; color: #7e96bd; font-family: monospace; }

.console-body {
  height: 320px;
  overflow-y: auto;
  margin: 0;
  padding: 12px 14px;
  background:
    radial-gradient(120% 80% at 50% 0%, rgba(0, 229, 255, 0.05), transparent 60%),
    linear-gradient(180deg, #0b1426 0%, #091020 100%);
  color: #cbe2ff;
  font-family: 'JetBrains Mono', 'Consolas', 'Courier New', monospace;
  font-size: 12.5px;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-all;
  letter-spacing: 0.2px;
}
.console-body .err { color: #ff9a9a; }
/* 细滚动条 */
.console-body::-webkit-scrollbar { width: 8px; }
.console-body::-webkit-scrollbar-thumb { background: rgba(0, 229, 255, 0.28); border-radius: 4px; }
.console-body::-webkit-scrollbar-thumb:hover { background: rgba(0, 229, 255, 0.5); }
.console-body::-webkit-scrollbar-track { background: transparent; }
</style>
