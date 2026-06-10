<script setup lang="ts">
import type { MaterialsCatalogAutocompleteItem } from '~/types/materials-catalog'
import type { ProcurementLineItemInput } from '~/types/procurement-line-item'

const props = defineProps<{
  procurementId: string
  procurementKind?: string
  procurementStatus?: string
  estimatedValue?: string | number | null
  currency?: string
  referenceLabel?: string
}>()

const authStore = useAuthStore()
const {
  lineItems,
  linesTotalAmount,
  loading,
  saving,
  deleting,
  error,
  fetchLineItems,
  saveLineItem,
  deleteLineItem
} = useProcurementLineItems()
const { autocompleteItems, autocompleteLoading, searchActiveCatalog } = useMaterialsCatalog()
const { saving: stockSaving, saveMovement } = useStockMovements()

const editingLineId = ref('')
const stockDialogVisible = ref(false)
const selectedLineIds = ref<string[]>([])
const stockInboundError = ref('')

const canStockInbound = computed(
  () =>
    props.procurementKind === 'acceptance' &&
    ['approved', 'completed'].includes(props.procurementStatus || '') &&
    lineItems.value.length > 0
)

const inboundCandidates = computed(() =>
  lineItems.value.filter((item) => item.catalog_item_id || item.item_code)
)

const lineForm = reactive<ProcurementLineItemInput>({
  line_number: undefined,
  item_name: '',
  item_code: '',
  unit: '',
  quantity: '1',
  unit_price: '',
  notes: ''
})

const estimatedMismatch = computed(() => {
  const estimated = Number(props.estimatedValue)
  const total = Number(linesTotalAmount.value)
  if (!estimated || Number.isNaN(estimated) || !total || Number.isNaN(total)) return false
  return Math.abs(total - estimated) / estimated > 0.01
})

function formatCurrency(value?: string | number | null, currency = props.currency || 'VND') {
  if (value === undefined || value === null || value === '') return '-'
  const amount = Number(value)
  if (Number.isNaN(amount)) return `${value} ${currency}`
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0
  }).format(amount)
}

function resetLineForm() {
  editingLineId.value = ''
  lineForm.line_number = undefined
  lineForm.item_name = ''
  lineForm.item_code = ''
  lineForm.unit = ''
  lineForm.quantity = '1'
  lineForm.unit_price = ''
  lineForm.catalog_item_id = null
  lineForm.notes = ''
}

function editLineItem(item: (typeof lineItems.value)[number]) {
  editingLineId.value = item.id
  lineForm.line_number = item.line_number
  lineForm.item_name = item.item_name
  lineForm.item_code = item.item_code || ''
  lineForm.unit = item.unit || ''
  lineForm.quantity = String(item.quantity)
  lineForm.unit_price = item.unit_price != null ? String(item.unit_price) : ''
  lineForm.catalog_item_id = item.catalog_item_id || null
  lineForm.notes = item.notes || ''
}

async function onCatalogSearch(event: { query: string }) {
  await searchActiveCatalog(event.query)
}

function onCatalogSelect(event: { value: MaterialsCatalogAutocompleteItem }) {
  const item = event.value
  lineForm.item_name = item.name
  lineForm.item_code = item.code || ''
  lineForm.unit = item.default_unit || lineForm.unit
  lineForm.catalog_item_id = item.id
}

async function submitLineForm() {
  if (!lineForm.item_name.trim()) return
  const result = await saveLineItem(props.procurementId, { ...lineForm }, editingLineId.value || undefined)
  if (result) resetLineForm()
}

async function removeLineItem(id: string) {
  const deleted = await deleteLineItem(props.procurementId, id)
  if (deleted && editingLineId.value === id) resetLineForm()
}

function openStockInboundDialog() {
  selectedLineIds.value = inboundCandidates.value.map((item) => item.id)
  stockInboundError.value = ''
  stockDialogVisible.value = true
}

async function submitStockInbound() {
  stockInboundError.value = ''
  const today = new Date().toISOString().slice(0, 10)
  const selected = lineItems.value.filter((item) => selectedLineIds.value.includes(item.id))
  if (!selected.length) {
    stockInboundError.value = 'Chọn ít nhất một dòng hàng.'
    return
  }
  for (const line of selected) {
    if (!line.catalog_item_id) {
      stockInboundError.value = `Dòng "${line.item_name}" chưa liên kết catalog — chọn từ autocomplete trước khi nhập kho.`
      return
    }
    const result = await saveMovement({
      catalog_item_id: line.catalog_item_id,
      movement_type: 'in',
      quantity: String(line.quantity),
      movement_date: today,
      reference_number: props.referenceLabel || undefined,
      procurement_id: props.procurementId,
      notes: `Nhập kho từ hồ sơ mua sắm — ${line.item_name}`
    })
    if (!result) {
      stockInboundError.value = 'Không tạo được phiếu nhập kho.'
      return
    }
  }
  stockDialogVisible.value = false
}

watch(
  () => props.procurementId,
  (procurementId) => {
    resetLineForm()
    if (procurementId) void fetchLineItems(procurementId)
  },
  { immediate: true }
)
</script>

