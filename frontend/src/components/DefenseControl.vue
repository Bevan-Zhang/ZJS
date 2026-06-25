<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { defenseApi } from '../api/client'

const props = defineProps<{
  name: string
  strategy: string
  node: string
  ip: string
  running?: boolean
  online: boolean
}>()
const emit = defineEmits<{ (e: 'changed'): void }>()

const busy = ref('')

async function act(kind: 'start' | 'stop') {
  busy.value = kind
  try {
    await (kind === 'start' ? defenseApi.start(props.strategy) : defenseApi.stop(props.strategy))
    ElMessage.success(kind === 'start' ? '已发送启动指令' : '已发送停止指令')
    emit('changed')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail ?? '操作失败')
  } finally {
    busy.value = ''
  }
}

const stateText = () => (!props.online ? '控制器离线' : props.running === undefined ? '状态未知' : props.running ? '运行中' : '已停止')
const stateCls = () => (!props.online ? 's-off' : props.running ? 's-on' : props.running === false ? 's-stop' : 's-unknown')
</script>

<template>
  <div class="dc">
    <div class="left">
      <span class="light" :class="stateCls()" />
      <div>
        <div class="name">{{ name }}</div>
        <div class="loc">{{ node }} · <span class="ip">{{ ip }}</span> · <span class="st" :class="stateCls()">{{ stateText() }}</span></div>
      </div>
    </div>
    <div class="ctl">
      <el-button type="success" :loading="busy === 'start'" :disabled="!online || running === true" @click="act('start')">
        ▶ 启动
      </el-button>
      <el-button type="danger" plain :loading="busy === 'stop'" :disabled="!online || running === false" @click="act('stop')">
        ■ 停止
      </el-button>
      <el-button text :icon="undefined" @click="emit('changed')">刷新</el-button>
    </div>
  </div>
</template>

<style scoped>
.dc {
  display: flex; justify-content: space-between; align-items: center;
  background: linear-gradient(90deg, rgba(10, 22, 44, 0.7), rgba(8, 16, 32, 0.5));
  border: 1px solid var(--tech-border); border-radius: 12px; padding: 16px 20px;
}
.left { display: flex; align-items: center; gap: 16px; }
.light { width: 16px; height: 16px; border-radius: 50%; flex: none; }
.light.s-on { background: #36e3a3; box-shadow: 0 0 14px #36e3a3; animation: pulse 1.6s infinite; }
.light.s-stop { background: #6b7a90; }
.light.s-off { background: #ff7a7a; box-shadow: 0 0 12px rgba(255,122,122,.6); }
.light.s-unknown { background: #ffb648; }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: .4; } }
.name { font-size: 18px; font-weight: 700; color: #eaf6ff; }
.loc { font-size: 13px; color: var(--tech-text-dim); margin-top: 3px; }
.ip { font-family: 'JetBrains Mono', monospace; }
.st { font-weight: 600; }
.st.s-on { color: #36e3a3; } .st.s-stop { color: #9fb0c8; } .st.s-off { color: #ff7a7a; } .st.s-unknown { color: #ffb648; }
.ctl { display: flex; gap: 10px; align-items: center; }
</style>
