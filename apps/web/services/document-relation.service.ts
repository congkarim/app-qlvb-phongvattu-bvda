import type {
  DocumentRelationCreateInput,
  DocumentRelationDeleteResponse,
  DocumentRelationsResponse,
  RelationSuggestionsResponse
} from '~/types/document-relation'
import { useApiClient } from './api'

export function createDocumentRelationService() {
  const api = useApiClient()

  return {
    list(documentId: string) {
      return api<DocumentRelationsResponse>(`/documents/${documentId}/relations`)
    },
    getRelationSuggestions(documentId: string) {
      return api<RelationSuggestionsResponse>(`/documents/${documentId}/relation-suggestions`)
    },
    create(documentId: string, input: DocumentRelationCreateInput) {
      return api<DocumentRelationsResponse['outgoing'][number]>(`/documents/${documentId}/relations`, {
        method: 'POST',
        body: {
          target_document_id: input.target_document_id.trim(),
          relation_type: input.relation_type,
          notes: input.notes?.trim() || null
        }
      })
    },
    delete(relationId: string) {
      return api<DocumentRelationDeleteResponse>(`/document-relations/${relationId}`, {
        method: 'DELETE'
      })
    }
  }
}
