<script setup lang="ts">
import type { StatusDetail } from '~/types/ops'

const authStore = useAuthStore()
const { status, loading, error, fetchSystemStatus } = useOpsStatus()

const components = computed(() => {
  if (!status.value) return []
  return [
    { key: 'ocr', title: 'OCR', value: status.value.ocr },
    { key: 'embedding', title: 'Model embedding', value: status.value.embedding },
    { key: 'qdrant', title: 'Qdrant', value: status.value.qdrant }
  ]
})

function severityFor(value?: string) {
  if (value === 'ok') return 'success'
  if (value === 'degraded') return 'warn'
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
  <section class="space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-2xl font-semibold">Status</h1>
        <p class="mt-1 text-sm text-slate-600">Trạng thái tối thiểu cho OCR, model và Qdrant.</p>
      </div>
      <Button label="Refresh" icon="pi pi-refresh" severity="secondary" :loading="loading" @click="fetchSystemStatus" />
    </div>

    <Message v-if="!authStore.isAdmin" severity="warn">Chỉ admin được xem trạng thái hệ thống.</Message>
    <Message v-if="error" severity="error">{{ error }}</Message>

    <div v-if="status" class="grid gap-4 md:grid-cols-4">
      <Card>
        <template #title>Tổng quan</template>
        <template #content>
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
        </template>
      </Card>

      <Card v-for="component in components" :key="component.key">
        <template #title>
          <div class="flex items-center justify-between gap-3">
            <span>{{ component.title }}</span>
            <Tag :value="component.value.status" :severity="severityFor(component.value.status)" />
          </div>
        </template>
        <template #content>
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
        </template>
      </Card>
    </div>

    <p v-else-if="loading" class="text-sm text-slate-600">Đang tải trạng thái hệ thống...</p>
  </section>
</template>
