<script setup lang="ts">
import type { ContractInput, ContractItem, ContractListFilters, ContractStatus } from '~/types/contract'
import { formatDate, formatDateTime } from '~/utils/format'
import { applyRoutePrefill } from '~/utils/moduleOnboarding'

const authStore = useAuthStore()
const route = useRoute()
const {
  contracts,
  contractsTotal,
  contractsLimit,
  contractsOffset,
  loading,
  saving,
  deleting,
  error,
  fetchContracts,
  saveContract,
  deleteContract
} = useContracts()

const filters = reactive<Required<Pick<ContractListFilters, 'q' | 'supplier_name' | 'status' | 'sort_by' | 'sort_dir'>> & { document_id: string }>({
  q: '',
  supplier_name: '',
  status: '',
  sort_by: 'created_at',
  sort_dir: 'desc',
  document_id: ''
})

const form = reactive<ContractInput>({
  document_id: '',
  contract_number: '',
  contract_title: '',
  supplier_name: '',
  sign_date: '',
  effective_from: '',
  effective_to: '',
  contract_value: '',
  currency: 'VND',
  status: 'draft',
  notes: ''
})

const editingId = ref('')

const statusOptions: Array<{ label: string; value: ContractStatus | '' }> = [
  { label: 'Tất cả trạng thái', value: '' },
  { label: 'Nháp', value: 'draft' },
  { label: 'Đang hiệu lực', value: 'active' },
  { label: 'Hết hạn', value: 'expired' },
  { label: 'Chấm dứt', value: 'terminated' },
  { label: 'Hoàn thành', value: 'completed' }
]

const editStatusOptions = statusOptions.filter((option) => option.value)

const sortOptions = [
  { label: 'Ngày tạo', value: 'created_at' },
  { label: 'Cập nhật', value: 'updated_at' },
  { label: 'Số hợp đồng', value: 'contract_number' },
  { label: 'Nhà cung cấp', value: 'supplier_name' },
  { label: 'Trạng thái', value: 'status' },
  { label: 'Ngày ký', value: 'sign_date' },
  { label: 'Hết hiệu lực', value: 'effective_to' }
]

const currentStart = computed(() => (contractsTotal.value === 0 ? 0 : contractsOffset.value + 1))
const currentEnd = computed(() => Math.min(contractsOffset.value + contracts.value.length, contractsTotal.value))
const canGoPrevious = computed(() => contractsOffset.value > 0)
const canGoNext = computed(() => contractsOffset.value + contractsLimit.value < contractsTotal.value)

function currentFilters(): ContractListFilters {
  return {
    q: filters.q,
    supplier_name: filters.supplier_name,
    status: filters.status,
    sort_by: filters.sort_by,
    sort_dir: filters.sort_dir,
    document_id: filters.document_id || undefined,
    limit: contractsLimit.value,
    offset: contractsOffset.value
  }
}

async function loadContracts(resetPage = false) {
  if (resetPage) contractsOffset.value = 0
  await fetchContracts(currentFilters())
}

function resetFilters() {
  filters.q = ''
  filters.supplier_name = ''
  filters.status = ''
  filters.sort_by = 'created_at'
  filters.sort_dir = 'desc'
  filters.document_id = ''
  void loadContracts(true)
}

function dashboardSearchLink(item: ContractItem) {
  const params = new URLSearchParams()
  const searchQuery = item.contract_title || item.contract_number || item.document_title || 'hợp đồng'
  params.set('q', searchQuery)
  if (item.document_number) params.set('document_number', item.document_number)
  return `/dashboard?${params.toString()}`
}

function resetForm() {
  editingId.value = ''
  form.document_id = ''
  form.contract_number = ''
  form.contract_title = ''
  form.supplier_name = ''
  form.sign_date = ''
  form.effective_from = ''
  form.effective_to = ''
  form.contract_value = ''
  form.currency = 'VND'
  form.status = 'draft'
  form.notes = ''
}

function editContract(item: ContractItem) {
  editingId.value = item.id
  form.document_id = item.document_id
  form.contract_number = item.contract_number || ''
  form.contract_title = item.contract_title || ''
  form.supplier_name = item.supplier_name || ''
  form.sign_date = item.sign_date || ''
  form.effective_from = item.effective_from || ''
  form.effective_to = item.effective_to || ''
  form.contract_value = item.contract_value ? String(item.contract_value) : ''
  form.currency = item.currency || 'VND'
  form.status = item.status
  form.notes = item.notes || ''
}

async function submitForm() {
  if (!form.document_id.trim()) return
  const result = await saveContract(form, editingId.value || undefined)
  if (result) {
    resetForm()
    await loadContracts()
  }
}

async function removeContract(id: string) {
  const deleted = await deleteContract(id)
  if (deleted && contracts.value.length === 0 && contractsOffset.value > 0) {
    contractsOffset.value = Math.max(0, contractsOffset.value - contractsLimit.value)
    await loadContracts()
  }
}

function goToPreviousPage() {
  if (!canGoPrevious.value) return
  contractsOffset.value = Math.max(0, contractsOffset.value - contractsLimit.value)
  void loadContracts()
}

function goToNextPage() {
  if (!canGoNext.value) return
  contractsOffset.value += contractsLimit.value
  void loadContracts()
}

function formatStatus(status: string) {
  const option = statusOptions.find((item) => item.value === status)
  return option?.label || status
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
  await loadContracts(Boolean(documentId))
  if (route.query.create === '1' && documentId) {
    form.document_id = documentId
    applyRoutePrefill(route.query, form, [
      'contract_number',
      'contract_title',
      'supplier_name',
      'sign_date',
      'effective_from',
      'effective_to',
      'contract_value',
      'currency',
      'status',
      'notes'
    ])
  }
})
</script>

