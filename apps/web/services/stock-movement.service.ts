import type {
  LowStockListResponse,
  StockBalanceItem,
  StockMovementInput,
  StockMovementItem,
  StockMovementListFilters,
  StockMovementListResponse
} from '~/types/stock-movement'
import { useApiClient } from './api'

export function createStockMovementService() {
  const api = useApiClient()

  return {
    list(filters: StockMovementListFilters = {}) {
      const params = new URLSearchParams()
      for (const [key, value] of Object.entries(filters)) {
        if (value !== undefined && value !== null && String(value).trim() !== '') {
          params.set(key, String(value))
        }
      }
      const query = params.toString()
      return api<StockMovementListResponse>(`/stock-movements${query ? `?${query}` : ''}`)
    },
    get(id: string) {
      return api<StockMovementItem>(`/stock-movements/${id}`)
    },
    create(input: StockMovementInput) {
      return api<StockMovementItem>('/stock-movements', {
        method: 'POST',
        body: normalizeMovementInput(input)
      })
    },
    delete(id: string) {
      return api<StockMovementItem>(`/stock-movements/${id}`, { method: 'DELETE' })
    },
    getBalance(catalogItemId: string) {
      return api<StockBalanceItem>(`/stock-balances/${catalogItemId}`)
    },
    listLowStock(limit = 10) {
      return api<LowStockListResponse>(`/stock-balances/low-stock?limit=${limit}`)
    }
  }
}

function normalizeMovementInput(input: StockMovementInput) {
  return {
    catalog_item_id: input.catalog_item_id,
    movement_type: input.movement_type,
    quantity: input.quantity,
    movement_date: input.movement_date,
    notes: input.notes?.trim() || null,
    reference_number: input.reference_number?.trim() || null,
    procurement_id: input.procurement_id?.trim() || null
  }
}
