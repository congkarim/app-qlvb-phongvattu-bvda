<script setup lang="ts">
import type {
  ProcurementInput,
  ProcurementItem,
  ProcurementKind,
  ProcurementListFilters,
  ProcurementStatus
} from '~/types/procurement'
import { formatDate, formatDateTime } from '~/utils/format'
import { applyRoutePrefill } from '~/utils/moduleOnboarding'

const authStore = useAuthStore()
const route = useRoute()
const {
  procurements,
  procurementsTotal,
  procurementsLimit,
  procurementsOffset,
  loading,
  saving,
  deleting,
  error,
  fetchProcurements,
  saveProcurement,
  deleteProcurement
} = useProcurements()

const filters = reactive<
  Required<Pick<ProcurementListFilters, 'q' | 'procurement_kind' | 'requesting_unit' | 'status' | 'sort_by' | 'sort_dir'>> & {
    document_id: string
  }
>({
  q: '',
  procurement_kind: '',
  requesting_unit: '',
  status: '',
  sort_by: 'created_at',
  sort_dir: 'desc',
  document_id: ''
})

const form = reactive<ProcurementInput>({
  document_id: '',
  procurement_kind: 'plan',
  reference_number: '',
  title_summary: '',
  requesting_unit: '',
  estimated_value: '',
  currency: 'VND',
  requested_date: '',
  status: 'draft',
  notes: ''
})

const editingId = ref('')
const lineItemsDialogVisible = ref(false)
const lineItemsTarget = ref<ProcurementItem | null>(null)

const kindOptions: Array<{ label: string; value: ProcurementKind | '' }> = [
  { label: 'Tất cả loại', value: '' },
  { label: 'Đề xuất mua sắm', value: 'proposal' },
  { label: 'Kế hoạch / dự toán', value: 'plan' },
  { label: 'Biên bản nghiệm thu', value: 'acceptance' }
]

const editKindOptions = kindOptions.filter((option) => option.value)

const statusOptions: Array<{ label: string; value: ProcurementStatus | '' }> = [
  { label: 'Tất cả trạng thái', value: '' },
  { label: 'Nháp', value: 'draft' },
  { label: 'Đã trình', value: 'submitted' },
  { label: 'Đã duyệt', value: 'approved' },
  { label: 'Từ chối', value: 'rejected' },
  { label: 'Hoàn thành', value: 'completed' },
  { label: 'Lưu trữ', value: 'archived' }
]

const editStatusOptions = statusOptions.filter((option) => option.value)

const sortOptions = [
  { label: 'Ngày tạo', value: 'created_at' },
  { label: 'Cập nhật', value: 'updated_at' },
  { label: 'Số tham chiếu', value: 'reference_number' },
  { label: 'Loại', value: 'procurement_kind' },
  { label: 'Đơn vị đề xuất', value: 'requesting_unit' },
  { label: 'Trạng thái', value: 'status' },
  { label: 'Ngày lập', value: 'requested_date' },
  { label: 'Giá trị dự kiến', value: 'estimated_value' }
]

const currentStart = computed(() => (procurementsTotal.value === 0 ? 0 : procurementsOffset.value + 1))
const currentEnd = computed(() => Math.min(procurementsOffset.value + procurements.value.length, procurementsTotal.value))
const canGoPrevious = computed(() => procurementsOffset.value > 0)
const canGoNext = computed(() => procurementsOffset.value + procurementsLimit.value < procurementsTotal.value)

function currentFilters(): ProcurementListFilters {
  return {
    q: filters.q,
    procurement_kind: filters.procurement_kind,
    requesting_unit: filters.requesting_unit,
    status: filters.status,
    sort_by: filters.sort_by,
    sort_dir: filters.sort_dir,
    document_id: filters.document_id || undefined,
    limit: procurementsLimit.value,
    offset: procurementsOffset.value
  }
}

