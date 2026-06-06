import type { CatalogItem } from '~/types/catalog'

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
