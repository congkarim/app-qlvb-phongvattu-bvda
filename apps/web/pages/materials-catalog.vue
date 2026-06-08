<script setup lang="ts">
import type { MaterialsCatalogInput, MaterialsCatalogItem } from '~/types/materials-catalog'

const authStore = useAuthStore()
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
  category: ''
})

const form = reactive<MaterialsCatalogInput>({
  code: '',
  name: '',
  default_unit: '',
  category: '',
  description: '',
  is_active: true
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

function currentFilters() {
  return {
    q: filters.q || undefined,
    is_active: filters.is_active === '' ? undefined : filters.is_active === 'true',
    category: filters.category || undefined,
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
}

function editItem(item: MaterialsCatalogItem) {
  editingId.value = item.id
  form.code = item.code || ''
  form.name = item.name
  form.default_unit = item.default_unit || ''
  form.category = item.category || ''
  form.description = item.description || ''
  form.is_active = item.is_active
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

onMounted(() => {
  if (authStore.isAdmin) void loadCatalog()
})
</script>

<template>
  <section class="space-y-5">
    <div>
      <h1 class="text-2xl font-semibold">Danh mục vật tư</h1>
      <p class="mt-1 text-sm text-slate-600">Quản lý mã vật tư dùng autocomplete khi nhập dòng hàng mua sắm.</p>
    </div>

    <Message v-if="!authStore.isAdmin" severity="warn">Chỉ admin được quản lý danh mục vật tư.</Message>

    <template v-else>
      <Card>
        <template #content>
          <div class="grid gap-3 md:grid-cols-4">
            <InputText v-model="filters.q" placeholder="Tìm mã, tên, nhóm" @keyup.enter="loadCatalog(true)" />
            <InputText v-model="filters.category" placeholder="Nhóm hàng" @keyup.enter="loadCatalog(true)" />
            <select v-model="filters.is_active" class="rounded border border-slate-300 px-3 py-2 text-sm">
              <option v-for="option in activeOptions" :key="String(option.value)" :value="option.value">
                {{ option.label }}
              </option>
            </select>
            <div class="flex gap-2">
              <Button label="Lọc" icon="pi pi-filter" :loading="loading" @click="loadCatalog(true)" />
              <Button label="Xóa lọc" icon="pi pi-times" severity="secondary" :disabled="loading" @click="resetFilters" />
            </div>
          </div>
        </template>
      </Card>

      <Card>
        <template #title>{{ editingId ? 'Sửa vật tư' : 'Thêm vật tư' }}</template>
        <template #content>
          <form class="grid gap-3 md:grid-cols-4" @submit.prevent="submitForm">
            <InputText v-model="form.code" placeholder="Mã vật tư (optional)" />
            <InputText v-model="form.name" class="md:col-span-2" required placeholder="Tên vật tư *" />
            <InputText v-model="form.default_unit" placeholder="ĐVT mặc định" />
            <InputText v-model="form.category" placeholder="Nhóm" />
            <InputText v-model="form.description" class="md:col-span-2" placeholder="Mô tả" />
            <label class="flex items-center gap-2 text-sm">
              <input v-model="form.is_active" type="checkbox" class="rounded border-slate-300" />
              Đang dùng (hiện autocomplete)
            </label>
            <div class="flex gap-2 md:col-span-4">
              <Button type="submit" :label="editingId ? 'Lưu' : 'Tạo'" icon="pi pi-save" :loading="saving" />
              <Button type="button" label="Hủy" icon="pi pi-times" severity="secondary" :disabled="saving" @click="resetForm" />
            </div>
          </form>
        </template>
      </Card>

      <Message v-if="error" severity="error">{{ error }}</Message>

      <div class="flex items-center justify-between rounded border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
        <span>Hiển thị {{ currentStart }}-{{ currentEnd }} / {{ catalogTotal }}</span>
        <div class="flex gap-2">
          <Button label="Trước" size="small" severity="secondary" :disabled="loading || !canGoPrevious" @click="goToPreviousPage" />
          <Button label="Sau" size="small" severity="secondary" :disabled="loading || !canGoNext" @click="goToNextPage" />
        </div>
      </div>

      <Card>
        <template #content>
          <DataTable :value="catalogItems" :loading="loading" data-key="id" responsive-layout="scroll" striped-rows>
            <Column field="code" header="Mã" />
            <Column field="name" header="Tên vật tư" />
            <Column field="default_unit" header="ĐVT" />
            <Column field="category" header="Nhóm" />
            <Column header="Trạng thái">
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
              <div class="py-6 text-center text-sm text-slate-500">Chưa có vật tư trong danh mục.</div>
            </template>
          </DataTable>
        </template>
      </Card>
    </template>
  </section>
</template>
