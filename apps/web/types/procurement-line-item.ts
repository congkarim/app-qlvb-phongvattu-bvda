export interface ProcurementLineItem {
  id: string
  procurement_id: string
  line_number: number
  item_name: string
  item_code?: string | null
  unit?: string | null
  quantity: string | number
  unit_price?: string | number | null
  amount?: string | number | null
  catalog_item_id?: string | null
  notes?: string | null
  created_at: string
  updated_at: string
}

export interface ProcurementLineItemInput {
  line_number?: number
  item_name: string
  item_code?: string
  unit?: string
  quantity?: string | number
  unit_price?: string | number | null
  amount?: string | number | null
  catalog_item_id?: string | null
  notes?: string
}

export interface ProcurementLineItemListResponse {
  items: ProcurementLineItem[]
  total: number
  lines_total_amount?: string | number | null
}
