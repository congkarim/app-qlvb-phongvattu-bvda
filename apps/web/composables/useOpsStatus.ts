import type { SystemStatus } from '~/types/ops'
import { createOpsService } from '~/services/ops.service'

export function useOpsStatus() {
  const status = ref<SystemStatus | null>(null)
  const loading = ref(false)
  const error = ref('')
  const service = createOpsService()

  async function fetchSystemStatus() {
    loading.value = true
    error.value = ''
    try {
      status.value = await service.getSystemStatus()
      return status.value
    } catch {
      error.value = 'Không tải được trạng thái hệ thống'
      return null
    } finally {
      loading.value = false
    }
  }

  return {
    status,
    loading,
    error,
    fetchSystemStatus
  }
}
