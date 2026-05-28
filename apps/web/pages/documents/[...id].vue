<script setup lang="ts">
import { formatDateTime } from '~/utils/format'

const route = useRoute()
const { document, loading, error, fetchDocument } = useDocuments()
let pollTimer: ReturnType<typeof setInterval> | undefined

const documentId = computed(() => {
  const value = route.params.id
  return Array.isArray(value) ? value.join('/') : String(value)
})

const latestOcrJob = computed(() => {
  return [...(document.value?.ocr_jobs || [])].sort((a, b) => {
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  })[0]
})

const shouldPoll = computed(() => {
  const status = document.value?.status
  return Boolean(status && status !== 'searchable' && status !== 'failed')
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
        <template #title>OCR job</template>
        <template #content>
          <div v-if="latestOcrJob" class="space-y-2 text-sm">
            <p>Job ID: {{ latestOcrJob.id }}</p>
            <p>Trạng thái: <BaseStatusBadge :status="latestOcrJob.status" /></p>
            <p>Số lần thử: {{ latestOcrJob.attempts }}</p>
            <Message v-if="latestOcrJob.error_message" severity="error">{{ latestOcrJob.error_message }}</Message>
            <p v-if="shouldPoll" class="text-slate-600">Đang tự cập nhật trạng thái OCR...</p>
          </div>
          <p v-else class="text-sm text-slate-600">Chưa có OCR job.</p>
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
