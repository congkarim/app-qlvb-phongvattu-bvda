<script setup lang="ts">
import type { DocumentListFilters } from '~/types/document'

const { documents, loading, error, fetchDocuments } = useDocuments()
const filters = reactive<Required<Pick<DocumentListFilters, 'q' | 'status' | 'document_type' | 'sort_by' | 'sort_dir'>>>({
  q: '',
  status: '',
  document_type: '',
  sort_by: 'created_at',
  sort_dir: 'desc'
})

const statusOptions = [
  { label: 'Tất cả trạng thái', value: '' },
  { label: 'Searchable', value: 'searchable' },
  { label: 'OCR pending', value: 'ocr_pending' },
  { label: 'OCR running', value: 'ocr_running' },
  { label: 'Reprocess pending', value: 'reprocess_pending' },
  { label: 'Reprocess running', value: 'reprocess_running' },
  { label: 'Failed', value: 'failed' }
]

const typeOptions = [
  { label: 'Tất cả loại', value: '' },
  { label: 'Document', value: 'document' },
  { label: 'Dispatch', value: 'dispatch' },
  { label: 'Contract', value: 'contract' },
  { label: 'Decision', value: 'decision' }
]

const sortOptions = [
  { label: 'Ngày tạo', value: 'created_at' },
  { label: 'Cập nhật', value: 'updated_at' },
  { label: 'Tên văn bản', value: 'title' },
  { label: 'Trạng thái', value: 'status' },
  { label: 'Loại', value: 'document_type' }
]

function currentFilters(): DocumentListFilters {
  return {
    q: filters.q,
    status: filters.status,
    document_type: filters.document_type,
    sort_by: filters.sort_by,
    sort_dir: filters.sort_dir,
    limit: 100
  }
}

async function loadDocuments() {
  await fetchDocuments(currentFilters())
}

function resetFilters() {
  filters.q = ''
  filters.status = ''
  filters.document_type = ''
  filters.sort_by = 'created_at'
  filters.sort_dir = 'desc'
  void loadDocuments()
}

onMounted(loadDocuments)
</script>

<template>
  <section class="space-y-5">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-semibold">Documents</h1>
        <p class="mt-1 text-sm text-slate-600">Danh sách văn bản đã upload.</p>
      </div>
      <div class="flex gap-2">
        <Button label="Refresh" icon="pi pi-refresh" severity="secondary" :loading="loading" @click="loadDocuments" />
        <NuxtLink to="/upload">
          <Button label="Upload" icon="pi pi-upload" />
        </NuxtLink>
      </div>
    </div>

    <Card>
      <template #content>
        <div class="grid gap-3 md:grid-cols-6">
          <InputText
            v-model="filters.q"
            class="md:col-span-2"
            placeholder="Tìm theo tên văn bản hoặc filename"
            @keyup.enter="loadDocuments"
          />
          <select v-model="filters.status" class="rounded border border-slate-300 px-3 py-2 text-sm">
            <option v-for="option in statusOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
          <select v-model="filters.document_type" class="rounded border border-slate-300 px-3 py-2 text-sm">
            <option v-for="option in typeOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
          <select v-model="filters.sort_by" class="rounded border border-slate-300 px-3 py-2 text-sm">
            <option v-for="option in sortOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
          <select v-model="filters.sort_dir" class="rounded border border-slate-300 px-3 py-2 text-sm">
            <option value="desc">Giảm dần</option>
            <option value="asc">Tăng dần</option>
          </select>
        </div>
        <div class="mt-3 flex flex-wrap gap-2">
          <Button label="Lọc" icon="pi pi-filter" :loading="loading" @click="loadDocuments" />
          <Button label="Xóa lọc" icon="pi pi-times" severity="secondary" :disabled="loading" @click="resetFilters" />
        </div>
      </template>
    </Card>

    <Message v-if="error" severity="error">{{ error }}</Message>
    <BaseDataTable :rows="documents" :loading="loading" />
  </section>
</template>
