import { defineBoot } from '#q-app'
import { useConfigStore } from '@/stores/config'
import { readPublicConfig } from '@/services/shop-config.js'
import { localeFromRequest } from '@/i18n/locales.js'

// Fill the public shop settings from .env on the server. The browser gets
// them through the serialized Pinia state, so they can change without a rebuild.
//
// The SPA build is only the static demo (GitHub Pages): there is no server
// and no .env, so it always runs on the built-in demo data with default settings.
export default defineBoot(({ store, ssrContext }) => {
  if (import.meta.env.SSR) {
    useConfigStore(store).$patch({ ...readPublicConfig(), locale: localeFromRequest(ssrContext?.req) })
    return
  }
  if (import.meta.env.QUASAR_MODE !== 'spa') return

  const siteUrl = new URL(import.meta.env.BASE_URL, window.location.origin).href
  // With hash routing the ?lang= of a shared link sits inside the hash.
  const url = window.location.hash.slice(1) || window.location.search
  const locale = localeFromRequest({
    url,
    headers: { cookie: document.cookie, 'accept-language': navigator.languages?.join(',') ?? '' },
  })
  useConfigStore(store).$patch({
    ...readPublicConfig({ MOCK_API: 'true', SITE_URL: siteUrl }),
    locale,
  })
})
