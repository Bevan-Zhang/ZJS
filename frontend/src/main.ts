import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import './styles/theme.css'

const app = createApp(App)

// 全量注册图标，菜单可用字符串名引用
for (const [name, comp] of Object.entries(ElementPlusIconsVue)) {
  app.component(name, comp as any)
}

// 启用 Element Plus 暗色模式
document.documentElement.classList.add('dark')

app.use(ElementPlus).use(router).mount('#app')
