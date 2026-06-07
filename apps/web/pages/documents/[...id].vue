<script setup lang="ts">
import type { ContractStatus } from '~/types/contract'
import type { DecisionKind, DecisionStatus } from '~/types/decision'
import type { DispatchStatus, DispatchType } from '~/types/dispatch'
import type { DocumentChunk, DocumentMetadataUpdateInput } from '~/types/document'
import { formatDate, formatDateTime, formatFileSize } from '~/utils/format'

const route = useRoute()
const authStore = useAuthStore()
const {
  businessTypeOptions,
  documentTypeOptions,
  fetchCatalogOptions,
  formatBusinessType,
  formatDocumentType,
  hasDocumentType
} = useCatalogs()
const {
  contractByDocument,
  contractByDocumentLoading,
  fetchContractByDocumentId
} = useContracts()
const {
  dispatchByDocument,
  dispatchByDocumentLoading,
  fetchDispatchByDocumentId
} = useDispatches()
const {
  decisionByDocument,
  decisionByDocumentLoading,
  fetchDecisionByDocumentId
} = useDecisions()
const {
  document,
  loading,
  metadataLoading,
  reprocessLoading,
  sourceFileLoading,
  sourceFileViewLoading,
  sourceFilePreviewLoading,
  chunkReviewLoading,
  sourceFilePreview,
  error,
  fetchDocument,
  updateDocumentMetadata,
  reprocessDocument,
  addSourceFiles,
  openSourceFile,
  previewSourceFile,
  clearSourceFilePreview,
  reorderSourceFiles,
  deleteSourceFile,
  markChunkReviewed
} = useDocuments()
let pollTimer: ReturnType<typeof setInterval> | undefined
const reprocessReason = ref('')
const selectedSourceFiles = ref<File[]>([])
const lastDetailRefreshedAt = ref<Date | null>(null)
const isEditingMetadata = ref(false)
const chunkFilter = ref<'all' | 'review' | 'appendix' | 'appendix_review'>('all')
const metadataForm = reactive<DocumentMetadataUpdateInput>({
  title: '',
  document_type: 'UNKNOWN',
  classification_confidence: null,
  document_number: '',
  document_symbol: '',
  issued_date: '',
  issued_place: '',
  issuing_agency: '',
  excerpt: '',
  recipient: '',
  signer_name: '',
  signer_title: '',
  seals_present: null,
  attachment_present: null,
  page_count: null,
  business_type: ''
})

const processingStatuses = new Set([
  'ocr_pending',
  'ocr_running',
  'reprocess_pending',
  'reprocess_running',
  'chunking'
])

const documentId = computed(() => {
  const value = route.params.id
  return Array.isArray(value) ? value.join('/') : String(value)
})

const sortedOcrJobs = computed(() => {
  return [...(document.value?.ocr_jobs || [])].sort((a, b) => {
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  })
})

const sortedAuditLogs = computed(() => {
  return [...(document.value?.audit_logs || [])].sort((a, b) => {
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  })
})

const sourceFiles = computed(() => {
  return [...(document.value?.files || [])].sort((a, b) => {
    return a.file_order - b.file_order || new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  })
})

const sourceSubtitle = computed(() => {
  if (!document.value) return ''
  if (sourceFiles.value.length) return `${sourceFiles.value.length} tệp nguồn`
  return document.value.original_filename
})

const shouldPoll = computed(() => {
  const status = document.value?.status
  return Boolean(status && processingStatuses.has(status))
})

const canReprocess = computed(() => {
  const status = document.value?.status
  return Boolean(authStore.isAdmin && status && !processingStatuses.has(status))
})

const canManageSourceFiles = computed(() => canReprocess.value && !sourceFileLoading.value)
const canSaveMetadata = computed(() => Boolean(metadataForm.title.trim()) && !metadataLoading.value)

const ocrText = computed(() => {
  return document.value?.pages.map((page) => page.text).join('\n\n') || ''
})

const allChunks = computed<DocumentChunk[]>(() => document.value?.chunks || [])

const reviewChunkCount = computed(() => {
  return allChunks.value.filter((chunk) => chunk.requires_review).length
})

const appendixChunkCount = computed(() => {
  return allChunks.value.filter((chunk) => chunk.section_role === 'appendix').length
})

const filteredChunks = computed(() => {
  if (chunkFilter.value === 'review') {
    return allChunks.value.filter((chunk) => chunk.requires_review)
  }
  if (chunkFilter.value === 'appendix') {
    return allChunks.value.filter((chunk) => chunk.section_role === 'appendix')
  }
  if (chunkFilter.value === 'appendix_review') {
    return allChunks.value.filter((chunk) => chunk.section_role === 'appendix' && chunk.requires_review)
  }
  return allChunks.value
})

const {
  highlightedChunkId,
  chunkAnchorMiss,
  focusChunkFromHash
} = useDocumentChunkAnchor({ allChunks, chunkFilter })

const lastDetailRefreshText = computed(() => {
  return lastDetailRefreshedAt.value ? formatDateTime(lastDetailRefreshedAt.value.toISOString()) : ''
})

const chunkFilterOptions = [
  { label: 'Tất cả chunks', value: 'all' },
  { label: 'Cần review', value: 'review' },
  { label: 'Phụ lục', value: 'appendix' },
  { label: 'Phụ lục cần review', value: 'appendix_review' }
]

function isActiveJob(status: string): boolean {
  return status.includes('pending') || status.includes('running')
}

function markDetailRefreshed() {
  lastDetailRefreshedAt.value = new Date()
}

