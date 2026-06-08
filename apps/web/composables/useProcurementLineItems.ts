import type { ProcurementLineItem, ProcurementLineItemInput } from '~/types/procurement-line-item'
import { createProcurementLineItemService } from '~/services/procurement-line-item.service'

export function useProcurementLineItems() {
  const lineItems = ref<ProcurementLineItem[]>([])
  const linesTotalAmount = ref<string | number | null>(null)
  const loading = ref(false)
  const saving = ref(false)
  const deleting = ref('')
  const error = ref('')
  const service = createProcurementLineItemService()

  async function fetchLineItems(procurementId: string) {
    loading.value = true
    error.value = ''
    try {
      const result = await service.list(procurementId)
      lineItems.value = result.items
      linesTotalAmount.value = result.lines_total_amount ?? null
    } catch {
      error.value = 'Không tải được danh sách dòng hàng'
      lineItems.value = []
      linesTotalAmount.value = null
    } finally {
      loading.value = false
    }
  }

  async function saveLineItem(
    procurementId: string,
    input: ProcurementLineItemInput,
    lineItemId?: string
  ): Promise<ProcurementLineItem | null> {
    saving.value = true
    error.value = ''
    try {
      const result = lineItemId
        ? await service.update(lineItemId, input)
        : await service.create(procurementId, input)
      await fetchLineItems(procurementId)
      return result
    } catch {
      error.value = lineItemId ? 'Không cập nhật được dòng hàng' : 'Không thêm được dòng hàng'
      return null
    } finally {
      saving.value = false
    }
  }

  async function deleteLineItem(procurementId: string, lineItemId: string): Promise<boolean> {
    deleting.value = lineItemId
    error.value = ''
    try {
      await service.delete(lineItemId)
      await fetchLineItems(procurementId)
      return true
    } catch {
      error.value = 'Không xóa được dòng hàng'
      return false
    } finally {
      deleting.value = ''
    }
  }

  function resetLineItems() {
    lineItems.value = []
    linesTotalAmount.value = null
    error.value = ''
  }

  return {
    lineItems,
    linesTotalAmount,
    loading,
    saving,
    deleting,
    error,
    fetchLineItems,
    saveLineItem,
    deleteLineItem,
    resetLineItems
  }
}
