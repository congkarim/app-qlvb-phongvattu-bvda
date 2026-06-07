import type { ConfidenceTier, RelationType } from '~/types/document-relation'

export const RELATION_TYPE_OPTIONS: Array<{ label: string; value: RelationType }> = [
  { label: 'Tham chiếu / căn cứ', value: 'references' },
  { label: 'Phụ lục của', value: 'appendix_of' },
  { label: 'Triển khai / thực hiện', value: 'implements' },
  { label: 'Liên quan', value: 'related' }
]

const outgoingLabels: Record<RelationType, string> = {
  references: 'Tham chiếu',
  appendix_of: 'Phụ lục của',
  implements: 'Triển khai',
  related: 'Liên quan'
}

const incomingLabels: Record<RelationType, string> = {
  references: 'Được tham chiếu bởi',
  appendix_of: 'Có phụ lục',
  implements: 'Được triển khai bởi',
  related: 'Liên quan tới'
}

export function formatOutgoingRelationType(type: RelationType): string {
  return outgoingLabels[type] || type
}

export function formatIncomingRelationType(type: RelationType): string {
  return incomingLabels[type] || type
}

export function documentRelationLink(documentId: string): string {
  return `/documents/${documentId}`
}

export function formatRelatedDocumentLabel(
  document: { title: string; document_number?: string | null; document_type: string }
): string {
  const number = document.document_number?.trim()
  if (number) return `${number} · ${document.title}`
  return `${document.document_type} · ${document.title}`
}

export function formatConfidenceTierLabel(tier: ConfidenceTier): string {
  return tier === 'high' ? 'Độ tin cậy cao' : 'Cần xem lại'
}

export function relationSuggestionCardClass(tier: ConfidenceTier): string {
  return tier === 'high'
    ? 'border-sky-300 bg-sky-50'
    : 'border-amber-300 bg-amber-50'
}
