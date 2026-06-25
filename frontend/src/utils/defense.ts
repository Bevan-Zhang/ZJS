// 内生防御共用：宽松解析 controller_server_v2 返回的运行状态

export function isRunning(v: any): boolean | undefined {
  if (v == null) return undefined
  if (typeof v === 'boolean') return v
  const raw = typeof v === 'string' ? v : (v.status ?? v.state ?? v.running ?? v.ok ?? '')
  if (raw === true) return true
  const s = String(raw).toLowerCase()
  if (!s) return undefined
  if (/(not.?run|stop|offline|down|inactive|false)/.test(s)) return false
  return /(run|online|active|started|up|true|ok|healthy)/.test(s)
}

// 从 dashboard 里取某个拟态策略的状态对象（字段名可能不同，尽量兼容）
export function pickMimetic(dash: any, key: string): any {
  if (!dash) return undefined
  const m = dash.mimetic_status ?? dash.mimetic ?? dash.mimetics ?? {}
  return m[key]
}
