// 检测展示共用：模态色板类名、置信度格式化

export function modClass(m?: string | null): string {
  const k = (m || '').toLowerCase()
  if (k.includes('ipv6')) return 'mod mod-ipv6'
  if (k.includes('ipv4') || k === 'ip') return 'mod mod-ipv4'
  if (k.includes('mpls')) return 'mod mod-mpls'
  if (k.includes('geo')) return 'mod mod-geo'
  if (k.includes('scion')) return 'mod mod-scion'
  return 'mod mod-na'
}

export function modLabel(m?: string | null): string {
  return m && m.trim() ? m : 'N/A'
}

export function confPct(c?: number | null): string {
  return c == null ? '—' : (c * 100).toFixed(1) + '%'
}

// 去掉样本名常见后缀，展示更紧凑
export function sampleLabel(name: string): string {
  return name.replace(/\.(pcap|pcapng|cap)$/i, '')
}
