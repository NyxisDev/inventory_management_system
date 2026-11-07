import { computed } from 'vue'
import { Lang } from 'quasar'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useConfigStore } from '@/stores/config'
import { quasarLangs } from '@/boot/i18n.js'
import { LOCALES, isLocale, localeInfo, rememberLocale } from '@/i18n/locales.js'

/** Current interface language and a switch that works without a page reload. */
export function useLocale() {
  const { locale } = useI18n({ useScope: 'global' })
  const config = useConfigStore()
  const route = useRoute()
  const router = useRouter()

  const current = computed(() => localeInfo(locale.value))

  async function setLocale(code) {
    if (!isLocale(code) || code === locale.value) return
    locale.value = code
    config.locale = code
    Lang.set(quasarLangs[code])
    rememberLocale(code)
    // A ?lang= from a shared link would override the new choice on reload.
    if (route.query.lang !== undefined) {
      const query = { ...route.query }
      delete query.lang
      await router.replace({ query })
    }
  }

  return { locales: LOCALES, current, setLocale }
}
