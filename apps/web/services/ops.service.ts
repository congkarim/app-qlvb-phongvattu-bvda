import type { SystemStatus, WorkerQueueStatus } from '~/types/ops'
import { useApiClient } from './api'

export function createOpsService() {
  const api = useApiClient()

  return {
    getWorkerQueueStatus() {
      return api<WorkerQueueStatus>('/ops/worker-queue')
    },
    getSystemStatus() {
      return api<SystemStatus>('/ops/system-status')
    }
  }
}
