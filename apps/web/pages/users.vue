<script setup lang="ts">
import type { UserCreateInput, UserItem, UserListFilters, UserRole, UserUpdateInput } from '~/types/user'
import { formatDateTime } from '~/utils/format'

const authStore = useAuthStore()
const {
  users,
  total,
  limit,
  offset,
  loading,
  mutationLoading,
  error,
  fetchUsers,
  createUser,
  updateUser,
  setUserActive,
  resetPassword,
  deleteUser
} = useUsers()

const filters = reactive<Required<Pick<UserListFilters, 'q' | 'role' | 'is_active' | 'sort_by' | 'sort_dir'>>>({
  q: '',
  role: '',
  is_active: '',
  sort_by: 'created_at',
  sort_dir: 'desc'
})

const createForm = reactive<UserCreateInput>({
  email: '',
  full_name: '',
  password: '',
  role: 'user',
  is_active: true
})

const editForms = reactive<Record<string, UserUpdateInput>>({})
const resetPasswordForms = reactive<Record<string, string>>({})
const editingUserId = ref('')
const pageSize = ref(20)
const currentOffset = ref(0)

const roleOptions: Array<{ label: string; value: '' | UserRole }> = [
  { label: 'Tất cả role', value: '' },
  { label: 'Admin', value: 'admin' },
  { label: 'User', value: 'user' }
]

const activeOptions = [
  { label: 'Tất cả trạng thái', value: '' },
  { label: 'Đang hoạt động', value: 'true' },
  { label: 'Đã vô hiệu hóa', value: 'false' }
]

const sortOptions = [
  { label: 'Ngày tạo', value: 'created_at' },
  { label: 'Cập nhật', value: 'updated_at' },
  { label: 'Email', value: 'email' },
  { label: 'Họ tên', value: 'full_name' },
  { label: 'Role', value: 'role' },
  { label: 'Trạng thái', value: 'is_active' }
]

const canSubmitCreate = computed(() => {
  return (
    createForm.email.trim().length > 0 &&
    createForm.full_name.trim().length > 0 &&
    createForm.password.length >= 8 &&
    ['admin', 'user'].includes(createForm.role)
  )
})

const currentPage = computed(() => Math.floor(offset.value / Math.max(limit.value, 1)) + 1)
const totalPages = computed(() => Math.max(Math.ceil(total.value / Math.max(limit.value, 1)), 1))
const canGoPrevious = computed(() => offset.value > 0)
const canGoNext = computed(() => offset.value + limit.value < total.value)

function currentFilters(): UserListFilters {
  return {
    q: filters.q,
    role: filters.role,
    is_active: filters.is_active,
    sort_by: filters.sort_by,
    sort_dir: filters.sort_dir,
    limit: pageSize.value,
    offset: currentOffset.value
  }
}

async function loadUsers(nextOffset = currentOffset.value) {
  currentOffset.value = Math.max(nextOffset, 0)
  await fetchUsers(currentFilters())
}

function resetFilters() {
  filters.q = ''
  filters.role = ''
  filters.is_active = ''
  filters.sort_by = 'created_at'
  filters.sort_dir = 'desc'
  pageSize.value = 20
  void loadUsers(0)
}

async function submitCreate() {
  if (!canSubmitCreate.value) return
  const created = await createUser(createForm)
  if (!created) return
  createForm.email = ''
  createForm.full_name = ''
  createForm.password = ''
  createForm.role = 'user'
  createForm.is_active = true
  await loadUsers(0)
}

function startEdit(user: UserItem) {
  editingUserId.value = user.id
  editForms[user.id] = {
    full_name: user.full_name,
    role: user.role === 'admin' ? 'admin' : 'user',
    is_active: user.is_active
  }
}

function cancelEdit() {
  editingUserId.value = ''
}

async function submitEdit(user: UserItem) {
  const form = editForms[user.id]
  if (!form) return
  const updated = await updateUser(user.id, form)
  if (updated) editingUserId.value = ''
}

async function toggleActive(user: UserItem) {
  await setUserActive(user.id, !user.is_active)
}

