import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { menu } from '../config/menu'

// 由菜单配置自动生成路由：首页用专属看板，溯源感知用专属三页，其它子功能用通用功能页
const routes: RouteRecordRaw[] = [{ path: '/', redirect: '/home' }]

// 溯源感知三页 → 专属视图（不走通用 ModulePage，以承载 threat 联动）
const traceViews: Record<string, () => Promise<any>> = {
  '/trace/overview': () => import('../views/TraceOverview.vue'),
  '/trace/analysis': () => import('../views/TraceAnalysis.vue'),
  '/trace/graph': () => import('../views/TraceGraph.vue'),
}

// 内生安全主动防御四页 → 专属视图（代理 controller_server_v2）
const defenseViews: Record<string, () => Promise<any>> = {
  '/defense/mimic-detect': () => import('../views/defense/MimicDetect.vue'),
  '/defense/mimic-adaptive': () => import('../views/defense/MimicAdaptive.vue'),
  '/defense/mimic-honeypot': () => import('../views/defense/MimicHoneypot.vue'),
  '/defense/game-theory': () => import('../views/defense/GameTheory.vue'),
}

for (const group of menu) {
  for (const child of group.children) {
    routes.push({
      path: child.path,
      name: child.path,
      component:
        child.path === '/home'
          ? () => import('../views/HomeView.vue')
          : traceViews[child.path]
            ? traceViews[child.path]
            : defenseViews[child.path]
              ? defenseViews[child.path]
              : () => import('../views/ModulePage.vue'),
      meta: {
        title: child.title, desc: child.desc, group: group.title,
        presets: child.presets ?? [], realRun: child.realRun ?? false, bindMain: child.bindMain ?? false,
        resultFile: child.resultFile ?? '',
      },
    })
  }
}

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
