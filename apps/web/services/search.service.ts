import type { RagAnswerFilters, RagAnswerResponse, SearchResult, SemanticSearchFilters } from '~/types/document'
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
    },
    answer(query: string, filters: RagAnswerFilters = {}) {
      const payload = normalizeSearchPayload(query, filters, { defaultLimit: 6 })
      if (filters.min_score !== undefined) {
        payload.min_score = filters.min_score
      }
      if (filters.max_citations !== undefined) {
        payload.max_citations = filters.max_citations
      }
      return api<RagAnswerResponse>('/search/answer', {
        method: 'POST',
        body: payload
      })
    }
  }
}

function normalizeSearchPayload(
  query: string,
  filters: SemanticSearchFilters,
  options: { defaultLimit?: number } = {}
) {
  const payload: Record<string, unknown> = {
    query,
    limit: filters.limit || options.defaultLimit || 10
  }
  for (const key of [
    'document_type',
    'business_type',
    'document_number',
    'issuing_agency',
    'issued_date',
    'doc_group',
    'section_role',
    'contract_number',
    'supplier_name',
    'effective_from',
    'effective_to',
    'reference_number',
    'requesting_unit'
  ] as const) {
    const value = filters[key]?.trim()
    if (value) payload[key] = value
  }
  if (filters.contract_status) {
    payload.contract_status = filters.contract_status
  }
  if (filters.dispatch_type) {
    payload.dispatch_type = filters.dispatch_type
  }
  if (filters.dispatch_status) {
    payload.dispatch_status = filters.dispatch_status
  }
  if (filters.decision_kind) {
    payload.decision_kind = filters.decision_kind
  }
  if (filters.decision_status) {
    payload.decision_status = filters.decision_status
  }
  if (filters.procurement_kind) {
    payload.procurement_kind = filters.procurement_kind
  }
  if (filters.procurement_status) {
    payload.procurement_status = filters.procurement_status
  }
  if (filters.requires_review !== null && filters.requires_review !== undefined) {
    payload.requires_review = filters.requires_review
  }
  return payload
}
