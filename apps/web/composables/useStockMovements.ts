import type { StockMovementInput, StockMovementItem, StockMovementListFilters } from '~/types/stock-movement'
import type { StockBalanceItem } from '~/types/stock-movement'
import { createStockMovementService } from '~/services/stock-movement.service'

export function useStockMovements() {
  const movements = ref<StockMovementItem[]>([])
  const movementsTotal = ref(0)
  const movementsLimit = ref(50)
  const movementsOffset = ref(0)
  const lowStockItems = ref<StockBalanceItem[]>([])
  const lowStockTotal = ref(0)
  const currentBalance = ref<StockBalanceItem | null>(null)
  const loading = ref(false)
  const saving = ref(false)
  const deleting = ref('')
  const error = ref('')
  const service = createStockMovementService()

  async function fetchMovements(filters: StockMovementListFilters = {}) {
    loading.value = true
    error.value = ''
    try {
      const result = await service.list(filters)
      movements.value = result.items
      movementsTotal.value = result.total
      movementsLimit.value = result.limit
      movementsOffset.value = result.offset
    } catch {
      error.value = 'Không tải được danh sách phiếu kho'
      movements.value = []
      movementsTotal.value = 0
    } finally {
      loading.value = false
    }
  }

  async function fetchLowStock(limit = 10) {
    try {
      const result = await service.listLowStock(limit)
      lowStockItems.value = result.items
      lowStockTotal.value = result.total
      return result
    } catch {
      lowStockItems.value = []
      lowStockTotal.value = 0
      return { items: [], total: 0 }
    }
  }

  async function fetchBalance(catalogItemId: string) {
    try {
      currentBalance.value = await service.getBalance(catalogItemId)
      return currentBalance.value
    } catch {
      currentBalance.value = null
      return null
    }
  }

  async function saveMovement(input: StockMovementInput): Promise<StockMovementItem | null> {
    saving.value = true
    error.value = ''
    try {
      return await service.create(input)
    } catch {
      error.value = 'Không lưu được phiếu kho'
      return null
    } finally {
      saving.value = false
    }
  }

  async function deleteMovement(id: string): Promise<boolean> {
    deleting.value = id
    error.value = ''
    try {
      await service.delete(id)
      movements.value = movements.value.filter((item) => item.id !== id)
      movementsTotal.value = Math.max(0, movementsTotal.value - 1)
      return true
    } catch {
      error.value = 'Không xóa được phiếu kho'
      return false
    } finally {
      deleting.value = ''
    }
  }

  return {
    movements,
    movementsTotal,
    movementsLimit,
    movementsOffset,
    lowStockItems,
    lowStockTotal,
    currentBalance,
    loading,
    saving,
    deleting,
    error,
    fetchMovements,
    fetchLowStock,
    fetchBalance,
    saveMovement,
    deleteMovement
  }
}
