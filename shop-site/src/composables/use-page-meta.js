import { useMeta } from 'quasar'
import { useConfigStore } from '@/stores/config'

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

  useMeta(() => {
    const m = getter()
    const siteName = config.siteName
    const fullTitle = m.title ? `${m.title} | ${siteName}` : siteName
    const canonical = absolute(config.siteUrl, m.path || '/')
    const meta = {
      description: { name: 'description', content: m.description || '' },
      ogType: { property: 'og:type', content: m.ogType || 'website' },
      ogSiteName: { property: 'og:site_name', content: siteName },
      ogTitle: { property: 'og:title', content: fullTitle },
      ogDescription: { property: 'og:description', content: m.description || '' },
      ogUrl: { property: 'og:url', content: canonical },
      twitterCard: { name: 'twitter:card', content: m.image ? 'summary_large_image' : 'summary' },
    }
    if (m.image) meta.ogImage = { property: 'og:image', content: absolute(config.siteUrl, m.image) }
    if (m.noindex) meta.robots = { name: 'robots', content: 'noindex, follow' }

    const result = {
      title: fullTitle,
      meta,
      link: { canonical: { rel: 'canonical', href: canonical } },
    }

    if (m.jsonLd) {
      result.script = {
        ldJson: { type: 'application/ld+json', innerHTML: safeJson(m.jsonLd) },
      }
    }

    return result
  })
}

export { absolute as absoluteUrl }
