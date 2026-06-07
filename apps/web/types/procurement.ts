export type ProcurementKind = 'proposal' | 'plan' | 'acceptance'
export type ProcurementStatus = 'draft' | 'submitted' | 'approved' | 'rejected' | 'completed' | 'archived'

export interface ProcurementItem {
  id: string
  document_id: string
  document_title?: string | null
  document_number?: string | null
  document_status?: string | null
  procurement_kind: ProcurementKind
  reference_number?: string | null
  title_summary?: string | null
  requesting_unit?: string | null
  estimated_value?: string | number | null
  currency: string
  requested_date?: string | null
  status: ProcurementStatus
  notes?: string | null
  created_at: string
  updated_at: string
}

export interface ProcurementInput {
  document_id: string
  procurement_kind: ProcurementKind
  reference_number?: string
  title_summary?: string
  requesting_unit?: string
  estimated_value?: string | number | null
  currency?: string
  requested_date?: string
  status: ProcurementStatus
  notes?: string
}

export interface ProcurementListFilters {
  q?: string
  document_id?: string
  procurement_kind?: ProcurementKind | ''
  reference_number?: string
  requesting_unit?: string
  status?: ProcurementStatus | ''
  requested_date_from?: string
  requested_date_to?: string
  sort_by?:
    | 'created_at'
    | 'updated_at'
    | 'reference_number'
    | 'procurement_kind'
    | 'requesting_unit'
    | 'status'
    | 'requested_date'
    | 'estimated_value'
  sort_dir?: 'asc' | 'desc'
  limit?: number
  offset?: number
}

export interface ProcurementListResponse {
  items: ProcurementItem[]
  total: number
  limit: number
  offset: number
}
