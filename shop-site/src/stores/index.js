import { defineStore } from '#q-app'
import { createPinia } from 'pinia'

// One Pinia instance per request on the server; state is sent to the browser.
export default defineStore((/* { ssrContext } */) => {
  return createPinia()
})
