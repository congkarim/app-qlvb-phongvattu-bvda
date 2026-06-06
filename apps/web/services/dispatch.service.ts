import type { DispatchInput, DispatchItem, DispatchListFilters, DispatchListResponse } from '~/types/dispatch'
import { useApiClient } from './api'

export function createDispatchService() {
  const api = useApiClient()

  return {
    list(filters: DispatchListFilters = {}) {
      const params = new URLSearchParams()
      for (const [key, value] of Object.entries(filters)) {
        if (value !== undefined && value !== null && String(value).trim() !== '') {
          params.set(key, String(value))
        }
      }
      const query = params.toString()
      return api<DispatchListResponse>(`/dispatches${query ? `?${query}` : ''}`)
    },
    get(id: string) {
      return api<DispatchItem>(`/dispatches/${id}`)
    },
    async getByDocumentId(documentId: string) {
      try {
        return await api<DispatchItem>(`/dispatches/by-document/${documentId}`)
      } catch (error: unknown) {
        const statusCode = (error as { statusCode?: number })?.statusCode
        if (statusCode === 404) return null
        throw error
      }
    },
    create(input: DispatchInput) {
      return api<DispatchItem>('/dispatches', {
        method: 'POST',
        body: normalizeDispatchInput(input)
      })
    },
    update(id: string, input: Omit<DispatchInput, 'document_id'>) {
      return api<DispatchItem>(`/dispatches/${id}`, {
        method: 'PATCH',
        body: normalizeDispatchInput(input)
      })
    },
    delete(id: string) {
      return api<DispatchItem>(`/dispatches/${id}`, {
        method: 'DELETE'
      })
    }
  }
}

function normalizeDispatchInput(input: Partial<DispatchInput>) {
  return {
    ...('document_id' in input ? { document_id: input.document_id?.trim() || '' } : {}),
    ...('dispatch_type' in input ? { dispatch_type: input.dispatch_type } : {}),
    document_number: input.document_number?.trim() || null,
    document_symbol: input.document_symbol?.trim() || null,
    issued_date: input.issued_date?.trim() || null,
    issuing_agency: input.issuing_agency?.trim() || null,
    recipient: input.recipient?.trim() || null,
    excerpt: input.excerpt?.trim() || null,
    status: input.status || 'draft',
    notes: input.notes?.trim() || null
  }
}
