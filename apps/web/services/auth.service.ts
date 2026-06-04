import { useApiClient } from './api'

export interface AuthenticatedUser {
  id: string
  email: string
  full_name: string
  role: 'admin' | 'user' | string
}

interface LoginResponse {
  access_token: string
  token_type: string
  user: AuthenticatedUser
}

export function createAuthService() {
  const api = useApiClient()

  return {
    login(email: string, password: string) {
      return api<LoginResponse>('/auth/login', {
        method: 'POST',
        body: { email, password }
      })
    }
  }
}
