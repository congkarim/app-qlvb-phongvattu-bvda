export type ContractStatus = 'draft' | 'active' | 'expired' | 'terminated' | 'completed'

export interface ContractItem {
  id: string
  document_id: string
  document_title?: string | null
  document_number?: string | null
  document_status?: string | null
  contract_number?: string | null
  contract_title?: string | null
  supplier_name?: string | null
  sign_date?: string | null
  effective_from?: string | null
  effective_to?: string | null
  contract_value?: string | number | null
  currency: string
  status: ContractStatus
  notes?: string | null
  created_at: string
  updated_at: string
}

export interface ContractInput {
  document_id: string
  contract_number?: string
  contract_title?: string
  supplier_name?: string
  sign_date?: string
  effective_from?: string
  effective_to?: string
  contract_value?: string
  currency: string
  status: ContractStatus
  notes?: string
}

export interface ContractListFilters {
  q?: string
  document_id?: string
  contract_number?: string
  supplier_name?: string
  status?: ContractStatus | ''
  sign_date_from?: string
  sign_date_to?: string
  effective_to_from?: string
  effective_to_to?: string
  sort_by?: 'created_at' | 'updated_at' | 'contract_number' | 'supplier_name' | 'status' | 'sign_date' | 'effective_to'
  sort_dir?: 'asc' | 'desc'
  limit?: number
  offset?: number
}

export interface ContractListResponse {
  items: ContractItem[]
  total: number
  limit: number
  offset: number
}
