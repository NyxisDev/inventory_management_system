import { defineBoot } from '#q-app'
import { Lang } from 'quasar'
import { createI18n } from 'vue-i18n'
import quasarEn from 'quasar/lang/en-US.js'
import quasarSk from 'quasar/lang/sk.js'
import messages from '@/i18n'
import { DEFAULT_LOCALE, slovakPlural } from '@/i18n/locales.js'
import { useConfigStore } from '@/stores/config'

// Labels inside Quasar components (pagination, select, dialogs) follow the site language.
export const quasarLangs = { en: quasarEn, sk: quasarSk }

// One i18n instance per request on the server (boot files run per request).
// The locale is picked on the server (boot/config.js) and reaches the browser
// in the serialized Pinia state, so both render the same language.
export default defineBoot(({ app, store, ssrContext }) => {
  const locale = useConfigStore(store).locale || DEFAULT_LOCALE

  const i18n = createI18n({
    locale,
    fallbackLocale: DEFAULT_LOCALE,
    globalInjection: true,
    legacy: false,
    messages,
    pluralRules: { sk: slovakPlural },
  })

  Lang.set(quasarLangs[locale] ?? quasarEn, ssrContext)
  app.use(i18n)
})
