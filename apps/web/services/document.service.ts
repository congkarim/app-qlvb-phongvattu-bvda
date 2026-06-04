import type { DocumentDetail, DocumentItem, ReprocessDocumentResponse, UploadResponse } from '~/types/document'
import { useApiClient } from './api'

export function createDocumentService() {
  const api = useApiClient()

  return {
    list() {
      return api<DocumentItem[]>('/documents')
    },
    get(id: string) {
      return api<DocumentDetail>(`/documents/${id}`)
    },
    upload(file: File, documentType = 'document') {
      const form = new FormData()
      form.append('file', file)
      return api<UploadResponse>(`/documents/upload?document_type=${documentType}`, {
        method: 'POST',
        body: form
      })
    },
    reprocess(id: string, reason: string) {
      return api<ReprocessDocumentResponse>(`/documents/${id}/reprocess`, {
        method: 'POST',
        body: {
          reason: reason.trim() || null
        }
      })
    }
  }
}
