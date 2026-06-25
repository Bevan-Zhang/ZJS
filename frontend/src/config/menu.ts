// 侧边栏导航结构 —— 改这里即可增删模块/子功能，路由会自动生成
export interface MenuChild {
  path: string
  title: string
  desc?: string // 功能页副标题/说明
  presets?: string[] // 该页要展示的预设按钮 id（来自 presets.yaml）
  realRun?: boolean // true=按钮真跑代码并回显输出；否则纯展示触发动效
  bindMain?: boolean // true=所有浮标/链路动效都绑定到「模型检测」运行
}

export interface MenuGroup {
  key: string
  title: string
  icon: string // @element-plus/icons-vue 的组件名
  children: MenuChild[]
}

export const menu: MenuGroup[] = [
  {
    key: 'home',
    title: '首页',
    icon: 'Monitor',
    children: [{ path: '/home', title: '态势总览', desc: '网元拓扑、在线状态与最近下发任务' }],
  },
  {
    key: 'traffic',
    title: '加密恶意流量检测',
    icon: 'DataLine',
    children: [
      { path: '/traffic/variant', title: '变种威胁检测', desc: '识别已知威胁的变种加密流量', presets: ['netunit1_main'], realRun: true, bindMain: true },
      { path: '/traffic/unknown', title: '未知攻击检测', desc: '发现未知 / 0day 攻击流量', presets: ['netunit1_main'], realRun: true, bindMain: true },
    ],
  },
  {
    key: 'trace',
    title: '溯源感知',
    icon: 'Connection',
    children: [
      { path: '/trace/overview', title: '检测总览', desc: '系统当前检测到了什么：threat 列表与检测结果' },
      { path: '/trace/analysis', title: '威胁溯源', desc: '从当前威胁回溯攻击阶段、传播路径与证据链' },
      { path: '/trace/graph', title: '意图感知', desc: '结合局部知识图谱感知攻击意图与战术技术' },
    ],
  },
  {
    key: 'defense',
    title: '内生安全主动防御',
    icon: 'Cpu',
    children: [
      { path: '/defense/mimic-detect', title: '拟态入侵检测', desc: 's1 拟态裁决入侵检测' },
      { path: '/defense/mimic-adaptive', title: '拟态自适应防御', desc: 's4 REMI-AIA 自适应防御' },
      { path: '/defense/mimic-honeypot', title: '拟态蜜罐', desc: 's7 拟态蜜罐诱捕' },
      { path: '/defense/game-theory', title: '博弈论选取', desc: 'Controller 博弈论策略选取' },
    ],
  },
]
