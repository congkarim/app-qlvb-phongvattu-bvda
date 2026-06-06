<script setup lang="ts">
import type { DispatchInput, DispatchItem, DispatchListFilters, DispatchStatus, DispatchType } from '~/types/dispatch'
import { formatDate, formatDateTime } from '~/utils/format'

const authStore = useAuthStore()
const route = useRoute()
const {
  dispatches,
  dispatchesTotal,
  dispatchesLimit,
  dispatchesOffset,
  loading,
  saving,
  deleting,
  error,
  fetchDispatches,
  saveDispatch,
  deleteDispatch
} = useDispatches()

const filters = reactive<
  Required<Pick<DispatchListFilters, 'q' | 'dispatch_type' | 'issuing_agency' | 'status' | 'sort_by' | 'sort_dir'>> & {
    document_id: string
  }
>({
  q: '',
  dispatch_type: '',
  issuing_agency: '',
  status: '',
  sort_by: 'created_at',
  sort_dir: 'desc',
  document_id: ''
})

const form = reactive<DispatchInput>({
  document_id: '',
  dispatch_type: 'incoming',
  document_number: '',
  document_symbol: '',
  issued_date: '',
  issuing_agency: '',
  recipient: '',
  excerpt: '',
  status: 'draft',
  notes: ''
})

const editingId = ref('')

const typeOptions: Array<{ label: string; value: DispatchType | '' }> = [
  { label: 'Tất cả loại', value: '' },
  { label: 'Công văn đến', value: 'incoming' },
  { label: 'Công văn đi', value: 'outgoing' }
]

const editTypeOptions = typeOptions.filter((option) => option.value)

const statusOptions: Array<{ label: string; value: DispatchStatus | '' }> = [
  { label: 'Tất cả trạng thái', value: '' },
  { label: 'Nháp', value: 'draft' },
  { label: 'Đã vào sổ', value: 'registered' },
  { label: 'Đang xử lý', value: 'processing' },
  { label: 'Hoàn thành', value: 'completed' },
  { label: 'Lưu trữ', value: 'archived' }
]

const editStatusOptions = statusOptions.filter((option) => option.value)

const sortOptions = [
  { label: 'Ngày tạo', value: 'created_at' },
  { label: 'Cập nhật', value: 'updated_at' },
  { label: 'Số công văn', value: 'document_number' },
  { label: 'Loại', value: 'dispatch_type' },
  { label: 'Đơn vị ban hành', value: 'issuing_agency' },
  { label: 'Trạng thái', value: 'status' },
  { label: 'Ngày ban hành', value: 'issued_date' }
]

const currentStart = computed(() => (dispatchesTotal.value === 0 ? 0 : dispatchesOffset.value + 1))
const currentEnd = computed(() => Math.min(dispatchesOffset.value + dispatches.value.length, dispatchesTotal.value))
const canGoPrevious = computed(() => dispatchesOffset.value > 0)
const canGoNext = computed(() => dispatchesOffset.value + dispatchesLimit.value < dispatchesTotal.value)

function currentFilters(): DispatchListFilters {
  return {
    q: filters.q,
    dispatch_type: filters.dispatch_type,
    issuing_agency: filters.issuing_agency,
    status: filters.status,
    sort_by: filters.sort_by,
    sort_dir: filters.sort_dir,
    document_id: filters.document_id || undefined,
    limit: dispatchesLimit.value,
    offset: dispatchesOffset.value
  }
}

async function loadDispatches(resetPage = false) {
  if (resetPage) dispatchesOffset.value = 0
  await fetchDispatches(currentFilters())
}

function resetFilters() {
  filters.q = ''
  filters.dispatch_type = ''
  filters.issuing_agency = ''
  filters.status = ''
  filters.sort_by = 'created_at'
  filters.sort_dir = 'desc'
  filters.document_id = ''
  void loadDispatches(true)
}

function dashboardSearchLink(item: DispatchItem) {
  const params = new URLSearchParams()
  const searchQuery = item.excerpt || item.document_number || item.document_title || 'công văn'
  params.set('q', searchQuery)
  if (item.document_number) params.set('document_number', item.document_number)
  return `/dashboard?${params.toString()}`
}

function resetForm() {
  editingId.value = ''
  form.document_id = ''
  form.dispatch_type = 'incoming'
  form.document_number = ''
  form.document_symbol = ''
  form.issued_date = ''
  form.issuing_agency = ''
  form.recipient = ''
  form.excerpt = ''
  form.status = 'draft'
  form.notes = ''
}

function editDispatch(item: DispatchItem) {
  editingId.value = item.id
  form.document_id = item.document_id
  form.dispatch_type = item.dispatch_type
  form.document_number = item.document_number || ''
  form.document_symbol = item.document_symbol || ''
  form.issued_date = item.issued_date || ''
  form.issuing_agency = item.issuing_agency || ''
  form.recipient = item.recipient || ''
  form.excerpt = item.excerpt || ''
  form.status = item.status
  form.notes = item.notes || ''
}

