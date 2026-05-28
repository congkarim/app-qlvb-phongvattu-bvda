import type { SearchResult } from '~/types/document'
import { createSearchService } from '~/services/search.service'

export function useSemanticSearch() {
  const results = ref<SearchResult[]>([])
  const loading = ref(false)
  const error = ref('')
  const hasSearched = ref(false)
  const service = createSearchService()

  async function search(query: string) {
    const trimmedQuery = query.trim()
    if (!trimmedQuery) {
      error.value = 'Vui lòng nhập nội dung tìm kiếm'
      results.value = []
      hasSearched.value = false
      return
    }

    loading.value = true
    error.value = ''
    hasSearched.value = true
    try {
      const response = await service.semantic(trimmedQuery)
      results.value = response.results
    } catch {
      error.value = 'Không tìm kiếm được'
      results.value = []
    } finally {
      loading.value = false
    }
  }

  return { results, loading, error, hasSearched, search }
}