function syncMetadataForm() {
  if (!document.value) return
  metadataForm.title = document.value.title || ''
  metadataForm.document_type = hasDocumentType(document.value.document_type)
    ? document.value.document_type
    : 'UNKNOWN'
  metadataForm.classification_confidence = document.value.classification_confidence ?? null
  metadataForm.document_number = document.value.document_number || ''
  metadataForm.document_symbol = document.value.document_symbol || ''
  metadataForm.issued_date = document.value.issued_date || ''
  metadataForm.issued_place = document.value.issued_place || ''
  metadataForm.issuing_agency = document.value.issuing_agency || ''
  metadataForm.excerpt = document.value.excerpt || ''
  metadataForm.recipient = document.value.recipient || ''
  metadataForm.signer_name = document.value.signer_name || ''
  metadataForm.signer_title = document.value.signer_title || ''
  metadataForm.seals_present = document.value.seals_present ?? null
  metadataForm.attachment_present = document.value.attachment_present ?? null
  metadataForm.page_count = document.value.page_count ?? null
  metadataForm.business_type = document.value.business_type || ''
}

function formatAuditAction(action: string): string {
  if (action === 'document.upload') return 'Upload văn bản'
  if (action === 'document.upload_zip') return 'Upload zip'
  if (action === 'document.reprocess_requested') return 'Yêu cầu reprocess'
  if (action === 'document.source_files_added') return 'Thêm tệp nguồn'
  if (action === 'document.source_files_reordered') return 'Đổi thứ tự tệp nguồn'
  if (action === 'document.source_file_deleted') return 'Xóa tệp nguồn'
  if (action === 'document.metadata_auto_extracted') return 'Tự trích xuất metadata'
  if (action === 'document.metadata_updated') return 'Cập nhật metadata'
  if (action === 'document_chunk.reviewed') return 'Đã review chunk'
  return action
}

function formatBoolean(value?: boolean | null): string {
  if (value === true) return 'Có'
  if (value === false) return 'Không'
  return '-'
}

const contractStatusLabels: Record<ContractStatus, string> = {
  draft: 'Nháp',
  active: 'Đang hiệu lực',
  expired: 'Hết hạn',
  terminated: 'Chấm dứt',
  completed: 'Hoàn thành'
}

function formatContractStatus(status?: ContractStatus | null) {
  return status ? contractStatusLabels[status] || status : '-'
}

function formatContractValue(value?: string | number | null, currency = 'VND') {
  if (value === undefined || value === null || value === '') return '-'
  const amount = Number(value)
  if (Number.isNaN(amount)) return `${value} ${currency}`
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0
  }).format(amount)
}

const contractsPageLink = computed(() => `/contracts?document_id=${encodeURIComponent(documentId.value)}`)
const createContractLink = computed(() => `${contractsPageLink.value}&create=1`)
const dispatchesPageLink = computed(() => `/dispatches?document_id=${encodeURIComponent(documentId.value)}`)
const createDispatchLink = computed(() => `${dispatchesPageLink.value}&create=1`)
const decisionsPageLink = computed(() => `/decisions?document_id=${encodeURIComponent(documentId.value)}`)
const createDecisionLink = computed(() => `${decisionsPageLink.value}&create=1`)

const decisionKindLabels: Record<DecisionKind, string> = {
  decision: 'Quyết định',
  notification: 'Thông báo'
}

const decisionStatusLabels: Record<DecisionStatus, string> = {
  draft: 'Nháp',
  registered: 'Đã vào sổ',
  effective: 'Đang hiệu lực',
  expired: 'Hết hiệu lực',
  revoked: 'Đã thu hồi',
  archived: 'Lưu trữ'
}

function formatDecisionKind(kind?: DecisionKind | null) {
  return kind ? decisionKindLabels[kind] || kind : '-'
}

function formatDecisionStatus(status?: DecisionStatus | null) {
  return status ? decisionStatusLabels[status] || status : '-'
}

const dispatchTypeLabels: Record<DispatchType, string> = {
  incoming: 'Công văn đến',
  outgoing: 'Công văn đi'
}

const dispatchStatusLabels: Record<DispatchStatus, string> = {
  draft: 'Nháp',
  registered: 'Đã vào sổ',
  processing: 'Đang xử lý',
  completed: 'Hoàn thành',
  archived: 'Lưu trữ'
}

function formatDispatchType(type?: DispatchType | null) {
  return type ? dispatchTypeLabels[type] || type : '-'
}

function formatDispatchStatus(status?: DispatchStatus | null) {
  return status ? dispatchStatusLabels[status] || status : '-'
}

function formatConfidence(value?: number | null): string {
  if (value === null || value === undefined) return '-'
  return `${Math.round(value * 100)}%`
}

function formatMetadataSource(value?: string | null): string {
  if (value === 'auto') return 'Tự động'
  if (value === 'manual') return 'Thủ công'
  if (value === 'mixed') return 'Kết hợp'
  return value || '-'
}

function formatChunkRole(value?: string | null): string {
  const labels: Record<string, string> = {
    header: 'Phần đầu',
    legal_basis: 'Căn cứ',
    promulgation: 'Ban hành',
    chapter: 'Chương',
    article: 'Điều',
    clause: 'Khoản',
    point: 'Điểm',
    task: 'Nhiệm vụ',
    appendix: 'Phụ lục',
    recipient: 'Nơi nhận',
    table: 'Bảng',
    signature: 'Chữ ký',
    unknown: 'Không xác định'
  }
  return value ? labels[value] || value : '-'
}

function formatChunkPath(path?: string[] | null): string {
  return path?.length ? path.join(' > ') : '-'
}

function formatAuditMetadataValue(value: unknown): string {
  if (value === null || value === undefined || value === '') return '-'
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return String(value)
  return JSON.stringify(value)
}

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
    markDetailRefreshed()
    if (!shouldPoll.value) stopPolling()
  }, 3000)
}