<template>
  <AppPageContainer>
    <AppPageHeader
      title="Contracts"
      description="Metadata hợp đồng liên kết với văn bản nguồn."
    >
      <template #actions>
        <Button label="Refresh" icon="pi pi-refresh" severity="secondary" :loading="loading" @click="() => loadContracts()" />
        <NuxtLink to="/upload">
          <Button label="Upload" icon="pi pi-upload" />
        </NuxtLink>
      </template>
    </AppPageHeader>

    <AppCard title="Bộ lọc">
      <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        <InputText
          v-model="filters.q"
          class="md:col-span-2"
          placeholder="Tìm số hợp đồng, tên, document"
          @keyup.enter="loadContracts(true)"
        />
        <InputText
          v-model="filters.supplier_name"
          placeholder="Nhà cung cấp"
          @keyup.enter="loadContracts(true)"
        />
        <AppSelect v-model="filters.status">
          <option v-for="option in statusOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
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
        <Button label="Lọc" icon="pi pi-filter" :loading="loading" @click="loadContracts(true)" />
        <Button label="Xóa lọc" icon="pi pi-times" severity="secondary" :disabled="loading" @click="resetFilters" />
      </div>
    </AppCard>

    <AppCard :title="editingId ? 'Sửa metadata hợp đồng' : 'Tạo metadata hợp đồng'">
      <form class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4" @submit.prevent="submitForm">
        <InputText
          v-model="form.document_id"
          :disabled="Boolean(editingId)"
          required
          placeholder="Document ID"
        />
        <InputText v-model="form.contract_number" placeholder="Số hợp đồng" />
        <InputText v-model="form.contract_title" class="md:col-span-2" placeholder="Tên hợp đồng" />
        <InputText v-model="form.supplier_name" placeholder="Nhà cung cấp" />
        <InputText v-model="form.sign_date" type="date" />
        <InputText v-model="form.effective_from" type="date" />
        <InputText v-model="form.effective_to" type="date" />
        <InputText v-model="form.contract_value" inputmode="decimal" placeholder="Giá trị" />
        <InputText v-model="form.currency" maxlength="8" placeholder="Tiền tệ" />
        <AppSelect v-model="form.status">
          <option v-for="option in editStatusOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </AppSelect>
        <InputText v-model="form.notes" class="md:col-span-1" placeholder="Ghi chú" />
        <div class="flex gap-2 md:col-span-4">
          <Button type="submit" :label="editingId ? 'Lưu' : 'Tạo'" icon="pi pi-save" :loading="saving" />
          <Button type="button" label="Hủy" icon="pi pi-times" severity="secondary" :disabled="saving" @click="resetForm" />
        </div>
      </form>
    </AppCard>

    <AppErrorState v-if="error" :message="error" />
    <Message v-if="filters.document_id" severity="info">
      Đang lọc theo văn bản nguồn: {{ filters.document_id }}
      <Button class="ml-2" label="Bỏ lọc" text size="small" @click="() => { filters.document_id = ''; void loadContracts(true) }" />
    </Message>

    <AppToolbar
      :summary="`Hiển thị ${currentStart}-${currentEnd} / ${contractsTotal} hợp đồng`"
      :loading="loading"
      :can-go-previous="canGoPrevious"
      :can-go-next="canGoNext"
      @previous="goToPreviousPage"
      @next="goToNextPage"
    />

    <AppCard no-padding>
      <div class="app-table-wrap">
        <DataTable :value="contracts" :loading="loading" data-key="id" responsive-layout="scroll" striped-rows>
          <Column field="contract_number" header="Số hợp đồng">
            <template #body="{ data }">
              <span class="font-medium">{{ data.contract_number || '-' }}</span>
            </template>
          </Column>
          <Column field="supplier_name" header="Nhà cung cấp">
            <template #body="{ data }">
              <div>
                <p class="font-medium">{{ data.supplier_name || '-' }}</p>
                <p class="text-xs text-slate-500">{{ data.contract_title || data.document_title || '-' }}</p>
              </div>
            </template>
          </Column>
          <Column field="status" header="Trạng thái">
            <template #body="{ data }">
              <span class="rounded border border-slate-200 px-2 py-1 text-xs">{{ formatStatus(data.status) }}</span>
            </template>
          </Column>
          <Column field="sign_date" header="Ngày ký">
            <template #body="{ data }">{{ formatDate(data.sign_date) }}</template>
          </Column>
          <Column field="effective_to" header="Hết hiệu lực">
            <template #body="{ data }">{{ formatDate(data.effective_to) }}</template>
          </Column>
          <Column field="contract_value" header="Giá trị">
            <template #body="{ data }">{{ formatCurrency(data.contract_value, data.currency) }}</template>
          </Column>
          <Column header="Document">
            <template #body="{ data }">
              <div class="space-y-1">
                <NuxtLink :to="`/documents/${data.document_id}`" class="block text-sm font-medium text-blue-700">
                  {{ data.document_number || data.document_title || 'Mở văn bản' }}
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
                <Button icon="pi pi-pencil" text rounded aria-label="Sửa" @click="editContract(data)" />
                <Button
                  v-if="authStore.isAdmin"
                  icon="pi pi-trash"
                  text
                  rounded
                  severity="danger"
                  aria-label="Xóa"
                  :loading="deleting === data.id"
                  @click="removeContract(data.id)"
                />
              </div>
            </template>
          </Column>
          <template #empty>
            <AppEmptyState title="Chưa có metadata hợp đồng" description="Tạo metadata hợp đồng liên kết với văn bản nguồn." />
          </template>
        </DataTable>
      </div>
    </AppCard>
  </AppPageContainer>
</template>
