import type { DocumentItem } from '~/types/document'
import type {
  DocumentRelationCreateInput,
  DocumentRelationsResponse
} from '~/types/document-relation'
import { createDocumentRelationService } from '~/services/document-relation.service'
import { createDocumentService } from '~/services/document.service'

function extractErrorMessage(error: unknown, fallback: string): string {
  const fetchError = error as { data?: { detail?: string }; statusCode?: number }
  if (typeof fetchError.data?.detail === 'string' && fetchError.data.detail.trim()) {
    return fetchError.data.detail
  }
  if (fetchError.statusCode === 409) return 'Liên kết này đã tồn tại'
  if (fetchError.statusCode === 403) return 'Bạn không có quyền thực hiện thao tác này'
  return fallback
}

export function useDocumentRelations() {
  const service = createDocumentRelationService()
  const documentService = createDocumentService()
  const relations = ref<DocumentRelationsResponse | null>(null)
  const targetSearchResults = ref<DocumentItem[]>([])
  const targetSearchLoading = ref(false)
  const loading = ref(false)
  const saving = ref(false)
  const deleting = ref('')
  const error = ref('')

  async function fetchRelations(documentId: string) {
    if (!documentId) return null
    loading.value = true
    error.value = ''
    try {
      relations.value = await service.list(documentId)
      return relations.value
    } catch {
      error.value = 'Không tải được danh sách liên kết văn bản'
      relations.value = null
      return null
    } finally {
      loading.value = false
    }
  }

  async function searchTargetDocuments(query: string, excludeDocumentId: string) {
    const normalized = query.trim()
    if (!normalized) {
      targetSearchResults.value = []
      return []
    }
    targetSearchLoading.value = true
    try {
      const result = await documentService.list({ q: normalized, limit: 10, offset: 0 })
      targetSearchResults.value = result.items.filter((item) => item.id !== excludeDocumentId)
      return targetSearchResults.value
    } catch {
      targetSearchResults.value = []
      return []
    } finally {
      targetSearchLoading.value = false
    }
  }

  async function createRelation(documentId: string, input: DocumentRelationCreateInput): Promise<boolean> {
    saving.value = true
    error.value = ''
    try {
      await service.create(documentId, input)
      await fetchRelations(documentId)
      return true
    } catch (err) {
      error.value = extractErrorMessage(err, 'Không tạo được liên kết văn bản')
      return false
    } finally {
      saving.value = false
    }
  }

  async function deleteRelation(documentId: string, relationId: string): Promise<boolean> {
    deleting.value = relationId
    error.value = ''
    try {
      await service.delete(relationId)
      await fetchRelations(documentId)
      return true
    } catch (err) {
      error.value = extractErrorMessage(err, 'Không xóa được liên kết văn bản')
      return false
    } finally {
      deleting.value = ''
    }
  }

  function clearRelations() {
    relations.value = null
    targetSearchResults.value = []
    error.value = ''
  }

  return {
    relations,
    targetSearchResults,
    targetSearchLoading,
    loading,
    saving,
    deleting,
    error,
    fetchRelations,
    searchTargetDocuments,
    createRelation,
    deleteRelation,
    clearRelations
  }
}
