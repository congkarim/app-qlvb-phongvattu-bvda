import type { OnboardingSuggestion } from '~/types/onboarding'
import { createDocumentService } from '~/services/document.service'

export function useDocumentOnboarding() {
  const service = createDocumentService()
  const suggestion = ref<OnboardingSuggestion | null>(null)
  const loading = ref(false)
  const error = ref('')

  async function fetchOnboardingSuggestions(documentId: string) {
    if (!documentId) return null
    loading.value = true
    error.value = ''
    try {
      suggestion.value = await service.getOnboardingSuggestions(documentId)
      return suggestion.value
    } catch {
      error.value = 'Không tải được gợi ý metadata module'
      suggestion.value = null
      return null
    } finally {
      loading.value = false
    }
  }

  function clearOnboardingSuggestions() {
    suggestion.value = null
    error.value = ''
  }

  return {
    suggestion,
    loading,
    error,
    fetchOnboardingSuggestions,
    clearOnboardingSuggestions
  }
}
