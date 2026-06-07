import type { ProcurementInput, ProcurementItem, ProcurementListFilters } from '~/types/procurement'
import { createProcurementService } from '~/services/procurement.service'

export function useProcurements() {
  const procurements = ref<ProcurementItem[]>([])
  const procurement = ref<ProcurementItem | null>(null)
  const procurementsTotal = ref(0)
  const procurementsLimit = ref(20)
  const procurementsOffset = ref(0)
  const procurementByDocument = ref<ProcurementItem | null>(null)
  const procurementByDocumentLoading = ref(false)
  const loading = ref(false)
  const saving = ref(false)
  const deleting = ref('')
  const error = ref('')
  const service = createProcurementService()

  async function fetchProcurements(filters: ProcurementListFilters = {}, options: { silent?: boolean } = {}) {
    if (!options.silent) loading.value = true
    error.value = ''
    try {
      const result = await service.list(filters)
      procurements.value = result.items
      procurementsTotal.value = result.total
      procurementsLimit.value = result.limit
      procurementsOffset.value = result.offset
    } catch {
      error.value = 'Không tải được danh sách đề xuất/kế hoạch mua sắm'
      procurements.value = []
      procurementsTotal.value = 0
      procurementsLimit.value = filters.limit || 20
      procurementsOffset.value = filters.offset || 0
    } finally {
      if (!options.silent) loading.value = false
    }
  }

  async function fetchProcurement(id: string) {
    loading.value = true
    error.value = ''
    try {
      procurement.value = await service.get(id)
      return procurement.value
    } catch {
      error.value = 'Không tải được metadata mua sắm'
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchProcurementByDocumentId(documentId: string) {
    procurementByDocumentLoading.value = true
    try {
      procurementByDocument.value = await service.getByDocumentId(documentId)
      return procurementByDocument.value
    } catch {
      procurementByDocument.value = null
      return null
    } finally {
      procurementByDocumentLoading.value = false
    }
  }

  async function saveProcurement(input: ProcurementInput, id?: string): Promise<ProcurementItem | null> {
    saving.value = true
    error.value = ''
    try {
      const result = id
        ? await service.update(id, {
            procurement_kind: input.procurement_kind,
            reference_number: input.reference_number,
            title_summary: input.title_summary,
            requesting_unit: input.requesting_unit,
            estimated_value: input.estimated_value,
            currency: input.currency,
            requested_date: input.requested_date,
            status: input.status,
            notes: input.notes
          })
        : await service.create(input)
      procurement.value = result
      return result
    } catch {
      error.value = id ? 'Không cập nhật được metadata mua sắm' : 'Không tạo được metadata mua sắm'
      return null
    } finally {
      saving.value = false
    }
  }

  async function deleteProcurement(id: string): Promise<boolean> {
    deleting.value = id
    error.value = ''
    try {
      await service.delete(id)
      procurements.value = procurements.value.filter((item) => item.id !== id)
      procurementsTotal.value = Math.max(0, procurementsTotal.value - 1)
      return true
    } catch {
      error.value = 'Không xóa được metadata mua sắm'
      return false
    } finally {
      deleting.value = ''
    }
  }

  return {
    procurements,
    procurement,
    procurementsTotal,
    procurementsLimit,
    procurementsOffset,
    procurementByDocument,
    procurementByDocumentLoading,
    loading,
    saving,
    deleting,
    error,
    fetchProcurements,
    fetchProcurement,
    fetchProcurementByDocumentId,
    saveProcurement,
    deleteProcurement
  }
}
