<script setup lang="ts">
import type { MaterialsCatalogInput, MaterialsCatalogItem } from '~/types/materials-catalog'

const authStore = useAuthStore()
const route = useRoute()
const {
  catalogItems,
  catalogTotal,
  catalogLimit,
  catalogOffset,
  loading,
  saving,
  deleting,
  error,
  fetchCatalogItems,
  saveCatalogItem,
  deleteCatalogItem
} = useMaterialsCatalog()

const filters = reactive({
  q: '',
  is_active: '' as '' | 'true' | 'false',
  category: '',
  below_min: '' as '' | 'true'
})

const form = reactive<MaterialsCatalogInput>({
  code: '',
  name: '',
  default_unit: '',
  category: '',
  description: '',
  is_active: true,
  min_stock_level: ''
})

const editingId = ref('')

const activeOptions = [
  { label: 'Tất cả', value: '' },
  { label: 'Đang dùng', value: 'true' },
  { label: 'Ẩn', value: 'false' }
]

const currentStart = computed(() => (catalogTotal.value === 0 ? 0 : catalogOffset.value + 1))
const currentEnd = computed(() => Math.min(catalogOffset.value + catalogItems.value.length, catalogTotal.value))
const canGoPrevious = computed(() => catalogOffset.value > 0)
const canGoNext = computed(() => catalogOffset.value + catalogLimit.value < catalogTotal.value)
const paginationSummary = computed(() => `Hiển thị ${currentStart.value}-${currentEnd.value} / ${catalogTotal.value} vật tư`)

function currentFilters() {
  return {
    q: filters.q || undefined,
    is_active: filters.is_active === '' ? undefined : filters.is_active === 'true',
    category: filters.category || undefined,
    below_min: filters.below_min === 'true' ? true : undefined,
    limit: catalogLimit.value,
    offset: catalogOffset.value
  }
}

async function loadCatalog(resetPage = false) {
  if (!authStore.isAdmin) return
  if (resetPage) catalogOffset.value = 0
  await fetchCatalogItems(currentFilters())
}

function resetFilters() {
  filters.q = ''
  filters.is_active = ''
  filters.category = ''
  filters.below_min = ''
  void loadCatalog(true)
}

function resetForm() {
  editingId.value = ''
  form.code = ''
  form.name = ''
  form.default_unit = ''
  form.category = ''
  form.description = ''
  form.is_active = true
  form.min_stock_level = ''
}

function editItem(item: MaterialsCatalogItem) {
  editingId.value = item.id
  form.code = item.code || ''
  form.name = item.name
  form.default_unit = item.default_unit || ''
  form.category = item.category || ''
  form.description = item.description || ''
  form.is_active = item.is_active
  form.min_stock_level = item.min_stock_level != null ? String(item.min_stock_level) : ''
}

async function submitForm() {
  if (!form.name.trim()) return
  const result = await saveCatalogItem(form, editingId.value || undefined)
  if (result) {
    resetForm()
    await loadCatalog()
  }
}

async function removeItem(id: string) {
  const deleted = await deleteCatalogItem(id)
  if (deleted) await loadCatalog()
}

function goToPreviousPage() {
  if (!canGoPrevious.value) return
  catalogOffset.value = Math.max(0, catalogOffset.value - catalogLimit.value)
  void loadCatalog()
}

function goToNextPage() {
  if (!canGoNext.value) return
  catalogOffset.value += catalogLimit.value
  void loadCatalog()
}

function formatStock(value?: string | number | null, unit?: string | null) {
  if (value === undefined || value === null || value === '') return '-'
  return unit ? `${value} ${unit}` : String(value)
}

onMounted(() => {
  if (route.query.below_min === '1' || route.query.below_min === 'true') {
    filters.below_min = 'true'
  }
  if (authStore.isAdmin) void loadCatalog()
})
</script>

