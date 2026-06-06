import { createCatalogService } from '~/services/catalog.service'
import type { CatalogItem, CatalogOption } from '~/types/catalog'

const fallbackBusinessTypeOptions: CatalogOption[] = [
  { label: 'Công văn đến', value: 'incoming_dispatch' },
  { label: 'Công văn đi', value: 'outgoing_dispatch' },
  { label: 'Hợp đồng', value: 'contract' },
  { label: 'Quyết định', value: 'decision' }
]

const fallbackDocumentTypeOptions: CatalogOption[] = [
  { label: 'Không đủ dữ liệu', value: 'UNKNOWN' },
  { label: 'Nghị quyết', value: 'NQ' },
  { label: 'Quyết định', value: 'QĐ' },
  { label: 'Chỉ thị', value: 'CT' },
  { label: 'Quy chế', value: 'QC' },
  { label: 'Quy định', value: 'QYĐ' },
  { label: 'Thông cáo', value: 'TC' },
  { label: 'Thông báo', value: 'TB' },
  { label: 'Hướng dẫn', value: 'HD' },
  { label: 'Chương trình', value: 'CTr' },
  { label: 'Kế hoạch', value: 'KH' },
  { label: 'Phương án', value: 'PA' },
  { label: 'Đề án', value: 'ĐA' },
  { label: 'Dự án', value: 'DA' },
  { label: 'Báo cáo', value: 'BC' },
  { label: 'Biên bản', value: 'BB' },
  { label: 'Tờ trình', value: 'TTr' },
  { label: 'Hợp đồng', value: 'HĐ' },
  { label: 'Công văn', value: 'CV' },
  { label: 'Công điện', value: 'CĐ' },
  { label: 'Bản ghi nhớ', value: 'BGN' },
  { label: 'Bản thỏa thuận', value: 'BTT' },
  { label: 'Giấy ủy quyền', value: 'GUQ' },
  { label: 'Giấy mời', value: 'GM' },
  { label: 'Giấy giới thiệu', value: 'GGT' },
  { label: 'Giấy nghỉ phép', value: 'GNP' },
  { label: 'Phiếu gửi', value: 'PG' },
  { label: 'Phiếu chuyển', value: 'PC' },
  { label: 'Phiếu báo', value: 'PB' },
  { label: 'Thư công', value: 'TCg' }
]

export function useCatalogs() {
  const businessTypes = ref<CatalogOption[]>([...fallbackBusinessTypeOptions])
  const documentTypes = ref<CatalogOption[]>([...fallbackDocumentTypeOptions])
  const loading = ref(false)
  const error = ref('')
  const service = createCatalogService()

  const businessTypeOptions = computed(() => [
    { label: 'Chưa phân loại', value: '' },
    ...businessTypes.value
  ])
  const businessTypeFilterOptions = computed(() => [
    { label: 'Tất cả nghiệp vụ', value: '' },
    ...businessTypes.value
  ])
  const documentTypeOptions = computed(() => documentTypes.value)
  const documentTypeFilterOptions = computed(() => [
    { label: 'Tất cả loại', value: '' },
    ...documentTypes.value
  ])

  async function fetchCatalogOptions() {
    loading.value = true
    error.value = ''
    try {
      const [businessTypeItems, documentTypeItems] = await Promise.all([
        service.listBusinessTypes(),
        service.listDocumentTypes()
      ])
      businessTypes.value = toOptions(businessTypeItems, fallbackBusinessTypeOptions)
      documentTypes.value = toOptions(documentTypeItems, fallbackDocumentTypeOptions)
    } catch {
      error.value = 'Không tải được danh mục, đang dùng option mặc định'
      businessTypes.value = [...fallbackBusinessTypeOptions]
      documentTypes.value = [...fallbackDocumentTypeOptions]
    } finally {
      loading.value = false
    }
  }

  function formatBusinessType(value?: string | null): string {
    return businessTypes.value.find((option) => option.value === value)?.label || value || '-'
  }

  function formatDocumentType(value?: string | null): string {
    const option = documentTypes.value.find((item) => item.value === value)
    return option ? `${option.label} (${option.value})` : value || '-'
  }

  function hasDocumentType(value?: string | null): boolean {
    return Boolean(value && documentTypes.value.some((option) => option.value === value))
  }

  return {
    businessTypeOptions,
    businessTypeFilterOptions,
    documentTypeOptions,
    documentTypeFilterOptions,
    loading,
    error,
    fetchCatalogOptions,
    formatBusinessType,
    formatDocumentType,
    hasDocumentType
  }
}

function toOptions(items: CatalogItem[], fallback: CatalogOption[]): CatalogOption[] {
  const options = items
    .filter((item) => item.is_active)
    .map((item) => ({ label: item.label, value: item.code }))
  return options.length ? options : [...fallback]
}