async function submitReprocess() {
  if (!document.value || !canReprocess.value) return
  const confirmed = window.confirm(
    'Reprocess sẽ OCR lại tài liệu này và thay thế page/chunk hiện có. Metadata đã sửa thủ công sẽ không bị ghi đè. Tiếp tục?'
  )
  if (!confirmed) return

  const result = await reprocessDocument(document.value.id, reprocessReason.value)
  if (!result) return

  reprocessReason.value = ''
  await fetchDocument(documentId.value, { silent: true })
  markDetailRefreshed()
  if (shouldPoll.value) startPolling()
}

async function submitMetadataUpdate() {
  if (!document.value || !canSaveMetadata.value) return
  const result = await updateDocumentMetadata(document.value.id, metadataForm)
  if (!result) return
  isEditingMetadata.value = false
  await fetchDocument(documentId.value, { silent: true })
  syncMetadataForm()
  markDetailRefreshed()
}

function cancelMetadataEdit() {
  syncMetadataForm()
  isEditingMetadata.value = false
}

function handleSourceFilesSelected(files: File[]) {
  selectedSourceFiles.value = files
}

async function submitAddSourceFiles() {
  if (!document.value || !selectedSourceFiles.value.length || !canManageSourceFiles.value) return
  const result = await addSourceFiles(document.value.id, selectedSourceFiles.value)
  if (!result) return
  selectedSourceFiles.value = []
  await refreshAfterSourceFileMutation()
}

async function moveSourceFile(fileId: string, direction: 'up' | 'down') {
  if (!document.value || !canManageSourceFiles.value) return
  const ids = sourceFiles.value.map((file) => file.id)
  const index = ids.indexOf(fileId)
  const targetIndex = direction === 'up' ? index - 1 : index + 1
  if (index < 0 || targetIndex < 0 || targetIndex >= ids.length) return
  const [file] = ids.splice(index, 1)
  ids.splice(targetIndex, 0, file)
  const result = await reorderSourceFiles(document.value.id, ids)
  if (!result) return
  await refreshAfterSourceFileMutation()
}

async function submitDeleteSourceFile(fileId: string, filename: string) {
  if (!document.value || !canManageSourceFiles.value) return
  const confirmed = window.confirm(`Xóa tệp nguồn "${filename}" và OCR lại văn bản này?`)
  if (!confirmed) return
  const result = await deleteSourceFile(document.value.id, fileId)
  if (!result) return
  await refreshAfterSourceFileMutation()
}

async function submitMarkChunkReviewed(chunk: DocumentChunk) {
  if (!document.value || !authStore.isAdmin || !chunk.requires_review) return
  const result = await markChunkReviewed(document.value.id, chunk.id)
  if (!result) return
  await fetchDocument(documentId.value, { silent: true })
  markDetailRefreshed()
}

async function submitOpenSourceFile(fileId: string) {
  if (!document.value) return
  const file = sourceFiles.value.find((sourceFile) => sourceFile.id === fileId)
  if (!file) return
  await openSourceFile(document.value.id, file)
}

async function submitPreviewSourceFile(fileId: string) {
  if (!document.value) return
  const file = sourceFiles.value.find((sourceFile) => sourceFile.id === fileId)
  if (!file) return
  await previewSourceFile(document.value.id, file)
}

async function refreshAfterSourceFileMutation() {
  clearSourceFilePreview()
  await fetchDocument(documentId.value, { silent: true })
  markDetailRefreshed()
  if (shouldPoll.value) startPolling()
}

onMounted(async () => {
  await Promise.all([
    fetchCatalogOptions(),
    fetchDocument(documentId.value),
    fetchContractByDocumentId(documentId.value),
    fetchDispatchByDocumentId(documentId.value),
    fetchDecisionByDocumentId(documentId.value)
  ])
  syncMetadataForm()
  markDetailRefreshed()
  if (shouldPoll.value) startPolling()
  await focusChunkFromHash()
})

watch(documentId, async (value) => {
  await Promise.all([
    fetchDocument(value),
    fetchContractByDocumentId(value),
    fetchDispatchByDocumentId(value),
    fetchDecisionByDocumentId(value)
  ])
  syncMetadataForm()
  markDetailRefreshed()
  if (shouldPoll.value) startPolling()
  else stopPolling()
  await focusChunkFromHash()
})

watch(shouldPoll, (value) => {
  if (value) startPolling()
  else stopPolling()
})

onBeforeUnmount(() => {
  stopPolling()
  clearSourceFilePreview()
})
</script>

