export type UserRole = 'admin' | 'user'

export interface UserItem {
  id: string
  email: string
  full_name: string
  role: UserRole | string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface UserListResponse {
  items: UserItem[]
  total: number
  limit: number
  offset: number
}

export interface UserListFilters {
  q?: string
  role?: string
  is_active?: string
  sort_by?: string
  sort_dir?: string
  limit?: number
  offset?: number
}

export interface UserCreateInput {
  email: string
  full_name: string
  password: string
  role: UserRole
  is_active: boolean
}

export interface UserUpdateInput {
  full_name: string
  role: UserRole
  is_active: boolean
}

export interface UserResetPasswordInput {
  password: string
}

export interface UserAuditActor {
  id: string
  email: string
  full_name: string
}

export interface UserAuditLog {
  id: string
  actor_user_id?: string | null
  actor?: UserAuditActor | null
  action: string
  entity_type: string
  entity_id: string
  metadata: Record<string, unknown>
  created_at: string
}
