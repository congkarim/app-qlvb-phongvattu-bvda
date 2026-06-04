import { defineStore } from 'pinia'
import type { AuthenticatedUser } from '~/services/auth.service'

export const useAuthStore = defineStore('auth', {
  state: () => {
    const tokenCookie = useCookie<string>('auth_token')
    const userCookie = useCookie<AuthenticatedUser | null>('auth_user')

    return {
      token: tokenCookie.value || '',
      user: userCookie.value || null
    }
  },
  getters: {
    isAdmin: (state) => state.user?.role === 'admin'
  },
  actions: {
    setSession(token: string, user: AuthenticatedUser) {
      const tokenCookie = useCookie<string>('auth_token', {
        sameSite: 'lax'
      })
      const userCookie = useCookie<AuthenticatedUser | null>('auth_user', {
        sameSite: 'lax'
      })
      tokenCookie.value = token
      userCookie.value = user
      this.token = token
      this.user = user
    },
    clear() {
      const tokenCookie = useCookie<string | null>('auth_token')
      const userCookie = useCookie<AuthenticatedUser | null>('auth_user')
      tokenCookie.value = null
      userCookie.value = null
      this.token = ''
      this.user = null
    }
  }
})
