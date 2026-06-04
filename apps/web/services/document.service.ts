import type {
  DocumentDetail,
  DocumentItem,
  MultiFileUploadResponse,
  ReprocessDocumentResponse,
  UploadResponse
} from '~/types/document'
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
    upload(file: File, documentType = 'document', title = '') {
      const form = new FormData()
      form.append('file', file)
      if (title.trim()) form.append('title', title.trim())
      return api<UploadResponse>(`/documents/upload?document_type=${documentType}`, {
        method: 'POST',
        body: form
      })
    },
    uploadMultiFile(files: File[], title: string, documentType = 'document') {
      const form = new FormData()
      form.append('title', title.trim())
      form.append('document_type', documentType)
      for (const file of files) {
        form.append('files', file)
      }
      return api<MultiFileUploadResponse>('/documents/upload/multi-file', {
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
