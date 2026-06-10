<script setup lang="ts">
import type { MaterialsCatalogAutocompleteItem } from '~/types/materials-catalog'
import type { StockMovementInput, StockMovementListFilters, StockMovementType } from '~/types/stock-movement'

const authStore = useAuthStore()
const {
  movements,
  movementsTotal,
  movementsLimit,
  movementsOffset,
  currentBalance,
  loading,
  saving,
  deleting,
  error,
  fetchMovements,
  fetchBalance,
  saveMovement,
  deleteMovement
} = useStockMovements()

const dialogVisible = ref(false)

const filters = reactive<
  Required<Pick<StockMovementListFilters, 'movement_type' | 'q' | 'reference_number' | 'movement_date_from' | 'movement_date_to'>>
>({
  movement_type: '',
  q: '',
  reference_number: '',
  movement_date_from: '',
  movement_date_to: ''
})

const form = reactive<StockMovementInput>({
  catalog_item_id: '',
  movement_type: 'in',
  quantity: '1',
  movement_date: new Date().toISOString().slice(0, 10),
  notes: '',
  reference_number: '',
  procurement_id: ''
})

const selectedCatalogName = ref('')
const outboundWarning = computed(() => {
  if (form.movement_type !== 'out' || !currentBalance.value) return false
  const qty = Number(form.quantity)
  const balance = Number(currentBalance.value.quantity)
  return !Number.isNaN(qty) && !Number.isNaN(balance) && qty > balance
})

const movementTypeOptions = [
  { label: 'Tất cả loại', value: '' },
  { label: 'Nhập kho', value: 'in' },
  { label: 'Xuất kho', value: 'out' }
]

const formMovementOptions = [
  { label: 'Nhập kho', value: 'in', icon: 'pi pi-arrow-down' },
  { label: 'Xuất kho', value: 'out', icon: 'pi pi-arrow-up' }
]

const currentStart = computed(() => (movementsTotal.value === 0 ? 0 : movementsOffset.value + 1))
const currentEnd = computed(() => Math.min(movementsOffset.value + movements.value.length, movementsTotal.value))
const canGoPrevious = computed(() => movementsOffset.value > 0)
const canGoNext = computed(() => movementsOffset.value + movementsLimit.value < movementsTotal.value)
const paginationSummary = computed(
  () => `Hiển thị ${currentStart.value}-${currentEnd.value} / ${movementsTotal.value} phiếu`
)

function currentFilterPayload(): StockMovementListFilters {
  return {
    movement_type: filters.movement_type || undefined,
    q: filters.q || undefined,
    reference_number: filters.reference_number || undefined,
    movement_date_from: filters.movement_date_from || undefined,
    movement_date_to: filters.movement_date_to || undefined,
    limit: movementsLimit.value,
    offset: movementsOffset.value
  }
}

async function loadMovements(resetPage = false) {
  if (resetPage) movementsOffset.value = 0
  await fetchMovements(currentFilterPayload())
}

function resetFilters() {
  filters.movement_type = ''
  filters.q = ''
  filters.reference_number = ''
  filters.movement_date_from = ''
  filters.movement_date_to = ''
  void loadMovements(true)
}

function resetForm() {
  form.catalog_item_id = ''
  form.movement_type = 'in'
  form.quantity = '1'
  form.movement_date = new Date().toISOString().slice(0, 10)
  form.notes = ''
  form.reference_number = ''
  form.procurement_id = ''
  selectedCatalogName.value = ''
}

function openCreateDialog() {
  resetForm()
  dialogVisible.value = true
}

async function onCatalogSelect(item: MaterialsCatalogAutocompleteItem) {
  form.catalog_item_id = item.id
  selectedCatalogName.value = item.name
  await fetchBalance(item.id)
}

function formatMovementType(type: StockMovementType) {
  return type === 'in' ? 'Nhập' : 'Xuất'
}

function formatQuantity(value?: string | number | null, unit?: string | null) {
  if (value === undefined || value === null || value === '') return '-'
  return unit ? `${value} ${unit}` : String(value)
}

async function submitForm() {
  if (!form.catalog_item_id || !form.quantity.trim()) return
  const result = await saveMovement({ ...form })
  if (result) {
    dialogVisible.value = false
    resetForm()
    await loadMovements()
  }
}

async function removeMovement(id: string) {
  const deleted = await deleteMovement(id)
  if (deleted) await loadMovements()
}

function goToPreviousPage() {
  if (!canGoPrevious.value) return
  movementsOffset.value = Math.max(0, movementsOffset.value - movementsLimit.value)
  void loadMovements()
}

function goToNextPage() {
  if (!canGoNext.value) return
  movementsOffset.value += movementsLimit.value
  void loadMovements()
}

onMounted(() => {
  void loadMovements()
})
</script>

