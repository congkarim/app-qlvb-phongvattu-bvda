import type { DecisionInput, DecisionItem, DecisionListFilters } from '~/types/decision'
import { createDecisionService } from '~/services/decision.service'

export function useDecisions() {
  const decisions = ref<DecisionItem[]>([])
  const decision = ref<DecisionItem | null>(null)
  const decisionsTotal = ref(0)
  const decisionsLimit = ref(20)
  const decisionsOffset = ref(0)
  const decisionByDocument = ref<DecisionItem | null>(null)
  const decisionByDocumentLoading = ref(false)
  const loading = ref(false)
  const saving = ref(false)
  const deleting = ref('')
  const error = ref('')
  const service = createDecisionService()

  async function fetchDecisions(filters: DecisionListFilters = {}, options: { silent?: boolean } = {}) {
    if (!options.silent) loading.value = true
    error.value = ''
    try {
      const result = await service.list(filters)
      decisions.value = result.items
      decisionsTotal.value = result.total
      decisionsLimit.value = result.limit
      decisionsOffset.value = result.offset
    } catch {
      error.value = 'Không tải được danh sách quyết định/thông báo'
      decisions.value = []
      decisionsTotal.value = 0
      decisionsLimit.value = filters.limit || 20
      decisionsOffset.value = filters.offset || 0
    } finally {
      if (!options.silent) loading.value = false
    }
  }

  async function fetchDecision(id: string) {
    loading.value = true
    error.value = ''
    try {
      decision.value = await service.get(id)
      return decision.value
    } catch {
      error.value = 'Không tải được metadata quyết định/thông báo'
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchDecisionByDocumentId(documentId: string) {
    decisionByDocumentLoading.value = true
    try {
      decisionByDocument.value = await service.getByDocumentId(documentId)
      return decisionByDocument.value
    } catch {
      decisionByDocument.value = null
      return null
    } finally {
      decisionByDocumentLoading.value = false
    }
  }

  async function saveDecision(input: DecisionInput, id?: string): Promise<DecisionItem | null> {
    saving.value = true
    error.value = ''
    try {
      const result = id
        ? await service.update(id, {
            decision_kind: input.decision_kind,
            document_number: input.document_number,
            document_symbol: input.document_symbol,
            issued_date: input.issued_date,
            issuing_agency: input.issuing_agency,
            excerpt: input.excerpt,
            effective_from: input.effective_from,
            effective_to: input.effective_to,
            status: input.status,
            notes: input.notes
          })
        : await service.create(input)
      decision.value = result
      return result
    } catch {
      error.value = id ? 'Không cập nhật được quyết định/thông báo' : 'Không tạo được quyết định/thông báo'
      return null
    } finally {
      saving.value = false
    }
  }

  async function deleteDecision(id: string): Promise<boolean> {
    deleting.value = id
    error.value = ''
    try {
      await service.delete(id)
      decisions.value = decisions.value.filter((item) => item.id !== id)
      decisionsTotal.value = Math.max(0, decisionsTotal.value - 1)
      return true
    } catch {
      error.value = 'Không xóa được quyết định/thông báo'
      return false
    } finally {
      deleting.value = ''
    }
  }

  return {
    decisions,
    decision,
    decisionsTotal,
    decisionsLimit,
    decisionsOffset,
    decisionByDocument,
    decisionByDocumentLoading,
    loading,
    saving,
    deleting,
    error,
    fetchDecisions,
    fetchDecision,
    fetchDecisionByDocumentId,
    saveDecision,
    deleteDecision
  }
}
