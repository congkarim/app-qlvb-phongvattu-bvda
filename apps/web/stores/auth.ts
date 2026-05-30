import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => {
    const tokenCookie = useCookie<string>('auth_token')

    return {
      token: tokenCookie.value || ''
    }
  },
  actions: {
    setToken(token: string) {
      const tokenCookie = useCookie<string>('auth_token', {
        sameSite: 'lax'
      })
      tokenCookie.value = token
      this.token = token
    },
    clear() {
      const tokenCookie = useCookie<string | null>('auth_token')
      tokenCookie.value = null
      this.token = ''
    }
  }
})
