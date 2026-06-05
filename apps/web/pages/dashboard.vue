<script setup lang="ts">
import type { ReviewQueueChunk, ReviewQueueFilters, SemanticSearchFilters } from '~/types/document'

const query = ref('')
const authStore = useAuthStore()
const { results, loading, error: searchError, hasSearched, search } = useSemanticSearch()
const {
  reviewQueue,
  reviewQueueTotal,
  reviewQueueLoading,
  chunkReviewLoading,
  error: reviewQueueError,
  fetchReviewQueue,
  markChunkReviewed
} = useDocuments()

const filters = reactive<SemanticSearchFilters>({
  limit: 10,
  business_type: '',
  document_number: '',
  issued_date: '',
  doc_group: '',
  section_role: '',
  requires_review: null
})

const reviewQueueFilters = reactive<ReviewQueueFilters>({
  limit: 20,
  offset: 0,
  section_role: '',
  document_id: '',
  max_confidence: null
})

const businessTypeOptions = [
  { label: 'Tất cả nghiệp vụ', value: '' },
  { label: 'Công văn đến', value: 'incoming_dispatch' },
  { label: 'Công văn đi', value: 'outgoing_dispatch' },
  { label: 'Hợp đồng', value: 'contract' },
  { label: 'Quyết định', value: 'decision' }
]

const docGroupOptions = [
  { label: 'Tất cả nhóm', value: '' },
  { label: 'A - Quy phạm', value: 'A' },
  { label: 'B - Công văn', value: 'B' },
  { label: 'C - Quyết định', value: 'C' },
  { label: 'D - Biểu mẫu', value: 'D' },
  { label: 'E - Khác/review', value: 'E' }
]

const sectionRoleOptions = [
  { label: 'Tất cả vai trò', value: '' },
  { label: 'Điều', value: 'article' },
  { label: 'Khoản', value: 'clause' },
  { label: 'Điểm', value: 'point' },
  { label: 'Nhiệm vụ', value: 'task' },
  { label: 'Phụ lục', value: 'appendix' },
  { label: 'Nơi nhận', value: 'recipient' },
  { label: 'Chữ ký', value: 'signature' },
  { label: 'Không xác định', value: 'unknown' }
]

const reviewOptions: Array<{ label: string; value: boolean | null }> = [
  { label: 'Tất cả review', value: null },
  { label: 'Cần review', value: true },
  { label: 'Đã ổn định', value: false }
]

const reviewQueueRoleOptions = [
  { label: 'Tất cả review', value: '' },
  { label: 'Phụ lục', value: 'appendix' },
  { label: 'Không xác định', value: 'unknown' }
]

const confidenceOptions: Array<{ label: string; value: number | null }> = [
  { label: 'Mọi confidence', value: null },
  { label: 'Không chắc <= 65%', value: 0.65 },
  { label: 'Cần xem <= 80%', value: 0.8 }
]

const reviewQueuePageStart = computed(() => (reviewQueueTotal.value ? reviewQueueFilters.offset + 1 : 0))
const reviewQueuePageEnd = computed(() => Math.min(reviewQueueFilters.offset + reviewQueue.value.length, reviewQueueTotal.value))
const canGoPreviousReviewPage = computed(() => reviewQueueFilters.offset > 0)
const canGoNextReviewPage = computed(() => reviewQueueFilters.offset + reviewQueue.value.length < reviewQueueTotal.value)

async function submitSearch() {
  await search(query.value, filters)
}

async function submitReviewQueue(options: { resetOffset?: boolean } = {}) {
  if (options.resetOffset) reviewQueueFilters.offset = 0
  const result = await fetchReviewQueue(normalizeReviewQueueFilters())
  if (
    result &&
    result.items.length === 0 &&
    result.total > 0 &&
    reviewQueueFilters.offset > 0
  ) {
    reviewQueueFilters.offset = Math.max(0, reviewQueueFilters.offset - (reviewQueueFilters.limit || 20))
    await fetchReviewQueue(normalizeReviewQueueFilters())
  }
}

