export type RelationType = 'references' | 'appendix_of' | 'implements' | 'related'

export interface RelatedDocumentSummary {
  id: string
  title: string
  document_number?: string | null
  document_type: string
  status: string
}

export interface DocumentRelationOutgoing {
  id: string
  relation_type: RelationType
  notes?: string | null
  target_document: RelatedDocumentSummary
  created_at: string
}

export interface DocumentRelationIncoming {
  id: string
  relation_type: RelationType
  notes?: string | null
  source_document: RelatedDocumentSummary
  created_at: string
}

export interface DocumentRelationsResponse {
  document_id: string
  outgoing: DocumentRelationOutgoing[]
  incoming: DocumentRelationIncoming[]
}

export interface DocumentRelationCreateInput {
  target_document_id: string
  relation_type: RelationType
  notes?: string
}

export interface DocumentRelationDeleteResponse {
  id: string
  source_document_id: string
  target_document_id: string
  relation_type: RelationType
  notes?: string | null
  created_at: string
}

export type ConfidenceTier = 'high' | 'review'

export interface RelationSuggestion {
  target_document_id: string
  relation_type: RelationType
  confidence: number
  confidence_tier: ConfidenceTier
  matched_reference: string
  source_chunk_id: string
  source_chunk_quote: string
  target_document_preview: RelatedDocumentSummary
  reasons: string[]
}

export interface RelationSuggestionsResponse {
  document_id: string
  suggestions: RelationSuggestion[]
  candidate_count: number
}
