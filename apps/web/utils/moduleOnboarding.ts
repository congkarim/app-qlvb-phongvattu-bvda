import type { TargetModule } from '~/types/onboarding'

const MODULE_ROUTES: Record<TargetModule, string> = {
  contract: '/contracts',
  dispatch: '/dispatches',
  decision: '/decisions',
  procurement: '/procurements'
}

const MODULE_LABELS: Record<TargetModule, string> = {
  contract: 'Hợp đồng',
  dispatch: 'Công văn',
  decision: 'Quyết định',
  procurement: 'Mua sắm'
}

export function moduleLabel(targetModule: TargetModule) {
  return MODULE_LABELS[targetModule]
}

export function buildModuleCreateLink(
  targetModule: TargetModule,
  documentId: string,
  suggestedFields: Record<string, unknown> = {}
) {
  const params = new URLSearchParams()
  params.set('document_id', documentId)
  params.set('create', '1')
  for (const [key, value] of Object.entries(suggestedFields)) {
    if (value !== undefined && value !== null && String(value).trim() !== '') {
      params.set(key, String(value))
    }
  }
  return `${MODULE_ROUTES[targetModule]}?${params.toString()}`
}

export function applyRoutePrefill<T extends Record<string, unknown>>(
  query: Record<string, string | string[] | undefined>,
  form: T,
  keys: (keyof T)[]
) {
  if (query.create !== '1') return
  for (const key of keys) {
    const value = query[key as string]
    if (typeof value === 'string' && value.trim()) {
      form[key] = value as T[keyof T]
    }
  }
}