async function submitResetPassword(user: UserItem) {
  const password = resetPasswordForms[user.id] || ''
  if (password.length < 8) return
  const updated = await resetPassword(user.id, { password })
  if (updated) resetPasswordForms[user.id] = ''
}

async function confirmDelete(user: UserItem) {
  if (!window.confirm(`Xóa người dùng ${user.email}?`)) return
  const deleted = await deleteUser(user.id)
  if (deleted && users.value.length === 0 && currentOffset.value > 0) {
    await loadUsers(Math.max(currentOffset.value - pageSize.value, 0))
  }
}

async function goPreviousPage() {
  await loadUsers(Math.max(offset.value - limit.value, 0))
}

async function goNextPage() {
  if (!canGoNext.value) return
  await loadUsers(offset.value + limit.value)
}

function roleSeverity(role: string) {
  return role === 'admin' ? 'danger' : 'secondary'
}

onMounted(loadUsers)
</script>

<template>
  <section class="space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-2xl font-semibold">Users</h1>
        <p class="mt-1 text-sm text-slate-600">Quản lý tài khoản local cho hệ thống OCR và semantic search.</p>
      </div>
      <Button label="Refresh" icon="pi pi-refresh" severity="secondary" :loading="loading" @click="loadUsers()" />
    </div>

    <Message v-if="!authStore.isAdmin" severity="warn">Chỉ admin được quản lý người dùng.</Message>
    <Message v-if="error" severity="error">{{ error }}</Message>

    <Card>
      <template #title>Tạo người dùng</template>
      <template #content>
        <form class="grid gap-3 md:grid-cols-6" @submit.prevent="submitCreate">
          <InputText v-model="createForm.email" class="md:col-span-2" type="email" required placeholder="Email" />
          <InputText v-model="createForm.full_name" class="md:col-span-2" required placeholder="Họ tên" />
          <InputText v-model="createForm.password" type="password" required placeholder="Mật khẩu tối thiểu 8 ký tự" />
          <select v-model="createForm.role" class="rounded border border-slate-300 px-3 py-2 text-sm">
            <option value="user">User</option>
            <option value="admin">Admin</option>
          </select>
          <label class="flex items-center gap-2 text-sm text-slate-700">
            <input v-model="createForm.is_active" type="checkbox" class="h-4 w-4 rounded border-slate-300" />
            Hoạt động
          </label>
          <div class="md:col-span-5">
            <Button type="submit" label="Tạo user" icon="pi pi-user-plus" :loading="mutationLoading" :disabled="!canSubmitCreate" />
          </div>
        </form>
      </template>
    </Card>

    <Card>
      <template #content>
        <div class="grid gap-3 md:grid-cols-6">
          <InputText
            v-model="filters.q"
            class="md:col-span-2"
            placeholder="Tìm theo email hoặc họ tên"
            @keyup.enter="loadUsers(0)"
          />
          <select v-model="filters.role" class="rounded border border-slate-300 px-3 py-2 text-sm">
            <option v-for="option in roleOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
          <select v-model="filters.is_active" class="rounded border border-slate-300 px-3 py-2 text-sm">
            <option v-for="option in activeOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
          <select v-model="filters.sort_by" class="rounded border border-slate-300 px-3 py-2 text-sm">
            <option v-for="option in sortOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
          <select v-model="filters.sort_dir" class="rounded border border-slate-300 px-3 py-2 text-sm">
            <option value="desc">Giảm dần</option>
            <option value="asc">Tăng dần</option>
          </select>
          <select v-model.number="pageSize" class="rounded border border-slate-300 px-3 py-2 text-sm">
            <option :value="10">10 dòng</option>
            <option :value="20">20 dòng</option>
            <option :value="50">50 dòng</option>
            <option :value="100">100 dòng</option>
          </select>
        </div>
        <div class="mt-3 flex flex-wrap gap-2">
          <Button label="Lọc" icon="pi pi-filter" :loading="loading" @click="loadUsers(0)" />
          <Button label="Xóa lọc" icon="pi pi-times" severity="secondary" :disabled="loading" @click="resetFilters" />
        </div>
      </template>
    </Card>

    <div class="flex flex-wrap items-center justify-between gap-3 text-sm text-slate-600">
      <span>Hiển thị {{ users.length }} / {{ total }} user · Trang {{ currentPage }} / {{ totalPages }}</span>
      <div class="flex gap-2">
        <Button label="Trước" size="small" severity="secondary" :disabled="loading || !canGoPrevious" @click="goPreviousPage" />
        <Button label="Sau" size="small" severity="secondary" :disabled="loading || !canGoNext" @click="goNextPage" />
      </div>
    </div>

    <DataTable :value="users" :loading="loading" data-key="id" table-style="min-width: 72rem">
      <Column field="email" header="Email">
        <template #body="{ data }">
          <div>
            <p class="font-medium text-slate-900">{{ data.email }}</p>
            <p v-if="data.id === authStore.user?.id" class="mt-1 text-xs text-slate-500">Tài khoản hiện tại</p>
          </div>
        </template>
      </Column>
      <Column field="full_name" header="Họ tên">
        <template #body="{ data }">
          <InputText v-if="editingUserId === data.id" v-model="editForms[data.id].full_name" class="w-full" />
          <span v-else>{{ data.full_name }}</span>
        </template>
      </Column>
      <Column field="role" header="Role">
        <template #body="{ data }">
          <select
            v-if="editingUserId === data.id"
            v-model="editForms[data.id].role"
            class="rounded border border-slate-300 px-3 py-2 text-sm"
            :disabled="data.id === authStore.user?.id"
          >
            <option value="user">User</option>
            <option value="admin">Admin</option>
          </select>
          <Tag v-else :value="data.role" :severity="roleSeverity(data.role)" />
        </template>
      </Column>
      <Column field="is_active" header="Trạng thái">
        <template #body="{ data }">
          <label v-if="editingUserId === data.id" class="flex items-center gap-2 text-sm">
            <input
              v-model="editForms[data.id].is_active"
              type="checkbox"
              class="h-4 w-4 rounded border-slate-300"
              :disabled="data.id === authStore.user?.id"
            />
            Hoạt động
          </label>
          <Tag v-else :value="data.is_active ? 'active' : 'disabled'" :severity="data.is_active ? 'success' : 'secondary'" />
        </template>
      </Column>
      <Column field="created_at" header="Ngày tạo">
        <template #body="{ data }">{{ formatDateTime(data.created_at) }}</template>
      </Column>
      <Column field="updated_at" header="Cập nhật">
        <template #body="{ data }">{{ formatDateTime(data.updated_at) }}</template>
      </Column>
      <Column header="Thao tác">
        <template #body="{ data }">
          <div v-if="editingUserId === data.id" class="flex flex-wrap gap-2">
            <Button label="Lưu" size="small" :loading="mutationLoading" @click="submitEdit(data)" />
            <Button label="Hủy" size="small" severity="secondary" :disabled="mutationLoading" @click="cancelEdit" />
          </div>
          <div v-else class="flex flex-wrap gap-2">
            <Button label="Sửa" size="small" severity="secondary" :disabled="mutationLoading" @click="startEdit(data)" />
            <Button
              :label="data.is_active ? 'Vô hiệu hóa' : 'Kích hoạt'"
              size="small"
              severity="secondary"
              :disabled="mutationLoading || data.id === authStore.user?.id"
              @click="toggleActive(data)"
            />
            <Button
              label="Xóa"
              size="small"
              severity="danger"
              :disabled="mutationLoading || data.id === authStore.user?.id"
              @click="confirmDelete(data)"
            />
            <div class="flex min-w-60 gap-2">
              <InputText
                v-model="resetPasswordForms[data.id]"
                type="password"
                size="small"
                class="w-36"
                placeholder="Mật khẩu mới"
              />
              <Button
                label="Reset"
                size="small"
                severity="secondary"
                :disabled="mutationLoading || !resetPasswordForms[data.id] || resetPasswordForms[data.id].length < 8"
                @click="submitResetPassword(data)"
              />
            </div>
          </div>
        </template>
      </Column>
      <template #empty>
        <div class="py-6 text-center text-sm text-slate-600">Chưa có người dùng phù hợp.</div>
      </template>
    </DataTable>
  </section>
</template>
