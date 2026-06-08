import type {
  MaterialsCatalogAutocompleteItem,
  MaterialsCatalogInput,
  MaterialsCatalogItem,
  MaterialsCatalogListFilters,
  MaterialsCatalogListResponse
} from '~/types/materials-catalog'
import { useApiClient } from './api'

export function createMaterialsCatalogService() {
  const api = useApiClient()

  return {
    listActive(query?: string, limit = 20) {
      const params = new URLSearchParams()
      if (query?.trim()) params.set('q', query.trim())
      params.set('limit', String(limit))
      const suffix = params.toString()
      return api<MaterialsCatalogAutocompleteItem[]>(`/materials-catalog${suffix ? `?${suffix}` : ''}`)
    },
    get(id: string) {
      return api<MaterialsCatalogItem>(`/materials-catalog/${id}`)
    },
    listAll(filters: MaterialsCatalogListFilters = {}) {
      const params = new URLSearchParams()
      for (const [key, value] of Object.entries(filters)) {
        if (value !== undefined && value !== null && String(value).trim() !== '') {
          params.set(key, String(value))
        }
      }
      const query = params.toString()
      return api<MaterialsCatalogListResponse>(`/materials-catalog/all${query ? `?${query}` : ''}`)
    },
    create(input: MaterialsCatalogInput) {
      return api<MaterialsCatalogItem>('/materials-catalog', {
        method: 'POST',
        body: normalizeCatalogInput(input)
      })
    },
    update(id: string, input: Partial<MaterialsCatalogInput>) {
      return api<MaterialsCatalogItem>(`/materials-catalog/${id}`, {
        method: 'PATCH',
        body: normalizeCatalogInput(input)
      })
    },
    delete(id: string) {
      return api<MaterialsCatalogItem>(`/materials-catalog/${id}`, {
        method: 'DELETE'
      })
    }
  }
}

function normalizeCatalogInput(input: Partial<MaterialsCatalogInput>) {
  const payload: Record<string, unknown> = {}
  if ('code' in input) payload.code = input.code?.trim() || null
  if ('name' in input) payload.name = input.name?.trim() || ''
  if ('default_unit' in input) payload.default_unit = input.default_unit?.trim() || null
  if ('category' in input) payload.category = input.category?.trim() || null
  if ('description' in input) payload.description = input.description?.trim() || null
  if ('is_active' in input && input.is_active !== undefined) payload.is_active = input.is_active
  return payload
}
