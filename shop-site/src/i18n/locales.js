// Interface languages of the catalog site and how the active one is chosen.
// Priority: ?lang= in the URL, then the "lang" cookie, then Accept-Language, then English.

export const DEFAULT_LOCALE = 'en'
export const LOCALE_COOKIE = 'lang'
const COOKIE_MAX_AGE = 60 * 60 * 24 * 365

/** `tag` is the BCP 47 tag for Intl and hreflang, `ogLocale` the Open Graph form. */
export const LOCALES = [
  { code: 'en', name: 'English', short: 'EN', tag: 'en', ogLocale: 'en_US' },
  { code: 'sk', name: 'Slovenčina', short: 'SK', tag: 'sk', ogLocale: 'sk_SK' },
]

const CODES = new Set(LOCALES.map((l) => l.code))

export function isLocale(value) {
  return typeof value === 'string' && CODES.has(value)
}

export function localeInfo(code) {
  return LOCALES.find((l) => l.code === code) ?? LOCALES[0]
}

function fromCookieHeader(header) {
  if (typeof header !== 'string') return null
  for (const part of header.split(';')) {
    const [name, ...rest] = part.trim().split('=')
    if (name === LOCALE_COOKIE) {
      const value = rest.join('=').trim()
      return isLocale(value) ? value : null
    }
  }
  return null
}

function fromAcceptLanguage(header) {
  if (typeof header !== 'string') return null
  const ranked = header
    .split(',')
    .map((part) => {
      const [tag, ...params] = part.trim().split(';')
      const q = params.map((p) => p.trim()).find((p) => p.startsWith('q='))
      return { lang: tag.trim().toLowerCase().split('-')[0], q: q ? Number(q.slice(2)) || 0 : 1 }
    })
    .filter((x) => x.q > 0)
    .sort((a, b) => b.q - a.q)
  return ranked.find((x) => isLocale(x.lang))?.lang ?? null
}

function fromUrl(url) {
  if (typeof url !== 'string') return null
  const value = new URL(url, 'http://x').searchParams.get('lang')
  return isLocale(value) ? value : null
}

/** Server side: pick the locale for an incoming Node request. */
export function localeFromRequest(req) {
  if (!req) return DEFAULT_LOCALE
  return (
    fromUrl(req.url) ??
    fromCookieHeader(req.headers?.cookie) ??
    fromAcceptLanguage(req.headers?.['accept-language']) ??
    DEFAULT_LOCALE
  )
}

/** Browser side: remember the choice for the next server render. */
export function rememberLocale(code) {
  if (typeof document === 'undefined' || !isLocale(code)) return
  const secure = window.location.protocol === 'https:' ? '; Secure' : ''
  document.cookie = `${LOCALE_COOKIE}=${code}; Path=/; Max-Age=${COOKIE_MAX_AGE}; SameSite=Lax${secure}`
}

/** Adds or replaces ?lang= on a path that may already have a query string. */
export function withLang(path, code) {
  const url = new URL(path || '/', 'http://x')
  if (code === DEFAULT_LOCALE) url.searchParams.delete('lang')
  else url.searchParams.set('lang', code)
  return url.pathname + url.search
}

/**
 * Slovak plural forms: 0 | 1 | 2–4 | 5 and more.
 * Messages with three forms (0 | 1 | n) fall back to the English rule.
 */
export function slovakPlural(choice, choicesLength) {
  const n = Math.abs(choice)
  if (choicesLength < 4) {
    if (n === 0) return 0
    return n === 1 ? 1 : 2
  }
  if (n === 0) return 0
  if (n === 1) return 1
  if (n >= 2 && n <= 4) return 2
  return 3
}