<template>
  <AppPageContainer>
    <AppPageHeader title="Danh mục vật tư" description="Quản lý mã vật tư, tồn tối thiểu và autocomplete dòng hàng mua sắm.">
      <template #actions>
        <NuxtLink to="/stock-movements">
          <Button label="Phiếu kho" icon="pi pi-box" severity="secondary" />
        </NuxtLink>
      </template>
    </AppPageHeader>

    <Message v-if="!authStore.isAdmin" severity="warn">Chỉ admin được quản lý danh mục vật tư.</Message>

    <template v-else>
      <AppCard title="Bộ lọc">
        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <InputText v-model="filters.q" placeholder="Tìm mã, tên, nhóm" @keyup.enter="loadCatalog(true)" />
          <InputText v-model="filters.category" placeholder="Nhóm hàng" @keyup.enter="loadCatalog(true)" />
          <AppSelect v-model="filters.is_active">
            <option v-for="option in activeOptions" :key="String(option.value)" :value="option.value">
              {{ option.label }}
            </option>
          </AppSelect>
          <AppSelect v-model="filters.below_min">
            <option value="">Tất cả tồn</option>
            <option value="true">Tồn thấp / hết</option>
          </AppSelect>
        </div>
        <div class="mt-4 flex flex-wrap gap-2">
          <Button label="Lọc" icon="pi pi-filter" :loading="loading" @click="loadCatalog(true)" />
          <Button label="Xóa lọc" icon="pi pi-times" severity="secondary" :disabled="loading" @click="resetFilters" />
        </div>
      </AppCard>

      <AppCard :title="editingId ? 'Sửa vật tư' : 'Thêm vật tư'">
        <form class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4" @submit.prevent="submitForm">
          <InputText v-model="form.code" placeholder="Mã vật tư (optional)" />
          <InputText v-model="form.name" class="sm:col-span-2" required placeholder="Tên vật tư *" />
          <InputText v-model="form.default_unit" placeholder="ĐVT mặc định" />
          <InputText v-model="form.category" placeholder="Nhóm" />
          <InputText v-model="form.min_stock_level" placeholder="Tồn tối thiểu" />
          <InputText v-model="form.description" class="sm:col-span-2" placeholder="Mô tả" />
          <label class="flex items-center gap-2 text-sm">
            <input v-model="form.is_active" type="checkbox" class="rounded border-slate-300" />
            Đang dùng (hiện autocomplete)
          </label>
          <div class="flex gap-2 sm:col-span-2 lg:col-span-4">
            <Button type="submit" :label="editingId ? 'Lưu' : 'Tạo'" icon="pi pi-save" :loading="saving" />
            <Button type="button" label="Hủy" icon="pi pi-times" severity="secondary" :disabled="saving" @click="resetForm" />
          </div>
        </form>
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
          <DataTable :value="catalogItems" :loading="loading" data-key="id" responsive-layout="scroll" striped-rows>
            <Column field="code" header="Mã" />
            <Column field="name" header="Tên vật tư" />
            <Column field="default_unit" header="ĐVT" />
            <Column header="Tồn hiện tại">
              <template #body="{ data }">
                {{ formatStock(data.stock_quantity, data.default_unit) }}
              </template>
            </Column>
            <Column header="Tồn tối thiểu">
              <template #body="{ data }">
                {{ formatStock(data.min_stock_level, data.default_unit) }}
              </template>
            </Column>
            <Column header="Trạng thái tồn">
              <template #body="{ data }">
                <StockLevelBadge :quantity="data.stock_quantity" :min-stock-level="data.min_stock_level" />
              </template>
            </Column>
            <Column field="category" header="Nhóm" />
            <Column header="Catalog">
              <template #body="{ data }">
                <Tag :value="data.is_active ? 'Active' : 'Ẩn'" :severity="data.is_active ? 'success' : 'secondary'" />
              </template>
            </Column>
            <Column header="">
              <template #body="{ data }">
                <div class="flex gap-2">
                  <Button icon="pi pi-pencil" text rounded aria-label="Sửa" @click="editItem(data)" />
                  <Button
                    icon="pi pi-trash"
                    text
                    rounded
                    severity="danger"
                    aria-label="Xóa"
                    :loading="deleting === data.id"
                    @click="removeItem(data.id)"
                  />
                </div>
              </template>
            </Column>
            <template #empty>
              <AppEmptyState title="Chưa có vật tư" description="Thêm vật tư vào danh mục để dùng autocomplete và tồn kho." />
            </template>
          </DataTable>
        </div>
      </AppCard>
    </template>
  </AppPageContainer>
</template>
