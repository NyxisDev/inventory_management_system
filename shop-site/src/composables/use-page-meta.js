import { useMeta } from 'quasar'
import { useI18n } from 'vue-i18n'
import { useConfigStore } from '@/stores/config'
import { DEFAULT_LOCALE, LOCALES, localeInfo, withLang } from '@/i18n/locales.js'

// JSON inside <script> must not be able to close the tag.
function safeJson(value) {
  return JSON.stringify(value).replace(/</g, '\\u003c').replace(/>/g, '\\u003e').replace(/&/g, '\\u0026')
}

function absolute(siteUrl, pathOrUrl) {
  if (!pathOrUrl) return ''
  if (/^https?:\/\//i.test(pathOrUrl)) return pathOrUrl
  return `${siteUrl}${pathOrUrl.startsWith('/') ? '' : '/'}${pathOrUrl}`
}

/**
 * Sets title, description, Open Graph tags and the canonical link.
 * @param {() => { title: string, description?: string, path: string, image?: string,
 *   noindex?: boolean, jsonLd?: object | null }} getter reactive source of meta values
 */
export function usePageMeta(getter) {
  const config = useConfigStore()
  const { locale } = useI18n({ useScope: 'global' })

  useMeta(() => {
    const m = getter()
    const siteName = config.siteName
    const fullTitle = m.title ? `${m.title} | ${siteName}` : siteName
    const path = m.path || '/'
    // Each language has its own URL (?lang=), so search engines can index both.
    const canonical = absolute(config.siteUrl, withLang(path, locale.value))
    const meta = {
      description: { name: 'description', content: m.description || '' },
      ogType: { property: 'og:type', content: m.ogType || 'website' },
      ogSiteName: { property: 'og:site_name', content: siteName },
      ogTitle: { property: 'og:title', content: fullTitle },
      ogDescription: { property: 'og:description', content: m.description || '' },
      ogUrl: { property: 'og:url', content: canonical },
      ogLocale: { property: 'og:locale', content: localeInfo(locale.value).ogLocale },
      twitterCard: { name: 'twitter:card', content: m.image ? 'summary_large_image' : 'summary' },
    }
    if (m.image) meta.ogImage = { property: 'og:image', content: absolute(config.siteUrl, m.image) }
    if (m.noindex) meta.robots = { name: 'robots', content: 'noindex, follow' }

    const link = { canonical: { rel: 'canonical', href: canonical } }
    if (!m.noindex) {
      for (const l of LOCALES) {
        link[`alt-${l.code}`] = { rel: 'alternate', hreflang: l.tag, href: absolute(config.siteUrl, withLang(path, l.code)) }
      }
      link.altDefault = {
        rel: 'alternate',
        hreflang: 'x-default',
        href: absolute(config.siteUrl, withLang(path, DEFAULT_LOCALE)),
      }
    }

    const result = { title: fullTitle, meta, link }

    if (m.jsonLd) {
      result.script = {
        ldJson: { type: 'application/ld+json', innerHTML: safeJson(m.jsonLd) },
      }
    }

    return result
  })
}

export { absolute as absoluteUrl }
