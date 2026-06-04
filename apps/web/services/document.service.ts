import type {
  DocumentDetail,
  DocumentItem,
  DocumentListFilters,
  MultiFileUploadResponse,
  ReprocessDocumentResponse,
  SourceFileMutationResponse,
  UploadResponse
} from '~/types/document'
import { useApiClient } from './api'

export function createDocumentService() {
  const api = useApiClient()

  return {
    list(filters: DocumentListFilters = {}) {
      const params = new URLSearchParams()
      for (const [key, value] of Object.entries(filters)) {
        if (value !== undefined && value !== null && String(value).trim() !== '') {
          params.set(key, String(value))
        }
      }
      const query = params.toString()
      return api<DocumentItem[]>(`/documents${query ? `?${query}` : ''}`)
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
    uploadZip(zipFile: File, title: string, documentType = 'document') {
      const form = new FormData()
      form.append('title', title.trim())
      form.append('document_type', documentType)
      form.append('zip_file', zipFile)
      return api<MultiFileUploadResponse>('/documents/upload/zip', {
        method: 'POST',
        body: form
      })
    },
    addSourceFiles(id: string, files: File[]) {
      const form = new FormData()
      for (const file of files) {
        form.append('files', file)
      }
      return api<SourceFileMutationResponse>(`/documents/${id}/files`, {
        method: 'POST',
        body: form
      })
    },
    reorderSourceFiles(id: string, fileIds: string[]) {
      return api<SourceFileMutationResponse>(`/documents/${id}/files/order`, {
        method: 'PATCH',
        body: {
          file_ids: fileIds
        }
      })
    },
    deleteSourceFile(id: string, fileId: string) {
      return api<SourceFileMutationResponse>(`/documents/${id}/files/${fileId}`, {
        method: 'DELETE'
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
