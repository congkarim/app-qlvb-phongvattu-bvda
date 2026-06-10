export interface MaterialsCatalogAutocompleteItem {
  id: string
  code?: string | null
  name: string
  default_unit?: string | null
  category?: string | null
  stock_quantity?: string | number | null
}

export interface MaterialsCatalogItem extends MaterialsCatalogAutocompleteItem {
  description?: string | null
  is_active: boolean
  min_stock_level?: string | number | null
  stock_quantity?: string | number
  is_below_min?: boolean
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
  min_stock_level?: string
}

export interface MaterialsCatalogListFilters {
  q?: string
  is_active?: boolean | ''
  category?: string
  below_min?: boolean | ''
  limit?: number
  offset?: number
}

export interface MaterialsCatalogListResponse {
  items: MaterialsCatalogItem[]
  total: number
  limit: number
  offset: number
}
