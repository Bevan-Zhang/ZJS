<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api, type DetectionResult } from '../api/client'
import SampleSpotlight from './SampleSpotlight.vue'
import DetectionStatsChart from './DetectionStatsChart.vue'
import ModalityPieChart from './ModalityPieChart.vue'

// file：本页只展示该结果 CSV（如 results_variant.csv）；为空则展示全部
const props = defineProps<{ file?: string }>()

const loading = ref(false)
const result = ref<DetectionResult | null>(null)

async function view() {
  loading.value = true
  try {
    result.value = await api.getDetectionResults(props.file || undefined)
    if (result.value.file_count === 0) ElMessage.warning(props.file ? `未找到结果文件：${props.file}` : '结果目录暂无 CSV 文件')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail ?? '读取结果失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="results">
    <div class="r-head">
      <div>
        <div class="r-title">检测结果</div>
        <div v-if="result && result.file_count" class="r-sub">
          {{ result.file_count }} 个结果文件 · 合计 {{ result.total.toLocaleString() }} 条样本 ·
          总准确率 <b>{{ result.accuracy }}%</b>
        </div>
        <div v-else class="r-sub">{{ file ? '本页绑定 ' + file + '，' : '' }}点「查看结果」展示攻击类型分布、模态分布与逐样本明细。</div>
      </div>
      <el-button type="primary" :loading="loading" @click="view">查看结果</el-button>
    </div>

    <template v-if="result && result.file_count">
      <DetectionStatsChart :files="result.files" />
      <ModalityPieChart :files="result.files" />
    </template>

    <div v-for="f in (result?.files ?? [])" :key="f.name" class="file-card">
      <div class="fc-name">
        <span class="fc-ico" />{{ f.name }}
      </div>
      <div class="fc-body">
        <div class="tiles">
          <div class="tile">
            <div class="num">{{ f.total.toLocaleString() }}</div>
            <div class="cap">检测样本数</div>
          </div>
          <div class="tile">
            <div class="num">{{ f.correct.toLocaleString() }}</div>
            <div class="cap">检测正确样本数</div>
          </div>
          <div class="tile acc">
            <div class="num">{{ f.accuracy }}<span class="pct">%</span></div>
            <div class="cap">准确率</div>
            <div class="ring"><i :style="{ width: f.accuracy + '%' }" /></div>
          </div>
        </div>
        <SampleSpotlight :samples="f.samples" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.results { display: flex; flex-direction: column; gap: 18px; }
.r-head {
  display: flex; justify-content: space-between; align-items: flex-start;
  background: var(--tech-panel); border: 1px solid var(--tech-border); border-radius: 12px; padding: 16px 18px;
}
.r-title { font-size: 17px; font-weight: 700; color: #e9f4ff; }
.r-sub { color: var(--tech-text-dim); font-size: 13px; margin-top: 5px; }
.r-sub b { color: var(--tech-cyan); }

.file-card {
  background: linear-gradient(180deg, rgba(14, 28, 54, 0.5), rgba(8, 16, 32, 0.5));
  border: 1px solid var(--tech-border); border-radius: 14px; padding: 16px 18px;
}
.fc-name {
  display: flex; align-items: center; gap: 10px; font-size: 15px; font-weight: 600; color: #e9f4ff;
  font-family: 'JetBrains Mono', monospace; margin-bottom: 16px;
}
.fc-ico {
  width: 10px; height: 16px; border-radius: 2px;
  background: linear-gradient(180deg, var(--tech-cyan), #1f6fff); box-shadow: 0 0 10px rgba(0, 229, 255, .5);
}
.fc-body { display: flex; gap: 16px; align-items: stretch; }
.tiles { flex: 1; display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.tile {
  position: relative; text-align: center; padding: 22px 10px;
  background: rgba(0, 229, 255, 0.03); border: 1px solid var(--tech-border); border-radius: 10px;
  display: flex; flex-direction: column; justify-content: center;
}
.num { font-size: 34px; font-weight: 700; color: #eef7ff; font-family: 'JetBrains Mono', monospace; line-height: 1.05; }
.tile.acc .num { color: var(--tech-cyan); text-shadow: 0 0 16px var(--tech-glow); }
.num .pct { font-size: 18px; margin-left: 1px; }
.cap { color: var(--tech-text-dim); font-size: 13px; margin-top: 8px; }
.ring { position: absolute; left: 14px; right: 14px; bottom: 12px; height: 3px; border-radius: 2px; background: rgba(125, 148, 184, .18); overflow: hidden; }
.ring i { display: block; height: 100%; background: linear-gradient(90deg, #1f8fff, #00e5ff); }

@media (max-width: 1100px) {
  .fc-body { flex-direction: column; }
}
</style>
