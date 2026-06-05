<script setup lang="ts">
import type { DocumentListFilters } from '~/types/document'

const { documents, documentsTotal, documentsLimit, documentsOffset, loading, error, fetchDocuments } = useDocuments()
const filters = reactive<
  Required<Pick<DocumentListFilters, 'q' | 'status' | 'document_type' | 'business_type' | 'sort_by' | 'sort_dir'>>
>({
  q: '',
  status: '',
  document_type: '',
  business_type: '',
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
  { label: 'Không đủ dữ liệu', value: 'UNKNOWN' },
  { label: 'Công văn', value: 'CV' },
  { label: 'Quyết định', value: 'QĐ' },
  { label: 'Thông báo', value: 'TB' },
  { label: 'Báo cáo', value: 'BC' },
  { label: 'Biên bản', value: 'BB' },
  { label: 'Tờ trình', value: 'TTr' },
  { label: 'Kế hoạch', value: 'KH' },
  { label: 'Hợp đồng', value: 'HĐ' },
  { label: 'Giấy mời', value: 'GM' }
]

const businessTypeOptions = [
  { label: 'Tất cả nghiệp vụ', value: '' },
  { label: 'Công văn đến', value: 'incoming_dispatch' },
  { label: 'Công văn đi', value: 'outgoing_dispatch' },
  { label: 'Hợp đồng', value: 'contract' },
  { label: 'Quyết định', value: 'decision' }
]

const sortOptions = [
  { label: 'Ngày tạo', value: 'created_at' },
  { label: 'Cập nhật', value: 'updated_at' },
  { label: 'Ngày ban hành', value: 'issued_date' },
  { label: 'Tên văn bản', value: 'title' },
  { label: 'Trạng thái', value: 'status' },
  { label: 'Loại', value: 'document_type' },
  { label: 'Loại nghiệp vụ', value: 'business_type' }
]

const currentStart = computed(() => (documentsTotal.value === 0 ? 0 : documentsOffset.value + 1))
const currentEnd = computed(() => Math.min(documentsOffset.value + documents.value.length, documentsTotal.value))
const canGoPrevious = computed(() => documentsOffset.value > 0)
const canGoNext = computed(() => documentsOffset.value + documentsLimit.value < documentsTotal.value)

function currentFilters(): DocumentListFilters {
  return {
    q: filters.q,
    status: filters.status,
    document_type: filters.document_type,
    business_type: filters.business_type,
    sort_by: filters.sort_by,
    sort_dir: filters.sort_dir,
    limit: documentsLimit.value,
    offset: documentsOffset.value
  }
}

async function loadDocuments(resetPage = false) {
  if (resetPage) documentsOffset.value = 0
  await fetchDocuments(currentFilters())
}

function resetFilters() {
  filters.q = ''
  filters.status = ''
  filters.document_type = ''
  filters.business_type = ''
  filters.sort_by = 'created_at'
  filters.sort_dir = 'desc'
  void loadDocuments(true)
}

function goToPreviousPage() {
  if (!canGoPrevious.value) return
  documentsOffset.value = Math.max(0, documentsOffset.value - documentsLimit.value)
  void loadDocuments()
}

function goToNextPage() {
  if (!canGoNext.value) return
  documentsOffset.value += documentsLimit.value
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
        <Button label="Refresh" icon="pi pi-refresh" severity="secondary" :loading="loading" @click="() => loadDocuments()" />
        <NuxtLink to="/upload">
          <Button label="Upload" icon="pi pi-upload" />
        </NuxtLink>
      </div>
    </div>

    <Card>
      <template #content>
        <div class="grid gap-3 md:grid-cols-7">
          <InputText
            v-model="filters.q"
            class="md:col-span-2"
            placeholder="Tìm theo tên, số văn bản, đơn vị hoặc filename"
            @keyup.enter="loadDocuments(true)"
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
          <select v-model="filters.business_type" class="rounded border border-slate-300 px-3 py-2 text-sm">
            <option v-for="option in businessTypeOptions" :key="option.value" :value="option.value">
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
          <Button label="Lọc" icon="pi pi-filter" :loading="loading" @click="loadDocuments(true)" />
          <Button label="Xóa lọc" icon="pi pi-times" severity="secondary" :disabled="loading" @click="resetFilters" />
        </div>
      </template>
    </Card>

    <Message v-if="error" severity="error">{{ error }}</Message>
    <div class="flex flex-col gap-3 rounded border border-slate-200 bg-white px-4 py-3 md:flex-row md:items-center md:justify-between">
      <p class="text-sm text-slate-600">
        Hiển thị {{ currentStart }}-{{ currentEnd }} / {{ documentsTotal }} văn bản
      </p>
      <div class="flex gap-2">
        <Button
          label="Trước"
          icon="pi pi-chevron-left"
          severity="secondary"
          size="small"
          :disabled="loading || !canGoPrevious"
          @click="goToPreviousPage"
        />
        <Button
          label="Sau"
          icon="pi pi-chevron-right"
          icon-pos="right"
          severity="secondary"
          size="small"
          :disabled="loading || !canGoNext"
          @click="goToNextPage"
        />
      </div>
    </div>
    <BaseDataTable :rows="documents" :loading="loading" />
  </section>
</template>
