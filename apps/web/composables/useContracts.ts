import type { ContractInput, ContractItem, ContractListFilters } from '~/types/contract'
import { createContractService } from '~/services/contract.service'

export function useContracts() {
  const contracts = ref<ContractItem[]>([])
  const contract = ref<ContractItem | null>(null)
  const contractsTotal = ref(0)
  const contractsLimit = ref(20)
  const contractsOffset = ref(0)
  const contractByDocument = ref<ContractItem | null>(null)
  const contractByDocumentLoading = ref(false)
  const loading = ref(false)
  const saving = ref(false)
  const deleting = ref('')
  const error = ref('')
  const service = createContractService()

  async function fetchContracts(filters: ContractListFilters = {}, options: { silent?: boolean } = {}) {
    if (!options.silent) loading.value = true
    error.value = ''
    try {
      const result = await service.list(filters)
      contracts.value = result.items
      contractsTotal.value = result.total
      contractsLimit.value = result.limit
      contractsOffset.value = result.offset
    } catch {
      error.value = 'Không tải được danh sách hợp đồng'
      contracts.value = []
      contractsTotal.value = 0
      contractsLimit.value = filters.limit || 20
      contractsOffset.value = filters.offset || 0
    } finally {
      if (!options.silent) loading.value = false
    }
  }

  async function fetchContract(id: string) {
    loading.value = true
    error.value = ''
    try {
      contract.value = await service.get(id)
      return contract.value
    } catch {
      error.value = 'Không tải được metadata hợp đồng'
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchContractByDocumentId(documentId: string) {
    contractByDocumentLoading.value = true
    try {
      contractByDocument.value = await service.getByDocumentId(documentId)
      return contractByDocument.value
    } catch {
      contractByDocument.value = null
      return null
    } finally {
      contractByDocumentLoading.value = false
    }
  }

  async function saveContract(input: ContractInput, id?: string): Promise<ContractItem | null> {
    saving.value = true
    error.value = ''
    try {
      const result = id
        ? await service.update(id, {
            contract_number: input.contract_number,
            contract_title: input.contract_title,
            supplier_name: input.supplier_name,
            sign_date: input.sign_date,
            effective_from: input.effective_from,
            effective_to: input.effective_to,
            contract_value: input.contract_value,
            currency: input.currency,
            status: input.status,
            notes: input.notes
          })
        : await service.create(input)
      contract.value = result
      return result
    } catch {
      error.value = id ? 'Không cập nhật được hợp đồng' : 'Không tạo được hợp đồng'
      return null
    } finally {
      saving.value = false
    }
  }

  async function deleteContract(id: string): Promise<boolean> {
    deleting.value = id
    error.value = ''
    try {
      await service.delete(id)
      contracts.value = contracts.value.filter((item) => item.id !== id)
      contractsTotal.value = Math.max(0, contractsTotal.value - 1)
      return true
    } catch {
      error.value = 'Không xóa được hợp đồng'
      return false
    } finally {
      deleting.value = ''
    }
  }

  return {
    contracts,
    contract,
    contractsTotal,
    contractsLimit,
    contractsOffset,
    contractByDocument,
    contractByDocumentLoading,
    loading,
    saving,
    deleting,
    error,
    fetchContracts,
    fetchContract,
    fetchContractByDocumentId,
    saveContract,
    deleteContract
  }
}
