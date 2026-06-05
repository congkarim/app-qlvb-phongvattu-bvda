import type {
  UserAuditLog,
  UserCreateInput,
  UserItem,
  UserListFilters,
  UserListResponse,
  UserResetPasswordInput,
  UserUpdateInput
} from '~/types/user'
import { useApiClient } from './api'

export function createUserService() {
  const api = useApiClient()

  return {
    list(filters: UserListFilters = {}) {
      const params = new URLSearchParams()
      for (const [key, value] of Object.entries(filters)) {
        if (value !== undefined && value !== null && String(value).trim() !== '') {
          params.set(key, String(value))
        }
      }
      const query = params.toString()
      return api<UserListResponse>(`/users${query ? `?${query}` : ''}`)
    },
    create(input: UserCreateInput) {
      return api<UserItem>('/users', {
        method: 'POST',
        body: normalizeCreateInput(input)
      })
    },
    update(id: string, input: UserUpdateInput) {
      return api<UserItem>(`/users/${id}`, {
        method: 'PATCH',
        body: normalizeUpdateInput(input)
      })
    },
    listAuditLogs(id: string, limit = 50) {
      return api<UserAuditLog[]>(`/users/${id}/audit-logs?limit=${limit}`)
    },
    activate(id: string) {
      return api<UserItem>(`/users/${id}/activate`, {
        method: 'POST'
      })
    },
    deactivate(id: string) {
      return api<UserItem>(`/users/${id}/deactivate`, {
        method: 'POST'
      })
    },
    resetPassword(id: string, input: UserResetPasswordInput) {
      return api<UserItem>(`/users/${id}/reset-password`, {
        method: 'POST',
        body: {
          password: input.password
        }
      })
    },
    delete(id: string) {
      return api<UserItem>(`/users/${id}`, {
        method: 'DELETE'
      })
    }
  }
}

function normalizeCreateInput(input: UserCreateInput) {
  return {
    email: input.email.trim().toLowerCase(),
    full_name: input.full_name.trim(),
    password: input.password,
    role: input.role,
    is_active: input.is_active
  }
}

function normalizeUpdateInput(input: UserUpdateInput) {
  return {
    full_name: input.full_name.trim(),
    role: input.role,
    is_active: input.is_active
  }
}
