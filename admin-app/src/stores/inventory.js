// Inventory data from the backend API. Same state shape and action names as the former demo
// store, so the pages stay simple: actions are async, call the API and reload what changed.
// Every rule (roles, stock limits, validation) is enforced by the backend; the checks here only
// give faster feedback in forms.
import { defineStore } from 'pinia'
import { api, apiErrorMessage } from '../boot/axios.js'
import { decimalString, parseQuantity, stockOperations } from '../lib/inventory-format.js'
import { useAuthStore } from './auth.js'

const PAGE_SIZE = 100
const MAX_PAGES = 50
const maxStock = 99999999999999n

// Errors shown by useInventoryActions: "api:<detail>" is the backend text, "errors.x" an i18n key
function fail(error) {
  if (error instanceof Error && error.message.startsWith('errors.')) throw error
  const detail = apiErrorMessage(error)
  throw new Error(detail ? 'api:' + detail : 'errors.generic', { cause: error })
}

async function call(request) {
  try {
    const { data } = await request
    return data
  } catch (error) {
    fail(error)
  }
}

async function allPages(url, params = {}) {
  const items = []
  for (let page = 1; page <= MAX_PAGES; page += 1) {
    const data = await call(api.get(url, { params: { ...params, page, page_size: PAGE_SIZE } }))
    items.push(...data.items)
    if (items.length >= data.total || data.items.length === 0) break
  }
  return items
}

function toProduct(item) {
  return {
    id: item.id,
    sku: item.sku,
    name: item.name,
    slug: item.slug,
    category_id: item.category_id,
    unit: item.unit,
    price: item.price,
    is_published: item.is_published,
    is_archived: item.is_archived,
    main_image: item.main_image,
    description: item.description ?? '',
  }
}

function toAudit(entry) {
  return {
    id: entry.id,
    employee_id: entry.employee_id,
    employee_name: entry.employee_name,
    action: entry.action,
    entity: entry.entity_type,
    entity_id: entry.entity_id,
    label: entry.summary,
    changes: entry.changes,
    ip_address: entry.ip_address,
    user_agent: entry.user_agent,
    created_at: entry.created_at,
  }
}

function blankToNull(value) {
  const text = String(value ?? '').trim()
  return text || null
}

