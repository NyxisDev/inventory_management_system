// HTTP client for the backend API (/api/v1).
// - cookies are sent (refresh token lives in an httpOnly cookie, path /api/v1/auth)
// - X-Requested-With is required by the backend for refresh / logout (CSRF protection)
// - on 401 the access token is refreshed ONCE (parallel requests share one refresh) and the
//   request is retried; if refreshing fails the user is signed out and sent to /login
import { defineBoot } from '#q-app'
import axios from 'axios'
import { useAuthStore } from '../stores/auth.js'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  withCredentials: true,
  timeout: 20000,
  headers: { 'X-Requested-With': 'XMLHttpRequest' },
})

// Requests that must never trigger a refresh loop
const AUTH_PATHS = ['/auth/login', '/auth/refresh', '/auth/logout']

export default defineBoot(({ router, store }) => {
  const auth = useAuthStore(store)

  api.interceptors.request.use((config) => {
    if (auth.accessToken) config.headers.Authorization = `Bearer ${auth.accessToken}`
    return config
  })

  api.interceptors.response.use(
    (response) => response,
    async (error) => {
      const config = error.config
      const status = error.response?.status
      const isAuthCall = AUTH_PATHS.some((path) => config?.url?.startsWith(path))
      if (status === 401 && config && !config._retried && !isAuthCall) {
        config._retried = true
        if (await auth.refresh()) {
          config.headers.Authorization = `Bearer ${auth.accessToken}`
          return api(config)
        }
        auth.clear()
        if (router.currentRoute.value.name !== 'login') {
          router.replace({ name: 'login', query: { redirect: router.currentRoute.value.fullPath } })
        }
      }
      return Promise.reject(error)
    },
  )
})

// Error text for the UI: the backend always answers {"detail": "..."} in English.
export function apiErrorMessage(error) {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string' && detail) return detail
  if (error?.code === 'ECONNABORTED' || !error?.response) return 'The server is not reachable.'
  return ''
}
