import type { DispatchInput, DispatchItem, DispatchListFilters } from '~/types/dispatch'
import { createDispatchService } from '~/services/dispatch.service'

export function useDispatches() {
  const dispatches = ref<DispatchItem[]>([])
  const dispatch = ref<DispatchItem | null>(null)
  const dispatchesTotal = ref(0)
  const dispatchesLimit = ref(20)
  const dispatchesOffset = ref(0)
  const dispatchByDocument = ref<DispatchItem | null>(null)
  const dispatchByDocumentLoading = ref(false)
  const loading = ref(false)
  const saving = ref(false)
  const deleting = ref('')
  const error = ref('')
  const service = createDispatchService()

  async function fetchDispatches(filters: DispatchListFilters = {}, options: { silent?: boolean } = {}) {
    if (!options.silent) loading.value = true
    error.value = ''
    try {
      const result = await service.list(filters)
      dispatches.value = result.items
      dispatchesTotal.value = result.total
      dispatchesLimit.value = result.limit
      dispatchesOffset.value = result.offset
    } catch {
      error.value = 'Không tải được danh sách công văn'
      dispatches.value = []
      dispatchesTotal.value = 0
      dispatchesLimit.value = filters.limit || 20
      dispatchesOffset.value = filters.offset || 0
    } finally {
      if (!options.silent) loading.value = false
    }
  }

  async function fetchDispatch(id: string) {
    loading.value = true
    error.value = ''
    try {
      dispatch.value = await service.get(id)
      return dispatch.value
    } catch {
      error.value = 'Không tải được metadata công văn'
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchDispatchByDocumentId(documentId: string) {
    dispatchByDocumentLoading.value = true
    try {
      dispatchByDocument.value = await service.getByDocumentId(documentId)
      return dispatchByDocument.value
    } catch {
      dispatchByDocument.value = null
      return null
    } finally {
      dispatchByDocumentLoading.value = false
    }
  }

  async function saveDispatch(input: DispatchInput, id?: string): Promise<DispatchItem | null> {
    saving.value = true
    error.value = ''
    try {
      const result = id
        ? await service.update(id, {
            dispatch_type: input.dispatch_type,
            document_number: input.document_number,
            document_symbol: input.document_symbol,
            issued_date: input.issued_date,
            issuing_agency: input.issuing_agency,
            recipient: input.recipient,
            excerpt: input.excerpt,
            status: input.status,
            notes: input.notes
          })
        : await service.create(input)
      dispatch.value = result
      return result
    } catch {
      error.value = id ? 'Không cập nhật được công văn' : 'Không tạo được công văn'
      return null
    } finally {
      saving.value = false
    }
  }

  async function deleteDispatch(id: string): Promise<boolean> {
    deleting.value = id
    error.value = ''
    try {
      await service.delete(id)
      dispatches.value = dispatches.value.filter((item) => item.id !== id)
      dispatchesTotal.value = Math.max(0, dispatchesTotal.value - 1)
      return true
    } catch {
      error.value = 'Không xóa được công văn'
      return false
    } finally {
      deleting.value = ''
    }
  }

  return {
    dispatches,
    dispatch,
    dispatchesTotal,
    dispatchesLimit,
    dispatchesOffset,
    dispatchByDocument,
    dispatchByDocumentLoading,
    loading,
    saving,
    deleting,
    error,
    fetchDispatches,
    fetchDispatch,
    fetchDispatchByDocumentId,
    saveDispatch,
    deleteDispatch
  }
}
