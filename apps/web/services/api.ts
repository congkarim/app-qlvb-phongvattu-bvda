import { useAuthStore } from '~/stores/auth'

export function useApiClient() {
  const config = useRuntimeConfig()

  return $fetch.create({
    baseURL: config.public.apiBase,
    onRequest({ options }) {
      const authStore = useAuthStore()
      if (!authStore.token) {
        return
      }

      const headers = new Headers(options.headers)
      headers.set('Authorization', `Bearer ${authStore.token}`)
      options.headers = headers
    }
  })
}
