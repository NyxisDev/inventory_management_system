// In-memory implementation of the public API contract (docs/public-api.md).
// Used only when MOCK_API=true. Responses have the same shape as the backend.
import { categories, products, warehouses } from './catalog-data.js'

const DAY = 24 * 60 * 60 * 1000
// Fixed reference date so server and client render the same "new" order.
const NOW = Date.UTC(2026, 10, 1)

function flatCategories() {
  const out = []
  for (const parent of categories) {
    out.push({ ...parent, parent: null })
    for (const child of parent.children ?? []) out.push({ ...child, parent })
  }
  return out
}

const categoryBySlug = new Map(flatCategories().map((c) => [c.slug, c]))

function sumQuantity(stock) {
  return Object.values(stock).reduce((acc, q) => acc + Number(q), 0)
}

function formatQty(n) {
  return n.toFixed(3)
}

function imagesOf(product) {
  const out = []
  for (let i = 1; i <= product.imageCount; i++) {
    // BASE_URL is '/' normally and the sub-path on GitHub Pages.
    const url = `${import.meta.env.BASE_URL}mock/products/${product.slug}-${i}.svg`
    out.push({ url, thumb_url: url, is_main: i === 1 })
  }
  return out
}

function categoryRef(slug) {
  const c = categoryBySlug.get(slug)
  if (!c) return null
  return {
    name: c.name,
    slug: c.slug,
    parent: c.parent ? { name: c.parent.name, slug: c.parent.slug } : null,
  }
}

function toListItem(product, index) {
  const images = imagesOf(product)
  return {
    id: index + 1,
    slug: product.slug,
    sku: product.sku,
    name: product.name,
    price: product.price,
    unit: product.unit,
    category: categoryRef(product.category),
    main_image: images[0] ?? null,
    total_quantity: formatQty(sumQuantity(product.stock)),
    created_at: new Date(NOW - product.daysAgo * DAY).toISOString(),
  }
}

const listItems = products.map(toListItem)

function slugsUnder(slug) {
  const c = categoryBySlug.get(slug)
  if (!c) return null
  return new Set([c.slug, ...(c.children ?? []).map((child) => child.slug)])
}

function countIn(slug) {
  const slugs = slugsUnder(slug)
  return products.filter((p) => slugs.has(p.category)).length
}

const SORTS = {
  price: (a, b) => Number(a.price) - Number(b.price),
  '-price': (a, b) => Number(b.price) - Number(a.price),
  name: (a, b) => a.name.localeCompare(b.name),
  '-created_at': (a, b) => b.created_at.localeCompare(a.created_at),
}

export function getCategories() {
  return categories.map((parent) => ({
    id: parent.id,
    name: parent.name,
    slug: parent.slug,
    product_count: countIn(parent.slug),
    children: (parent.children ?? []).map((child) => ({
      id: child.id,
      name: child.name,
      slug: child.slug,
      product_count: countIn(child.slug),
      children: [],
    })),
  }))
}

export function getProducts(params = {}) {
  const page = Math.max(1, Number(params.page) || 1)
  const pageSize = Math.min(100, Math.max(1, Number(params.page_size) || 12))
  let items = listItems

  if (params.category_slug) {
    const slugs = slugsUnder(params.category_slug)
    if (slugs === null) {
      const error = new Error('Category not found')
      error.status = 404
      throw error
    }
    items = items.filter((p) => p.category && slugs.has(p.category.slug))
  }
  if (params.q) {
    const q = String(params.q).toLowerCase().trim()
    items = items.filter((p) => p.name.toLowerCase().includes(q) || p.sku.toLowerCase().includes(q))
  }
  if (params.price_min !== undefined && params.price_min !== '') {
    items = items.filter((p) => Number(p.price) >= Number(params.price_min))
  }
  if (params.price_max !== undefined && params.price_max !== '') {
    items = items.filter((p) => Number(p.price) <= Number(params.price_max))
  }
  if (params.in_stock === true || params.in_stock === 'true') {
    items = items.filter((p) => Number(p.total_quantity) > 0)
  }

  const sort = SORTS[params.sort] ?? SORTS['-created_at']
  items = items.slice().sort(sort)

  const start = (page - 1) * pageSize
  return {
    items: items.slice(start, start + pageSize),
    total: items.length,
    page,
    page_size: pageSize,
  }
}

export function getProduct(slug) {
  const index = products.findIndex((p) => p.slug === slug)
  if (index === -1) return null
  const product = products[index]
  return {
    ...toListItem(product, index),
    description: product.description,
    images: imagesOf(product),
    stock: warehouses.map((w) => ({
      warehouse_name: w.name,
      address: w.address,
      quantity: formatQty(Number(product.stock[w.key] ?? 0)),
    })),
  }
}

export function getWarehouses() {
  return warehouses.map(({ name, address }) => ({ name, address }))
}

export function getSitemapEntries() {
  return {
    categories: flatCategories().map((c) => c.slug),
    products: listItems.map((p) => ({ slug: p.slug, updated_at: p.created_at })),
  }
}