async function loadProcurements(resetPage = false) {
  if (resetPage) procurementsOffset.value = 0
  await fetchProcurements(currentFilters())
}

function resetFilters() {
  filters.q = ''
  filters.procurement_kind = ''
  filters.requesting_unit = ''
  filters.status = ''
  filters.sort_by = 'created_at'
  filters.sort_dir = 'desc'
  filters.document_id = ''
  void loadProcurements(true)
}

function dashboardSearchLink(item: ProcurementItem) {
  const params = new URLSearchParams()
  const searchQuery = item.title_summary || item.reference_number || item.document_title || 'mua sam vat tu'
  params.set('q', searchQuery)
  params.set('business_type', 'procurement')
  if (item.reference_number) params.set('reference_number', item.reference_number)
  if (item.requesting_unit) params.set('requesting_unit', item.requesting_unit)
  if (item.procurement_kind) params.set('procurement_kind', item.procurement_kind)
  if (item.status) params.set('procurement_status', item.status)
  return `/dashboard?${params.toString()}`
}

function resetForm() {
  editingId.value = ''
  form.document_id = ''
  form.procurement_kind = 'plan'
  form.reference_number = ''
  form.title_summary = ''
  form.requesting_unit = ''
  form.estimated_value = ''
  form.currency = 'VND'
  form.requested_date = ''
  form.status = 'draft'
  form.notes = ''
}

function editProcurement(item: ProcurementItem) {
  editingId.value = item.id
  form.document_id = item.document_id
  form.procurement_kind = item.procurement_kind
  form.reference_number = item.reference_number || ''
  form.title_summary = item.title_summary || ''
  form.requesting_unit = item.requesting_unit || ''
  form.estimated_value = item.estimated_value ?? ''
  form.currency = item.currency || 'VND'
  form.requested_date = item.requested_date || ''
  form.status = item.status
  form.notes = item.notes || ''
}

async function submitForm() {
  if (!form.document_id.trim()) return
  const result = await saveProcurement(form, editingId.value || undefined)
  if (result) {
    resetForm()
    await loadProcurements()
  }
}

async function removeProcurement(id: string) {
  const deleted = await deleteProcurement(id)
  if (deleted && procurements.value.length === 0 && procurementsOffset.value > 0) {
    procurementsOffset.value = Math.max(0, procurementsOffset.value - procurementsLimit.value)
    await loadProcurements()
  }
}

function goToPreviousPage() {
  if (!canGoPrevious.value) return
  procurementsOffset.value = Math.max(0, procurementsOffset.value - procurementsLimit.value)
  void loadProcurements()
}

function goToNextPage() {
  if (!canGoNext.value) return
  procurementsOffset.value += procurementsLimit.value
  void loadProcurements()
}

function formatKind(kind: string) {
  const option = kindOptions.find((item) => item.value === kind)
  return option?.label || kind
}

function formatStatus(status: string) {
  const option = statusOptions.find((item) => item.value === status)
  return option?.label || status
}

function openLineItems(item: ProcurementItem) {
  lineItemsTarget.value = item
  lineItemsDialogVisible.value = true
}

function closeLineItemsDialog() {
  lineItemsDialogVisible.value = false
  lineItemsTarget.value = null
}

function lineItemsReferenceLabel(item: ProcurementItem) {
  return item.reference_number || item.title_summary || item.id
}

function formatCurrency(value?: string | number | null, currency = 'VND') {
  if (value === undefined || value === null || value === '') return '-'
  const amount = Number(value)
  if (Number.isNaN(amount)) return `${value} ${currency}`
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0
  }).format(amount)
}

onMounted(async () => {
  const documentId = typeof route.query.document_id === 'string' ? route.query.document_id : ''
  if (documentId) filters.document_id = documentId
  await loadProcurements(Boolean(documentId))
  if (route.query.create === '1' && documentId) {
    form.document_id = documentId
    applyRoutePrefill(route.query, form, [
      'procurement_kind',
      'reference_number',
      'title_summary',
      'requesting_unit',
      'estimated_value',
      'currency',
      'requested_date',
      'status',
      'notes'
    ])
  }
})
</script>

