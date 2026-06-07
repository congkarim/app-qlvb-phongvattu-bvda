import type {
  DocumentChunk,
  DocumentDetail,
  DocumentFile,
  DocumentItem,
  DocumentListFilters,
  DocumentListResponse,
  DocumentMetadataInput,
  DocumentMetadataUpdateInput,
  MultiFileUploadResponse,
  ReprocessDocumentResponse,
  ReviewQueueFilters,
  ReviewQueueResponse,
  SourceFileMutationResponse,
  UploadResponse
} from '~/types/document'
import type { OnboardingSuggestion } from '~/types/onboarding'
import { useAuthStore } from '~/stores/auth'
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
      return api<DocumentListResponse>(`/documents${query ? `?${query}` : ''}`)
    },
    get(id: string) {
      return api<DocumentDetail>(`/documents/${id}`)
    },
    getOnboardingSuggestions(id: string) {
      return api<OnboardingSuggestion>(`/documents/${id}/onboarding-suggestions`)
    },
    listReviewQueue(filters: ReviewQueueFilters = {}) {
      const params = new URLSearchParams()
      for (const [key, value] of Object.entries(filters)) {
        if (value !== undefined && value !== null && String(value).trim() !== '') {
          params.set(key, String(value))
        }
      }
      const query = params.toString()
      return api<ReviewQueueResponse>(`/documents/chunks/review-queue${query ? `?${query}` : ''}`)
    },
    async downloadSourceFile(id: string, file: DocumentFile) {
      const config = useRuntimeConfig()
      const authStore = useAuthStore()
      const response = await fetch(`${config.public.apiBase}/documents/${id}/files/${file.id}/download`, {
        headers: authStore.token ? { Authorization: `Bearer ${authStore.token}` } : {}
      })
      if (!response.ok) {
        throw new Error(`Cannot download source file: ${response.status}`)
      }
      return response.blob()
    },
    updateMetadata(id: string, metadata: DocumentMetadataUpdateInput) {
      return api<DocumentItem>(`/documents/${id}/metadata`, {
        method: 'PATCH',
        body: normalizeMetadataUpdate(metadata)
      })
    },
    upload(file: File, documentType = 'document', title = '', metadata: DocumentMetadataInput = {}) {
      const form = new FormData()
      form.append('file', file)
      if (title.trim()) form.append('title', title.trim())
      appendMetadata(form, metadata)
      return api<UploadResponse>(`/documents/upload?document_type=${documentType}`, {
        method: 'POST',
        body: form
      })
    },
    uploadMultiFile(files: File[], title: string, documentType = 'document', metadata: DocumentMetadataInput = {}) {
      const form = new FormData()
      form.append('title', title.trim())
      form.append('document_type', documentType)
      appendMetadata(form, metadata)
      for (const file of files) {
        form.append('files', file)
      }
      return api<MultiFileUploadResponse>('/documents/upload/multi-file', {
        method: 'POST',
        body: form
      })
    },
    uploadZip(zipFile: File, title: string, documentType = 'document', metadata: DocumentMetadataInput = {}) {
      const form = new FormData()
      form.append('title', title.trim())
      form.append('document_type', documentType)
      appendMetadata(form, metadata)
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
    },
    markChunkReviewed(id: string, chunkId: string) {
      return api<DocumentChunk>(`/documents/${id}/chunks/${chunkId}/reviewed`, {
        method: 'PATCH'
      })
    }
  }
}

function appendMetadata(form: FormData, metadata: DocumentMetadataInput) {
  if (metadata.document_number?.trim()) form.append('document_number', metadata.document_number.trim())
  if (metadata.issued_date?.trim()) form.append('issued_date', metadata.issued_date.trim())
  if (metadata.issuing_agency?.trim()) form.append('issuing_agency', metadata.issuing_agency.trim())
  if (metadata.business_type?.trim()) form.append('business_type', metadata.business_type.trim())
}

function normalizeMetadataUpdate(metadata: DocumentMetadataUpdateInput) {
  return {
    title: metadata.title.trim(),
    document_type: metadata.document_type || 'UNKNOWN',
    classification_confidence: metadata.classification_confidence ?? null,
    document_number: metadata.document_number?.trim() || null,
    document_symbol: metadata.document_symbol?.trim() || null,
    issued_date: metadata.issued_date?.trim() || null,
    issued_place: metadata.issued_place?.trim() || null,
    issuing_agency: metadata.issuing_agency?.trim() || null,
    excerpt: metadata.excerpt?.trim() || null,
    recipient: metadata.recipient?.trim() || null,
    signer_name: metadata.signer_name?.trim() || null,
    signer_title: metadata.signer_title?.trim() || null,
    seals_present: metadata.seals_present ?? null,
    attachment_present: metadata.attachment_present ?? null,
    page_count: metadata.page_count || null,
    business_type: metadata.business_type?.trim() || null
  }
}
