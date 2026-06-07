export type DecisionKind = 'decision' | 'notification'
export type DecisionStatus = 'draft' | 'registered' | 'effective' | 'expired' | 'revoked' | 'archived'

export interface DecisionItem {
  id: string
  document_id: string
  document_title?: string | null
  document_type?: string | null
  document_status?: string | null
  decision_kind: DecisionKind
  document_number?: string | null
  document_symbol?: string | null
  issued_date?: string | null
  issuing_agency?: string | null
  excerpt?: string | null
  effective_from?: string | null
  effective_to?: string | null
  status: DecisionStatus
  notes?: string | null
  created_at: string
  updated_at: string
}

export interface DecisionInput {
  document_id: string
  decision_kind: DecisionKind
  document_number?: string
  document_symbol?: string
  issued_date?: string
  issuing_agency?: string
  excerpt?: string
  effective_from?: string
  effective_to?: string
  status: DecisionStatus
  notes?: string
}

export interface DecisionListFilters {
  q?: string
  document_id?: string
  decision_kind?: DecisionKind | ''
  document_number?: string
  issuing_agency?: string
  status?: DecisionStatus | ''
  issued_date_from?: string
  issued_date_to?: string
  effective_from?: string
  effective_to?: string
  sort_by?:
    | 'created_at'
    | 'updated_at'
    | 'document_number'
    | 'decision_kind'
    | 'issuing_agency'
    | 'status'
    | 'issued_date'
    | 'effective_from'
    | 'effective_to'
  sort_dir?: 'asc' | 'desc'
  limit?: number
  offset?: number
}

export interface DecisionListResponse {
  items: DecisionItem[]
  total: number
  limit: number
  offset: number
}
