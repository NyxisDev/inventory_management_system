// Shop settings come from environment variables of the SSR server (.env).
// Only public values go to the browser; API_URL stays on the server.

const DEFAULTS = {
  SITE_NAME: 'BuildStock',
  SITE_URL: 'http://localhost:8080',
  SHOP_PHONE: '+000 000 000 000',
  SHOP_EMAIL: 'info@example.com',
  SHOP_ADDRESS: 'Sample Street 12, Industrial Zone (demo address)',
  SHOP_HOURS: 'Mon–Fri 7:00–18:00; Sat 8:00–14:00; Sun closed',
  CURRENCY: 'EUR',
}

function env() {
  // Read at runtime on the server; never inlined into the client bundle.
  return globalThis.process?.env ?? {}
}

function pick(source, key) {
  const value = source[key]
  return typeof value === 'string' && value.trim() !== '' ? value.trim() : DEFAULTS[key]
}

/** Public settings, safe to serialize into the page. */
export function readPublicConfig(source = env()) {
  const currency = pick(source, 'CURRENCY').toUpperCase()
  return {
    siteName: pick(source, 'SITE_NAME'),
    siteUrl: pick(source, 'SITE_URL').replace(/\/$/, ''),
    phone: pick(source, 'SHOP_PHONE'),
    email: pick(source, 'SHOP_EMAIL'),
    address: pick(source, 'SHOP_ADDRESS'),
    hours: pick(source, 'SHOP_HOURS')
      .split(';')
      .map((line) => line.trim())
      .filter(Boolean),
    currency: /^[A-Z]{3}$/.test(currency) ? currency : 'EUR',
    mock: isMock(source),
  }
}

/** Server-only: where the SSR server reaches the backend. */
export function readServerApiUrl(source = env()) {
  return (source.API_URL ?? '').trim() || 'http://localhost:8000'
}

export function isMock(source = env()) {
  const value = (source.MOCK_API ?? '').trim().toLowerCase()
  if (value === '') return !(source.API_URL ?? '').trim()
  return value === 'true' || value === '1'
}
