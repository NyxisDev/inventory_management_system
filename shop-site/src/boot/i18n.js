import { defineBoot } from '#q-app'
import { createI18n } from 'vue-i18n'
import messages from '@/i18n'

// One i18n instance per request on the server (boot files run per request).
export default defineBoot(({ app }) => {
  const i18n = createI18n({
    locale: 'en',
    fallbackLocale: 'en',
    globalInjection: true,
    legacy: false,
    messages,
  })

  app.use(i18n)
})
