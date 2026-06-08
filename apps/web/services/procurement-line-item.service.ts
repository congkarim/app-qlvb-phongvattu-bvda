import type {
  ProcurementLineItem,
  ProcurementLineItemInput,
  ProcurementLineItemListResponse
} from '~/types/procurement-line-item'
import { useApiClient } from './api'

export function createProcurementLineItemService() {
  const api = useApiClient()

  return {
    list(procurementId: string) {
      return api<ProcurementLineItemListResponse>(`/procurements/${procurementId}/line-items`)
    },
    create(procurementId: string, input: ProcurementLineItemInput) {
      return api<ProcurementLineItem>(`/procurements/${procurementId}/line-items`, {
        method: 'POST',
        body: normalizeLineItemInput(input)
      })
    },
    update(lineItemId: string, input: Partial<ProcurementLineItemInput>) {
      return api<ProcurementLineItem>(`/procurement-line-items/${lineItemId}`, {
        method: 'PATCH',
        body: normalizeLineItemInput(input)
      })
    },
    delete(lineItemId: string) {
      return api<ProcurementLineItem>(`/procurement-line-items/${lineItemId}`, {
        method: 'DELETE'
      })
    }
  }
}

function normalizeLineItemInput(input: Partial<ProcurementLineItemInput>) {
  const payload: Record<string, unknown> = {}
  if ('line_number' in input && input.line_number !== undefined) payload.line_number = input.line_number
  if ('item_name' in input) payload.item_name = input.item_name?.trim() || ''
  if ('item_code' in input) payload.item_code = input.item_code?.trim() || null
  if ('unit' in input) payload.unit = input.unit?.trim() || null
  if ('quantity' in input && input.quantity !== undefined && input.quantity !== '') payload.quantity = String(input.quantity)
  if ('unit_price' in input) payload.unit_price = normalizeOptionalNumber(input.unit_price)
  if ('amount' in input) payload.amount = normalizeOptionalNumber(input.amount)
  if ('catalog_item_id' in input) payload.catalog_item_id = input.catalog_item_id || null
  if ('notes' in input) payload.notes = input.notes?.trim() || null
  return payload
}

function normalizeOptionalNumber(value: string | number | null | undefined) {
  if (value === undefined || value === null || value === '') return null
  const normalized = String(value).trim().replace(/,/g, '')
  return normalized || null
}
