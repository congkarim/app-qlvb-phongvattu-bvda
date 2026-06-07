import type { RagAnswerFilters, RagCitation, RagFallbackReason, RagGenerationMode } from '~/types/document'
import { createSearchService } from '~/services/search.service'

export function useRagAnswer() {
  const question = ref('')
  const answer = ref('')
  const citations = ref<RagCitation[]>([])
  const grounded = ref(false)
  const confidence = ref(0)
  const fallbackReason = ref<RagFallbackReason | null>(null)
  const generationMode = ref<RagGenerationMode | null>(null)
  const modelName = ref<string | null>(null)
  const latencyMs = ref<number | null>(null)
  const loading = ref(false)
  const error = ref('')
  const hasAsked = ref(false)
  const service = createSearchService()

  function clear() {
    answer.value = ''
    citations.value = []
    grounded.value = false
    confidence.value = 0
    fallbackReason.value = null
    generationMode.value = null
    modelName.value = null
    latencyMs.value = null
    error.value = ''
    hasAsked.value = false
  }

  function resetQuestion() {
    question.value = ''
    clear()
  }

  async function ask(questionText: string, filters: RagAnswerFilters = {}) {
    const trimmedQuestion = questionText.trim()
    if (!trimmedQuestion) {
      error.value = 'Vui lòng nhập câu hỏi'
      hasAsked.value = false
      return
    }

    loading.value = true
    error.value = ''
    hasAsked.value = true
    try {
      const response = await service.answer(trimmedQuestion, filters)
      answer.value = response.answer
      citations.value = response.citations
      grounded.value = response.grounded
      confidence.value = response.confidence
      fallbackReason.value = response.fallback_reason ?? null
      generationMode.value = response.generation_mode ?? 'extractive'
      modelName.value = response.model_name ?? null
      latencyMs.value = response.latency_ms ?? null
    } catch {
      error.value = 'Không trả lời được câu hỏi'
      answer.value = ''
      citations.value = []
      grounded.value = false
      confidence.value = 0
      fallbackReason.value = null
      generationMode.value = null
      modelName.value = null
      latencyMs.value = null
    } finally {
      loading.value = false
    }
  }

  return {
    question,
    answer,
    citations,
    grounded,
    confidence,
    fallbackReason,
    generationMode,
    modelName,
    latencyMs,
    loading,
    error,
    hasAsked,
    ask,
    clear,
    resetQuestion
  }
}
