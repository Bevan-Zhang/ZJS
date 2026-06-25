<script setup lang="ts">
import { computed, ref } from 'vue'
import { isRunning, pickMimetic } from '../../utils/defense'
import { useDashboard } from '../../composables/useDashboard'
import DefenseControl from '../../components/DefenseControl.vue'
import RawJson from '../../components/RawJson.vue'

const { dash, online, refresh } = useDashboard()
const STRATEGY = 'mimetic_intrusion_detection'
const running = computed(() => isRunning(pickMimetic(dash.value, STRATEGY)))

// ---- 异构裁决模型（后端控制上下线）----
interface ModelItem {
  id: number    // 序号 ①~④
  name: string  // 模型原名
  desc: string  // 特征描述
  active: boolean
}
const MODELS = ref<ModelItem[]>([
  { id: 1, name: 'CNN', desc: '卷积特征提取', active: true },
  { id: 2, name: 'GRU', desc: '时序门控推理', active: true },
  { id: 3, name: 'DNN', desc: '深度全连接', active: true },
  { id: 4, name: 'MLP', desc: '多层感知', active: false },
])

const activeModels = computed(() => MODELS.value.filter((m) => m.active))
const dormantModel = computed(() => MODELS.value.find((m) => !m.active))

// ---- 恶意流量捕获列表 ----
interface MalFlow {
  id: number
  time: string
  src: string
  dst: string
  type: string
  verdict: string
}
const malFlows = ref<MalFlow[]>([
  { id: 1, time: '14:32:07', src: '10.0.4.51', dst: '192.168.1.2', type: 'TLS 隧道', verdict: '恶意' },
  { id: 2, time: '14:32:11', src: '10.0.4.88', dst: '192.168.1.2', type: 'DNS 隐蔽', verdict: '恶意' },
  { id: 3, time: '14:32:18', src: '10.0.5.12', dst: '192.168.1.2', type: 'HTTP C2', verdict: '恶意' },
  { id: 4, time: '14:32:25', src: '10.0.4.63', dst: '192.168.1.2', type: 'ICMP 隧道', verdict: '恶意' },
  { id: 5, time: '14:32:31', src: '10.0.6.7',  dst: '192.168.1.2', type: 'SSH 异常', verdict: '恶意' },
  { id: 6, time: '14:32:39', src: '10.0.4.51', dst: '192.168.1.2', type: 'TLS 隧道', verdict: '恶意' },
  { id: 7, time: '14:32:44', src: '10.0.5.99', dst: '192.168.1.2', type: 'DNS 隐蔽', verdict: '恶意' },
  { id: 8, time: '14:32:50', src: '10.0.4.17', dst: '192.168.1.2', type: 'HTTP C2', verdict: '恶意' },
])
</script>

<template>
  <div class="page">
    <h2 class="title">拟态入侵检测</h2>
    <DefenseControl name="拟态入侵检测" :strategy="STRATEGY" node="网元 s1（入口）" ip="192.168.1.2"
      :running="running" :online="online" @changed="refresh" />

    <div class="cols">
      <!-- 左：异构裁决模型 · 4选3 图解 -->
      <div class="tech-panel">
        <div class="tech-h">异构裁决模型</div>
        <p class="tech-sub">4 个异构模型组成裁决阵列，每轮动态选取 3 个上线推理，多数表决判定恶意流量。</p>

        <!-- 流量 → 模型 → 裁决 流程示意 -->
        <div class="flow-diagram">
          <div class="flow-node flow-src">
            <el-icon :size="24"><component is="Upload" /></el-icon>
            <span>多模态流量</span>
          </div>
          <div class="flow-arrow">→</div>
          <div class="flow-models">
            <div
              v-for="m in MODELS"
              :key="m.id"
              class="flow-model"
              :class="{ active: m.active, dormant: !m.active }"
            >
              <span class="fm-num">{{ '①②③④'[m.id - 1] }}</span>
              <span class="fm-name">{{ m.name }}</span>
              <span class="fm-badge">{{ m.active ? '裁决中' : '休眠' }}</span>
            </div>
          </div>
          <div class="flow-arrow">→</div>
          <div class="flow-node flow-dst">
            <el-icon :size="24"><component is="Select" /></el-icon>
            <span>拟态裁决</span>
          </div>
          <div class="flow-arrow">→</div>
          <div class="flow-verdict" :class="running ? 'mal' : 'idle'">
            {{ running ? 'MALICIOUS' : '待启动' }}
          </div>
        </div>

        <p class="rotation-hint">
          当前休眠：<b>{{ dormantModel ? '①②③④'[dormantModel.id - 1] + ' ' + dormantModel.name : '—' }}</b>
          &nbsp;·&nbsp; 后端动态调度，仅上线模型参与裁决
        </p>
      </div>

      <!-- 右：恶意流量捕获统计 -->
      <div class="tech-panel">
        <div class="tech-h">恶意流量捕获</div>
        <div class="stat-row">
          <div class="stat-card mal">
            <div class="stat-num">{{ malFlows.length }}</div>
            <div class="stat-label">恶意流量总数</div>
          </div>
        </div>

        <el-table :data="malFlows" size="small" max-height="340" style="background:transparent;margin-top:12px"
          :row-class-name="()=>'row-mal'">
          <el-table-column prop="time" label="时间" width="90" />
          <el-table-column prop="src" label="源 IP" width="115" />
          <el-table-column prop="dst" label="目的 IP" width="120" />
          <el-table-column prop="type" label="攻击类型" min-width="110" />
          <el-table-column prop="verdict" label="裁决" width="70" align="center">
            <template #default="{ row }">
              <span class="verdict-tag mal">恶意</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <RawJson :data="dash" />
  </div>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: 18px; }
