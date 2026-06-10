<script setup lang="ts">
import type { StatusDetail } from '~/types/ops'

const authStore = useAuthStore()
const { status, loading, error, fetchSystemStatus } = useOpsStatus()

const components = computed(() => {
  if (!status.value) return []
  return [
    { key: 'ocr', title: 'OCR', value: status.value.ocr },
    { key: 'embedding', title: 'Model embedding', value: status.value.embedding },
    { key: 'qdrant', title: 'Qdrant', value: status.value.qdrant },
    { key: 'llm', title: 'LLM (RAG)', value: status.value.llm }
  ]
})

function severityFor(value?: string) {
  if (value === 'ok') return 'success'
  if (value === 'degraded') return 'warn'
  if (value === 'unavailable') return 'warn'
  return 'info'
}

function formatKey(key: string) {
  return key.replaceAll('_', ' ')
}

function formatValue(value: string | number | boolean | null) {
  if (value === null || value === '') return '-'
  if (typeof value === 'boolean') return value ? 'Có' : 'Không'
  return String(value)
}

function detailRows(component: StatusDetail) {
  return Object.entries(component.details)
}

onMounted(() => {
  if (authStore.isAdmin) {
    void fetchSystemStatus()
  }
})
</script>

<template>
  <AppPageContainer>
    <AppPageHeader
      title="Status"
      description="Trạng thái tối thiểu cho OCR, embedding, Qdrant và LLM RAG."
    >
      <template #actions>
        <Button label="Refresh" icon="pi pi-refresh" severity="secondary" :loading="loading" @click="fetchSystemStatus" />
      </template>
    </AppPageHeader>

    <Message v-if="!authStore.isAdmin" severity="warn">Chỉ admin được xem trạng thái hệ thống.</Message>
    <AppErrorState v-if="error" :message="error" />

    <div v-if="status" class="grid gap-4 md:grid-cols-4">
      <AppCard title="Tổng quan">
        <div class="space-y-4">
          <Tag :value="status.status" :severity="severityFor(status.status)" />
          <div class="grid grid-cols-2 gap-3 text-sm">
            <div>
              <p class="text-slate-500">Pending</p>
              <p class="text-lg font-semibold">{{ status.worker_queue.pending_ready }}</p>
            </div>
            <div>
              <p class="text-slate-500">Delayed</p>
              <p class="text-lg font-semibold">{{ status.worker_queue.pending_delayed }}</p>
            </div>
            <div>
              <p class="text-slate-500">Running</p>
              <p class="text-lg font-semibold">{{ status.worker_queue.running }}</p>
            </div>
            <div>
              <p class="text-slate-500">Failed</p>
              <p class="text-lg font-semibold">{{ status.worker_queue.failed }}</p>
            </div>
          </div>
        </div>
      </AppCard>

      <AppCard v-for="component in components" :key="component.key">
        <template #header>
          <div class="flex items-center justify-between gap-3">
            <span class="text-base font-semibold text-slate-900">{{ component.title }}</span>
            <Tag :value="component.value.status" :severity="severityFor(component.value.status)" />
          </div>
        </template>
        <div class="space-y-3">
          <p class="text-sm font-medium text-slate-800">{{ component.value.name }}</p>
          <Message v-if="component.value.error" severity="warn">{{ component.value.error }}</Message>
          <dl class="space-y-2 text-sm">
            <div
              v-for="[key, value] in detailRows(component.value)"
              :key="key"
              class="flex items-start justify-between gap-3 border-b border-slate-100 pb-2"
            >
              <dt class="capitalize text-slate-500">{{ formatKey(key) }}</dt>
              <dd class="max-w-[12rem] break-words text-right text-slate-800">{{ formatValue(value) }}</dd>
            </div>
          </dl>
        </div>
      </AppCard>
    </div>

    <p v-else-if="loading" class="text-sm text-slate-600">Đang tải trạng thái hệ thống...</p>
  </AppPageContainer>
</template>
