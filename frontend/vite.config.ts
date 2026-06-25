import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: true,
    port: 5173,
    // 开发期把 /api 代理到本地后端，避免跨域
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
  build: {
    // controller 上 docker 构建内存有限：跳过逐 chunk 的 gzip 体积统计（省内存/提速），
    // 并把大依赖拆成独立 chunk，避免单个 1MB+ 巨块拉高生成阶段峰值内存。
    reportCompressedSize: false,
    chunkSizeWarningLimit: 1500,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return
          if (id.includes('echarts') || id.includes('zrender')) return 'echarts'
          if (id.includes('element-plus') || id.includes('@element-plus')) return 'element-plus'
          return 'vendor'
        },
      },
    },
  },
})
