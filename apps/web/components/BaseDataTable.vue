<script setup lang="ts">
import type { DocumentItem } from '~/types/document'
import { formatDate, formatDateTime } from '~/utils/format'

defineProps<{
  rows: DocumentItem[]
  loading?: boolean
}>()
</script>

<template>
  <DataTable :value="rows" :loading="loading" data-key="id" table-style="min-width: 72rem">
    <Column field="title" header="Tên văn bản">
      <template #body="{ data }">
        <div>
          <NuxtLink class="font-medium text-sky-700" :to="`/documents/${data.id}`">{{ data.title }}</NuxtLink>
          <p v-if="data.issuing_agency" class="mt-1 text-xs text-slate-500">{{ data.issuing_agency }}</p>
        </div>
      </template>
    </Column>
    <Column field="document_number" header="Số văn bản">
      <template #body="{ data }">
        {{ data.document_number || '-' }}
      </template>
    </Column>
    <Column field="issued_date" header="Ngày ban hành">
      <template #body="{ data }">
        {{ formatDate(data.issued_date) }}
      </template>
    </Column>
    <Column field="document_type" header="Loại" />
    <Column field="business_type" header="Nghiệp vụ">
      <template #body="{ data }">
        {{ data.business_type || '-' }}
      </template>
    </Column>
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
    <Column field="updated_at" header="Cập nhật">
      <template #body="{ data }">
        {{ formatDateTime(data.updated_at) }}
      </template>
    </Column>
    <template #empty>
      <div class="py-6 text-center text-sm text-slate-600">Chưa có văn bản.</div>
    </template>
  </DataTable>
</template>
