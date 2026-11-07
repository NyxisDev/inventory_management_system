import { defineBoot } from '#q-app'
import { useConfigStore } from '@/stores/config'
import { readPublicConfig } from '@/services/shop-config.js'
import { localeFromRequest } from '@/i18n/locales.js'

// Fill the public shop settings from .env on the server. The browser gets
// them through the serialized Pinia state, so they can change without a rebuild.
export default defineBoot(({ store, ssrContext }) => {
  if (!import.meta.env.SSR) return
  useConfigStore(store).$patch({ ...readPublicConfig(), locale: localeFromRequest(ssrContext?.req) })
})
