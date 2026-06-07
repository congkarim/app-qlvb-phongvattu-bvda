import type { RelationSuggestion, RelationSuggestionsResponse } from '~/types/document-relation'
import { createDocumentRelationService } from '~/services/document-relation.service'

export function useDocumentRelationSuggestions() {
  const service = createDocumentRelationService()
  const response = ref<RelationSuggestionsResponse | null>(null)
  const loading = ref(false)
  const error = ref('')

  const suggestions = computed<RelationSuggestion[]>(() => response.value?.suggestions ?? [])

  async function fetchRelationSuggestions(documentId: string) {
    if (!documentId) return null
    loading.value = true
    error.value = ''
    try {
      response.value = await service.getRelationSuggestions(documentId)
      return response.value
    } catch (err) {
      const fetchError = err as { statusCode?: number }
      if (fetchError.statusCode === 404) {
        response.value = null
        return null
      }
      error.value = 'Không tải được gợi ý liên kết văn bản'
      response.value = null
      return null
    } finally {
      loading.value = false
    }
  }

  function clearRelationSuggestions() {
    response.value = null
    error.value = ''
  }

  return {
    response,
    suggestions,
    loading,
    error,
    fetchRelationSuggestions,
    clearRelationSuggestions
  }
}
