import type { CatalogItem } from '~/types/catalog'
import { useApiClient } from './api'

export function createCatalogService() {
  const api = useApiClient()

  return {
    listBusinessTypes() {
      return api<CatalogItem[]>('/catalogs/business-types')
    },
    listDocumentTypes() {
      return api<CatalogItem[]>('/catalogs/document-types')
    }
  }
}
