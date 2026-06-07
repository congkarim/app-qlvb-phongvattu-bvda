<script setup lang="ts">
import type { DecisionInput, DecisionItem, DecisionKind, DecisionListFilters, DecisionStatus } from '~/types/decision'
import { formatDate, formatDateTime } from '~/utils/format'

const authStore = useAuthStore()
const route = useRoute()
const {
  decisions,
  decisionsTotal,
  decisionsLimit,
  decisionsOffset,
  loading,
  saving,
  deleting,
  error,
  fetchDecisions,
  saveDecision,
  deleteDecision
} = useDecisions()

const filters = reactive<
  Required<Pick<DecisionListFilters, 'q' | 'decision_kind' | 'issuing_agency' | 'status' | 'sort_by' | 'sort_dir'>> & {
    document_id: string
  }
>({
  q: '',
  decision_kind: '',
  issuing_agency: '',
  status: '',
  sort_by: 'created_at',
  sort_dir: 'desc',
  document_id: ''
})

const form = reactive<DecisionInput>({
  document_id: '',
  decision_kind: 'decision',
  document_number: '',
  document_symbol: '',
  issued_date: '',
  issuing_agency: '',
  excerpt: '',
  effective_from: '',
  effective_to: '',
  status: 'draft',
  notes: ''
})

const editingId = ref('')

const kindOptions: Array<{ label: string; value: DecisionKind | '' }> = [
  { label: 'Tất cả loại', value: '' },
  { label: 'Quyết định', value: 'decision' },
  { label: 'Thông báo', value: 'notification' }
]

const editKindOptions = kindOptions.filter((option) => option.value)

const statusOptions: Array<{ label: string; value: DecisionStatus | '' }> = [
  { label: 'Tất cả trạng thái', value: '' },
  { label: 'Nháp', value: 'draft' },
  { label: 'Đã vào sổ', value: 'registered' },
  { label: 'Đang hiệu lực', value: 'effective' },
  { label: 'Hết hiệu lực', value: 'expired' },
  { label: 'Đã thu hồi', value: 'revoked' },
  { label: 'Lưu trữ', value: 'archived' }
]

const editStatusOptions = statusOptions.filter((option) => option.value)

const sortOptions = [
  { label: 'Ngày tạo', value: 'created_at' },
  { label: 'Cập nhật', value: 'updated_at' },
  { label: 'Số văn bản', value: 'document_number' },
  { label: 'Loại', value: 'decision_kind' },
  { label: 'Đơn vị ban hành', value: 'issuing_agency' },
  { label: 'Trạng thái', value: 'status' },
  { label: 'Ngày ban hành', value: 'issued_date' },
  { label: 'Hiệu lực từ', value: 'effective_from' },
  { label: 'Hiệu lực đến', value: 'effective_to' }
]

const currentStart = computed(() => (decisionsTotal.value === 0 ? 0 : decisionsOffset.value + 1))
const currentEnd = computed(() => Math.min(decisionsOffset.value + decisions.value.length, decisionsTotal.value))
const canGoPrevious = computed(() => decisionsOffset.value > 0)
const canGoNext = computed(() => decisionsOffset.value + decisionsLimit.value < decisionsTotal.value)

function currentFilters(): DecisionListFilters {
  return {
    q: filters.q,
    decision_kind: filters.decision_kind,
    issuing_agency: filters.issuing_agency,
    status: filters.status,
    sort_by: filters.sort_by,
    sort_dir: filters.sort_dir,
    document_id: filters.document_id || undefined,
    limit: decisionsLimit.value,
    offset: decisionsOffset.value
  }
}

async function loadDecisions(resetPage = false) {
  if (resetPage) decisionsOffset.value = 0
  await fetchDecisions(currentFilters())
}

