<script setup lang="ts">
import { formatDateTime, formatFileSize } from '~/utils/format'

const route = useRoute()
const {
  document,
  loading,
  reprocessLoading,
  sourceFileLoading,
  error,
  fetchDocument,
  reprocessDocument,
  addSourceFiles,
  reorderSourceFiles,
  deleteSourceFile
} = useDocuments()
let pollTimer: ReturnType<typeof setInterval> | undefined
const reprocessReason = ref('')
const selectedSourceFiles = ref<File[]>([])
const lastDetailRefreshedAt = ref<Date | null>(null)

const processingStatuses = new Set([
  'ocr_pending',
  'ocr_running',
  'reprocess_pending',
  'reprocess_running',
  'chunking'
])

const documentId = computed(() => {
  const value = route.params.id
  return Array.isArray(value) ? value.join('/') : String(value)
})

const sortedOcrJobs = computed(() => {
  return [...(document.value?.ocr_jobs || [])].sort((a, b) => {
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  })
})

const sortedAuditLogs = computed(() => {
  return [...(document.value?.audit_logs || [])].sort((a, b) => {
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  })
})

const sourceFiles = computed(() => {
  return [...(document.value?.files || [])].sort((a, b) => {
    return a.file_order - b.file_order || new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  })
})

const sourceSubtitle = computed(() => {
  if (!document.value) return ''
  if (sourceFiles.value.length) return `${sourceFiles.value.length} tệp nguồn`
  return document.value.original_filename
})

const shouldPoll = computed(() => {
  const status = document.value?.status
  return Boolean(status && processingStatuses.has(status))
})

const canReprocess = computed(() => {
  const status = document.value?.status
  return Boolean(status && !processingStatuses.has(status))
})

const canManageSourceFiles = computed(() => canReprocess.value && !sourceFileLoading.value)

const ocrText = computed(() => {
  return document.value?.pages.map((page) => page.text).join('\n\n') || ''
})

const lastDetailRefreshText = computed(() => {
  return lastDetailRefreshedAt.value ? formatDateTime(lastDetailRefreshedAt.value.toISOString()) : ''
})

function isActiveJob(status: string): boolean {
  return status.includes('pending') || status.includes('running')
}

function markDetailRefreshed() {
  lastDetailRefreshedAt.value = new Date()
}

function formatAuditAction(action: string): string {
  if (action === 'document.upload') return 'Upload văn bản'
  if (action === 'document.upload_zip') return 'Upload zip'
  if (action === 'document.reprocess_requested') return 'Yêu cầu reprocess'
  if (action === 'document.source_files_added') return 'Thêm tệp nguồn'
  if (action === 'document.source_files_reordered') return 'Đổi thứ tự tệp nguồn'
  if (action === 'document.source_file_deleted') return 'Xóa tệp nguồn'
  return action
}

function formatAuditMetadataValue(value: unknown): string {
  if (value === null || value === undefined || value === '') return '-'
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return String(value)
  return JSON.stringify(value)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = undefined
  }
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(async () => {
    await fetchDocument(documentId.value, { silent: true })
    markDetailRefreshed()
    if (!shouldPoll.value) stopPolling()
  }, 3000)
}

async function submitReprocess() {
  if (!document.value || !canReprocess.value) return
  const confirmed = window.confirm('Reprocess sẽ OCR lại tài liệu này và thay thế page/chunk hiện có. Tiếp tục?')
  if (!confirmed) return

  const result = await reprocessDocument(document.value.id, reprocessReason.value)
  if (!result) return

  reprocessReason.value = ''
  await fetchDocument(documentId.value, { silent: true })
  markDetailRefreshed()
  if (shouldPoll.value) startPolling()
}

function handleSourceFilesSelected(files: File[]) {
  selectedSourceFiles.value = files
}

async function submitAddSourceFiles() {
  if (!document.value || !selectedSourceFiles.value.length || !canManageSourceFiles.value) return
  const result = await addSourceFiles(document.value.id, selectedSourceFiles.value)
  if (!result) return
  selectedSourceFiles.value = []
  await refreshAfterSourceFileMutation()
}

async function moveSourceFile(fileId: string, direction: 'up' | 'down') {
  if (!document.value || !canManageSourceFiles.value) return
  const ids = sourceFiles.value.map((file) => file.id)
  const index = ids.indexOf(fileId)
  const targetIndex = direction === 'up' ? index - 1 : index + 1
  if (index < 0 || targetIndex < 0 || targetIndex >= ids.length) return
  const [file] = ids.splice(index, 1)
  ids.splice(targetIndex, 0, file)
  const result = await reorderSourceFiles(document.value.id, ids)
  if (!result) return
  await refreshAfterSourceFileMutation()
}

async function submitDeleteSourceFile(fileId: string, filename: string) {
  if (!document.value || !canManageSourceFiles.value) return
  const confirmed = window.confirm(`Xóa tệp nguồn "${filename}" và OCR lại văn bản này?`)
  if (!confirmed) return
  const result = await deleteSourceFile(document.value.id, fileId)
  if (!result) return
  await refreshAfterSourceFileMutation()
}