.title { margin: 0; font-size: 26px; color: #eaf6ff; text-shadow: 0 0 16px var(--tech-glow); }
.cols { display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 18px; }
@media (max-width: 960px) { .cols { grid-template-columns: 1fr; } }

/* ===== 流量 → 拟态裁决 流程示意 ===== */
.flow-diagram {
  display: flex; align-items: center; gap: 10px;
  padding: 26px 22px; margin: 14px 0;
  background: linear-gradient(135deg, rgba(0,229,255,.03), rgba(0,229,255,.01));
  border: 1px solid rgba(0,229,255,.12); border-radius: 12px;
  overflow-x: auto;
}
.flow-node {
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  padding: 16px 22px; border-radius: 10px;
  background: rgba(255,255,255,.04); color: var(--tech-cyan);
  font-size: 14px; font-weight: 700; white-space: nowrap;
  border: 1px solid rgba(0,229,255,.18);
  flex-shrink: 0;
}
.flow-arrow { color: var(--tech-cyan); font-size: 24px; font-weight: 700; opacity: .5; flex-shrink: 0; }
.flow-models { display: flex; flex-direction: column; gap: 6px; flex-shrink: 0; }
.flow-model {
  display: flex; flex-direction: row; align-items: center; gap: 12px;
  padding: 10px 16px; border-radius: 8px; font-size: 13px;
  border: 1.5px solid var(--tech-border); min-width: 130px;
  transition: all .5s;
}
.flow-model.active {
  border-color: var(--tech-cyan); background: rgba(0,229,255,.1);
  box-shadow: 0 0 12px rgba(0,229,255,.08);
}
.flow-model.dormant { opacity: .3; border-style: dashed; }
.fm-num { font-size: 22px; color: var(--tech-cyan); font-weight: 700; min-width: 26px; text-align: center; }
.flow-model.dormant .fm-num { color: #6b7a90; }
.fm-name { color: #9fc4ec; font-weight: 600; font-size: 14px; }
.fm-badge { font-size: 12px; color: var(--tech-text-dim); margin-left: auto; }
.flow-model.active .fm-badge { color: #36e3a3; font-weight: 600; }
.flow-model.dormant .fm-badge { color: #6b7a90; }
.flow-dst { background: rgba(255,182,72,.06); border-color: rgba(255,182,72,.25); }
.flow-verdict {
  padding: 16px 24px; border-radius: 8px; font-weight: 700; font-size: 16px; letter-spacing: 3px;
  flex-shrink: 0;
}
.flow-verdict.mal { background: rgba(255,122,122,.12); color: #ff7a7a; border: 1.5px solid rgba(255,122,122,.25); animation: pulse-verdict 1.6s infinite; }
.flow-verdict.idle { background: rgba(255,255,255,.03); color: #6b7a90; border: 1px solid var(--tech-border); }
@keyframes pulse-verdict { 0%,100% { opacity: 1; } 50% { opacity: .55; } }

.rotation-hint { font-size: 12px; color: var(--tech-text-dim); margin-top: 12px; text-align: center; }
.rotation-hint b { color: #ffb648; }

/* ===== 恶意流量统计卡片 ===== */
.stat-row { display: flex; gap: 10px; margin-top: 8px; }
.stat-card {
  flex: 1; text-align: center; padding: 14px 8px; border-radius: 10px;
  border: 1px solid var(--tech-border); background: rgba(255,255,255,.02);
}
.stat-card.mal { border-color: rgba(255,122,122,.3); }
.stat-num { font-size: 28px; font-weight: 700; color: #eaf6ff; font-family: 'JetBrains Mono', monospace; }
.stat-card.mal .stat-num { color: #ff7a7a; }
.stat-label { font-size: 11px; color: var(--tech-text-dim); margin-top: 2px; }

/* ===== 表格覆盖 ===== */
:deep(.row-mal) { background: rgba(255,122,122,.06) !important; }
.verdict-tag { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px; }
.verdict-tag.mal { background: rgba(255,122,122,.18); color: #ff7a7a; }

.tech-sub { color: var(--tech-text-dim); font-size: 12px; margin-bottom: 4px; line-height: 1.6; }
</style>
