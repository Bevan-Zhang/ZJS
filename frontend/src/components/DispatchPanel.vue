<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api, type NodeInfo, type TaskInfo } from '../api/client'

// 可选：限定可下发的节点角色；默认全部启用节点
const props = defineProps<{ title?: string }>()

const nodes = ref<NodeInfo[]>([])
const selected = ref<string>('')
const mode = ref<'command' | 'script'>('command')
const command = ref('')
const script = ref({ filename: 'task.py', content: '', remote_dir: '/tmp', run_cmd: 'python3 /tmp/task.py' })
const running = ref(false)
const result = ref<TaskInfo | null>(null)
let timer: number | undefined

const statusType: Record<string, string> = {
  pending: 'info', running: 'warning', success: 'success', failed: 'danger', error: 'danger',
}

async function loadNodes() {
  try {
    nodes.value = (await api.listNodes()).filter((n) => n.enabled)
    if (!selected.value && nodes.value.length) selected.value = nodes.value[0].id
  } catch {
    ElMessage.warning('后端未连接，节点列表暂不可用')
  }
}

function poll(id: number) {
  timer = window.setInterval(async () => {
    const t = await api.getTask(id)
    result.value = t
    if (['success', 'failed', 'error'].includes(t.status)) {
      window.clearInterval(timer)
      running.value = false
    }
  }, 1000)
}

async function submit() {
  if (!selected.value) return ElMessage.warning('请先选择目标网元')
  running.value = true
  result.value = null
  try {
    const task =
      mode.value === 'command'
        ? await api.execCommand(selected.value, command.value)
        : await api.execScript(selected.value, script.value)
    result.value = task
    poll(task.id)
  } catch (e: any) {
    running.value = false
    ElMessage.error(e?.response?.data?.detail ?? '下发失败')
  }
}

onMounted(loadNodes)
onUnmounted(() => timer && window.clearInterval(timer))
</script>

<template>
  <div class="tech-panel">
    <div class="tech-h">{{ props.title ?? '指令下发' }}</div>
    <div class="tech-sub">选择目标网元，下发 shell 命令或脚本，实时回收执行状态</div>

    <el-form label-width="84px">
      <el-form-item label="目标网元">
        <el-select v-model="selected" placeholder="选择网元" style="width: 260px">
          <el-option v-for="n in nodes" :key="n.id" :label="`${n.name}（${n.ssh_host}）`" :value="n.id" />
        </el-select>
        <el-radio-group v-model="mode" style="margin-left: 16px">
          <el-radio-button value="command">命令</el-radio-button>
          <el-radio-button value="script">脚本</el-radio-button>
        </el-radio-group>
      </el-form-item>

      <el-form-item v-if="mode === 'command'" label="命令">
        <el-input v-model="command" type="textarea" :rows="3" placeholder="例如：uname -a && uptime" />
      </el-form-item>
      <template v-else>
        <el-form-item label="文件名">
          <el-input v-model="script.filename" style="width: 260px" />
        </el-form-item>
        <el-form-item label="脚本内容">
          <el-input v-model="script.content" type="textarea" :rows="5" placeholder="脚本文本" />
        </el-form-item>
        <el-form-item label="执行命令">
          <el-input v-model="script.run_cmd" placeholder="留空则仅上传" />
        </el-form-item>
      </template>

      <el-form-item>
        <el-button type="primary" :loading="running" @click="submit">提交下发</el-button>
      </el-form-item>
    </el-form>

    <div v-if="result">
      <div style="margin-bottom: 8px">
        任务 #{{ result.id }}
        <el-tag size="small" :type="(statusType[result.status] as any)">{{ result.status }}</el-tag>
        <span v-if="result.exit_code !== null && result.exit_code !== undefined" class="header-stat">
          exit=<b>{{ result.exit_code }}</b>
        </span>
      </div>
      <pre v-if="result.stdout" class="tech-out">{{ result.stdout }}</pre>
      <pre v-if="result.stderr" class="tech-out err">{{ result.stderr }}</pre>
      <pre v-if="result.error" class="tech-out err">{{ result.error }}</pre>
    </div>
  </div>
</template>
