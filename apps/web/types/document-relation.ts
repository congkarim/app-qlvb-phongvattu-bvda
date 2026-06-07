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
