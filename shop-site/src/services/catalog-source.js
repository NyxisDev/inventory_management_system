// Reads the public catalog API (/api/v1/public/...). Read-only, no auth.
// With mock=true it answers from the demo data in src/mock instead.
// The response shapes are described in docs/public-api.md.
import axios from 'axios'

const PUBLIC_PATH = '/api/v1/public'
const TIMEOUT_MS = 8000

export class NotFoundError extends Error {
  constructor(message = 'Not found') {
    super(message)
    this.name = 'NotFoundError'
    this.status = 404
  }
}

function cleanParams(params) {
  const out = {}
  for (const [key, value] of Object.entries(params ?? {})) {
    if (value === undefined || value === null || value === '' || value === false) continue
    out[key] = value
  }
  return out
}

function createHttpSource(baseURL) {
  const http = axios.create({
    baseURL: `${baseURL.replace(/\/$/, '')}${PUBLIC_PATH}`,
    timeout: TIMEOUT_MS,
    headers: { Accept: 'application/json' },
  })

  async function get(path, params) {
    try {
      const { data } = await http.get(path, { params: cleanParams(params) })
      return data
    } catch (err) {
      if (err.response?.status === 404) throw new NotFoundError()
      throw err
    }
  }

  return {
    getCategories: () => get('/categories'),
    getProducts: (params) => get('/products', params),
    async getProduct(slug) {
      try {
        return await get(`/products/${encodeURIComponent(slug)}`)
      } catch (err) {
        if (err instanceof NotFoundError) return null
        throw err
      }
    },
    getWarehouses: () => get('/warehouses'),
  }
}

function createMockSource() {
  // Loaded on demand, so the demo data is not shipped when the real API is used.
  const load = () => import('../mock/mock-api.js')
  return {
    getCategories: async () => (await load()).getCategories(),
    async getProducts(params) {
      const api = await load()
      try {
        return api.getProducts(cleanParams(params))
      } catch (err) {
        if (err.status === 404) throw new NotFoundError()
        throw err
      }
    },
    getProduct: async (slug) => (await load()).getProduct(slug),
    getWarehouses: async () => (await load()).getWarehouses(),
  }
}

/**
 * @param {{ baseURL: string, mock: boolean }} options
 *   baseURL: '' in the browser (same origin, nginx proxies /api),
 *   the internal backend URL on the server (for example http://backend:8000).
 */
export function createCatalogSource({ baseURL, mock }) {
  return mock ? createMockSource() : createHttpSource(baseURL)
}
