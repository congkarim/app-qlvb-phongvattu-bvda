import type { DecisionInput, DecisionItem, DecisionListFilters, DecisionListResponse } from '~/types/decision'
import { useApiClient } from './api'

export function createDecisionService() {
  const api = useApiClient()

  return {
    list(filters: DecisionListFilters = {}) {
      const params = new URLSearchParams()
      for (const [key, value] of Object.entries(filters)) {
        if (value !== undefined && value !== null && String(value).trim() !== '') {
          params.set(key, String(value))
        }
      }
      const query = params.toString()
      return api<DecisionListResponse>(`/decisions${query ? `?${query}` : ''}`)
    },
    get(id: string) {
      return api<DecisionItem>(`/decisions/${id}`)
    },
    async getByDocumentId(documentId: string) {
      try {
        return await api<DecisionItem>(`/decisions/by-document/${documentId}`)
      } catch (error: unknown) {
        const statusCode = (error as { statusCode?: number })?.statusCode
        if (statusCode === 404) return null
        throw error
      }
    },
    create(input: DecisionInput) {
      return api<DecisionItem>('/decisions', {
        method: 'POST',
        body: normalizeDecisionInput(input)
      })
    },
    update(id: string, input: Omit<DecisionInput, 'document_id'>) {
      return api<DecisionItem>(`/decisions/${id}`, {
        method: 'PATCH',
        body: normalizeDecisionInput(input)
      })
    },
    delete(id: string) {
      return api<DecisionItem>(`/decisions/${id}`, {
        method: 'DELETE'
      })
    }
  }
}

function normalizeDecisionInput(input: Partial<DecisionInput>) {
  return {
    ...('document_id' in input ? { document_id: input.document_id?.trim() || '' } : {}),
    ...('decision_kind' in input ? { decision_kind: input.decision_kind } : {}),
    document_number: input.document_number?.trim() || null,
    document_symbol: input.document_symbol?.trim() || null,
    issued_date: input.issued_date?.trim() || null,
    issuing_agency: input.issuing_agency?.trim() || null,
    excerpt: input.excerpt?.trim() || null,
    effective_from: input.effective_from?.trim() || null,
    effective_to: input.effective_to?.trim() || null,
    status: input.status || 'draft',
    notes: input.notes?.trim() || null
  }
}
