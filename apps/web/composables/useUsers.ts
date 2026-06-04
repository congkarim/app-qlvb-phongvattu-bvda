import type { UserCreateInput, UserItem, UserListFilters, UserUpdateInput } from '~/types/user'
import { createUserService } from '~/services/user.service'

export function useUsers() {
  const users = ref<UserItem[]>([])
  const loading = ref(false)
  const mutationLoading = ref(false)
  const error = ref('')
  const service = createUserService()

  async function fetchUsers(filters: UserListFilters = {}) {
    loading.value = true
    error.value = ''
    try {
      users.value = await service.list(filters)
    } catch {
      error.value = 'Không tải được danh sách người dùng'
    } finally {
      loading.value = false
    }
  }

  async function createUser(input: UserCreateInput): Promise<UserItem | null> {
    mutationLoading.value = true
    error.value = ''
    try {
      const user = await service.create(input)
      users.value = [user, ...users.value]
      return user
    } catch {
      error.value = 'Không tạo được người dùng. Kiểm tra email trùng hoặc mật khẩu chưa đủ 8 ký tự.'
      return null
    } finally {
      mutationLoading.value = false
    }
  }

  async function updateUser(id: string, input: UserUpdateInput): Promise<UserItem | null> {
    mutationLoading.value = true
    error.value = ''
    try {
      const user = await service.update(id, input)
      users.value = users.value.map((item) => (item.id === user.id ? user : item))
      return user
    } catch {
      error.value = 'Không cập nhật được người dùng'
      return null
    } finally {
      mutationLoading.value = false
    }
  }

  async function setUserActive(id: string, isActive: boolean): Promise<UserItem | null> {
    mutationLoading.value = true
    error.value = ''
    try {
      const user = isActive ? await service.activate(id) : await service.deactivate(id)
      users.value = users.value.map((item) => (item.id === user.id ? user : item))
      return user
    } catch {
      error.value = 'Không đổi được trạng thái người dùng'
      return null
    } finally {
      mutationLoading.value = false
    }
  }

  async function deleteUser(id: string): Promise<UserItem | null> {
    mutationLoading.value = true
    error.value = ''
    try {
      const user = await service.delete(id)
      users.value = users.value.filter((item) => item.id !== user.id)
      return user
    } catch {
      error.value = 'Không xóa được người dùng'
      return null
    } finally {
      mutationLoading.value = false
    }
  }

  return {
    users,
    loading,
    mutationLoading,
    error,
    fetchUsers,
    createUser,
    updateUser,
    setUserActive,
    deleteUser
  }
}
