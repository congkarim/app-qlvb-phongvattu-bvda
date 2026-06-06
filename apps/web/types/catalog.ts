export interface CatalogItem {
  id: string
  catalog_type: 'business_type' | 'document_type'
  code: string
  label: string
  description?: string | null
  sort_order: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CatalogOption {
  label: string
  value: string
}