function resetFilters() {
  filters.q = ''
  filters.decision_kind = ''
  filters.issuing_agency = ''
  filters.status = ''
  filters.sort_by = 'created_at'
  filters.sort_dir = 'desc'
  filters.document_id = ''
  void loadDecisions(true)
}

function dashboardSearchLink(item: DecisionItem) {
  const params = new URLSearchParams()
  const searchQuery = item.excerpt || item.document_number || item.document_title || 'quyết định'
  params.set('q', searchQuery)
  if (item.document_number) params.set('document_number', item.document_number)
  params.set('business_type', 'decision')
  return `/dashboard?${params.toString()}`
}

function resetForm() {
  editingId.value = ''
  form.document_id = ''
  form.decision_kind = 'decision'
  form.document_number = ''
  form.document_symbol = ''
  form.issued_date = ''
  form.issuing_agency = ''
  form.excerpt = ''
  form.effective_from = ''
  form.effective_to = ''
  form.status = 'draft'
  form.notes = ''
}

function editDecision(item: DecisionItem) {
  editingId.value = item.id
  form.document_id = item.document_id
  form.decision_kind = item.decision_kind
  form.document_number = item.document_number || ''
  form.document_symbol = item.document_symbol || ''
  form.issued_date = item.issued_date || ''
  form.issuing_agency = item.issuing_agency || ''
  form.excerpt = item.excerpt || ''
  form.effective_from = item.effective_from || ''
  form.effective_to = item.effective_to || ''
  form.status = item.status
  form.notes = item.notes || ''
}

async function submitForm() {
  if (!form.document_id.trim()) return
  const result = await saveDecision(form, editingId.value || undefined)
  if (result) {
    resetForm()
    await loadDecisions()
  }
}

async function removeDecision(id: string) {
  const deleted = await deleteDecision(id)
  if (deleted && decisions.value.length === 0 && decisionsOffset.value > 0) {
    decisionsOffset.value = Math.max(0, decisionsOffset.value - decisionsLimit.value)
    await loadDecisions()
  }
}

function goToPreviousPage() {
  if (!canGoPrevious.value) return
  decisionsOffset.value = Math.max(0, decisionsOffset.value - decisionsLimit.value)
  void loadDecisions()
}

function goToNextPage() {
  if (!canGoNext.value) return
  decisionsOffset.value += decisionsLimit.value
  void loadDecisions()
}

function formatKind(kind: string) {
  const option = kindOptions.find((item) => item.value === kind)
  return option?.label || kind
}

function formatStatus(status: string) {
  const option = statusOptions.find((item) => item.value === status)
  return option?.label || status
}

onMounted(async () => {
  const documentId = typeof route.query.document_id === 'string' ? route.query.document_id : ''
  if (documentId) filters.document_id = documentId
  await loadDecisions(Boolean(documentId))
  if (route.query.create === '1' && documentId) {
    form.document_id = documentId
  }
})
</script>

