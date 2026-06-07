<script setup lang="ts">
import type { ContractStatus } from '~/types/contract'
import type { DecisionKind, DecisionStatus } from '~/types/decision'
import type { DispatchStatus, DispatchType } from '~/types/dispatch'
import type { ProcurementKind, ProcurementStatus } from '~/types/procurement'
import type { ReviewQueueChunk, ReviewQueueFilters, SearchResult, SemanticSearchFilters } from '~/types/document'
import { buildDocumentChunkUrl } from '~/utils/documentLinks'

const query = ref('')
const route = useRoute()
const authStore = useAuthStore()
const isAdmin = computed(() => Boolean(authStore?.isAdmin))
const { results, loading, error: searchError, hasSearched, search } = useSemanticSearch()
const {
  question: ragQuestion,
  answer: ragAnswer,
  citations: ragCitations,
  grounded: ragGrounded,
  confidence: ragConfidence,
  fallbackReason: ragFallbackReason,
  generationMode: ragGenerationMode,
  modelName: ragModelName,
  latencyMs: ragLatencyMs,
  loading: ragLoading,
  error: ragError,
  hasAsked: ragHasAsked,
  ask: askRag,
  clear: clearRagAnswer,
  resetQuestion: resetRagQuestion
} = useRagAnswer()
const ragFilterChangedHint = ref(false)
const { businessTypeFilterOptions, fetchCatalogOptions, formatBusinessType } = useCatalogs()
const {
  reviewQueue,
  reviewQueueTotal,
  reviewQueueLimit,
  reviewQueueOffset,
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
  issuing_agency: '',
  issued_date: '',
  doc_group: '',
  section_role: '',
  requires_review: null,
  contract_number: '',
  supplier_name: '',
  contract_status: '',
  dispatch_type: '',
  dispatch_status: '',
  decision_kind: '',
  decision_status: '',
  effective_from: '',
  effective_to: '',
  procurement_kind: '',
  procurement_status: '',
  reference_number: '',
  requesting_unit: ''
})

const reviewQueueFilters = reactive<ReviewQueueFilters>({
  limit: 20,
  offset: 0,
  section_role: '',
  document_id: '',
  max_confidence: null
})

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

const contractStatusOptions: Array<{ label: string; value: ContractStatus | '' }> = [
  { label: 'Tất cả HĐ', value: '' },
  { label: 'Nháp', value: 'draft' },
  { label: 'Đang hiệu lực', value: 'active' },
  { label: 'Hết hạn', value: 'expired' },
  { label: 'Chấm dứt', value: 'terminated' },
  { label: 'Hoàn thành', value: 'completed' }
]

const dispatchTypeOptions: Array<{ label: string; value: DispatchType | '' }> = [
  { label: 'Tất cả loại CV', value: '' },
  { label: 'Công văn đến', value: 'incoming' },
  { label: 'Công văn đi', value: 'outgoing' }
]

const dispatchStatusOptions: Array<{ label: string; value: DispatchStatus | '' }> = [
  { label: 'Tất cả CV', value: '' },
  { label: 'Nháp', value: 'draft' },
  { label: 'Đã vào sổ', value: 'registered' },
  { label: 'Đang xử lý', value: 'processing' },
  { label: 'Hoàn thành', value: 'completed' },
  { label: 'Lưu trữ', value: 'archived' }
]

const decisionKindOptions: Array<{ label: string; value: DecisionKind | '' }> = [
  { label: 'Tất cả loại QĐ', value: '' },
  { label: 'Quyết định', value: 'decision' },
  { label: 'Thông báo', value: 'notification' }
]

const decisionStatusOptions: Array<{ label: string; value: DecisionStatus | '' }> = [
  { label: 'Tất cả QĐ/TB', value: '' },
  { label: 'Nháp', value: 'draft' },
  { label: 'Đã vào sổ', value: 'registered' },
  { label: 'Đang hiệu lực', value: 'effective' },
  { label: 'Hết hiệu lực', value: 'expired' },
  { label: 'Đã thu hồi', value: 'revoked' },
  { label: 'Lưu trữ', value: 'archived' }
]

const showDispatchFilters = computed(() => {
  const businessType = filters.business_type
  return !businessType || businessType === 'incoming_dispatch' || businessType === 'outgoing_dispatch'
})

