<script setup lang="ts">
import type { DocumentListFilters } from '~/types/document'

const { documents, documentsTotal, documentsLimit, documentsOffset, loading, error, fetchDocuments } = useDocuments()
const { businessTypeFilterOptions, documentTypeFilterOptions, fetchCatalogOptions } = useCatalogs()
const filters = reactive<
  Required<Pick<DocumentListFilters, 'q' | 'status' | 'document_type' | 'business_type' | 'sort_by' | 'sort_dir'>> & {
    missing_module_metadata: '' | '1'
    has_relations: '' | '1'
  }
>({
  q: '',
  status: '',
  document_type: '',
  business_type: '',
  missing_module_metadata: '',
  has_relations: '',
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
const paginationSummary = computed(
  () => `Hiển thị ${currentStart.value}-${currentEnd.value} / ${documentsTotal.value} văn bản`
)

function currentFilters(): DocumentListFilters {
  return {
    q: filters.q,
    status: filters.status,
    document_type: filters.document_type,
    business_type: filters.business_type,
    missing_module_metadata: filters.missing_module_metadata === '1' ? true : undefined,
    has_relations: filters.has_relations === '1' ? true : undefined,
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
  filters.missing_module_metadata = ''
  filters.has_relations = ''
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

onMounted(async () => {
  await Promise.all([fetchCatalogOptions(), loadDocuments()])
})
</script>

<template>
  <AppPageContainer>
    <AppPageHeader title="Documents" description="Danh sách văn bản đã upload.">
      <template #actions>
        <Button label="Refresh" icon="pi pi-refresh" severity="secondary" :loading="loading" @click="() => loadDocuments()" />
        <NuxtLink to="/upload">
          <Button label="Upload" icon="pi pi-upload" />
        </NuxtLink>
      </template>
    </AppPageHeader>

    <AppCard title="Bộ lọc">
      <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        <InputText
          v-model="filters.q"
          class="sm:col-span-2 lg:col-span-2"
          placeholder="Tìm theo tên, số văn bản, đơn vị hoặc filename"
          @keyup.enter="loadDocuments(true)"
        />
        <AppSelect v-model="filters.status">
          <option v-for="option in statusOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </AppSelect>
        <AppSelect v-model="filters.document_type">
          <option v-for="option in documentTypeFilterOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </AppSelect>
        <AppSelect v-model="filters.business_type">
          <option v-for="option in businessTypeFilterOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </AppSelect>
        <AppSelect v-model="filters.missing_module_metadata">
          <option value="">Tất cả module</option>
          <option value="1">Chưa có metadata module</option>
        </AppSelect>
        <AppSelect v-model="filters.has_relations">
          <option value="">Tất cả liên kết</option>
          <option value="1">Có liên kết văn bản</option>
        </AppSelect>
        <AppSelect v-model="filters.sort_by">
          <option v-for="option in sortOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </AppSelect>
        <AppSelect v-model="filters.sort_dir">
          <option value="desc">Giảm dần</option>
          <option value="asc">Tăng dần</option>
        </AppSelect>
      </div>
      <div class="mt-4 flex flex-wrap gap-2">
        <Button label="Lọc" icon="pi pi-filter" :loading="loading" @click="loadDocuments(true)" />
        <Button label="Xóa lọc" icon="pi pi-times" severity="secondary" :disabled="loading" @click="resetFilters" />
      </div>
    </AppCard>

    <AppErrorState v-if="error" :message="error" />

    <AppToolbar
      :summary="paginationSummary"
      :loading="loading"
      :can-go-previous="canGoPrevious"
      :can-go-next="canGoNext"
      @previous="goToPreviousPage"
      @next="goToNextPage"
    />

    <AppCard no-padding>
      <BaseDataTable :rows="documents" :loading="loading" />
    </AppCard>
  </AppPageContainer>
</template>
