export type StockMovementType = 'in' | 'out'

export interface StockMovementItem {
  id: string
  catalog_item_id: string
  catalog_item_code?: string | null
  catalog_item_name: string
  catalog_item_unit?: string | null
  movement_type: StockMovementType
  quantity: string | number
  movement_date: string
  notes?: string | null
  reference_number?: string | null
  procurement_id?: string | null
  balance_after: string | number
  created_by_user_id: string
  created_by_email?: string | null
  created_at: string
  updated_at: string
}

export interface StockMovementInput {
  catalog_item_id: string
  movement_type: StockMovementType
  quantity: string
  movement_date: string
  notes?: string
  reference_number?: string
  procurement_id?: string
}

export interface StockMovementListFilters {
  movement_type?: StockMovementType | ''
  catalog_item_id?: string
  q?: string
  reference_number?: string
  movement_date_from?: string
  movement_date_to?: string
  limit?: number
  offset?: number
}

export interface StockMovementListResponse {
  items: StockMovementItem[]
  total: number
  limit: number
  offset: number
}

export interface StockBalanceItem {
  catalog_item_id: string
  catalog_item_code?: string | null
  catalog_item_name: string
  catalog_item_unit?: string | null
  quantity: string | number
  min_stock_level?: string | number | null
  is_below_min: boolean
}

export interface LowStockListResponse {
  items: StockBalanceItem[]
  total: number
}