<template>
  <section class="space-y-5">
    <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <div>
        <h1 class="text-2xl font-semibold">Đề xuất & kế hoạch mua sắm</h1>
        <p class="mt-1 text-sm text-slate-600">Metadata đề xuất/kế hoạch mua sắm vật tư liên kết với văn bản nguồn.</p>
      </div>
      <div class="flex gap-2">
        <Button label="Refresh" icon="pi pi-refresh" severity="secondary" :loading="loading" @click="() => loadProcurements()" />
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
            placeholder="Tìm số tham chiếu, trích yếu, document"
            @keyup.enter="loadProcurements(true)"
          />
          <select v-model="filters.procurement_kind" class="rounded border border-slate-300 px-3 py-2 text-sm">
            <option v-for="option in kindOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
          <InputText
            v-model="filters.requesting_unit"
            placeholder="Đơn vị đề xuất"
            @keyup.enter="loadProcurements(true)"
          />
          <select v-model="filters.status" class="rounded border border-slate-300 px-3 py-2 text-sm">
            <option v-for="option in statusOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
          <select v-model="filters.sort_by" class="rounded border border-slate-300 px-3 py-2 text-sm">
            <option v-for="option in sortOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </div>
        <div class="mt-3 flex flex-wrap gap-2">
          <select v-model="filters.sort_dir" class="rounded border border-slate-300 px-3 py-2 text-sm">
            <option value="desc">Giảm dần</option>
            <option value="asc">Tăng dần</option>
          </select>
          <Button label="Lọc" icon="pi pi-filter" :loading="loading" @click="loadProcurements(true)" />
          <Button label="Xóa lọc" icon="pi pi-times" severity="secondary" :disabled="loading" @click="resetFilters" />
        </div>
      </template>
    </Card>

    <Card>
      <template #title>{{ editingId ? 'Sửa metadata mua sắm' : 'Tạo metadata mua sắm' }}</template>
      <template #content>
        <form class="grid gap-3 md:grid-cols-4" @submit.prevent="submitForm">
          <InputText
            v-model="form.document_id"
            :disabled="Boolean(editingId)"
            required
            placeholder="Document ID"
          />
          <select v-model="form.procurement_kind" class="rounded border border-slate-300 px-3 py-2 text-sm">
            <option v-for="option in editKindOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
          <InputText v-model="form.reference_number" placeholder="Số tham chiếu (DX/KH/BB)" />
          <InputText v-model="form.requested_date" type="date" />
          <InputText v-model="form.requesting_unit" placeholder="Đơn vị đề xuất" />
          <InputText v-model="form.estimated_value" placeholder="Giá trị dự kiến" />
          <InputText v-model="form.currency" placeholder="Tiền tệ (VND)" />
          <select v-model="form.status" class="rounded border border-slate-300 px-3 py-2 text-sm">
            <option v-for="option in editStatusOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
          <InputText v-model="form.title_summary" class="md:col-span-2" placeholder="Trích yếu / tên hồ sơ" />
          <InputText v-model="form.notes" class="md:col-span-2" placeholder="Ghi chú" />
          <div class="flex gap-2 md:col-span-4">
            <Button type="submit" :label="editingId ? 'Lưu' : 'Tạo'" icon="pi pi-save" :loading="saving" />
            <Button type="button" label="Hủy" icon="pi pi-times" severity="secondary" :disabled="saving" @click="resetForm" />
          </div>
        </form>
      </template>
    </Card>

    <Message v-if="error" severity="error">{{ error }}</Message>
    <Message v-if="filters.document_id" severity="info">
      Đang lọc theo văn bản nguồn: {{ filters.document_id }}
      <Button class="ml-2" label="Bỏ lọc" text size="small" @click="() => { filters.document_id = ''; void loadProcurements(true) }" />
    </Message>

    <div class="flex flex-col gap-3 rounded border border-slate-200 bg-white px-4 py-3 md:flex-row md:items-center md:justify-between">
      <p class="text-sm text-slate-600">
        Hiển thị {{ currentStart }}-{{ currentEnd }} / {{ procurementsTotal }} hồ sơ mua sắm
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

    <Card>
      <template #content>
        <DataTable :value="procurements" :loading="loading" data-key="id" responsive-layout="scroll" striped-rows>
          <Column field="reference_number" header="Số tham chiếu">
            <template #body="{ data }">
              <span class="font-medium">{{ data.reference_number || '-' }}</span>
            </template>
          </Column>
          <Column field="procurement_kind" header="Loại">
            <template #body="{ data }">
              <span class="rounded border border-slate-200 px-2 py-1 text-xs">{{ formatKind(data.procurement_kind) }}</span>
            </template>
          </Column>
          <Column field="requesting_unit" header="Đơn vị / trích yếu">
            <template #body="{ data }">
              <div>
                <p class="font-medium">{{ data.requesting_unit || '-' }}</p>
                <p class="text-xs text-slate-500">{{ data.title_summary || data.document_title || '-' }}</p>
              </div>
            </template>
          </Column>
          <Column field="status" header="Trạng thái">
            <template #body="{ data }">
              <span class="rounded border border-slate-200 px-2 py-1 text-xs">{{ formatStatus(data.status) }}</span>
            </template>
          </Column>
          <Column field="requested_date" header="Ngày lập">
            <template #body="{ data }">{{ formatDate(data.requested_date) }}</template>
          </Column>
          <Column header="Giá trị dự kiến">
            <template #body="{ data }">{{ formatCurrency(data.estimated_value, data.currency) }}</template>
          </Column>
          <Column header="Document">
            <template #body="{ data }">
              <div class="space-y-1">
                <NuxtLink :to="`/documents/${data.document_id}`" class="block text-sm font-medium text-blue-700">
                  {{ data.document_title || 'Mở văn bản' }}
                </NuxtLink>
                <NuxtLink :to="dashboardSearchLink(data)" class="block text-xs text-sky-700">
                  Search trong văn bản
                </NuxtLink>
              </div>
            </template>
          </Column>
          <Column field="updated_at" header="Cập nhật">
            <template #body="{ data }">{{ formatDateTime(data.updated_at) }}</template>
          </Column>
          <Column header="">
            <template #body="{ data }">
              <div class="flex gap-2">
                <Button icon="pi pi-list" text rounded aria-label="Dòng hàng" @click="openLineItems(data)" />
                <Button icon="pi pi-pencil" text rounded aria-label="Sửa" @click="editProcurement(data)" />
                <Button
                  v-if="authStore.isAdmin"
                  icon="pi pi-trash"
                  text
                  rounded
                  severity="danger"
                  aria-label="Xóa"
                  :loading="deleting === data.id"
                  @click="removeProcurement(data.id)"
                />
              </div>
            </template>
          </Column>
          <template #empty>
            <div class="py-6 text-center text-sm text-slate-500">Chưa có metadata mua sắm.</div>
          </template>
        </DataTable>
      </template>
    </Card>

    <Dialog
      v-model:visible="lineItemsDialogVisible"
      modal
      header="Dòng hàng mua sắm"
      :style="{ width: 'min(960px, 96vw)' }"
      @hide="closeLineItemsDialog"
    >
      <ProcurementLineItemsPanel
        v-if="lineItemsTarget"
        :procurement-id="lineItemsTarget.id"
        :estimated-value="lineItemsTarget.estimated_value"
        :currency="lineItemsTarget.currency"
        :reference-label="lineItemsReferenceLabel(lineItemsTarget)"
      />
    </Dialog>
  </section>
</template>
