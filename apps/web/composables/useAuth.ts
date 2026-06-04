import { createAuthService } from '~/services/auth.service'

export function useAuth() {
  const authStore = useAuthStore()
  const loading = ref(false)
  const error = ref('')
  const service = createAuthService()

  async function login(email: string, password: string) {
    loading.value = true
    error.value = ''
    try {
      const response = await service.login(email, password)
      authStore.setSession(response.access_token, response.user)
      await navigateTo('/dashboard')
    } catch {
      error.value = 'Đăng nhập không thành công'
    } finally {
      loading.value = false
    }
  }

  return { loading, error, login }
}