<template>
  <AppPageContainer>
    <AppPageHeader title="Phiếu nhập / xuất kho" description="Quản lý tồn kho vật tư theo danh mục — một kho logic.">
      <template #actions>
        <Button label="Refresh" icon="pi pi-refresh" severity="secondary" :loading="loading" @click="() => loadMovements()" />
        <Button label="Tạo phiếu" icon="pi pi-plus" @click="openCreateDialog" />
      </template>
    </AppPageHeader>

    <AppCard title="Bộ lọc">
      <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <InputText v-model="filters.q" placeholder="Tìm tên/mã vật tư, mã tham chiếu" @keyup.enter="loadMovements(true)" />
        <AppSelect v-model="filters.movement_type">
          <option v-for="option in movementTypeOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </AppSelect>
        <InputText v-model="filters.reference_number" placeholder="Mã tham chiếu" @keyup.enter="loadMovements(true)" />
        <InputText v-model="filters.movement_date_from" type="date" placeholder="Từ ngày" />
        <InputText v-model="filters.movement_date_to" type="date" placeholder="Đến ngày" />
      </div>
      <div class="mt-4 flex flex-wrap gap-2">
        <Button label="Lọc" icon="pi pi-filter" :loading="loading" @click="loadMovements(true)" />
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
      <div class="app-table-wrap">
        <DataTable :value="movements" :loading="loading" data-key="id" responsive-layout="scroll" striped-rows>
          <Column field="movement_date" header="Ngày">
            <template #body="{ data }">{{ data.movement_date }}</template>
          </Column>
          <Column header="Loại">
            <template #body="{ data }">
              <Tag
                :value="formatMovementType(data.movement_type)"
                :severity="data.movement_type === 'in' ? 'success' : 'warn'"
              />
            </template>
          </Column>
          <Column header="Vật tư">
            <template #body="{ data }">
              <div>
                <p class="font-medium">{{ data.catalog_item_name }}</p>
                <p v-if="data.catalog_item_code" class="text-xs text-slate-500">{{ data.catalog_item_code }}</p>
              </div>
            </template>
          </Column>
          <Column header="Số lượng">
            <template #body="{ data }">
              {{ formatQuantity(data.quantity, data.catalog_item_unit) }}
            </template>
          </Column>
          <Column header="Tồn sau">
            <template #body="{ data }">
              {{ formatQuantity(data.balance_after, data.catalog_item_unit) }}
            </template>
          </Column>
          <Column field="reference_number" header="Tham chiếu">
            <template #body="{ data }">{{ data.reference_number || '-' }}</template>
          </Column>
          <Column field="created_by_email" header="Người tạo">
            <template #body="{ data }">{{ data.created_by_email || '-' }}</template>
          </Column>
          <Column header="">
            <template #body="{ data }">
              <Button
                v-if="authStore.isAdmin"
                icon="pi pi-trash"
                text
                rounded
                severity="danger"
                aria-label="Xóa phiếu"
                :loading="deleting === data.id"
                @click="removeMovement(data.id)"
              />
            </template>
          </Column>
          <template #empty>
            <AppEmptyState title="Chưa có phiếu kho" description="Tạo phiếu nhập hoặc xuất để cập nhật tồn." />
          </template>
        </DataTable>
      </div>
    </AppCard>

    <Dialog v-model:visible="dialogVisible" modal header="Tạo phiếu kho" :style="{ width: 'min(560px, 96vw)' }">
      <form class="space-y-4" @submit.prevent="submitForm">
        <div>
          <label class="mb-2 block text-sm font-medium text-slate-700">Loại phiếu</label>
          <AppActionGroup v-model="form.movement_type" :options="formMovementOptions" />
        </div>

        <div>
          <label class="mb-1 block text-xs font-medium text-slate-600">Vật tư *</label>
          <MaterialsCatalogAutocomplete
            v-model="selectedCatalogName"
            :catalog-item-id="form.catalog_item_id"
            placeholder="Chọn vật tư từ danh mục..."
            @update:catalog-item-id="form.catalog_item_id = $event || ''"
            @select="onCatalogSelect"
          />
          <p v-if="currentBalance" class="mt-1 text-xs text-slate-500">
            Tồn hiện tại:
            <span class="font-medium text-slate-800">
              {{ formatQuantity(currentBalance.quantity, currentBalance.catalog_item_unit) }}
            </span>
          </p>
        </div>

        <Message v-if="outboundWarning" severity="warn" :closable="false">
          Số lượng xuất lớn hơn tồn hiện tại — hệ thống vẫn cho phép lưu (cảnh báo).
        </Message>

        <div class="grid gap-3 sm:grid-cols-2">
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-600">Số lượng *</label>
            <InputText v-model="form.quantity" required placeholder="Số lượng" />
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-600">Ngày *</label>
            <InputText v-model="form.movement_date" type="date" required />
          </div>
          <InputText v-model="form.reference_number" placeholder="Mã tham chiếu" />
          <InputText v-model="form.procurement_id" placeholder="Procurement ID (optional)" />
          <InputText v-model="form.notes" class="sm:col-span-2" placeholder="Ghi chú" />
        </div>

        <div class="flex justify-end gap-2">
          <Button type="button" label="Hủy" severity="secondary" :disabled="saving" @click="dialogVisible = false" />
          <Button type="submit" label="Lưu phiếu" icon="pi pi-save" :loading="saving" />
        </div>
      </form>
    </Dialog>
  </AppPageContainer>
</template>