async function refreshAfterSourceFileMutation() {
  await fetchDocument(documentId.value, { silent: true })
  markDetailRefreshed()
  if (shouldPoll.value) startPolling()
}

onMounted(async () => {
  await fetchDocument(documentId.value)
  markDetailRefreshed()
  if (shouldPoll.value) startPolling()
})

watch(shouldPoll, (value) => {
  if (value) startPolling()
  else stopPolling()
})

onBeforeUnmount(stopPolling)
</script>

<template>
  <section class="space-y-5">
    <Message v-if="error" severity="error">{{ error }}</Message>
    <p v-if="loading" class="text-sm text-slate-600">Đang tải...</p>

    <template v-if="document">
      <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 class="break-words text-2xl font-semibold">{{ document.title }}</h1>
          <p class="mt-1 break-words text-sm text-slate-600">{{ sourceSubtitle }}</p>
          <p v-if="lastDetailRefreshText" class="mt-1 text-xs text-slate-500">
            Cập nhật detail lần cuối: {{ lastDetailRefreshText }}
          </p>
        </div>
        <BaseStatusBadge :status="document.status" />
      </div>

      <Card>
        <template #title>Metadata</template>
        <template #content>
          <dl class="grid gap-3 text-sm sm:grid-cols-2">
            <div>
              <dt class="text-slate-500">Loại văn bản</dt>
              <dd class="font-medium">{{ document.document_type }}</dd>
            </div>
            <div>
              <dt class="text-slate-500">Trạng thái</dt>
              <dd><BaseStatusBadge :status="document.status" /></dd>
            </div>
            <div>
              <dt class="text-slate-500">Ngày tạo</dt>
              <dd class="font-medium">{{ formatDateTime(document.created_at) }}</dd>
            </div>
            <div>
              <dt class="text-slate-500">Cập nhật</dt>
              <dd class="font-medium">{{ formatDateTime(document.updated_at) }}</dd>
            </div>
          </dl>
        </template>
      </Card>

      <Card>
        <template #title>Tệp nguồn</template>
        <template #content>
          <div class="mb-4 space-y-3 rounded border border-slate-200 bg-slate-50 p-3">
            <BaseUploadDropzone :multiple="true" @selected="handleSourceFilesSelected" />
            <div v-if="selectedSourceFiles.length" class="space-y-2 text-sm">
              <p class="font-medium">Tệp sẽ thêm: {{ selectedSourceFiles.length }}</p>
              <ul class="space-y-1 text-slate-700">
                <li v-for="(file, index) in selectedSourceFiles" :key="`${file.name}-${index}`" class="break-words">
                  {{ index + 1 }}. {{ file.name }} · {{ formatFileSize(file.size) }}
                </li>
              </ul>
            </div>
            <div class="flex flex-wrap items-center gap-3">
              <Button
                label="Thêm tệp nguồn"
                icon="pi pi-plus"
                :disabled="!selectedSourceFiles.length || !canManageSourceFiles"
                :loading="sourceFileLoading"
                @click="submitAddSourceFiles"
              />
              <p v-if="!canManageSourceFiles" class="text-sm text-slate-600">
                Chỉ đổi tệp nguồn khi document không có job đang xử lý.
              </p>
            </div>
          </div>

          <div v-if="sourceFiles.length" class="space-y-3 text-sm">
            <article
              v-for="(file, index) in sourceFiles"
              :key="file.id"
              class="rounded border border-slate-200 p-3"
            >
              <div class="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p class="break-words font-medium">{{ file.file_order + 1 }}. {{ file.original_filename }}</p>
                  <p class="mt-1 text-xs text-slate-600">
                    {{ formatFileSize(file.file_size) }} · {{ file.content_type || 'Không xác định' }}
                  </p>
                </div>
                <div class="flex flex-wrap items-center gap-2">
                  <BaseStatusBadge :status="file.status" />
                  <Button
                    icon="pi pi-arrow-up"
                    severity="secondary"
                    size="small"
                    :disabled="index === 0 || !canManageSourceFiles"
                    :loading="sourceFileLoading"
                    @click="moveSourceFile(file.id, 'up')"
                  />
                  <Button
                    icon="pi pi-arrow-down"
                    severity="secondary"
                    size="small"
                    :disabled="index === sourceFiles.length - 1 || !canManageSourceFiles"
                    :loading="sourceFileLoading"
                    @click="moveSourceFile(file.id, 'down')"
                  />
                  <Button
                    icon="pi pi-trash"
                    severity="danger"
                    size="small"
                    :disabled="sourceFiles.length <= 1 || !canManageSourceFiles"
                    :loading="sourceFileLoading"
                    @click="submitDeleteSourceFile(file.id, file.original_filename)"
                  />
                </div>
              </div>
            </article>
          </div>
          <p v-else class="break-words text-sm text-slate-600">
            Tệp nguồn cũ: {{ document.original_filename }}
          </p>
        </template>
      </Card>

      <Card>
        <template #title>Reprocess</template>
        <template #content>
          <div class="space-y-3">
            <Textarea
              v-model="reprocessReason"
              class="w-full"
              rows="3"
              maxlength="500"
              placeholder="Lý do reprocess, ví dụ: kiểm tra lại OCR sau khi tối ưu engine"
              :disabled="!canReprocess || reprocessLoading"
            />
            <div class="flex flex-wrap items-center gap-3">
              <Button
                label="Reprocess"
                icon="pi pi-refresh"
                :disabled="!canReprocess"
                :loading="reprocessLoading"
                @click="submitReprocess"
              />
              <p v-if="!canReprocess" class="text-sm text-slate-600">
                Document đang xử lý nên chưa thể reprocess.
              </p>
            </div>
            <p v-if="shouldPoll" class="text-sm text-slate-600">Đang tự cập nhật trạng thái OCR/reprocess...</p>
            <p v-if="lastDetailRefreshText" class="text-xs text-slate-500">
              Lần refresh gần nhất: {{ lastDetailRefreshText }}
            </p>
          </div>
        </template>
      </Card>

      <Card>
        <template #title>Job audit</template>
        <template #content>
          <div v-if="sortedOcrJobs.length" class="space-y-3 text-sm">
            <article
              v-for="job in sortedOcrJobs"
              :key="job.id"
              class="rounded border p-3"
              :class="isActiveJob(job.status) ? 'border-amber-300 bg-amber-50' : 'border-slate-200'"
            >
              <div class="flex flex-wrap items-center justify-between gap-2">
                <div class="flex flex-wrap items-center gap-2">
                  <Tag :value="job.job_type" severity="info" />
                  <BaseStatusBadge :status="job.status" />
                  <Tag v-if="isActiveJob(job.status)" value="Đang xử lý" severity="warn" />
                </div>
                <span class="text-xs text-slate-500">{{ formatDateTime(job.created_at) }}</span>
              </div>
              <dl class="mt-3 grid gap-2 sm:grid-cols-2">
                <div>
                  <dt class="text-slate-500">Job ID</dt>
                  <dd class="break-all font-medium">{{ job.id }}</dd>
                </div>
                <div>
                  <dt class="text-slate-500">Số lần thử</dt>
                  <dd class="font-medium">{{ job.attempts }}</dd>
                </div>
                <div>
                  <dt class="text-slate-500">Cập nhật</dt>
                  <dd class="font-medium">{{ formatDateTime(job.updated_at) }}</dd>
                </div>
                <div v-if="job.reason">
                  <dt class="text-slate-500">Lý do</dt>
                  <dd class="break-words font-medium">{{ job.reason }}</dd>
                </div>
              </dl>
              <Message v-if="job.error_message" class="mt-3" severity="error">
                {{ job.error_message }}
              </Message>
            </article>
          </div>
          <p v-else class="text-sm text-slate-600">Chưa có OCR/reprocess job.</p>
        </template>
      </Card>

      <Card>
        <template #title>Admin audit log</template>
        <template #content>
          <div v-if="sortedAuditLogs.length" class="space-y-3 text-sm">
            <article v-for="event in sortedAuditLogs" :key="event.id" class="rounded border border-slate-200 p-3">
              <div class="flex flex-wrap items-center justify-between gap-2">
                <div class="flex flex-wrap items-center gap-2">
                  <Tag :value="formatAuditAction(event.action)" severity="info" />
                  <span class="text-slate-700">
                    {{ event.actor?.full_name || event.actor?.email || 'Không xác định' }}
                  </span>
                </div>
                <span class="text-xs text-slate-500">{{ formatDateTime(event.created_at) }}</span>
              </div>
              <dl class="mt-3 grid gap-2 sm:grid-cols-2">
                <div>
                  <dt class="text-slate-500">Event ID</dt>
                  <dd class="break-all font-medium">{{ event.id }}</dd>
                </div>
                <div v-for="(value, key) in event.metadata" :key="key">
                  <dt class="text-slate-500">{{ key }}</dt>
                  <dd class="break-words font-medium">{{ formatAuditMetadataValue(value) }}</dd>
                </div>
              </dl>
            </article>
          </div>
          <p v-else class="text-sm text-slate-600">Chưa có audit log admin.</p>
        </template>
      </Card>

      <Card>
        <template #title>OCR text</template>
        <template #content>
          <Textarea
            v-if="ocrText"
            :model-value="ocrText"
            class="w-full"
            rows="10"
            readonly
          />
          <p v-else class="text-sm text-slate-600">Chưa có OCR text.</p>
        </template>
      </Card>

      <Card>
        <template #title>Chunks</template>
        <template #content>
          <div v-if="document.chunks.length" class="space-y-3">
            <article v-for="chunk in document.chunks" :key="chunk.id" class="border-b border-slate-200 pb-3">
              <p class="break-words text-xs text-slate-500">#{{ chunk.chunk_index }} {{ chunk.section_title }}</p>
              <p class="mt-1 text-sm text-slate-700">{{ chunk.text }}</p>
            </article>
          </div>
          <p v-else class="text-sm text-slate-600">Chưa có chunk.</p>
        </template>
      </Card>
    </template>
  </section>
</template>