<template>
  <section class="space-y-5">
    <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <div>
        <h1 class="text-2xl font-semibold">Quyết định & thông báo</h1>
        <p class="mt-1 text-sm text-slate-600">Metadata quyết định/thông báo liên kết với văn bản nguồn.</p>
      </div>
      <div class="flex gap-2">
        <Button label="Refresh" icon="pi pi-refresh" severity="secondary" :loading="loading" @click="() => loadDecisions()" />
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
            placeholder="Tìm số QĐ/TB, trích yếu, document"
            @keyup.enter="loadDecisions(true)"
          />
          <select v-model="filters.decision_kind" class="rounded border border-slate-300 px-3 py-2 text-sm">
            <option v-for="option in kindOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
          <InputText
            v-model="filters.issuing_agency"
            placeholder="Đơn vị ban hành"
            @keyup.enter="loadDecisions(true)"
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
          <Button label="Lọc" icon="pi pi-filter" :loading="loading" @click="loadDecisions(true)" />
          <Button label="Xóa lọc" icon="pi pi-times" severity="secondary" :disabled="loading" @click="resetFilters" />
        </div>
      </template>
    </Card>

    <Card>
      <template #title>{{ editingId ? 'Sửa metadata quyết định/thông báo' : 'Tạo metadata quyết định/thông báo' }}</template>
      <template #content>
        <form class="grid gap-3 md:grid-cols-4" @submit.prevent="submitForm">
          <InputText
            v-model="form.document_id"
            :disabled="Boolean(editingId)"
            required
            placeholder="Document ID"
          />
          <select v-model="form.decision_kind" class="rounded border border-slate-300 px-3 py-2 text-sm">
            <option v-for="option in editKindOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
          <InputText v-model="form.document_number" placeholder="Số quyết định/thông báo" />
          <InputText v-model="form.document_symbol" placeholder="Ký hiệu" />
          <InputText v-model="form.issued_date" type="date" />
          <InputText v-model="form.issuing_agency" placeholder="Đơn vị ban hành" />
          <InputText v-model="form.effective_from" type="date" placeholder="Hiệu lực từ" />
          <InputText v-model="form.effective_to" type="date" placeholder="Hiệu lực đến" />
          <select v-model="form.status" class="rounded border border-slate-300 px-3 py-2 text-sm">
            <option v-for="option in editStatusOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
          <InputText v-model="form.excerpt" class="md:col-span-2" placeholder="Trích yếu" />
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
      <Button class="ml-2" label="Bỏ lọc" text size="small" @click="() => { filters.document_id = ''; void loadDecisions(true) }" />
    </Message>

    <div class="flex flex-col gap-3 rounded border border-slate-200 bg-white px-4 py-3 md:flex-row md:items-center md:justify-between">
      <p class="text-sm text-slate-600">
        Hiển thị {{ currentStart }}-{{ currentEnd }} / {{ decisionsTotal }} quyết định/thông báo
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
        <DataTable :value="decisions" :loading="loading" data-key="id" responsive-layout="scroll" striped-rows>
          <Column field="document_number" header="Số văn bản">
            <template #body="{ data }">
              <span class="font-medium">{{ data.document_number || '-' }}</span>
            </template>
          </Column>
          <Column field="decision_kind" header="Loại">
            <template #body="{ data }">
              <span class="rounded border border-slate-200 px-2 py-1 text-xs">{{ formatKind(data.decision_kind) }}</span>
            </template>
          </Column>
          <Column field="issuing_agency" header="Đơn vị / trích yếu">
            <template #body="{ data }">
              <div>
                <p class="font-medium">{{ data.issuing_agency || '-' }}</p>
                <p class="text-xs text-slate-500">{{ data.excerpt || data.document_title || '-' }}</p>
              </div>
            </template>
          </Column>
          <Column field="status" header="Trạng thái">
            <template #body="{ data }">
              <span class="rounded border border-slate-200 px-2 py-1 text-xs">{{ formatStatus(data.status) }}</span>
            </template>
          </Column>
          <Column field="issued_date" header="Ngày ban hành">
            <template #body="{ data }">{{ formatDate(data.issued_date) }}</template>
          </Column>
          <Column header="Hiệu lực">
            <template #body="{ data }">
              {{ formatDate(data.effective_from) }} - {{ formatDate(data.effective_to) }}
            </template>
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
                <Button icon="pi pi-pencil" text rounded aria-label="Sửa" @click="editDecision(data)" />
                <Button
                  v-if="authStore.isAdmin"
                  icon="pi pi-trash"
                  text
                  rounded
                  severity="danger"
                  aria-label="Xóa"
                  :loading="deleting === data.id"
                  @click="removeDecision(data.id)"
                />
              </div>
            </template>
          </Column>
          <template #empty>
            <div class="py-6 text-center text-sm text-slate-500">Chưa có metadata quyết định/thông báo.</div>
          </template>
        </DataTable>
      </template>
    </Card>
  </section>
</template>
