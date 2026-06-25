<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { trace, current, selectThreat } from '../stores/trace'
import type { TraceThreat } from '../api/client'
import ThreatBar from '../components/trace/ThreatBar.vue'

const keyword = ref('')
const attackFilter = ref('')
const modalityFilter = ref('')
const page = ref(1)
const pageSize = ref(20)

const sevType = (s?: string) =>
  s === 'high' ? 'danger' : s === 'medium' ? 'warning' : s ? 'info' : 'info'

const attackOptions = computed(() =>
  [...new Set(trace.threats.map((item) => item.attack_type).filter(Boolean) as string[])].sort(),
)
const modalityOptions = computed(() =>
  [...new Set(trace.threats.map((item) => item.modality).filter(Boolean) as string[])].sort(),
)
const filteredThreats = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  return trace.threats.filter((item) => {
    if (attackFilter.value && item.attack_type !== attackFilter.value) return false
    if (modalityFilter.value && item.modality !== modalityFilter.value) return false
    if (!q) return true
    return [
      item.threat_id,
      item.file_name,
      item.attack_type,
      item.stage,
      item.modality,
    ].some((value) => String(value ?? '').toLowerCase().includes(q))
  })
})
const pagedThreats = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filteredThreats.value.slice(start, start + pageSize.value)
})

watch([keyword, attackFilter, modalityFilter, pageSize], () => {
  page.value = 1
})

const rowClass = ({ row }: { row: TraceThreat }) =>
  row.threat_id === trace.currentId ? 'cur-row' : ''
const onRowClick = (row: TraceThreat) => selectThreat(row.threat_id)
</script>

<template>
  <div>
    <h2 class="page-title">检测总览</h2>
    <p class="page-desc">展示网元3当前批次提交的 120 条真实多模态流量检测结果。</p>

    <ThreatBar :show-detect="true" />

    <div class="filters tech-panel">
      <el-input v-model="keyword" clearable placeholder="搜索 threat_id、PCAP、攻击类型或阶段" />
      <el-select v-model="attackFilter" clearable placeholder="全部攻击类型">
        <el-option v-for="item in attackOptions" :key="item" :label="item" :value="item" />
      </el-select>
      <el-select v-model="modalityFilter" clearable placeholder="全部模态">
        <el-option v-for="item in modalityOptions" :key="item" :label="item" :value="item" />
      </el-select>
      <span class="batch-count">本批 {{ trace.total }} 条，当前匹配 {{ filteredThreats.length }} 条</span>
    </div>

    <div class="grid">
      <div class="tech-panel">
        <div class="tech-h">威胁列表 <span class="cnt">点击任意行联动完整分析</span></div>
        <el-table
          :data="pagedThreats"
          size="small"
          height="500"
          v-loading="trace.loadingThreats"
          highlight-current-row
          :row-class-name="rowClass"
          @row-click="onRowClick"
          style="background: transparent; cursor: pointer"
        >
          <el-table-column prop="threat_id" label="threat_id" min-width="205" show-overflow-tooltip />
          <el-table-column prop="file_name" label="PCAP 文件" min-width="210" show-overflow-tooltip />
          <el-table-column prop="attack_type" label="攻击类型" width="115" />
          <el-table-column prop="stage" label="阶段" width="145" show-overflow-tooltip />
          <el-table-column prop="modality" label="模态" width="90" />
          <el-table-column label="置信度" width="90" align="center">
            <template #default="{ row }">{{ row.ml_confidence ?? '-' }}</template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          class="pagination"
          background
          layout="total, sizes, prev, pager, next"
          :page-sizes="[10, 20, 50, 100]"
          :total="filteredThreats.length"
        />
      </div>

      <div class="tech-panel">
        <div class="tech-h">当前威胁详情</div>
        <template v-if="current()">
          <dl class="kv">
            <div><dt>threat_id</dt><dd class="mono">{{ current()!.threat_id }}</dd></div>
            <div><dt>PCAP 文件</dt><dd>{{ current()!.file_name ?? '—' }}</dd></div>
            <div><dt>攻击类型</dt><dd><b class="cyan">{{ current()!.attack_type ?? '—' }}</b></dd></div>
            <div><dt>攻击阶段</dt><dd>{{ current()!.stage ?? '—' }}</dd></div>
            <div><dt>阶段来源</dt><dd>{{ current()!.stage_source ?? '—' }}</dd></div>
            <div><dt>阶段置信度</dt><dd>{{ current()!.stage_confidence ?? '—' }}</dd></div>
            <div>
              <dt>严重程度</dt>
              <dd><el-tag :type="sevType(current()!.severity)" size="small" effect="dark">{{ current()!.severity ?? '—' }}</el-tag></dd>
            </div>
            <div><dt>ML 置信度</dt><dd><b class="cyan">{{ current()!.ml_confidence ?? '—' }}</b></dd></div>
            <div><dt>预测类别</dt><dd>{{ current()!.ml_class ?? '—' }}</dd></div>
            <div><dt>模态</dt><dd>{{ current()!.modality ?? '—' }}</dd></div>
            <div><dt>检测时间</dt><dd class="mono">{{ current()!.timestamp?.replace('T', ' ').slice(0, 19) ?? '—' }}</dd></div>
          </dl>
          <div class="evidence">
            <div class="evidence-title">阶段推断依据</div>
            <el-tag
              v-for="item in current()!.stage_evidence ?? []"
              :key="item"
              size="small"
              effect="plain"
            >{{ item }}</el-tag>
            <span v-if="!(current()!.stage_evidence?.length)" class="dim">暂无阶段证据</span>
          </div>
        </template>
        <p v-else class="tech-sub" style="margin: 0">请从左侧选择一条真实威胁记录。</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-title { margin: 0 0 6px; font-size: 26px; color: #eaf6ff; text-shadow: 0 0 16px var(--tech-glow); }
.page-desc { color: var(--tech-text-dim); margin: 0 0 18px; }
.filters { display: grid; grid-template-columns: minmax(280px, 1fr) 180px 150px auto; gap: 12px; align-items: center; margin-bottom: 18px; }
.batch-count { color: var(--tech-text-dim); white-space: nowrap; font-size: 13px; }
.grid { display: grid; grid-template-columns: minmax(0, 1.8fr) minmax(320px, 0.8fr); gap: 18px; }
.cnt { color: var(--tech-text-dim); font-size: 13px; font-weight: 400; margin-left: 8px; }
.cyan { color: var(--tech-cyan); }
.kv { margin: 0; }
.kv > div { display: flex; padding: 8px 0; border-bottom: 1px dashed var(--tech-border); }
.kv dt { width: 96px; color: var(--tech-text-dim); font-size: 13px; flex-shrink: 0; }
.kv dd { margin: 0; color: #eaf6ff; font-size: 14px; word-break: break-all; }
.mono { font-family: 'Consolas', monospace; }
.pagination { justify-content: flex-end; margin-top: 14px; }
.evidence { margin-top: 14px; display: flex; flex-wrap: wrap; gap: 6px; }
.evidence-title { width: 100%; color: var(--tech-text-dim); font-size: 13px; margin-bottom: 2px; }
.dim { color: var(--tech-text-dim); font-size: 13px; }
:deep(.cur-row) { background: rgba(0, 229, 255, 0.1) !important; }
@media (max-width: 1100px) {
  .filters { grid-template-columns: 1fr 1fr; }
  .grid { grid-template-columns: 1fr; }
}
</style>
