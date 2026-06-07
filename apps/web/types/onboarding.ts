export type TargetModule = 'contract' | 'dispatch' | 'decision' | 'procurement'

export type OnboardingBlockReason =
  | 'not_searchable'
  | 'module_exists'
  | 'manual_metadata'
  | 'unmapped_document_type'
  | 'low_confidence'

export interface OnboardingSuggestion {
  document_id: string
  eligible: boolean
  block_reason: OnboardingBlockReason | null
  needs_metadata_review: boolean
  suggested_business_type: string | null
  business_type_confidence: number | null
  target_module: TargetModule | null
  module_confidence: number | null
  module_kind: string | null
  reasons: string[]
  suggested_module_fields: Record<string, string | number | boolean | null>
}
