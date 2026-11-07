// Signed-in employee. The access token is kept ONLY in memory (never localStorage or
// sessionStorage); after a page reload the session is restored from the refresh cookie.
import { defineStore } from 'pinia'
import { api } from '../boot/axios.js'

const IDLE_LIMIT_MS = 30 * 60 * 1000
const ACTIVITY_EVENTS = ['mousemove', 'mousedown', 'keydown', 'touchstart', 'scroll']
const CHANNEL_NAME = 'budmaster-admin-auth'

let refreshPromise = null
let idleTimer = null
let channel = null
let resetIdle = null

export const useAuthStore = defineStore('auth', {
  state: () => ({
    accessToken: null,
    employee: null,
    restored: false,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.accessToken && state.employee),
    isAdmin: (state) => state.employee?.role === 'admin',
    fullName: (state) =>
      state.employee ? `${state.employee.first_name} ${state.employee.last_name}` : '',
  },
  actions: {
    setSession(data) {
      this.accessToken = data.access_token
      this.employee = data.employee
      this.startIdleWatch()
    },
    clear() {
      this.accessToken = null
      this.employee = null
      this.stopIdleWatch()
    },
    async login(username, password) {
      const { data } = await api.post('/auth/login', { username, password })
      this.setSession(data)
    },
    // Exchange the refresh cookie for a new access token. Parallel callers share one request.
    refresh() {
      if (!refreshPromise) {
        refreshPromise = api
          .post('/auth/refresh')
          .then(({ data }) => {
            this.setSession(data)
            return true
          })
          .catch(() => {
            this.clear()
            return false
          })
          .finally(() => {
            refreshPromise = null
          })
      }
      return refreshPromise
    },
    // Called once at start-up: restore the session from the cookie, if there is one.
    async restore() {
      if (this.restored) return this.isAuthenticated
      this.restored = true
      this.listenToOtherTabs()
      return this.refresh()
    },
    async logout({ broadcast = true } = {}) {
      try {
        await api.post('/auth/logout')
      } catch {
        // the session ends locally anyway
      }
      this.clear()
      if (broadcast) channel?.postMessage('logout')
    },
    listenToOtherTabs() {
      if (channel || typeof BroadcastChannel === 'undefined') return
      channel = new BroadcastChannel(CHANNEL_NAME)
      channel.onmessage = (event) => {
        if (event.data === 'logout') {
          this.clear()
          window.location.hash = '#/login'
        }
      }
    },
    startIdleWatch() {
      if (idleTimer !== null || typeof window === 'undefined') return
      const reset = () => {
        clearTimeout(idleTimer)
        idleTimer = setTimeout(async () => {
          await this.logout()
          window.location.hash = '#/login?reason=idle'
        }, IDLE_LIMIT_MS)
      }
      resetIdle = reset
      ACTIVITY_EVENTS.forEach((name) => window.addEventListener(name, reset, { passive: true }))
      reset()
    },
    stopIdleWatch() {
      if (idleTimer === null) return
      clearTimeout(idleTimer)
      idleTimer = null
      if (resetIdle) {
        ACTIVITY_EVENTS.forEach((name) => window.removeEventListener(name, resetIdle))
        resetIdle = null
      }
    },
  },
})
