export interface MaterialsCatalogAutocompleteItem {
  id: string
  code?: string | null
  name: string
  default_unit?: string | null
  category?: string | null
}

export interface MaterialsCatalogItem extends MaterialsCatalogAutocompleteItem {
  description?: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface MaterialsCatalogInput {
  code?: string
  name: string
  default_unit?: string
  category?: string
  description?: string
  is_active?: boolean
}

export interface MaterialsCatalogListFilters {
  q?: string
  is_active?: boolean | ''
  category?: string
  limit?: number
  offset?: number
}

export interface MaterialsCatalogListResponse {
  items: MaterialsCatalogItem[]
  total: number
  limit: number
  offset: number
}
