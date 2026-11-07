import { defineSsrMiddleware } from '#q-app'
import { createCatalogSource } from '../../src/services/catalog-source.js'
import { isMock, readPublicConfig, readServerApiUrl } from '../../src/services/shop-config.js'

const SITEMAP_TTL_MS = 10 * 60 * 1000
const MAX_PAGES = 50 // 50 x 100 products is plenty for one shop

let cached = { xml: '', at: 0 }

function escapeXml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function flatten(tree) {
  const out = []
  for (const node of tree ?? []) {
    out.push(node.slug)
    out.push(...flatten(node.children))
  }
  return out
}

async function buildSitemap() {
  const { siteUrl } = readPublicConfig()
  const source = createCatalogSource({ baseURL: readServerApiUrl(), mock: isMock() })

  const urls = [
    { loc: `${siteUrl}/`, priority: '1.0' },
    { loc: `${siteUrl}/catalog`, priority: '0.9' },
    { loc: `${siteUrl}/contacts`, priority: '0.5' },
  ]

  const categories = await source.getCategories()
  for (const slug of flatten(categories)) {
    urls.push({ loc: `${siteUrl}/catalog/${encodeURIComponent(slug)}`, priority: '0.8' })
  }

  for (let page = 1; page <= MAX_PAGES; page++) {
    const data = await source.getProducts({ page, page_size: 100, sort: 'name' })
    for (const item of data.items) {
      urls.push({
        loc: `${siteUrl}/product/${encodeURIComponent(item.slug)}`,
        lastmod: item.updated_at ?? item.created_at,
        priority: '0.7',
      })
    }
    if (page * data.page_size >= data.total) break
  }

  const body = urls
    .map(
      (u) =>
        `  <url><loc>${escapeXml(u.loc)}</loc>${u.lastmod ? `<lastmod>${escapeXml(u.lastmod.slice(0, 10))}</lastmod>` : ''}<priority>${u.priority}</priority></url>`,
    )
    .join('\n')

  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${body}\n</urlset>\n`
}

export default defineSsrMiddleware(({ app, resolve }) => {
  app.get(resolve.urlPath('/robots.txt'), (c) => {
    const { siteUrl } = readPublicConfig()
    const text = ['User-agent: *', 'Allow: /', 'Disallow: /search', '', `Sitemap: ${siteUrl}/sitemap.xml`, ''].join('\n')
    return c.text(text, 200, { 'Cache-Control': 'public, max-age=3600' })
  })

  app.get(resolve.urlPath('/sitemap.xml'), async (c) => {
    try {
      if (!cached.xml || Date.now() - cached.at > SITEMAP_TTL_MS) {
        cached = { xml: await buildSitemap(), at: Date.now() }
      }
      return c.body(cached.xml, 200, {
        'Content-Type': 'application/xml; charset=utf-8',
        'Cache-Control': 'public, max-age=600',
      })
    } catch (err) {
      console.error('sitemap.xml failed:', err instanceof Error ? err.message : err)
      return c.text('Sitemap is temporarily unavailable', 503)
    }
  })
})
