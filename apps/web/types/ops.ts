export interface WorkerQueueStatus {
  status: string
  pending_ready: number
  pending_delayed: number
  running: number
  failed: number
  completed: number
  active: number
}

export interface StatusDetail {
  status: string
  name: string
  details: Record<string, string | number | boolean | null>
  error?: string | null
}

export interface SystemStatus {
  status: string
  ocr: StatusDetail
  embedding: StatusDetail
  qdrant: StatusDetail
  llm: StatusDetail
  worker_queue: WorkerQueueStatus
}
