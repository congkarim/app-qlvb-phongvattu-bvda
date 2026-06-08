import type {
  MaterialsCatalogAutocompleteItem,
  MaterialsCatalogInput,
  MaterialsCatalogItem,
  MaterialsCatalogListFilters
} from '~/types/materials-catalog'
import { createMaterialsCatalogService } from '~/services/materials-catalog.service'

export function useMaterialsCatalog() {
  const catalogItems = ref<MaterialsCatalogItem[]>([])
  const catalogTotal = ref(0)
  const catalogLimit = ref(50)
  const catalogOffset = ref(0)
  const autocompleteItems = ref<MaterialsCatalogAutocompleteItem[]>([])
  const autocompleteLoading = ref(false)
  const loading = ref(false)
  const saving = ref(false)
  const deleting = ref('')
  const error = ref('')
  const service = createMaterialsCatalogService()

  async function searchActiveCatalog(query: string, limit = 20) {
    autocompleteLoading.value = true
    try {
      autocompleteItems.value = await service.listActive(query, limit)
      return autocompleteItems.value
    } catch {
      autocompleteItems.value = []
      return []
    } finally {
      autocompleteLoading.value = false
    }
  }

  async function fetchCatalogItems(filters: MaterialsCatalogListFilters = {}) {
    loading.value = true
    error.value = ''
    try {
      const result = await service.listAll(filters)
      catalogItems.value = result.items
      catalogTotal.value = result.total
      catalogLimit.value = result.limit
      catalogOffset.value = result.offset
    } catch {
      error.value = 'Không tải được danh mục vật tư'
      catalogItems.value = []
      catalogTotal.value = 0
    } finally {
      loading.value = false
    }
  }

  async function saveCatalogItem(input: MaterialsCatalogInput, id?: string): Promise<MaterialsCatalogItem | null> {
    saving.value = true
    error.value = ''
    try {
      return id ? await service.update(id, input) : await service.create(input)
    } catch {
      error.value = id ? 'Không cập nhật được danh mục vật tư' : 'Không tạo được danh mục vật tư'
      return null
    } finally {
      saving.value = false
    }
  }

  async function deleteCatalogItem(id: string): Promise<boolean> {
    deleting.value = id
    error.value = ''
    try {
      await service.delete(id)
      catalogItems.value = catalogItems.value.filter((item) => item.id !== id)
      catalogTotal.value = Math.max(0, catalogTotal.value - 1)
      return true
    } catch {
      error.value = 'Không xóa được danh mục vật tư'
      return false
    } finally {
      deleting.value = ''
    }
  }

  return {
    catalogItems,
    catalogTotal,
    catalogLimit,
    catalogOffset,
    autocompleteItems,
    autocompleteLoading,
    loading,
    saving,
    deleting,
    error,
    searchActiveCatalog,
    fetchCatalogItems,
    saveCatalogItem,
    deleteCatalogItem
  }
}
