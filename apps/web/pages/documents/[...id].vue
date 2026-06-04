<script setup lang="ts">
import { formatDateTime } from '~/utils/format'

const route = useRoute()
const { document, loading, reprocessLoading, error, fetchDocument, reprocessDocument } = useDocuments()
let pollTimer: ReturnType<typeof setInterval> | undefined
const reprocessReason = ref('')

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

const shouldPoll = computed(() => {
  const status = document.value?.status
  return Boolean(status && processingStatuses.has(status))
})

const canReprocess = computed(() => {
  const status = document.value?.status
  return Boolean(status && !processingStatuses.has(status))
})

const ocrText = computed(() => {
  return document.value?.pages.map((page) => page.text).join('\n\n') || ''
})

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
    if (!shouldPoll.value) stopPolling()
  }, 3000)
}

async function submitReprocess() {
  if (!document.value || !canReprocess.value) return

  const result = await reprocessDocument(document.value.id, reprocessReason.value)
  if (!result) return

  reprocessReason.value = ''
  await fetchDocument(documentId.value, { silent: true })
  if (shouldPoll.value) startPolling()
}

onMounted(async () => {
  await fetchDocument(documentId.value)
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
      <div class="flex items-start justify-between gap-4">
        <div>
          <h1 class="text-2xl font-semibold">{{ document.title }}</h1>
          <p class="mt-1 text-sm text-slate-600">{{ document.original_filename }}</p>
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
              class="rounded border border-slate-200 p-3"
            >
              <div class="flex flex-wrap items-center justify-between gap-2">
                <div class="flex flex-wrap items-center gap-2">
                  <Tag :value="job.job_type" severity="info" />
                  <BaseStatusBadge :status="job.status" />
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
                  <dd class="font-medium">{{ job.reason }}</dd>
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
              <p class="text-xs text-slate-500">#{{ chunk.chunk_index }} {{ chunk.section_title }}</p>
              <p class="mt-1 text-sm text-slate-700">{{ chunk.text }}</p>
            </article>
          </div>
          <p v-else class="text-sm text-slate-600">Chưa có chunk.</p>
        </template>
      </Card>
    </template>
  </section>
</template>