<template>
  <section class="space-y-5">
    <Message v-if="error" severity="error">{{ error }}</Message>
    <p v-if="loading" class="text-sm text-slate-600">Đang tải...</p>

    <template v-if="document">
      <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 class="break-words text-2xl font-semibold">{{ document.title }}</h1>
          <p class="mt-1 break-words text-sm text-slate-600">{{ sourceSubtitle }}</p>
          <p v-if="lastDetailRefreshText" class="mt-1 text-xs text-slate-500">
            Cập nhật detail lần cuối: {{ lastDetailRefreshText }}
          </p>
        </div>
        <BaseStatusBadge :status="document.status" />
      </div>

      <Card>
        <template #title>Hợp đồng</template>
        <template #content>
          <p v-if="contractByDocumentLoading" class="text-sm text-slate-600">Đang kiểm tra metadata hợp đồng...</p>
          <div v-else-if="contractByDocument" class="space-y-3">
            <div class="grid gap-3 sm:grid-cols-2">
              <div>
                <p class="text-xs text-slate-500">Số hợp đồng</p>
                <p class="font-medium">{{ contractByDocument.contract_number || '-' }}</p>
              </div>
              <div>
                <p class="text-xs text-slate-500">Nhà cung cấp</p>
                <p class="font-medium">{{ contractByDocument.supplier_name || '-' }}</p>
              </div>
              <div>
                <p class="text-xs text-slate-500">Trạng thái</p>
                <p class="font-medium">{{ formatContractStatus(contractByDocument.status) }}</p>
              </div>
              <div>
                <p class="text-xs text-slate-500">Giá trị</p>
                <p class="font-medium">{{ formatContractValue(contractByDocument.contract_value, contractByDocument.currency) }}</p>
              </div>
              <div>
                <p class="text-xs text-slate-500">Ngày ký</p>
                <p class="font-medium">{{ formatDate(contractByDocument.sign_date) }}</p>
              </div>
              <div>
                <p class="text-xs text-slate-500">Hiệu lực</p>
                <p class="font-medium">
                  {{ formatDate(contractByDocument.effective_from) }} - {{ formatDate(contractByDocument.effective_to) }}
                </p>
              </div>
            </div>
            <div class="flex flex-wrap gap-2">
              <NuxtLink :to="contractsPageLink">
                <Button label="Mở Contracts" icon="pi pi-briefcase" severity="secondary" size="small" />
              </NuxtLink>
            </div>
          </div>
          <div v-else class="space-y-3">
            <p class="text-sm text-slate-600">Văn bản này chưa có metadata hợp đồng liên kết.</p>
            <NuxtLink :to="createContractLink">
              <Button label="Tạo metadata hợp đồng" icon="pi pi-plus" size="small" />
            </NuxtLink>
          </div>
        </template>
      </Card>

      <Card>
        <template #title>Công văn</template>
        <template #content>
          <p v-if="dispatchByDocumentLoading" class="text-sm text-slate-600">Đang kiểm tra metadata công văn...</p>
          <div v-else-if="dispatchByDocument" class="space-y-3">
            <div class="grid gap-3 sm:grid-cols-2">
              <div>
                <p class="text-xs text-slate-500">Loại</p>
                <p class="font-medium">{{ formatDispatchType(dispatchByDocument.dispatch_type) }}</p>
              </div>
              <div>
                <p class="text-xs text-slate-500">Số công văn</p>
                <p class="font-medium">{{ dispatchByDocument.document_number || '-' }}</p>
              </div>
              <div>
                <p class="text-xs text-slate-500">Đơn vị ban hành</p>
                <p class="font-medium">{{ dispatchByDocument.issuing_agency || '-' }}</p>
              </div>
              <div>
                <p class="text-xs text-slate-500">Trạng thái</p>
                <p class="font-medium">{{ formatDispatchStatus(dispatchByDocument.status) }}</p>
              </div>
              <div>
                <p class="text-xs text-slate-500">Ngày ban hành</p>
                <p class="font-medium">{{ formatDate(dispatchByDocument.issued_date) }}</p>
              </div>
              <div>
                <p class="text-xs text-slate-500">Nơi nhận</p>
                <p class="font-medium">{{ dispatchByDocument.recipient || '-' }}</p>
              </div>
              <div class="sm:col-span-2">
                <p class="text-xs text-slate-500">Trích yếu</p>
                <p class="font-medium">{{ dispatchByDocument.excerpt || '-' }}</p>
              </div>
            </div>
            <div class="flex flex-wrap gap-2">
              <NuxtLink :to="dispatchesPageLink">
                <Button label="Mở Công văn" icon="pi pi-envelope" severity="secondary" size="small" />
              </NuxtLink>
            </div>
          </div>
          <div v-else class="space-y-3">
            <p class="text-sm text-slate-600">Văn bản này chưa có metadata công văn liên kết.</p>
            <NuxtLink :to="createDispatchLink">
              <Button label="Tạo metadata công văn" icon="pi pi-plus" size="small" />
            </NuxtLink>
          </div>
        </template>
      </Card>

      <Card>
        <template #title>Quyết định & thông báo</template>
        <template #content>
          <p v-if="decisionByDocumentLoading" class="text-sm text-slate-600">Đang kiểm tra metadata quyết định/thông báo...</p>
          <div v-else-if="decisionByDocument" class="space-y-3">
            <div class="grid gap-3 sm:grid-cols-2">
              <div>
                <p class="text-xs text-slate-500">Loại</p>
                <p class="font-medium">{{ formatDecisionKind(decisionByDocument.decision_kind) }}</p>
              </div>
              <div>
                <p class="text-xs text-slate-500">Số văn bản</p>
                <p class="font-medium">{{ decisionByDocument.document_number || '-' }}</p>
              </div>
              <div>
                <p class="text-xs text-slate-500">Đơn vị ban hành</p>
                <p class="font-medium">{{ decisionByDocument.issuing_agency || '-' }}</p>
              </div>
              <div>
                <p class="text-xs text-slate-500">Trạng thái</p>
                <p class="font-medium">{{ formatDecisionStatus(decisionByDocument.status) }}</p>
              </div>
              <div>
                <p class="text-xs text-slate-500">Ngày ban hành</p>
                <p class="font-medium">{{ formatDate(decisionByDocument.issued_date) }}</p>
              </div>
              <div>
                <p class="text-xs text-slate-500">Hiệu lực</p>
                <p class="font-medium">
                  {{ formatDate(decisionByDocument.effective_from) }} - {{ formatDate(decisionByDocument.effective_to) }}
                </p>
              </div>
              <div class="sm:col-span-2">
                <p class="text-xs text-slate-500">Trích yếu</p>
                <p class="font-medium">{{ decisionByDocument.excerpt || '-' }}</p>
              </div>
            </div>
            <div class="flex flex-wrap gap-2">
              <NuxtLink :to="decisionsPageLink">
                <Button label="Mở Quyết định" icon="pi pi-file-edit" severity="secondary" size="small" />
              </NuxtLink>
            </div>
          </div>
          <div v-else class="space-y-3">
            <p class="text-sm text-slate-600">Văn bản này chưa có metadata quyết định/thông báo liên kết.</p>
            <NuxtLink :to="createDecisionLink">
              <Button label="Tạo metadata quyết định/thông báo" icon="pi pi-plus" size="small" />
            </NuxtLink>
          </div>
        </template>
      </Card>

      <Card>
        <template #title>
          <div class="flex flex-wrap items-center justify-between gap-2">
            <span>Metadata</span>
            <Button
              v-if="!isEditingMetadata"
              label="Sửa metadata"
              icon="pi pi-pencil"
              severity="secondary"
              size="small"
              @click="isEditingMetadata = true"
            />
          </div>
        </template>
        <template #content>
          <form v-if="isEditingMetadata" class="space-y-4" @submit.prevent="submitMetadataUpdate">
            <div class="grid gap-3 sm:grid-cols-2">
              <div class="space-y-2 sm:col-span-2">
                <label for="metadata-title" class="block text-sm font-medium text-slate-700">Tên văn bản *</label>
                <InputText
                  id="metadata-title"
                  v-model="metadataForm.title"
                  class="w-full"
                  maxlength="512"
                  :disabled="metadataLoading"
                />
              </div>
              <div class="space-y-2">
                <label for="metadata-document-type" class="block text-sm font-medium text-slate-700">Loại văn bản hành chính</label>
                <select
                  id="metadata-document-type"
                  v-model="metadataForm.document_type"
                  class="w-full rounded border border-slate-300 px-3 py-2 text-sm"
                  :disabled="metadataLoading"
                >
                  <option v-for="option in documentTypeOptions" :key="option.value" :value="option.value">
                    {{ option.label }} ({{ option.value }})
                  </option>
                </select>
              </div>
              <div class="space-y-2">
                <label for="metadata-confidence" class="block text-sm font-medium text-slate-700">Độ tin cậy OCR metadata</label>
                <InputText
                  id="metadata-confidence"
                  :model-value="formatConfidence(metadataForm.classification_confidence)"
                  class="w-full"
                  disabled
                />
              </div>
              <div class="space-y-2">
                <label for="metadata-number" class="block text-sm font-medium text-slate-700">Số văn bản</label>
                <InputText
                  id="metadata-number"
                  v-model="metadataForm.document_number"
                  class="w-full"
                  maxlength="128"
                  :disabled="metadataLoading"
                />
              </div>
              <div class="space-y-2">
                <label for="metadata-symbol" class="block text-sm font-medium text-slate-700">Ký hiệu văn bản</label>
                <InputText
                  id="metadata-symbol"
                  v-model="metadataForm.document_symbol"
                  class="w-full"
                  maxlength="128"
                  :disabled="metadataLoading"
                />
              </div>
              <div class="space-y-2">
                <label for="metadata-issued-date" class="block text-sm font-medium text-slate-700">Ngày ban hành</label>
                <InputText
                  id="metadata-issued-date"
                  v-model="metadataForm.issued_date"
                  class="w-full"
                  type="date"
                  :disabled="metadataLoading"
                />
              </div>
              <div class="space-y-2">
                <label for="metadata-issued-place" class="block text-sm font-medium text-slate-700">Địa danh ban hành</label>
                <InputText
                  id="metadata-issued-place"
                  v-model="metadataForm.issued_place"
                  class="w-full"
                  maxlength="255"
                  :disabled="metadataLoading"
                />
              </div>
              <div class="space-y-2">
                <label for="metadata-agency" class="block text-sm font-medium text-slate-700">Đơn vị ban hành</label>
                <InputText
                  id="metadata-agency"
                  v-model="metadataForm.issuing_agency"
                  class="w-full"
                  maxlength="255"
                  :disabled="metadataLoading"
                />
              </div>
              <div class="space-y-2 sm:col-span-2">
                <label for="metadata-excerpt" class="block text-sm font-medium text-slate-700">Trích yếu</label>
                <Textarea
                  id="metadata-excerpt"
                  v-model="metadataForm.excerpt"
                  class="w-full"
                  rows="3"
                  :disabled="metadataLoading"
                />
              </div>
              <div class="space-y-2 sm:col-span-2">
                <label for="metadata-recipient" class="block text-sm font-medium text-slate-700">Nơi nhận / người nhận</label>
                <Textarea
                  id="metadata-recipient"
                  v-model="metadataForm.recipient"
                  class="w-full"
                  rows="3"
                  :disabled="metadataLoading"
                />
              </div>
              <div class="space-y-2">
                <label for="metadata-signer-name" class="block text-sm font-medium text-slate-700">Người ký</label>
                <InputText
                  id="metadata-signer-name"
                  v-model="metadataForm.signer_name"
                  class="w-full"
                  maxlength="255"
                  :disabled="metadataLoading"
                />
              </div>
              <div class="space-y-2">
                <label for="metadata-signer-title" class="block text-sm font-medium text-slate-700">Chức vụ người ký</label>
                <InputText
                  id="metadata-signer-title"
                  v-model="metadataForm.signer_title"
                  class="w-full"
                  maxlength="255"
                  :disabled="metadataLoading"
                />
              </div>
              <div class="space-y-2">
                <label for="metadata-seals" class="block text-sm font-medium text-slate-700">Dấu cơ quan</label>
                <select
                  id="metadata-seals"
                  v-model="metadataForm.seals_present"
                  class="w-full rounded border border-slate-300 px-3 py-2 text-sm"
                  :disabled="metadataLoading"
                >
                  <option :value="null">Chưa xác định</option>
                  <option :value="true">Có</option>
                  <option :value="false">Không</option>
                </select>
              </div>
              <div class="space-y-2">
                <label for="metadata-attachment" class="block text-sm font-medium text-slate-700">Phụ lục / tệp kèm</label>
                <select
                  id="metadata-attachment"
                  v-model="metadataForm.attachment_present"
                  class="w-full rounded border border-slate-300 px-3 py-2 text-sm"
                  :disabled="metadataLoading"
                >
                  <option :value="null">Chưa xác định</option>
                  <option :value="true">Có</option>
                  <option :value="false">Không</option>
                </select>
              </div>
              <div class="space-y-2">
                <label for="metadata-page-count" class="block text-sm font-medium text-slate-700">Số trang</label>
                <InputNumber
                  id="metadata-page-count"
                  v-model="metadataForm.page_count"
                  class="w-full"
                  input-class="w-full"
                  :min="1"
                  :disabled="metadataLoading"
                />
              </div>
              <div class="space-y-2">
                <label for="metadata-business-type" class="block text-sm font-medium text-slate-700">Loại nghiệp vụ</label>
                <select
                  id="metadata-business-type"
                  v-model="metadataForm.business_type"
                  class="w-full rounded border border-slate-300 px-3 py-2 text-sm"
                  :disabled="metadataLoading"
                >
                  <option v-for="option in businessTypeOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
              </div>
            </div>
            <div class="flex flex-wrap gap-2">
              <Button
                type="submit"
                label="Lưu metadata"
                icon="pi pi-save"
                :disabled="!canSaveMetadata"
                :loading="metadataLoading"
              />
              <Button
                type="button"
                label="Hủy"
                icon="pi pi-times"
                severity="secondary"
                :disabled="metadataLoading"
                @click="cancelMetadataEdit"
              />
            </div>
          </form>

          <dl v-else class="grid gap-3 text-sm sm:grid-cols-2">
            <div>
              <dt class="text-slate-500">Loại văn bản</dt>
              <dd class="font-medium">{{ formatDocumentType(document.document_type) }}</dd>
            </div>
            <div>
              <dt class="text-slate-500">Độ tin cậy</dt>
              <dd class="font-medium">{{ formatConfidence(document.classification_confidence) }}</dd>
            </div>
            <div>
              <dt class="text-slate-500">Loại nghiệp vụ</dt>
              <dd class="font-medium">{{ formatBusinessType(document.business_type) }}</dd>
            </div>
            <div>
              <dt class="text-slate-500">Nguồn metadata</dt>
              <dd class="font-medium">{{ formatMetadataSource(document.metadata_source) }}</dd>
            </div>
            <div>
              <dt class="text-slate-500">Số văn bản</dt>
              <dd class="break-words font-medium">{{ document.document_number || '-' }}</dd>
            </div>
            <div>
              <dt class="text-slate-500">Ký hiệu</dt>
              <dd class="break-words font-medium">{{ document.document_symbol || '-' }}</dd>
            </div>
            <div>
              <dt class="text-slate-500">Ngày ban hành</dt>
              <dd class="font-medium">{{ formatDate(document.issued_date) }}</dd>
            </div>
            <div>
              <dt class="text-slate-500">Địa danh</dt>
              <dd class="break-words font-medium">{{ document.issued_place || '-' }}</dd>
            </div>
            <div>
              <dt class="text-slate-500">Đơn vị ban hành</dt>
              <dd class="break-words font-medium">{{ document.issuing_agency || '-' }}</dd>
            </div>
            <div>
              <dt class="text-slate-500">Số trang</dt>
              <dd class="font-medium">{{ document.page_count || '-' }}</dd>
            </div>
            <div class="sm:col-span-2">
              <dt class="text-slate-500">Trích yếu</dt>
              <dd class="break-words font-medium">{{ document.excerpt || '-' }}</dd>
            </div>
            <div class="sm:col-span-2">
              <dt class="text-slate-500">Nơi nhận / người nhận</dt>
              <dd class="break-words font-medium">{{ document.recipient || '-' }}</dd>
            </div>
            <div>
              <dt class="text-slate-500">Người ký</dt>
              <dd class="break-words font-medium">{{ document.signer_name || '-' }}</dd>
            </div>
            <div>
              <dt class="text-slate-500">Chức vụ người ký</dt>
              <dd class="break-words font-medium">{{ document.signer_title || '-' }}</dd>
            </div>
            <div>
              <dt class="text-slate-500">Dấu cơ quan</dt>
              <dd class="font-medium">{{ formatBoolean(document.seals_present) }}</dd>
            </div>
            <div>
              <dt class="text-slate-500">Phụ lục / tệp kèm</dt>
              <dd class="font-medium">{{ formatBoolean(document.attachment_present) }}</dd>
            </div>
            <div>
              <dt class="text-slate-500">Đã review metadata</dt>
              <dd class="font-medium">{{ document.metadata_reviewed_at ? formatDateTime(document.metadata_reviewed_at) : '-' }}</dd>
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
        <template #title>Tệp nguồn</template>
        <template #content>
          <div v-if="authStore.isAdmin" class="mb-4 space-y-3 rounded border border-slate-200 bg-slate-50 p-3">
            <BaseUploadDropzone :multiple="true" @selected="handleSourceFilesSelected" />
            <div v-if="selectedSourceFiles.length" class="space-y-2 text-sm">
              <p class="font-medium">Tệp sẽ thêm: {{ selectedSourceFiles.length }}</p>
              <ul class="space-y-1 text-slate-700">
                <li v-for="(file, index) in selectedSourceFiles" :key="`${file.name}-${index}`" class="break-words">
                  {{ index + 1 }}. {{ file.name }} · {{ formatFileSize(file.size) }}
                </li>
              </ul>
            </div>
            <div class="flex flex-wrap items-center gap-3">
              <Button
                label="Thêm tệp nguồn"
                icon="pi pi-plus"
                :disabled="!selectedSourceFiles.length || !canManageSourceFiles"
                :loading="sourceFileLoading"
                @click="submitAddSourceFiles"
              />
              <p v-if="!canManageSourceFiles" class="text-sm text-slate-600">
                Chỉ đổi tệp nguồn khi document không có job đang xử lý.
              </p>
            </div>
          </div>
          <p v-else class="mb-4 rounded border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600">
            Chỉ admin được thêm, đổi thứ tự hoặc xóa tệp nguồn.
          </p>

          <div v-if="sourceFiles.length" class="space-y-3 text-sm">
            <article
              v-for="(file, index) in sourceFiles"
              :key="file.id"
              class="rounded border border-slate-200 p-3"
            >
              <div class="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p class="break-words font-medium">{{ file.file_order + 1 }}. {{ file.original_filename }}</p>
                  <p class="mt-1 text-xs text-slate-600">
                    {{ formatFileSize(file.file_size) }} · {{ file.content_type || 'Không xác định' }}
                  </p>
                </div>
                <div class="flex flex-wrap items-center gap-2">
                  <BaseStatusBadge :status="file.status" />
                  <Button
                    label="Xem trước"
                    icon="pi pi-eye"
                    severity="secondary"
                    size="small"
                    :loading="sourceFilePreviewLoading === file.id"
                    @click="submitPreviewSourceFile(file.id)"
                  />
                  <Button
                    label="Mở"
                    icon="pi pi-external-link"
                    severity="secondary"
                    size="small"
                    :loading="sourceFileViewLoading === file.id"
                    @click="submitOpenSourceFile(file.id)"
                  />
                  <Button
                    icon="pi pi-arrow-up"
                    severity="secondary"
                    size="small"
                    :disabled="index === 0 || !canManageSourceFiles"
                    :loading="sourceFileLoading"
                    @click="moveSourceFile(file.id, 'up')"
                  />
                  <Button
                    icon="pi pi-arrow-down"
                    severity="secondary"
                    size="small"
                    :disabled="index === sourceFiles.length - 1 || !canManageSourceFiles"
                    :loading="sourceFileLoading"
                    @click="moveSourceFile(file.id, 'down')"
                  />
                  <Button
                    icon="pi pi-trash"
                    severity="danger"
                    size="small"
                    :disabled="sourceFiles.length <= 1 || !canManageSourceFiles"
                    :loading="sourceFileLoading"
                    @click="submitDeleteSourceFile(file.id, file.original_filename)"
                  />
                </div>
              </div>
            </article>
          </div>
          <div v-if="sourceFilePreview" class="mt-4 rounded border border-slate-200 bg-white">
            <div class="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 p-3">
              <div>
                <p class="break-words text-sm font-medium">{{ sourceFilePreview.file.original_filename }}</p>
                <p class="text-xs text-slate-500">
                  Xem trước inline · {{ sourceFilePreview.file.content_type || 'Không xác định' }}
                </p>
              </div>
              <Button
                label="Đóng preview"
                icon="pi pi-times"
                severity="secondary"
                size="small"
                @click="clearSourceFilePreview"
              />
            </div>
            <div class="min-h-64 overflow-hidden bg-slate-50">
              <iframe
                v-if="sourceFilePreview.mode === 'pdf'"
                :src="sourceFilePreview.object_url"
                title="Preview PDF"
                class="h-[70vh] w-full border-0"
              />
              <div v-else-if="sourceFilePreview.mode === 'image'" class="flex max-h-[70vh] items-start justify-center overflow-auto p-3">
                <img
                  :src="sourceFilePreview.object_url"
                  :alt="sourceFilePreview.file.original_filename"
                  class="max-h-[68vh] max-w-full object-contain"
                />
              </div>
              <pre
                v-else
                class="max-h-[70vh] overflow-auto whitespace-pre-wrap break-words p-4 text-sm leading-6 text-slate-800"
              >{{ sourceFilePreview.text }}</pre>
            </div>
          </div>
          <p v-if="!sourceFiles.length" class="break-words text-sm text-slate-600">
            Tệp nguồn cũ: {{ document.original_filename }}
          </p>
        </template>
      </Card>

      <Card>
        <template #title>Reprocess</template>
        <template #content>
          <div class="space-y-3">
            <Textarea
              v-model="reprocessReason"
              class="w-full"
              rows="3"
              maxlength="500"
              placeholder="Lý do reprocess, ví dụ: kiểm tra lại OCR sau khi tối ưu engine"
              :disabled="!canReprocess || reprocessLoading"
            />
            <div class="flex flex-wrap items-center gap-3">
              <Button
                label="Reprocess"
                icon="pi pi-refresh"
                :disabled="!canReprocess"
                :loading="reprocessLoading"
                @click="submitReprocess"
              />
              <p v-if="!authStore.isAdmin" class="text-sm text-slate-600">
                Chỉ admin được reprocess văn bản.
              </p>
              <p v-else-if="!canReprocess" class="text-sm text-slate-600">
                Document đang xử lý nên chưa thể reprocess.
              </p>
            </div>
            <p v-if="shouldPoll" class="text-sm text-slate-600">Đang tự cập nhật trạng thái OCR/reprocess...</p>
            <p v-if="lastDetailRefreshText" class="text-xs text-slate-500">
              Lần refresh gần nhất: {{ lastDetailRefreshText }}
            </p>
          </div>
        </template>
      </Card>

      <Card>
        <template #title>Job audit</template>
        <template #content>
          <div v-if="sortedOcrJobs.length" class="space-y-3 text-sm">
            <article
              v-for="job in sortedOcrJobs"
              :key="job.id"
              class="rounded border p-3"
              :class="isActiveJob(job.status) ? 'border-amber-300 bg-amber-50' : 'border-slate-200'"
            >
              <div class="flex flex-wrap items-center justify-between gap-2">
                <div class="flex flex-wrap items-center gap-2">
                  <Tag :value="job.job_type" severity="info" />
                  <BaseStatusBadge :status="job.status" />
                  <Tag v-if="isActiveJob(job.status)" value="Đang xử lý" severity="warn" />
                </div>
                <span class="text-xs text-slate-500">{{ formatDateTime(job.created_at) }}</span>
              </div>
              <dl class="mt-3 grid gap-2 sm:grid-cols-2">
                <div>
                  <dt class="text-slate-500">Job ID</dt>
                  <dd class="break-all font-medium">{{ job.id }}</dd>
                </div>
                <div>
                  <dt class="text-slate-500">Số lần thử</dt>
                  <dd class="font-medium">{{ job.attempts }}/{{ job.max_attempts }}</dd>
                </div>
                <div>
                  <dt class="text-slate-500">Cập nhật</dt>
                  <dd class="font-medium">{{ formatDateTime(job.updated_at) }}</dd>
                </div>
                <div v-if="job.next_run_at">
                  <dt class="text-slate-500">Thử lại lúc</dt>
                  <dd class="font-medium">{{ formatDateTime(job.next_run_at) }}</dd>
                </div>
                <div v-if="job.failed_reason">
                  <dt class="text-slate-500">Nhóm lỗi</dt>
                  <dd class="break-words font-medium">{{ job.failed_reason }}</dd>
                </div>
                <div v-if="job.reason">
                  <dt class="text-slate-500">Lý do</dt>
                  <dd class="break-words font-medium">{{ job.reason }}</dd>
                </div>
              </dl>
              <Message v-if="job.error_message" class="mt-3" severity="error">
                {{ job.error_message }}
              </Message>
            </article>
          </div>
          <p v-else class="text-sm text-slate-600">Chưa có OCR/reprocess job.</p>
        </template>
      </Card>

      <Card>
        <template #title>Admin audit log</template>
        <template #content>
          <div v-if="sortedAuditLogs.length" class="space-y-3 text-sm">
            <article v-for="event in sortedAuditLogs" :key="event.id" class="rounded border border-slate-200 p-3">
              <div class="flex flex-wrap items-center justify-between gap-2">
                <div class="flex flex-wrap items-center gap-2">
                  <Tag :value="formatAuditAction(event.action)" severity="info" />
                  <span class="text-slate-700">
                    {{ event.actor?.full_name || event.actor?.email || 'Không xác định' }}
                  </span>
                </div>
                <span class="text-xs text-slate-500">{{ formatDateTime(event.created_at) }}</span>
              </div>
              <dl class="mt-3 grid gap-2 sm:grid-cols-2">
                <div>
                  <dt class="text-slate-500">Event ID</dt>
                  <dd class="break-all font-medium">{{ event.id }}</dd>
                </div>
                <div v-for="(value, key) in event.metadata" :key="key">
                  <dt class="text-slate-500">{{ key }}</dt>
                  <dd class="break-words font-medium">{{ formatAuditMetadataValue(value) }}</dd>
                </div>
              </dl>
            </article>
          </div>
          <p v-else class="text-sm text-slate-600">Chưa có audit log admin.</p>
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
        <template #title>
          <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <span>Chunks</span>
              <p class="mt-1 text-xs font-normal text-slate-500">
                Tổng {{ allChunks.length }} · Cần review {{ reviewChunkCount }} · Phụ lục {{ appendixChunkCount }}
              </p>
            </div>
            <select
              v-model="chunkFilter"
              class="w-full rounded border border-slate-300 px-3 py-2 text-sm sm:w-56"
            >
              <option v-for="option in chunkFilterOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>
        </template>
        <template #content>
          <Message v-if="chunkAnchorMiss" class="mb-4" severity="warn" :closable="false">
            Không tìm thấy đoạn đã liên kết trong danh sách chunks.
          </Message>
          <div v-if="allChunks.length && filteredChunks.length" class="space-y-3">
            <article
              v-for="chunk in filteredChunks"
              :id="`chunk-${chunk.id}`"
              :key="chunk.id"
              class="scroll-mt-4 border-b border-slate-200 pb-3"
              :class="{
                'rounded-md bg-sky-50/50 ring-2 ring-sky-400 ring-offset-2': highlightedChunkId === chunk.id
              }"
            >
              <div class="flex flex-wrap items-center gap-2 text-xs">
                <span class="text-slate-500">#{{ chunk.chunk_index }}</span>
                <Tag v-if="chunk.doc_group" :value="`Nhóm ${chunk.doc_group}`" severity="info" />
                <Tag
                  v-if="chunk.section_role"
                  :value="formatChunkRole(chunk.section_role)"
                  :severity="chunk.section_role === 'appendix' ? 'success' : 'secondary'"
                />
                <Tag v-if="chunk.requires_review" value="Cần review" severity="warn" />
                <span v-if="chunk.chunk_confidence !== null && chunk.chunk_confidence !== undefined" class="text-slate-500">
                  {{ formatConfidence(chunk.chunk_confidence) }}
                </span>
                <Button
                  v-if="authStore.isAdmin && chunk.requires_review"
                  label="Đã review"
                  icon="pi pi-check"
                  severity="secondary"
                  size="small"
                  :loading="chunkReviewLoading === chunk.id"
                  :disabled="Boolean(chunkReviewLoading)"
                  @click="submitMarkChunkReviewed(chunk)"
                />
              </div>
              <p class="mt-1 break-words text-xs text-slate-500">
                {{ formatChunkPath(chunk.section_path) }}
              </p>
              <p class="mt-1 break-words text-xs text-slate-500">{{ chunk.section_title }}</p>
              <p class="mt-1 text-sm text-slate-700">{{ chunk.text }}</p>
            </article>
          </div>
          <p v-else-if="allChunks.length" class="text-sm text-slate-600">Không có chunk phù hợp với bộ lọc.</p>
          <p v-else class="text-sm text-slate-600">Chưa có chunk.</p>
        </template>
      </Card>
    </template>
  </section>
</template>
