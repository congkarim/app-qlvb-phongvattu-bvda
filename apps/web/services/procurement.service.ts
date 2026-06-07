import type {
  ProcurementInput,
  ProcurementItem,
  ProcurementListFilters,
  ProcurementListResponse
} from '~/types/procurement'
import { useApiClient } from './api'

export function createProcurementService() {
  const api = useApiClient()

  return {
    list(filters: ProcurementListFilters = {}) {
      const params = new URLSearchParams()
      for (const [key, value] of Object.entries(filters)) {
        if (value !== undefined && value !== null && String(value).trim() !== '') {
          params.set(key, String(value))
        }
      }
      const query = params.toString()
      return api<ProcurementListResponse>(`/procurements${query ? `?${query}` : ''}`)
    },
    get(id: string) {
      return api<ProcurementItem>(`/procurements/${id}`)
    },
    async getByDocumentId(documentId: string) {
      try {
        return await api<ProcurementItem>(`/procurements/by-document/${documentId}`)
      } catch (error: unknown) {
        const statusCode = (error as { statusCode?: number })?.statusCode
        if (statusCode === 404) return null
        throw error
      }
    },
    create(input: ProcurementInput) {
      return api<ProcurementItem>('/procurements', {
        method: 'POST',
        body: normalizeProcurementInput(input)
      })
    },
    update(id: string, input: Omit<ProcurementInput, 'document_id'>) {
      return api<ProcurementItem>(`/procurements/${id}`, {
        method: 'PATCH',
        body: normalizeProcurementInput(input)
      })
    },
    delete(id: string) {
      return api<ProcurementItem>(`/procurements/${id}`, {
        method: 'DELETE'
      })
    }
  }
}

function normalizeProcurementInput(input: Partial<ProcurementInput>) {
  const estimatedValue = normalizeEstimatedValue(input.estimated_value)
  return {
    ...('document_id' in input ? { document_id: input.document_id?.trim() || '' } : {}),
    ...('procurement_kind' in input ? { procurement_kind: input.procurement_kind } : {}),
    reference_number: input.reference_number?.trim() || null,
    title_summary: input.title_summary?.trim() || null,
    requesting_unit: input.requesting_unit?.trim() || null,
    estimated_value: estimatedValue,
    currency: input.currency?.trim()?.toUpperCase() || 'VND',
    requested_date: input.requested_date?.trim() || null,
    status: input.status || 'draft',
    notes: input.notes?.trim() || null
  }
}

function normalizeEstimatedValue(value: string | number | null | undefined) {
  if (value === undefined || value === null || value === '') return null
  const normalized = String(value).trim().replace(/,/g, '')
  return normalized || null
}
