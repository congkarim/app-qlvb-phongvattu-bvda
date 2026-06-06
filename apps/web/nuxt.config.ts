export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  modules: ['@pinia/nuxt', '@nuxtjs/tailwindcss'],
  css: ['primeicons/primeicons.css', '~/assets/css/main.css'],
  experimental: {
    appManifest: false
  },
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000/api/v1',
      uploadMaxFileSizeMb: Number(process.env.NUXT_PUBLIC_UPLOAD_MAX_FILE_SIZE_MB || 50),
      uploadMaxFiles: Number(process.env.NUXT_PUBLIC_UPLOAD_MAX_FILES || 20),
      uploadMaxZipSizeMb: Number(process.env.NUXT_PUBLIC_UPLOAD_MAX_ZIP_SIZE_MB || 200)
    }
  },
  typescript: {
    strict: true
  }
})
