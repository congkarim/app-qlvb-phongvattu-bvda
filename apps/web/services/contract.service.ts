import type { ContractInput, ContractItem, ContractListFilters, ContractListResponse } from '~/types/contract'
import { useApiClient } from './api'

export function createContractService() {
  const api = useApiClient()

  return {
    list(filters: ContractListFilters = {}) {
      const params = new URLSearchParams()
      for (const [key, value] of Object.entries(filters)) {
        if (value !== undefined && value !== null && String(value).trim() !== '') {
          params.set(key, String(value))
        }
      }
      const query = params.toString()
      return api<ContractListResponse>(`/contracts${query ? `?${query}` : ''}`)
    },
    get(id: string) {
      return api<ContractItem>(`/contracts/${id}`)
    },
    create(input: ContractInput) {
      return api<ContractItem>('/contracts', {
        method: 'POST',
        body: normalizeContractInput(input)
      })
    },
    update(id: string, input: Omit<ContractInput, 'document_id'>) {
      return api<ContractItem>(`/contracts/${id}`, {
        method: 'PATCH',
        body: normalizeContractInput(input)
      })
    },
    delete(id: string) {
      return api<ContractItem>(`/contracts/${id}`, {
        method: 'DELETE'
      })
    }
  }
}

function normalizeContractInput(input: Partial<ContractInput>) {
  return {
    ...('document_id' in input ? { document_id: input.document_id?.trim() || '' } : {}),
    contract_number: input.contract_number?.trim() || null,
    contract_title: input.contract_title?.trim() || null,
    supplier_name: input.supplier_name?.trim() || null,
    sign_date: input.sign_date?.trim() || null,
    effective_from: input.effective_from?.trim() || null,
    effective_to: input.effective_to?.trim() || null,
    contract_value: input.contract_value?.trim() || null,
    currency: input.currency?.trim().toUpperCase() || 'VND',
    status: input.status || 'draft',
    notes: input.notes?.trim() || null
  }
}
