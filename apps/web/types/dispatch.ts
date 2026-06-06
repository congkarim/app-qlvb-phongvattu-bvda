export type DispatchType = 'incoming' | 'outgoing'
export type DispatchStatus = 'draft' | 'registered' | 'processing' | 'completed' | 'archived'

export interface DispatchItem {
  id: string
  document_id: string
  document_title?: string | null
  document_number?: string | null
  document_status?: string | null
  dispatch_type: DispatchType
  document_symbol?: string | null
  issued_date?: string | null
  issuing_agency?: string | null
  recipient?: string | null
  excerpt?: string | null
  status: DispatchStatus
  notes?: string | null
  created_at: string
  updated_at: string
}

export interface DispatchInput {
  document_id: string
  dispatch_type: DispatchType
  document_number?: string
  document_symbol?: string
  issued_date?: string
  issuing_agency?: string
  recipient?: string
  excerpt?: string
  status: DispatchStatus
  notes?: string
}

export interface DispatchListFilters {
  q?: string
  document_id?: string
  dispatch_type?: DispatchType | ''
  document_number?: string
  issuing_agency?: string
  status?: DispatchStatus | ''
  issued_date_from?: string
  issued_date_to?: string
  sort_by?: 'created_at' | 'updated_at' | 'document_number' | 'dispatch_type' | 'issuing_agency' | 'status' | 'issued_date'
  sort_dir?: 'asc' | 'desc'
  limit?: number
  offset?: number
}

export interface DispatchListResponse {
  items: DispatchItem[]
  total: number
  limit: number
  offset: number
}