export const useInventory = defineStore('inventory', {
  state: () => ({
    categories: [],
    warehouses: [],
    employees: [],
    products: [],
    stock: [],
    movements: [],
    audit: [],
    loaded: false,
    loading: false,
  }),
  getters: {
    isAdmin: () => useAuthStore().isAdmin,
    actorId: () => useAuthStore().employee?.id ?? null,
    availableProducts: (state) => state.products.filter((product) => !product.is_archived),
    activeWarehouses: (state) => state.warehouses.filter((warehouse) => warehouse.is_active),
  },
  actions: {
    // ---------- loading ----------
    async loadAll() {
      this.loading = true
      try {
        await Promise.all([
          this.loadCategories(),
          this.loadWarehouses(),
          this.loadProducts(),
          this.loadStock(),
          this.loadMovements(),
          this.isAdmin ? this.loadEmployees() : Promise.resolve(),
          this.isAdmin ? this.loadAudit() : Promise.resolve(),
        ])
        if (!this.isAdmin) this.employeesFromMovements()
        this.loaded = true
      } finally {
        this.loading = false
      }
    },
    async ensureLoaded() {
      if (!this.loaded && !this.loading) await this.loadAll()
    },
    reset() {
      this.$reset()
    },
    async loadCategories() {
      this.categories = await call(api.get('/categories'))
    },
    async loadWarehouses() {
      this.warehouses = await call(api.get('/warehouses'))
    },
    async loadProducts() {
      const [active, archived] = await Promise.all([
        allPages('/products', { is_archived: false, sort: 'name' }),
        allPages('/products', { is_archived: true, sort: 'name' }),
      ])
      this.products = [...active, ...archived].map(toProduct)
    },
    async loadStock() {
      this.stock = await call(api.get('/stock'))
    },
    async loadMovements() {
      const data = await call(api.get('/stock/movements', { params: { page_size: PAGE_SIZE } }))
      this.movements = data.items
    },
    async loadEmployees() {
      this.employees = await allPages('/employees')
    },
    async loadAudit() {
      const data = await call(api.get('/audit', { params: { page_size: PAGE_SIZE } }))
      this.audit = data.items.map(toAudit)
    },
    // Staff cannot read /employees; names for the history come with the movements
    employeesFromMovements() {
      const known = new Map()
      for (const movement of this.movements) {
        if (movement.employee_id && !known.has(movement.employee_id)) {
          known.set(movement.employee_id, {
            id: movement.employee_id,
            first_name: movement.employee_name ?? '',
            last_name: '',
          })
        }
      }
      this.employees = [...known.values()]
    },
    async afterChange(...parts) {
      const loaders = {
        products: this.loadProducts,
        stock: this.loadStock,
        movements: this.loadMovements,
        categories: this.loadCategories,
        warehouses: this.loadWarehouses,
        employees: this.loadEmployees,
      }
      const tasks = parts.map((part) => loaders[part].call(this))
      if (this.isAdmin) tasks.push(this.loadAudit())
      await Promise.all(tasks)
      if (!this.isAdmin) this.employeesFromMovements()
    },

    // ---------- read helpers (local data) ----------
    stockAt(productId, warehouseId) {
      return this.stock.find(
        (row) => row.product_id === productId && row.warehouse_id === warehouseId,
      )
    },
    totalFor(productId, warehouseId) {
      const total = this.stock
        .filter(
          (row) =>
            row.product_id === productId && (!warehouseId || row.warehouse_id === warehouseId),
        )
        .reduce((sum, row) => sum + parseQuantity(row.quantity), 0n)
      return decimalString(total)
    },
    // Same rule as the backend: a minimum of 0 means "not tracked"
    isLow(productId, warehouseId) {
      return this.stock.some(
        (row) =>
          row.product_id === productId &&
          (!warehouseId || row.warehouse_id === warehouseId) &&
          parseQuantity(row.min_quantity) > 0n &&
          parseQuantity(row.quantity) <= parseQuantity(row.min_quantity),
      )
    },
    async loadProductDetails(id) {
      const data = await call(api.get(`/products/${id}`))
      const product = this.products.find((item) => item.id === id)
      if (product) Object.assign(product, toProduct(data))
      return data
    },
    async productHistory(id) {
      if (!this.isAdmin) return []
      const data = await call(api.get(`/audit/entity/product/${id}`))
      return data.items.map(toAudit)
    },

    // ---------- products ----------
    async saveProduct(draft) {
      const body = {
        sku: String(draft.sku ?? '').trim(),
        name: String(draft.name ?? '').trim(),
        category_id: draft.category_id ?? null,
        unit: draft.unit,
        price: String(draft.price ?? '')
          .trim()
          .replace(',', '.'),
        is_published: Boolean(draft.is_published),
        description: blankToNull(draft.description),
      }
      const saved = draft.id
        ? await call(api.patch(`/products/${draft.id}`, body))
        : await call(api.post('/products', body))
      await this.afterChange('products')
      return saved.id
    },
    async setPublished(id, published) {
      await call(api.patch(`/products/${id}`, { is_published: Boolean(published) }))
      await this.afterChange('products')
    },
    async archiveProduct(id) {
      await call(api.patch(`/products/${id}`, { is_archived: true }))
      await this.afterChange('products')
    },
    async uploadImages(productId, files) {
      const form = new FormData()
      for (const file of files) form.append('files', file)
      await call(api.post(`/products/${productId}/images`, form))
      return this.loadProductDetails(productId)
    },
    async setMainImage(productId, imageId) {
      await call(api.patch(`/products/${productId}/images/${imageId}`, { is_main: true }))
      return this.loadProductDetails(productId)
    },
    async deleteImage(productId, imageId) {
      await call(api.delete(`/products/${productId}/images/${imageId}`))
      return this.loadProductDetails(productId)
    },
    async setMinimum(productId, warehouseId, value) {
      const minimum = parseQuantity(value)
      if (minimum === null) throw new Error('errors.quantity')
      await call(
        api.patch('/stock/min-quantity', {
          product_id: productId,
          warehouse_id: warehouseId,
          min_quantity: decimalString(minimum),
        }),
      )
      await this.afterChange('stock')
    },

    // ---------- stock ----------
    // Local preview of an operation ("will be after"). The backend re-checks everything.
    planStock(
      { operation, product_id, warehouse_id, to_warehouse_id, quantity, comment },
      requireComment = true,
    ) {
      if (!stockOperations.includes(operation)) throw new Error('errors.required')
      const product = this.availableProducts.find((item) => item.id === product_id)
      if (!product) throw new Error('errors.productMissing')
      if (!this.activeWarehouses.some((item) => item.id === warehouse_id))
        throw new Error('errors.warehouseInactive')
      const amount = parseQuantity(quantity)
      if (amount === null || (operation !== 'adjustment' && amount === 0n))
        throw new Error('errors.quantity')
      const note = String(comment ?? '').trim()
      if (note.length > 500) throw new Error('errors.comment')
      if (requireComment && operation === 'adjustment' && !note) throw new Error('errors.comment')

      const current = parseQuantity(this.stockAt(product_id, warehouse_id)?.quantity ?? '0')
      const makeLine = (warehouseId, type, before, after) => {
        if (after < 0n) throw new Error('errors.insufficientStock')
        if (after > maxStock) throw new Error('errors.quantity')
        return {
          warehouse_id: warehouseId,
          type,
          quantity_before: decimalString(before),
          quantity_change: decimalString(after - before),
          quantity_after: decimalString(after),
        }
      }

      if (operation === 'transfer') {
        if (warehouse_id === to_warehouse_id) throw new Error('errors.sameWarehouse')
        if (!this.activeWarehouses.some((item) => item.id === to_warehouse_id))
          throw new Error('errors.warehouseInactive')
        const destination = parseQuantity(
          this.stockAt(product_id, to_warehouse_id)?.quantity ?? '0',
        )
        return [
          makeLine(warehouse_id, 'transfer_out', current, current - amount),
          makeLine(to_warehouse_id, 'transfer_in', destination, destination + amount),
        ]
      }

      const next =
        operation === 'adjustment' ? amount : current + (operation === 'income' ? amount : -amount)
      return [makeLine(warehouse_id, operation, current, next)]
    },
    async recordStock(draft) {
      this.planStock(draft)
      const quantity = decimalString(parseQuantity(draft.quantity))
      const comment = blankToNull(draft.comment)
      const base = { product_id: draft.product_id }
      const requests = {
        income: () =>
          api.post('/stock/income', {
            ...base,
            warehouse_id: draft.warehouse_id,
            quantity,
            comment,
          }),
        outcome: () =>
          api.post('/stock/outcome', {
            ...base,
            warehouse_id: draft.warehouse_id,
            quantity,
            comment,
          }),
        adjustment: () =>
          api.post('/stock/adjustment', {
            ...base,
            warehouse_id: draft.warehouse_id,
            new_quantity: quantity,
            comment,
          }),
        transfer: () =>
          api.post('/stock/transfer', {
            ...base,
            from_warehouse_id: draft.warehouse_id,
            to_warehouse_id: draft.to_warehouse_id,
            quantity,
            comment,
          }),
      }
      await call(requests[draft.operation]())
      await this.afterChange('stock', 'movements')
    },

    // ---------- directories ----------
    async saveCategory(draft) {
      const body = {
        name: String(draft.name ?? '').trim(),
        parent_id: draft.parent_id ?? null,
        sort_order: Number(draft.sort_order) || 0,
      }
      if (draft.id) await call(api.patch(`/categories/${draft.id}`, body))
      else await call(api.post('/categories', body))
      await this.afterChange('categories')
    },
    async deleteCategory(id) {
      await call(api.delete(`/categories/${id}`))
      await this.afterChange('categories')
    },
    async saveWarehouse(draft) {
      const body = {
        name: String(draft.name ?? '').trim(),
        address: blankToNull(draft.address),
        is_active: Boolean(draft.is_active),
        show_on_site: Boolean(draft.show_on_site),
      }
      if (draft.id) await call(api.patch(`/warehouses/${draft.id}`, body))
      else await call(api.post('/warehouses', body))
      await this.afterChange('warehouses')
    },
    async saveEmployee(draft) {
      const password = String(draft.password ?? '')
      if (draft.id) {
        await call(
          api.patch(`/employees/${draft.id}`, {
            first_name: String(draft.first_name ?? '').trim(),
            last_name: String(draft.last_name ?? '').trim(),
            role: draft.role,
            is_active: Boolean(draft.is_active),
          }),
        )
        if (password) {
          await call(api.post(`/employees/${draft.id}/reset-password`, { new_password: password }))
        }
      } else {
        await call(
          api.post('/employees', {
            first_name: String(draft.first_name ?? '').trim(),
            last_name: String(draft.last_name ?? '').trim(),
            username: String(draft.username ?? '').trim(),
            password,
            role: draft.role,
          }),
        )
      }
      await this.afterChange('employees')
    },
  },
})

export function employeeName(employee) {
  return employee ? `${employee.first_name} ${employee.last_name}`.trim() : '—'
}
