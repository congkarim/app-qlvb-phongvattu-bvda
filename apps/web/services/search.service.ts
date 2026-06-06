import type { SearchResult, SemanticSearchFilters } from '~/types/document'
import { useApiClient } from './api'

interface SearchResponse {
  query: string
  results: SearchResult[]
}

export function createSearchService() {
  const api = useApiClient()

  return {
    semantic(query: string, filters: SemanticSearchFilters = {}) {
      return api<SearchResponse>('/search/semantic', {
        method: 'POST',
        body: normalizeSearchPayload(query, filters)
      })
    }
  }
}

function normalizeSearchPayload(query: string, filters: SemanticSearchFilters) {
  const payload: Record<string, unknown> = {
    query,
    limit: filters.limit || 10
  }
  for (const key of [
    'document_type',
    'business_type',
    'document_number',
    'issued_date',
    'doc_group',
    'section_role',
    'contract_number',
    'supplier_name'
  ] as const) {
    const value = filters[key]?.trim()
    if (value) payload[key] = value
  }
  if (filters.contract_status) {
    payload.contract_status = filters.contract_status
  }
  if (filters.requires_review !== null && filters.requires_review !== undefined) {
    payload.requires_review = filters.requires_review
  }
  return payload
}
