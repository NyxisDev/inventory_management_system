import { defineStore } from 'pinia'
import { useConfigStore } from './config'
import { createCatalogSource, NotFoundError } from '@/services/catalog-source.js'
import { readServerApiUrl } from '@/services/shop-config.js'
import { toApiParams } from '@/composables/catalog-query.js'

// The data source is not part of the state: it holds functions and, on the
// server, the internal API URL. One source per Pinia instance (per request).
const sources = new WeakMap()

function sourceFor(store) {
  // store._p is the Pinia instance the store belongs to (per request on the server).
  const pinia = store._p
  let source = sources.get(pinia)
  if (source) return source
  const config = useConfigStore(pinia)
  const baseURL = import.meta.env.SSR ? readServerApiUrl() : ''
  source = createCatalogSource({ baseURL, mock: config.mock })
  sources.set(pinia, source)
  return source
}

function emptyList() {
  return { items: [], total: 0, page: 1, page_size: 12 }
}

export const useCatalogStore = defineStore('catalog', {
  state: () => ({
    categories: [],
    categoriesLoaded: false,
    warehouses: [],
    warehousesLoaded: false,
    warehousesError: false,

    newArrivals: [],
    productTotal: 0,
    homeLoaded: false,

    list: emptyList(),
    listKey: '',
    listStatus: 'idle', // idle | loading | ready | error | not-found

    product: null,
    productSlug: '',
    productStatus: 'idle', // idle | loading | ready | error | not-found
    similar: [],

    search: emptyList(),
    searchKey: '',
    searchStatus: 'idle', // idle | loading | ready | error
  }),

  getters: {
    flatCategories(state) {
      const out = []
      for (const parent of state.categories) {
        out.push({ ...parent, parent: null })
        for (const child of parent.children ?? []) out.push({ ...child, parent })
      }
      return out
    },
    categoryBySlug() {
      return (slug) => this.flatCategories.find((c) => c.slug === slug) ?? null
    },
  },

  actions: {
    async loadCategories() {
      if (this.categoriesLoaded) return
      try {
        this.categories = await sourceFor(this).getCategories()
        this.categoriesLoaded = true
      } catch {
        this.categories = []
      }
    },

    async loadWarehouses() {
      if (this.warehousesLoaded) return
      try {
        this.warehouses = await sourceFor(this).getWarehouses()
        this.warehousesError = false
      } catch {
        this.warehouses = []
        this.warehousesError = true
      }
      this.warehousesLoaded = true
    },

    async loadHome() {
      if (this.homeLoaded) return
      await this.loadCategories()
      try {
        const latest = await sourceFor(this).getProducts({ sort: '-created_at', page: 1, page_size: 8 })
        this.newArrivals = latest.items
        this.productTotal = latest.total
        this.homeLoaded = true
      } catch {
        this.newArrivals = []
      }
    },

    async loadList(filters, categorySlug = '') {
      const params = toApiParams(filters, categorySlug)
      const key = JSON.stringify(params)
      if (key === this.listKey && this.listStatus === 'ready') return
      this.listKey = key
      this.listStatus = 'loading'
      await this.loadCategories()
      if (categorySlug && this.categoriesLoaded && !this.categoryBySlug(categorySlug)) {
        this.list = emptyList()
        this.listStatus = 'not-found'
        return
      }
      try {
        const data = await sourceFor(this).getProducts(params)
        if (this.listKey !== key) return // a newer request started meanwhile
        this.list = data
        this.listStatus = 'ready'
      } catch (err) {
        if (this.listKey !== key) return
        this.list = emptyList()
        this.listStatus = err instanceof NotFoundError ? 'not-found' : 'error'
      }
    },

    async loadProduct(slug) {
      if (slug === this.productSlug && this.productStatus === 'ready') return
      this.productSlug = slug
      this.productStatus = 'loading'
      try {
        const product = await sourceFor(this).getProduct(slug)
        if (this.productSlug !== slug) return
        if (product === null) {
          this.product = null
          this.similar = []
          this.productStatus = 'not-found'
          return
        }
        this.product = product
        this.productStatus = 'ready'
        await this.loadSimilar(product)
      } catch {
        if (this.productSlug !== slug) return
        this.product = null
        this.productStatus = 'error'
      }
    },

    async loadSimilar(product) {
      this.similar = []
      if (!product.category) return
      const source = sourceFor(this)
      // Same category first; if it is small, fill up from the parent category.
      const slugs = [product.category.slug, product.category.parent?.slug].filter(Boolean)
      const picked = []
      try {
        for (const slug of slugs) {
          const data = await source.getProducts({ category_slug: slug, sort: '-created_at', page: 1, page_size: 8 })
          for (const item of data.items) {
            if (item.slug !== product.slug && !picked.some((p) => p.slug === item.slug)) picked.push(item)
          }
          if (picked.length >= 4) break
        }
        this.similar = picked.slice(0, 4)
      } catch {
        this.similar = []
      }
    },

    async loadSearch(filters) {
      const params = toApiParams(filters, '')
      const key = JSON.stringify(params)
      if (key === this.searchKey && this.searchStatus === 'ready') return
      this.searchKey = key
      if (!filters.q) {
        this.search = emptyList()
        this.searchStatus = 'ready'
        return
      }
      this.searchStatus = 'loading'
      try {
        const data = await sourceFor(this).getProducts(params)
        if (this.searchKey !== key) return
        this.search = data
        this.searchStatus = 'ready'
      } catch {
        if (this.searchKey !== key) return
        this.search = emptyList()
        this.searchStatus = 'error'
      }
    },

    /** Header suggestions. Not kept in the state; the component holds them. */
    async suggest(q) {
      const data = await sourceFor(this).getProducts({ q, sort: 'name', page: 1, page_size: 5 })
      return { items: data.items, total: data.total }
    },
  },
})
