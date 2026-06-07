import type { RelationSuggestion, RelationSuggestionsResponse } from '~/types/document-relation'
import { createDocumentRelationService } from '~/services/document-relation.service'
import { buildRelationSuggestionKey } from '~/utils/documentRelations'

export function useDocumentRelationSuggestions() {
  const service = createDocumentRelationService()
  const response = ref<RelationSuggestionsResponse | null>(null)
  const loading = ref(false)
  const error = ref('')
  const dismissedKeys = ref<Set<string>>(new Set())

  const suggestions = computed<RelationSuggestion[]>(() => response.value?.suggestions ?? [])

  const visibleSuggestions = computed<RelationSuggestion[]>(() =>
    suggestions.value.filter((item) => !dismissedKeys.value.has(buildRelationSuggestionKey(item)))
  )

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

  function dismissSuggestion(suggestion: RelationSuggestion) {
    const next = new Set(dismissedKeys.value)
    next.add(buildRelationSuggestionKey(suggestion))
    dismissedKeys.value = next
  }

  function clearDismissedSuggestions() {
    dismissedKeys.value = new Set()
  }

  function clearRelationSuggestions() {
    response.value = null
    error.value = ''
    clearDismissedSuggestions()
  }

  return {
    response,
    suggestions,
    visibleSuggestions,
    loading,
    error,
    fetchRelationSuggestions,
    dismissSuggestion,
    clearDismissedSuggestions,
    clearRelationSuggestions
  }
}