<template>
  <div class="space-y-4">
    <div v-if="referenceLabel" class="text-sm text-slate-600">
      Hồ sơ: <span class="font-medium text-slate-800">{{ referenceLabel }}</span>
    </div>

    <Message v-if="error" severity="error">{{ error }}</Message>
    <Message v-if="estimatedMismatch" severity="warn" :closable="false">
      Tổng dòng hàng ({{ formatCurrency(linesTotalAmount) }}) lệch hơn 1% so với giá trị dự kiến
      ({{ formatCurrency(estimatedValue) }}).
    </Message>

    <div v-if="canStockInbound" class="flex flex-wrap gap-2">
      <Button label="Nhập kho từ hồ sơ" icon="pi pi-box" severity="secondary" @click="openStockInboundDialog" />
    </div>

    <DataTable :value="lineItems" :loading="loading" data-key="id" responsive-layout="scroll" striped-rows size="small">
      <Column field="line_number" header="STT" style="width: 4rem" />
      <Column field="item_name" header="Tên vật tư">
        <template #body="{ data }">
          <div>
            <p class="font-medium">{{ data.item_name }}</p>
            <p v-if="data.item_code" class="text-xs text-slate-500">{{ data.item_code }}</p>
          </div>
        </template>
      </Column>
      <Column field="unit" header="ĐVT" />
      <Column field="quantity" header="SL" />
      <Column field="unit_price" header="Đơn giá">
        <template #body="{ data }">{{ formatCurrency(data.unit_price) }}</template>
      </Column>
      <Column field="amount" header="Thành tiền">
        <template #body="{ data }">{{ formatCurrency(data.amount) }}</template>
      </Column>
      <Column header="">
        <template #body="{ data }">
          <div class="flex gap-1">
            <Button icon="pi pi-pencil" text rounded aria-label="Sửa dòng" @click="editLineItem(data)" />
            <Button
              v-if="authStore.isAdmin"
              icon="pi pi-trash"
              text
              rounded
              severity="danger"
              aria-label="Xóa dòng"
              :loading="deleting === data.id"
              @click="removeLineItem(data.id)"
            />
          </div>
        </template>
      </Column>
      <template #empty>
        <div class="py-4 text-center text-sm text-slate-500">Chưa có dòng hàng nào.</div>
      </template>
    </DataTable>

    <div class="flex flex-wrap items-center justify-between gap-2 rounded border border-slate-200 bg-slate-50 px-3 py-2 text-sm">
      <span class="font-medium text-slate-700">Tổng cộng dòng hàng</span>
      <span class="text-base font-semibold text-slate-900">{{ formatCurrency(linesTotalAmount) }}</span>
    </div>

    <form class="grid gap-3 rounded border border-slate-200 p-3 md:grid-cols-4" @submit.prevent="submitLineForm">
      <div class="md:col-span-2">
        <label class="mb-1 block text-xs font-medium text-slate-600">Tên vật tư (autocomplete catalog)</label>
        <AutoComplete
          v-model="lineForm.item_name"
          :suggestions="autocompleteItems"
          option-label="name"
          class="w-full"
          input-class="w-full"
          :loading="autocompleteLoading"
          placeholder="Gõ để tìm hoặc nhập tên vật tư..."
          @complete="onCatalogSearch"
          @item-select="onCatalogSelect"
        />
      </div>
      <InputText v-model="lineForm.item_code" placeholder="Mã vật tư" />
      <InputText v-model="lineForm.unit" placeholder="Đơn vị tính" />
      <InputText v-model="lineForm.quantity" placeholder="Số lượng" />
      <InputText v-model="lineForm.unit_price" placeholder="Đơn giá" />
      <InputText v-model="lineForm.notes" class="md:col-span-2" placeholder="Ghi chú" />
      <div class="flex gap-2 md:col-span-4">
        <Button type="submit" :label="editingLineId ? 'Lưu dòng' : 'Thêm dòng'" icon="pi pi-plus" :loading="saving" />
        <Button
          v-if="editingLineId"
          type="button"
          label="Hủy sửa"
          icon="pi pi-times"
          severity="secondary"
          :disabled="saving"
          @click="resetLineForm"
        />
      </div>
    </form>

    <Dialog v-model:visible="stockDialogVisible" modal header="Nhập kho từ dòng hàng" :style="{ width: 'min(520px, 96vw)' }">
      <p class="mb-3 text-sm text-slate-600">Chọn dòng hàng để tạo phiếu nhập kho (mỗi dòng một phiếu).</p>
      <AppErrorState v-if="stockInboundError" :message="stockInboundError" />
      <div class="space-y-2">
        <label
          v-for="line in inboundCandidates"
          :key="line.id"
          class="flex items-start gap-2 rounded border border-slate-200 p-2 text-sm"
        >
          <input v-model="selectedLineIds" type="checkbox" :value="line.id" class="mt-1 rounded border-slate-300" />
          <span>
            <span class="font-medium">{{ line.item_name }}</span>
            <span class="text-slate-500"> — SL {{ line.quantity }} {{ line.unit || '' }}</span>
            <span v-if="!line.catalog_item_id" class="block text-xs text-amber-700">Chưa liên kết danh mục vật tư</span>
          </span>
        </label>
      </div>
      <div class="mt-4 flex justify-end gap-2">
        <Button label="Hủy" severity="secondary" :disabled="stockSaving" @click="stockDialogVisible = false" />
        <Button label="Tạo phiếu nhập" icon="pi pi-save" :loading="stockSaving" @click="submitStockInbound" />
      </div>
    </Dialog>
  </div>
</template>