async function submitMarkQueueChunkReviewed(chunk: ReviewQueueChunk) {
  const result = await markChunkReviewed(chunk.document_id, chunk.id)
  if (!result) return
  await submitReviewQueue()
}

async function goReviewQueuePage(direction: 'previous' | 'next') {
  const limit = reviewQueueFilters.limit || 20
  if (direction === 'previous') {
    reviewQueueFilters.offset = Math.max(0, reviewQueueFilters.offset - limit)
  } else if (canGoNextReviewPage.value) {
    reviewQueueFilters.offset += limit
  }
  await submitReviewQueue()
}

function resetFilters() {
  filters.limit = 10
  filters.business_type = ''
  filters.document_number = ''
  filters.issued_date = ''
  filters.doc_group = ''
  filters.section_role = ''
  filters.requires_review = null
}

async function resetReviewQueueFilters() {
  reviewQueueFilters.limit = 20
  reviewQueueFilters.offset = 0
  reviewQueueFilters.section_role = ''
  reviewQueueFilters.document_id = ''
  reviewQueueFilters.max_confidence = null
  await submitReviewQueue()
}

function formatBusinessType(value?: string | null) {
  return businessTypeOptions.find((option) => option.value === value)?.label || value || '-'
}

function formatChunkMeta(result: { doc_group?: string | null; section_role?: string | null; section_path?: string[] }) {
  const parts = [result.doc_group, formatSectionRole(result.section_role), result.section_path?.join(' > ')].filter(Boolean)
  return parts.length ? parts.join(' · ') : 'Chưa có metadata chunk'
}

function formatSectionRole(value?: string | null) {
  if (value === 'article') return 'Điều'
  if (value === 'clause') return 'Khoản'
  if (value === 'point') return 'Điểm'
  if (value === 'task') return 'Nhiệm vụ'
  if (value === 'appendix') return 'Phụ lục'
  if (value === 'recipient') return 'Nơi nhận'
  if (value === 'signature') return 'Chữ ký'
  if (value === 'unknown') return 'Không xác định'
  return value || ''
}

function formatConfidence(value?: number | null) {
  if (value === null || value === undefined) return '-'
  return `${Math.round(value * 100)}%`
}

function normalizeReviewQueueFilters(): ReviewQueueFilters {
  return {
    limit: reviewQueueFilters.limit || 20,
    offset: reviewQueueFilters.offset || 0,
    section_role: reviewQueueFilters.section_role?.trim() || undefined,
    document_id: reviewQueueFilters.document_id?.trim() || undefined,
    max_confidence: reviewQueueFilters.max_confidence ?? undefined
  }
}

onMounted(async () => {
  if (authStore.isAdmin) {
    await submitReviewQueue()
  }
})
</script>

