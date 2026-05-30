import { useAuthStore } from '~/stores/auth'

export default defineNuxtRouteMiddleware((to) => {
  const authStore = useAuthStore()
  const isLoginRoute = to.path === '/login'

  if (!authStore.token && !isLoginRoute) {
    return navigateTo('/login')
  }

  if (authStore.token && isLoginRoute) {
    return navigateTo('/dashboard')
  }
})
