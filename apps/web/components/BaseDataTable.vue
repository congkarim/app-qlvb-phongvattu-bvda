<script setup lang="ts">
import type { DocumentItem } from '~/types/document'
import { formatDateTime } from '~/utils/format'

defineProps<{
  rows: DocumentItem[]
  loading?: boolean
}>()
</script>

<template>
  <DataTable :value="rows" :loading="loading" data-key="id" table-style="min-width: 56rem">
    <Column field="title" header="Tên văn bản">
      <template #body="{ data }">
        <NuxtLink class="font-medium text-sky-700" :to="`/documents/${data.id}`">{{ data.title }}</NuxtLink>
      </template>
    </Column>
    <Column field="document_type" header="Loại" />
    <Column field="status" header="Trạng thái">
      <template #body="{ data }">
        <BaseStatusBadge :status="data.status" />
      </template>
    </Column>
    <Column field="created_at" header="Ngày tạo">
      <template #body="{ data }">
        {{ formatDateTime(data.created_at) }}
      </template>
    </Column>
    <template #empty>
      <div class="py-6 text-center text-sm text-slate-600">Chưa có văn bản.</div>
    </template>
  </DataTable>
</template>