const showDecisionFilters = computed(() => {
  const businessType = filters.business_type
  return !businessType || businessType === 'decision'
})

const showProcurementFilters = computed(() => {
  const businessType = filters.business_type
  return !businessType || businessType === 'procurement'
})

const procurementKindOptions: Array<{ label: string; value: ProcurementKind | '' }> = [
  { label: 'Tất cả loại MS', value: '' },
  { label: 'Đề xuất mua sắm', value: 'proposal' },
  { label: 'Kế hoạch / dự toán', value: 'plan' },
  { label: 'Biên bản nghiệm thu', value: 'acceptance' }
]

const procurementStatusOptions: Array<{ label: string; value: ProcurementStatus | '' }> = [
  { label: 'Tất cả MS', value: '' },
  { label: 'Nháp', value: 'draft' },
  { label: 'Đã trình', value: 'submitted' },
  { label: 'Đã duyệt', value: 'approved' },
  { label: 'Từ chối', value: 'rejected' },
  { label: 'Hoàn thành', value: 'completed' },
  { label: 'Lưu trữ', value: 'archived' }
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

const reviewQueuePageStart = computed(() => (reviewQueueTotal.value ? reviewQueueOffset.value + 1 : 0))
const reviewQueuePageEnd = computed(() => Math.min(reviewQueueOffset.value + reviewQueue.value.length, reviewQueueTotal.value))
const reviewQueueCurrentPage = computed(() => Math.floor((reviewQueueOffset.value || 0) / (reviewQueueLimit.value || 20)) + 1)
const reviewQueuePageCount = computed(() => Math.max(1, Math.ceil(reviewQueueTotal.value / (reviewQueueLimit.value || 20))))
const canGoPreviousReviewPage = computed(() => reviewQueueOffset.value > 0)
const canGoNextReviewPage = computed(() => reviewQueueOffset.value + reviewQueueLimit.value < reviewQueueTotal.value)

async function submitSearch() {
  await search(query.value, filters)
}

async function submitRagAnswer() {
  ragFilterChangedHint.value = false
  await askRag(ragQuestion.value, filters)
}

function clearRagPanel() {
  ragFilterChangedHint.value = false
  resetRagQuestion()
}

async function submitReviewQueue(options: { resetOffset?: boolean } = {}) {
  if (options.resetOffset) reviewQueueFilters.offset = 0
  const result = await fetchReviewQueue(normalizeReviewQueueFilters())
  if (result) {
    reviewQueueFilters.limit = result.limit
    reviewQueueFilters.offset = result.offset
  }
  if (
    result &&
    result.items.length === 0 &&
    result.total > 0 &&
    reviewQueueFilters.offset > 0
  ) {
    reviewQueueFilters.offset = Math.max(0, reviewQueueFilters.offset - (reviewQueueFilters.limit || 20))
    const retryResult = await fetchReviewQueue(normalizeReviewQueueFilters())
    if (retryResult) {
      reviewQueueFilters.limit = retryResult.limit
      reviewQueueFilters.offset = retryResult.offset
    }
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

async function goReviewQueueBoundary(direction: 'first' | 'last') {
  const limit = reviewQueueFilters.limit || 20
  reviewQueueFilters.offset = direction === 'first'
    ? 0
    : Math.max(0, (reviewQueuePageCount.value - 1) * limit)
  await submitReviewQueue()
}

function resetFilters() {
  filters.limit = 10
  filters.business_type = ''
  filters.document_number = ''
  filters.issuing_agency = ''
  filters.issued_date = ''
  filters.doc_group = ''
  filters.section_role = ''
  filters.requires_review = null
  filters.contract_number = ''
  filters.supplier_name = ''
  filters.contract_status = ''
  filters.dispatch_type = ''
  filters.dispatch_status = ''
  filters.decision_kind = ''
  filters.decision_status = ''
  filters.effective_from = ''
  filters.effective_to = ''
  filters.procurement_kind = ''
  filters.procurement_status = ''
  filters.reference_number = ''
  filters.requesting_unit = ''
}

function formatContractStatus(value?: string | null) {
  const option = contractStatusOptions.find((item) => item.value === value)
  return option?.label || value || ''
}

function formatDispatchType(value?: string | null) {
  const option = dispatchTypeOptions.find((item) => item.value === value)
  return option?.label || value || ''
}

function formatDispatchStatus(value?: string | null) {
  const option = dispatchStatusOptions.find((item) => item.value === value)
  return option?.label || value || ''
}

function formatDecisionKind(value?: string | null) {
  const option = decisionKindOptions.find((item) => item.value === value)
  return option?.label || value || ''
}

function formatDecisionStatus(value?: string | null) {
  const option = decisionStatusOptions.find((item) => item.value === value)
  return option?.label || value || ''
}

function formatProcurementKind(value?: string | null) {
  const option = procurementKindOptions.find((item) => item.value === value)
  return option?.label || value || ''
}

function formatProcurementStatus(value?: string | null) {
  const option = procurementStatusOptions.find((item) => item.value === value)
  return option?.label || value || ''
}

async function resetReviewQueueFilters() {
  reviewQueueFilters.limit = 20
  reviewQueueFilters.offset = 0
  reviewQueueFilters.section_role = ''
  reviewQueueFilters.document_id = ''
  reviewQueueFilters.max_confidence = null
  await submitReviewQueue()
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

function searchResultUrl(result: SearchResult) {
  return buildDocumentChunkUrl(result.document_id, result.chunk_id)
}

function hasModuleMetadata(result: SearchResult) {
  return Boolean(
    result.contract_id
      || result.contract_number
      || result.dispatch_id
      || result.dispatch_type
      || result.decision_id
      || result.decision_kind
      || result.procurement_id
      || result.procurement_kind
  )
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

function routeQueryValue(key: string) {
  const value = route.query[key]
  return typeof value === 'string' ? value.trim() : ''
}

function applyRouteSearchPresets() {
  const presetBusinessType = routeQueryValue('business_type')
  const presetIssuingAgency = routeQueryValue('issuing_agency')
  const presetDispatchType = routeQueryValue('dispatch_type')
  const presetDispatchStatus = routeQueryValue('dispatch_status')
  const presetDecisionKind = routeQueryValue('decision_kind')
  const presetDecisionStatus = routeQueryValue('decision_status')
  const presetEffectiveFrom = routeQueryValue('effective_from')
  const presetEffectiveTo = routeQueryValue('effective_to')
  const presetProcurementKind = routeQueryValue('procurement_kind')
  const presetProcurementStatus = routeQueryValue('procurement_status')

  if (presetBusinessType) filters.business_type = presetBusinessType
  if (routeQueryValue('document_number')) filters.document_number = routeQueryValue('document_number')
  if (presetIssuingAgency) filters.issuing_agency = presetIssuingAgency
  if (routeQueryValue('contract_number')) filters.contract_number = routeQueryValue('contract_number')
  if (routeQueryValue('supplier_name')) filters.supplier_name = routeQueryValue('supplier_name')
  if (presetDispatchType === 'incoming' || presetDispatchType === 'outgoing') {
    filters.dispatch_type = presetDispatchType
  }
  if (dispatchStatusOptions.some((option) => option.value && option.value === presetDispatchStatus)) {
    filters.dispatch_status = presetDispatchStatus as DispatchStatus
  }
  if (presetDecisionKind === 'decision' || presetDecisionKind === 'notification') {
    filters.decision_kind = presetDecisionKind
  }
  if (decisionStatusOptions.some((option) => option.value && option.value === presetDecisionStatus)) {
    filters.decision_status = presetDecisionStatus as DecisionStatus
  }
  if (presetEffectiveFrom) filters.effective_from = presetEffectiveFrom
  if (presetEffectiveTo) filters.effective_to = presetEffectiveTo
  if (presetProcurementKind === 'proposal' || presetProcurementKind === 'plan' || presetProcurementKind === 'acceptance') {
    filters.procurement_kind = presetProcurementKind
  }
  if (procurementStatusOptions.some((option) => option.value && option.value === presetProcurementStatus)) {
    filters.procurement_status = presetProcurementStatus as ProcurementStatus
  }
  if (routeQueryValue('reference_number')) filters.reference_number = routeQueryValue('reference_number')
  if (routeQueryValue('requesting_unit')) filters.requesting_unit = routeQueryValue('requesting_unit')

  return routeQueryValue('q')
}

watch(
  () => ({ ...filters }),
  () => {
    if (!ragHasAsked.value) return
    clearRagAnswer()
    ragFilterChangedHint.value = true
  },
  { deep: true }
)

onMounted(async () => {
  await fetchCatalogOptions()
  const presetQuery = applyRouteSearchPresets()
  if (isAdmin.value) {
    await submitReviewQueue()
  }
  if (presetQuery) {
    query.value = presetQuery
    await submitSearch()
  }
})
</script>

<template>
  <section class="space-y-6">
    <div>
      <h1 class="text-2xl font-semibold">Dashboard</h1>
      <p class="mt-1 text-sm text-slate-600">Upload, OCR và semantic search skeleton.</p>
    </div>

    <Card v-if="isAdmin">
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
          <span>Hiển thị {{ reviewQueuePageStart }}-{{ reviewQueuePageEnd }} / {{ reviewQueueTotal }} · Trang {{ reviewQueueCurrentPage }}/{{ reviewQueuePageCount }}</span>
          <div class="flex flex-wrap gap-2">
            <Button
              type="button"
              icon="pi pi-angle-double-left"
              severity="secondary"
              size="small"
              aria-label="Trang đầu"
              :disabled="reviewQueueLoading || !canGoPreviousReviewPage"
              @click="goReviewQueueBoundary('first')"
            />
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
            <Button
              type="button"
              icon="pi pi-angle-double-right"
              severity="secondary"
              size="small"
              aria-label="Trang cuối"
              :disabled="reviewQueueLoading || !canGoNextReviewPage"
              @click="goReviewQueueBoundary('last')"
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
          <div class="grid gap-3 md:grid-cols-3">
            <select v-model="filters.business_type" class="rounded border border-slate-300 px-3 py-2 text-sm">
              <option v-for="option in businessTypeFilterOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
            <InputText v-model="filters.document_number" placeholder="Số văn bản" />
            <InputText v-model="filters.issuing_agency" placeholder="Đơn vị ban hành" />
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
            <InputText v-model="filters.contract_number" placeholder="Số hợp đồng" />
            <InputText v-model="filters.supplier_name" placeholder="Nhà cung cấp" />
            <select v-model="filters.contract_status" class="rounded border border-slate-300 px-3 py-2 text-sm">
              <option v-for="option in contractStatusOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
            <template v-if="showDispatchFilters">
              <select v-model="filters.dispatch_type" class="rounded border border-slate-300 px-3 py-2 text-sm">
                <option v-for="option in dispatchTypeOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
              <select v-model="filters.dispatch_status" class="rounded border border-slate-300 px-3 py-2 text-sm">
                <option v-for="option in dispatchStatusOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </template>
            <template v-if="showDecisionFilters">
              <select v-model="filters.decision_kind" class="rounded border border-slate-300 px-3 py-2 text-sm">
                <option v-for="option in decisionKindOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
              <select v-model="filters.decision_status" class="rounded border border-slate-300 px-3 py-2 text-sm">
                <option v-for="option in decisionStatusOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
              <InputText v-model="filters.effective_from" type="date" placeholder="Hiệu lực từ" />
              <InputText v-model="filters.effective_to" type="date" placeholder="Hiệu lực đến" />
            </template>
            <template v-if="showProcurementFilters">
              <select v-model="filters.procurement_kind" class="rounded border border-slate-300 px-3 py-2 text-sm">
                <option v-for="option in procurementKindOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
              <select v-model="filters.procurement_status" class="rounded border border-slate-300 px-3 py-2 text-sm">
                <option v-for="option in procurementStatusOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
              <InputText v-model="filters.reference_number" placeholder="Số tham chiếu MS" />
              <InputText v-model="filters.requesting_unit" placeholder="Đơn vị đề xuất" />
            </template>
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
            <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <NuxtLink class="font-medium text-sky-700" :to="searchResultUrl(result)">
                  {{ result.title || result.document_id }}
                </NuxtLink>
                <div v-if="hasModuleMetadata(result)" class="mt-1 flex flex-wrap gap-1">
                  <Tag
                    v-if="result.contract_id || result.contract_number"
                    :value="result.contract_number ? `HĐ ${result.contract_number}` : 'Hợp đồng'"
                    severity="info"
                  />
                  <Tag
                    v-if="result.dispatch_id || result.dispatch_type"
                    :value="formatDispatchType(result.dispatch_type) || 'Công văn'"
                    severity="secondary"
                  />
                  <Tag
                    v-if="result.decision_id || result.decision_kind"
                    :value="formatDecisionKind(result.decision_kind) || 'Quyết định'"
                    severity="contrast"
                  />
                  <Tag
                    v-if="result.procurement_id || result.procurement_kind"
                    :value="formatProcurementKind(result.procurement_kind) || 'Mua sắm'"
                    severity="success"
                  />
                </div>
              </div>
              <NuxtLink
                :to="searchResultUrl(result)"
                class="inline-flex shrink-0 items-center gap-1 text-sm text-sky-700 hover:underline"
              >
                <i class="pi pi-external-link text-xs" />
                Mở đoạn
              </NuxtLink>
            </div>
            <p class="mt-1 text-sm text-slate-700">{{ result.text }}</p>
            <p class="mt-1 text-xs text-slate-500">
              Score: {{ result.score.toFixed(4) }}
              <span v-if="result.business_type"> · {{ formatBusinessType(result.business_type) }}</span>
              <span v-if="result.document_number"> · Số {{ result.document_number }}</span>
              <span v-if="result.issued_date"> · {{ result.issued_date }}</span>
              <span v-if="result.issuing_agency"> · {{ result.issuing_agency }}</span>
              <span v-if="result.page_from"> · Trang {{ result.page_from }}{{ result.page_to && result.page_to !== result.page_from ? `-${result.page_to}` : '' }}</span>
            </p>
            <p v-if="result.contract_number || result.supplier_name" class="mt-1 text-xs text-slate-500">
              <span v-if="result.contract_number">HĐ {{ result.contract_number }}</span>
              <span v-if="result.supplier_name"> · {{ result.supplier_name }}</span>
              <span v-if="result.contract_status"> · {{ formatContractStatus(result.contract_status) }}</span>
            </p>
            <p v-if="result.dispatch_id || result.dispatch_type || result.dispatch_status" class="mt-1 text-xs text-slate-500">
              <span v-if="result.dispatch_type">{{ formatDispatchType(result.dispatch_type) }}</span>
              <span v-if="result.dispatch_status"> · {{ formatDispatchStatus(result.dispatch_status) }}</span>
            </p>
            <p v-if="result.decision_id || result.decision_kind || result.decision_status" class="mt-1 text-xs text-slate-500">
              <span v-if="result.decision_kind">{{ formatDecisionKind(result.decision_kind) }}</span>
              <span v-if="result.decision_status"> · {{ formatDecisionStatus(result.decision_status) }}</span>
              <span v-if="result.effective_from"> · HL từ {{ result.effective_from }}</span>
              <span v-if="result.effective_to"> · HL đến {{ result.effective_to }}</span>
            </p>
            <p v-if="result.procurement_id || result.procurement_kind || result.procurement_status" class="mt-1 text-xs text-slate-500">
              <span v-if="result.procurement_kind">{{ formatProcurementKind(result.procurement_kind) }}</span>
              <span v-if="result.procurement_status"> · {{ formatProcurementStatus(result.procurement_status) }}</span>
              <span v-if="result.reference_number"> · {{ result.reference_number }}</span>
              <span v-if="result.requesting_unit"> · {{ result.requesting_unit }}</span>
            </p>
            <p class="mt-1 text-xs text-slate-500">
              {{ formatChunkMeta(result) }}
              <Tag v-if="result.requires_review" class="ml-2" value="review" severity="warn" />
            </p>
          </article>
        </div>
      </template>
    </Card>

    <Card>
      <template #title>Hỏi đáp (RAG)</template>
      <template #content>
        <RagAnswerPanel
          v-model:question="ragQuestion"
          :answer="ragAnswer"
          :citations="ragCitations"
          :grounded="ragGrounded"
          :confidence="ragConfidence"
          :fallback-reason="ragFallbackReason"
          :generation-mode="ragGenerationMode"
          :model-name="ragModelName"
          :latency-ms="ragLatencyMs"
          :loading="ragLoading"
          :error="ragError"
          :has-asked="ragHasAsked"
          :filter-changed-hint="ragFilterChangedHint"
          @ask="submitRagAnswer"
          @clear="clearRagPanel"
        />
      </template>
    </Card>
  </section>
</template>
