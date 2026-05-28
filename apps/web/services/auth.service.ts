import { useApiClient } from './api'

interface LoginResponse {
  access_token: string
  token_type: string
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
