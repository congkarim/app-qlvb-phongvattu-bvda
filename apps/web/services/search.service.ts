import type { SearchResult } from '~/types/document'
import { useApiClient } from './api'

interface SearchResponse {
  query: string
  results: SearchResult[]
}

export function createSearchService() {
  const api = useApiClient()

  return {
    semantic(query: string, limit = 10) {
      return api<SearchResponse>('/search/semantic', {
        method: 'POST',
        body: { query, limit }
      })
    }
  }
}
