<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { defenseApi } from '../../api/client'
import { isRunning, pickMimetic } from '../../utils/defense'
import { useDashboard } from '../../composables/useDashboard'
import RawJson from '../../components/RawJson.vue'

const { dash, online, loading, refresh } = useDashboard()
const busy = ref('')

const plan = computed(() => dash.value?.latest_defense_plan ?? dash.value?.defense_plan ?? null)
const assignments = computed(() => {
  const a = plan.value?.assignments
  if (!a) return []
  return Object.entries(a).map(([sid, v]: [string, any]) => ({
    sid,
    name: v.display_name ?? v.name ?? '—',
    loc: v.deploy_location ?? '—',
    utility: typeof v.utility === 'number' ? v.utility.toFixed(3) : (v.utility ?? '—'),
  }))
})

// 11 种防御策略目录（来自接口文档）；拟态 3 项的运行状态从 mimetic_status 取
const STRATEGIES = [
  { name: '端口阻断', cat: '传统', node: 's1' },
  { name: '端口过滤', cat: '传统', node: 's1' },
  { name: '网络混淆', cat: '传统', node: 's1+s7' },
  { name: '隔离主机', cat: '传统', node: 's1' },
  { name: '连接限制', cat: '传统', node: 's1' },
  { name: '速率限制', cat: '传统', node: 's7' },
  { name: '流量控制', cat: '传统', node: 's1,s3,s4,s7' },
  { name: '负载均衡', cat: '传统', node: 's1,s3,s4,s7' },
  { name: '跨膜态诱捕蜜罐', cat: '拟态', node: 's7', key: 'mimetic_honeypot' },
  { name: '多模协同入侵检测', cat: '拟态', node: 's1', key: 'mimetic_intrusion_detection' },
  { name: '拟态防御', cat: '拟态', node: 's4', key: 'mimetic_adaptive_defense' },
]
function stratOn(s: any): boolean | undefined {
  if (!s.key) return undefined
  return isRunning(pickMimetic(dash.value, s.key))
}

async function call(kind: 'query' | 'apply' | 'stopAll') {
  busy.value = kind
  try {
    if (kind === 'query') {
      const r = await defenseApi.gameOptimal([1, 3, 4, 7])
      ElMessage.success('已查询最优策略')
      dash.value = { ...dash.value, _last_query: r }
    } else if (kind === 'apply') {
      await defenseApi.gameApply([1, 3, 4, 7])
      ElMessage.success('已下发最优策略')
      refresh()
    } else {
      await defenseApi.stopAll()
      ElMessage.success('已停止全部拟态')
      refresh()
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail ?? '操作失败')
  } finally {
    busy.value = ''
  }
}
</script>

<template>
  <div class="page">
    <div class="head">
      <div>
        <h2 class="title">博弈论选取</h2>
        <p class="sub">Controller 博弈论协同选取 · <span :class="online ? 'ok' : 'off'">{{ online ? '控制器在线' : '控制器离线 (8000)' }}</span></p>
      </div>
      <div class="acts">
        <el-button :loading="busy === 'query'" :disabled="!online" @click="call('query')">查询最优策略</el-button>
        <el-button type="primary" :loading="busy === 'apply'" :disabled="!online" @click="call('apply')">应用最优策略</el-button>
        <el-button type="danger" plain :loading="busy === 'stopAll'" :disabled="!online" @click="call('stopAll')">一键停全部拟态</el-button>
        <el-button text :loading="loading" @click="refresh">刷新</el-button>
      </div>
    </div>

    <!-- 博弈分配 -->
    <div class="tech-panel">
      <div class="p-head">
        <div class="tech-h" style="margin:0">博弈论选取结果</div>
        <span v-if="plan?.attack_type" class="atk">攻击类型：<b>{{ plan.attack_type }}</b></span>
      </div>
      <el-table v-if="assignments.length" :data="assignments" size="small" style="background:transparent">
        <el-table-column prop="sid" label="网元" width="90"><template #default="{ row }">s{{ row.sid }}</template></el-table-column>
        <el-table-column prop="name" label="分配策略" min-width="140" />
        <el-table-column prop="loc" label="部署位置" min-width="180" />
        <el-table-column prop="utility" label="效用值" width="110" align="center">
          <template #default="{ row }"><span class="util">{{ row.utility }}</span></template>
        </el-table-column>
      </el-table>
      <p v-else class="empty">{{ online ? '暂无博弈分配结果，点「查询/应用最优策略」或先模拟攻击触发。' : '控制器离线，无法获取。' }}</p>
    </div>

    <!-- 11 种策略状态 -->
    <div class="tech-panel">
      <div class="tech-h">防御方法运行状态（11 种）</div>
      <div class="grid">
        <div v-for="s in STRATEGIES" :key="s.name" class="chip" :class="{ run: stratOn(s) === true }">
          <span class="dot" :class="stratOn(s) === true ? 'on' : stratOn(s) === false ? 'stop' : 'na'" />
          <span class="sn">{{ s.name }}</span>
          <span class="cat" :class="s.cat === '拟态' ? 'm' : 't'">{{ s.cat }}</span>
          <span class="nd">{{ s.node }}</span>
        </div>
      </div>
    </div>

    <!-- 流量路径 -->
    <div class="tech-panel path">
      <div class="tech-h" style="margin-bottom:10px">流量路径</div>
      <div class="flow">host1 <i>›</i> s1 <i>›</i> s3 <i>›</i> s4 <i>›</i> s7 <i>›</i> server1</div>
    </div>

    <RawJson :data="dash" />
  </div>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: 18px; }
.head { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; flex-wrap: wrap; }
.title { margin: 0 0 6px; font-size: 26px; color: #eaf6ff; text-shadow: 0 0 16px var(--tech-glow); }
.sub { margin: 0; color: var(--tech-text-dim); font-size: 13px; }
.sub .ok { color: #36e3a3; } .sub .off { color: #ff7a7a; }
.acts { display: flex; gap: 10px; flex-wrap: wrap; }
.p-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.atk { font-size: 13px; color: var(--tech-text-dim); } .atk b { color: #ff9a5c; }
.util { font-family: 'JetBrains Mono', monospace; color: var(--tech-cyan); }
.empty { color: var(--tech-text-dim); font-size: 13px; margin: 6px 0 0; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 10px; }
.chip { display: flex; align-items: center; gap: 8px; padding: 9px 12px; border: 1px solid var(--tech-border); border-radius: 8px; background: rgba(255,255,255,.02); }
.chip.run { border-color: rgba(54,227,163,.4); background: rgba(54,227,163,.06); }
.dot { width: 9px; height: 9px; border-radius: 50%; flex: none; }
.dot.on { background: #36e3a3; box-shadow: 0 0 7px #36e3a3; } .dot.stop { background: #6b7a90; } .dot.na { background: #46546b; }
.sn { flex: 1; color: #dcebff; font-size: 13px; }
.cat { font-size: 11px; padding: 1px 7px; border-radius: 4px; }
.cat.t { color: #8fb4dd; border: 1px solid rgba(120,150,200,.3); }
.cat.m { color: var(--tech-cyan); border: 1px solid rgba(0,229,255,.35); }
.nd { font-size: 11px; color: var(--tech-text-dim); font-family: 'JetBrains Mono', monospace; }
.flow { font-family: 'JetBrains Mono', monospace; font-size: 16px; color: #cfe3fb; letter-spacing: 1px; }
.flow i { color: var(--tech-cyan); font-style: normal; margin: 0 4px; }
</style>