<template>
  <section class="space-y-6">
    <div>
      <h1 class="text-2xl font-semibold">Dashboard</h1>
      <p class="mt-1 text-sm text-slate-600">Upload, OCR và semantic search skeleton.</p>
    </div>

    <Card v-if="authStore.isAdmin">
      <template #title>
        <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <span>Review queue</span>
            <p class="mt-1 text-xs font-normal text-slate-500">
              {{ reviewQueueTotal }} chunks cần review
              <span v-if="reviewQueueTotal"> · {{ reviewQueuePageStart }}-{{ reviewQueuePageEnd }}</span>
            </p>
          </div>
          <Button
            label="Refresh"
            icon="pi pi-refresh"
            severity="secondary"
            size="small"
            :loading="reviewQueueLoading"
            @click="submitReviewQueue()"
          />
        </div>
      </template>
      <template #content>
        <form class="grid gap-3 md:grid-cols-5" @submit.prevent="submitReviewQueue({ resetOffset: true })">
          <select v-model="reviewQueueFilters.section_role" class="rounded border border-slate-300 px-3 py-2 text-sm">
            <option v-for="option in reviewQueueRoleOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
          <select v-model="reviewQueueFilters.max_confidence" class="rounded border border-slate-300 px-3 py-2 text-sm">
            <option v-for="option in confidenceOptions" :key="String(option.value)" :value="option.value">
              {{ option.label }}
            </option>
          </select>
          <InputText v-model="reviewQueueFilters.document_id" placeholder="Document ID" />
          <select v-model.number="reviewQueueFilters.limit" class="rounded border border-slate-300 px-3 py-2 text-sm">
            <option :value="10">10 chunks</option>
            <option :value="20">20 chunks</option>
            <option :value="50">50 chunks</option>
            <option :value="100">100 chunks</option>
          </select>
          <div class="flex gap-2">
            <Button type="submit" label="Lọc" icon="pi pi-filter" :loading="reviewQueueLoading" />
            <Button type="button" label="Xóa" icon="pi pi-times" severity="secondary" :disabled="reviewQueueLoading" @click="resetReviewQueueFilters" />
          </div>
        </form>
        <Message v-if="reviewQueueError" class="mt-4" severity="error">{{ reviewQueueError }}</Message>
        <p v-else-if="reviewQueueLoading" class="mt-4 text-sm text-slate-600">Đang tải review queue...</p>
        <p v-else-if="!reviewQueue.length" class="mt-4 text-sm text-slate-600">Không có chunk cần review.</p>
        <div
          v-if="reviewQueueTotal"
          class="mt-4 flex flex-col gap-3 border-y border-slate-200 py-3 text-sm text-slate-600 sm:flex-row sm:items-center sm:justify-between"
        >
          <span>Hiển thị {{ reviewQueuePageStart }}-{{ reviewQueuePageEnd }} / {{ reviewQueueTotal }}</span>
          <div class="flex gap-2">
            <Button
              type="button"
              label="Trước"
              icon="pi pi-chevron-left"
              severity="secondary"
              size="small"
              :disabled="reviewQueueLoading || !canGoPreviousReviewPage"
              @click="goReviewQueuePage('previous')"
            />
            <Button
              type="button"
              label="Sau"
              icon="pi pi-chevron-right"
              icon-pos="right"
              severity="secondary"
              size="small"
              :disabled="reviewQueueLoading || !canGoNextReviewPage"
              @click="goReviewQueuePage('next')"
            />
          </div>
        </div>
        <div class="mt-5 space-y-3">
          <article v-for="chunk in reviewQueue" :key="chunk.id" class="border-b border-slate-200 pb-3">
            <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <NuxtLink class="font-medium text-sky-700" :to="`/documents/${chunk.document_id}`">
                  {{ chunk.document_title || chunk.document_id }}
                </NuxtLink>
                <p class="mt-1 text-xs text-slate-500">
                  #{{ chunk.chunk_index }}
                  <span v-if="chunk.document_number"> · Số {{ chunk.document_number }}</span>
                  <span v-if="chunk.issued_date"> · {{ chunk.issued_date }}</span>
                  <span v-if="chunk.page_from"> · Trang {{ chunk.page_from }}{{ chunk.page_to && chunk.page_to !== chunk.page_from ? `-${chunk.page_to}` : '' }}</span>
                </p>
              </div>
              <div class="flex flex-wrap items-center gap-2">
                <Tag v-if="chunk.section_role" :value="formatSectionRole(chunk.section_role)" :severity="chunk.section_role === 'appendix' ? 'success' : 'secondary'" />
                <Tag value="review" severity="warn" />
                <span class="text-xs text-slate-500">{{ formatConfidence(chunk.chunk_confidence) }}</span>
                <Button
                  label="Đã review"
                  icon="pi pi-check"
                  severity="secondary"
                  size="small"
                  :loading="chunkReviewLoading === chunk.id"
                  :disabled="Boolean(chunkReviewLoading)"
                  @click="submitMarkQueueChunkReviewed(chunk)"
                />
              </div>
            </div>
            <p class="mt-1 break-words text-xs text-slate-500">{{ chunk.section_path?.join(' > ') || '-' }}</p>
            <p class="mt-1 break-words text-xs text-slate-500">{{ chunk.section_title }}</p>
            <p class="mt-1 text-sm text-slate-700">{{ chunk.text }}</p>
          </article>
        </div>
      </template>
    </Card>

    <Card>
      <template #title>Semantic search</template>
      <template #content>
        <form class="space-y-3" @submit.prevent="submitSearch">
          <div class="flex gap-3">
            <InputText v-model="query" class="w-full" required placeholder="Tìm điều khoản, trách nhiệm, hợp đồng..." />
            <Button type="submit" label="Search" icon="pi pi-search" :loading="loading" :disabled="!query.trim()" />
          </div>
          <div class="grid gap-3 md:grid-cols-6">
            <select v-model="filters.business_type" class="rounded border border-slate-300 px-3 py-2 text-sm">
              <option v-for="option in businessTypeOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
            <InputText v-model="filters.document_number" placeholder="Số văn bản" />
            <InputText v-model="filters.issued_date" type="date" />
            <select v-model="filters.doc_group" class="rounded border border-slate-300 px-3 py-2 text-sm">
              <option v-for="option in docGroupOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
            <select v-model="filters.section_role" class="rounded border border-slate-300 px-3 py-2 text-sm">
              <option v-for="option in sectionRoleOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
            <select v-model="filters.requires_review" class="rounded border border-slate-300 px-3 py-2 text-sm">
              <option v-for="option in reviewOptions" :key="String(option.value)" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>
          <div class="flex flex-wrap gap-2">
            <select v-model.number="filters.limit" class="rounded border border-slate-300 px-3 py-2 text-sm">
              <option :value="5">5 kết quả</option>
              <option :value="10">10 kết quả</option>
              <option :value="20">20 kết quả</option>
              <option :value="50">50 kết quả</option>
            </select>
            <Button type="button" label="Xóa lọc" icon="pi pi-times" severity="secondary" :disabled="loading" @click="resetFilters" />
          </div>
        </form>
        <Message v-if="searchError" class="mt-4" severity="error">{{ searchError }}</Message>
        <p v-else-if="loading" class="mt-4 text-sm text-slate-600">Đang tìm kiếm...</p>
        <p v-else-if="hasSearched && !results.length" class="mt-4 text-sm text-slate-600">Không có kết quả phù hợp.</p>
        <div class="mt-5 space-y-3">
          <article v-for="result in results" :key="result.chunk_id" class="border-b border-slate-200 pb-3">
            <NuxtLink class="font-medium text-sky-700" :to="`/documents/${result.document_id}`">
              {{ result.title || result.document_id }}
            </NuxtLink>
            <p class="mt-1 text-sm text-slate-700">{{ result.text }}</p>
            <p class="mt-1 text-xs text-slate-500">
              Score: {{ result.score.toFixed(4) }}
              <span v-if="result.business_type"> · {{ formatBusinessType(result.business_type) }}</span>
              <span v-if="result.document_number"> · Số {{ result.document_number }}</span>
              <span v-if="result.issued_date"> · {{ result.issued_date }}</span>
              <span v-if="result.page_from"> · Trang {{ result.page_from }}{{ result.page_to && result.page_to !== result.page_from ? `-${result.page_to}` : '' }}</span>
            </p>
            <p class="mt-1 text-xs text-slate-500">
              {{ formatChunkMeta(result) }}
              <Tag v-if="result.requires_review" class="ml-2" value="review" severity="warn" />
            </p>
          </article>
        </div>
      </template>
    </Card>
  </section>
</template>
