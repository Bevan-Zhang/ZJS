import { onBeforeUnmount, onMounted, ref } from 'vue'
import { defenseApi } from '../api/client'

// 周期拉取 controller_server_v2 的 /defense/dashboard；连不上则 online=false
export function useDashboard(intervalMs = 12000) {
  const dash = ref<any>(null)
  const online = ref(true)
  const loading = ref(false)
  let timer: number | undefined

  async function refresh() {
    loading.value = true
    try {
      dash.value = await defenseApi.dashboard()
      online.value = true
    } catch {
      online.value = false
    } finally {
      loading.value = false
    }
  }

  onMounted(() => {
    refresh()
    timer = window.setInterval(refresh, intervalMs)
  })
  onBeforeUnmount(() => timer && window.clearInterval(timer))

  return { dash, online, loading, refresh }
}