async function submitForm() {
  if (!form.document_id.trim()) return
  const result = await saveDispatch(form, editingId.value || undefined)
  if (result) {
    resetForm()
    await loadDispatches()
  }
}

async function removeDispatch(id: string) {
  const deleted = await deleteDispatch(id)
  if (deleted && dispatches.value.length === 0 && dispatchesOffset.value > 0) {
    dispatchesOffset.value = Math.max(0, dispatchesOffset.value - dispatchesLimit.value)
    await loadDispatches()
  }
}

function goToPreviousPage() {
  if (!canGoPrevious.value) return
  dispatchesOffset.value = Math.max(0, dispatchesOffset.value - dispatchesLimit.value)
  void loadDispatches()
}

function goToNextPage() {
  if (!canGoNext.value) return
  dispatchesOffset.value += dispatchesLimit.value
  void loadDispatches()
}

function formatType(type: string) {
  const option = typeOptions.find((item) => item.value === type)
  return option?.label || type
}

function formatStatus(status: string) {
  const option = statusOptions.find((item) => item.value === status)
  return option?.label || status
}

onMounted(async () => {
  const documentId = typeof route.query.document_id === 'string' ? route.query.document_id : ''
  if (documentId) filters.document_id = documentId
  await loadDispatches(Boolean(documentId))
  if (route.query.create === '1' && documentId) {
    form.document_id = documentId
  }
})
</script>

<template>
  <section class="space-y-5">
    <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <div>
        <h1 class="text-2xl font-semibold">Công văn</h1>
        <p class="mt-1 text-sm text-slate-600">Metadata công văn đến/đi liên kết với văn bản nguồn.</p>
      </div>
      <div class="flex gap-2">
        <Button label="Refresh" icon="pi pi-refresh" severity="secondary" :loading="loading" @click="() => loadDispatches()" />
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
            placeholder="Tìm số CV, trích yếu, document"
            @keyup.enter="loadDispatches(true)"
          />
          <select v-model="filters.dispatch_type" class="rounded border border-slate-300 px-3 py-2 text-sm">
            <option v-for="option in typeOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
          <InputText
            v-model="filters.issuing_agency"
            placeholder="Đơn vị ban hành"
            @keyup.enter="loadDispatches(true)"
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
          <Button label="Lọc" icon="pi pi-filter" :loading="loading" @click="loadDispatches(true)" />
          <Button label="Xóa lọc" icon="pi pi-times" severity="secondary" :disabled="loading" @click="resetFilters" />
        </div>
      </template>
    </Card>

    <Card>
      <template #title>{{ editingId ? 'Sửa metadata công văn' : 'Tạo metadata công văn' }}</template>
      <template #content>
        <form class="grid gap-3 md:grid-cols-4" @submit.prevent="submitForm">
          <InputText
            v-model="form.document_id"
            :disabled="Boolean(editingId)"
            required
            placeholder="Document ID"
          />
          <select v-model="form.dispatch_type" class="rounded border border-slate-300 px-3 py-2 text-sm">
            <option v-for="option in editTypeOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
          <InputText v-model="form.document_number" placeholder="Số công văn" />
          <InputText v-model="form.document_symbol" placeholder="Ký hiệu" />
          <InputText v-model="form.issued_date" type="date" />
          <InputText v-model="form.issuing_agency" placeholder="Đơn vị ban hành" />
          <InputText v-model="form.recipient" placeholder="Nơi nhận" />
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
      <Button class="ml-2" label="Bỏ lọc" text size="small" @click="() => { filters.document_id = ''; void loadDispatches(true) }" />
    </Message>

    <div class="flex flex-col gap-3 rounded border border-slate-200 bg-white px-4 py-3 md:flex-row md:items-center md:justify-between">
      <p class="text-sm text-slate-600">
        Hiển thị {{ currentStart }}-{{ currentEnd }} / {{ dispatchesTotal }} công văn
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
        <DataTable :value="dispatches" :loading="loading" data-key="id" responsive-layout="scroll" striped-rows>
          <Column field="document_number" header="Số CV">
            <template #body="{ data }">
              <span class="font-medium">{{ data.document_number || '-' }}</span>
            </template>
          </Column>
          <Column field="dispatch_type" header="Loại">
            <template #body="{ data }">
              <span class="rounded border border-slate-200 px-2 py-1 text-xs">{{ formatType(data.dispatch_type) }}</span>
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
          <Column field="recipient" header="Nơi nhận">
            <template #body="{ data }">{{ data.recipient || '-' }}</template>
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
                <Button icon="pi pi-pencil" text rounded aria-label="Sửa" @click="editDispatch(data)" />
                <Button
                  v-if="authStore.isAdmin"
                  icon="pi pi-trash"
                  text
                  rounded
                  severity="danger"
                  aria-label="Xóa"
                  :loading="deleting === data.id"
                  @click="removeDispatch(data.id)"
                />
              </div>
            </template>
          </Column>
          <template #empty>
            <div class="py-6 text-center text-sm text-slate-500">Chưa có metadata công văn.</div>
          </template>
        </DataTable>
      </template>
    </Card>
  </section>
</template>
