// Catalog filters live in the URL query so a link can be shared.
// Everything coming from the URL is validated here before use.

export const PAGE_SIZE = 12
export const SORT_OPTIONS = ['-created_at', 'price', '-price', 'name']
export const DEFAULT_SORT = '-created_at'
export const PRICE_SLIDER_MAX = 400

function toPrice(value) {
  if (value === undefined || value === null || value === '') return null
  const n = Number(String(value).replace(',', '.'))
  if (!Number.isFinite(n) || n < 0 || n > 10_000_000) return null
  return Math.round(n * 100) / 100
}

function first(value) {
  return Array.isArray(value) ? value[0] : value
}

/** Route query -> validated filters. */
export function parseCatalogQuery(query = {}) {
  const sort = first(query.sort)
  const page = Number.parseInt(first(query.page), 10)
  let priceMin = toPrice(first(query.price_min))
  let priceMax = toPrice(first(query.price_max))
  if (priceMin !== null && priceMax !== null && priceMin > priceMax) {
    const swap = priceMin
    priceMin = priceMax
    priceMax = swap
  }
  const q = String(first(query.q) ?? '')
    .trim()
    .slice(0, 100)
  return {
    q,
    sort: SORT_OPTIONS.includes(sort) ? sort : DEFAULT_SORT,
    page: Number.isFinite(page) && page > 0 && page < 10_000 ? page : 1,
    priceMin,
    priceMax,
    inStock: first(query.in_stock) === 'true' || first(query.in_stock) === '1',
  }
}

/** Filters -> route query. Defaults are left out to keep URLs short. */
export function toCatalogQuery(filters) {
  const query = {}
  if (filters.q) query.q = filters.q
  if (filters.sort && filters.sort !== DEFAULT_SORT) query.sort = filters.sort
  if (filters.priceMin !== null && filters.priceMin !== undefined) query.price_min = String(filters.priceMin)
  if (filters.priceMax !== null && filters.priceMax !== undefined) query.price_max = String(filters.priceMax)
  if (filters.inStock) query.in_stock = 'true'
  if (filters.page && filters.page > 1) query.page = String(filters.page)
  return query
}

/** Filters -> public API parameters. */
export function toApiParams(filters, categorySlug) {
  return {
    q: filters.q || undefined,
    category_slug: categorySlug || undefined,
    price_min: filters.priceMin ?? undefined,
    price_max: filters.priceMax ?? undefined,
    in_stock: filters.inStock || undefined,
    sort: filters.sort,
    page: filters.page,
    page_size: PAGE_SIZE,
  }
}

export function hasActiveFilters(filters) {
  return filters.priceMin !== null || filters.priceMax !== null || filters.inStock
}
