import { defineStore } from 'pinia'
import {
  decimalString,
  parsePrice,
  parseQuantity,
  stockOperations,
  units,
} from '../lib/inventory-format.js'
import { createDemoData } from './demo-data.js'

const maxStock = 99999999999999n

function nextId(records) {
  return records.reduce((max, item) => Math.max(max, item.id), 0) + 1
}

function requireText(value, maximum) {
  const text = String(value ?? '').trim()
  if (!text || text.length > maximum) throw new Error('errors.required')
  return text
}

export const useDemoInventory = defineStore('demo-inventory', {
  state: () => ({ ...createDemoData(), role: 'admin' }),
  getters: {
    isAdmin: (state) => state.role === 'admin',
    actorId: (state) => (state.role === 'admin' ? 1 : 2),
    availableProducts: (state) => state.products.filter((product) => !product.is_archived),
    activeWarehouses: (state) => state.warehouses.filter((warehouse) => warehouse.is_active),
  },
  actions: {
    setRole(role) {
      if (role === 'admin' || role === 'staff') this.role = role
    },
    requireAdmin() {
      if (!this.isAdmin) throw new Error('errors.adminOnly')
    },
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
    isLow(productId, warehouseId) {
      return this.stock.some(
        (row) =>
          row.product_id === productId &&
          (!warehouseId || row.warehouse_id === warehouseId) &&
          parseQuantity(row.quantity) <= parseQuantity(row.min_quantity),
      )
    },
    logChange(action, entity, entityId, label, before = {}, after = {}) {
      const fields = new Set([...Object.keys(before), ...Object.keys(after)])
      const changes = [...fields]
        .filter((field) => before[field] !== after[field])
        .map((field) => ({ field, old: before[field] ?? null, new: after[field] ?? null }))

      if (changes.length === 0) return

      this.audit.unshift({
        id: nextId(this.audit),
        employee_id: this.actorId,
        action,
        entity,
        entity_id: entityId,
        label,
        changes,
        created_at: new Date().toISOString(),
      })
    },
    saveProduct(draft) {
      const product = this.products.find((item) => item.id === draft.id)
      if (draft.id && !product) throw new Error('errors.productMissing')
      if (product?.is_archived) throw new Error('errors.productArchived')

      const sku = requireText(draft.sku, 64)
      const price = parsePrice(draft.price)
      if (price === null) throw new Error('errors.price')
      if (!units.includes(draft.unit)) throw new Error('errors.required')
      if (
        this.products.some(
          (item) => item.id !== draft.id && item.sku.toLowerCase() === sku.toLowerCase(),
        )
      ) {
        throw new Error('errors.skuExists')
      }
      if (
        draft.category_id !== null &&
        !this.categories.some((item) => item.id === draft.category_id)
      ) {
        throw new Error('errors.required')
      }

      const saved = {
        id: product?.id ?? nextId(this.products),
        sku,
        name: requireText(draft.name, 255),
        category_id: draft.category_id,
        unit: draft.unit,
        price: decimalString(price, 2),
        is_published: Boolean(draft.is_published),
        is_archived: false,
        description: String(draft.description ?? '').trim(),
      }
      this.logChange(product ? 'update' : 'create', 'product', saved.id, saved.name, product, saved)
      if (product) Object.assign(product, saved)
      else this.products.push(saved)
      return saved.id
    },
    setPublished(id, published) {
      const product = this.products.find((item) => item.id === id)
      if (!product) throw new Error('errors.productMissing')
      if (product.is_archived) throw new Error('errors.productArchived')
      const isPublished = Boolean(published)
      this.logChange(
        'update',
        'product',
        id,
        product.name,
        { is_published: product.is_published },
        { is_published: isPublished },
      )
      product.is_published = isPublished
    },
    archiveProduct(id) {
      const product = this.products.find((item) => item.id === id)
      if (!product) throw new Error('errors.productMissing')
      const updated = { is_archived: true, is_published: false }
      this.logChange('archive', 'product', id, product.name, product, { ...product, ...updated })
      Object.assign(product, updated)
    },
    setMinimum(productId, warehouseId, value) {
      const product = this.availableProducts.find((item) => item.id === productId)
      if (!product) throw new Error('errors.productArchived')
      if (!this.activeWarehouses.some((item) => item.id === warehouseId))
        throw new Error('errors.warehouseInactive')
      const minimum = parseQuantity(value)
      if (minimum === null) throw new Error('errors.quantity')

      const row = this.stockAt(productId, warehouseId)
      const previous = row?.min_quantity ?? '0.000'
      const next = decimalString(minimum)
      if (next === previous) return

      if (row) row.min_quantity = next
      else
        this.stock.push({
          product_id: productId,
          warehouse_id: warehouseId,
          quantity: '0.000',
          min_quantity: next,
        })
      this.logChange(
        'update',
        'stock',
        productId + ':' + warehouseId,
        product.name,
        { min_quantity: previous },
        { min_quantity: next },
      )
    },
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
    recordStock(draft) {
      const lines = this.planStock(draft).filter((line) => line.quantity_change !== '0.000')
      if (!lines.length) throw new Error('errors.noStockChange')
      const product = this.products.find((item) => item.id === draft.product_id)
      const timestamp = new Date().toISOString()
      const firstId = nextId(this.movements)
      const group = lines.length === 2 ? String(firstId) : null
      const comment = String(draft.comment ?? '').trim()

      lines.forEach((line, index) => {
        const stock = this.stockAt(product.id, line.warehouse_id)
        if (stock) stock.quantity = line.quantity_after
        else
          this.stock.push({
            product_id: product.id,
            warehouse_id: line.warehouse_id,
            quantity: line.quantity_after,
            min_quantity: '0.000',
          })
        this.movements.unshift({
          id: firstId + index,
          product_id: product.id,
          warehouse_id: line.warehouse_id,
          employee_id: this.actorId,
          type: line.type,
          quantity_change: line.quantity_change,
          quantity_after: line.quantity_after,
          comment,
          transfer_group: group,
          created_at: timestamp,
        })
        this.logChange(
          'stock_change',
          'stock',
          product.id + ':' + line.warehouse_id,
          product.name,
          { quantity: line.quantity_before },
          { quantity: line.quantity_after },
        )
      })
    },
    saveCategory(draft) {
      const current = this.categories.find((item) => item.id === draft.id)
      let parentId = draft.parent_id
      while (parentId !== null) {
        if (parentId === draft.id) throw new Error('errors.categoryParent')
        const parent = this.categories.find((item) => item.id === parentId)
        if (!parent) throw new Error('errors.categoryParent')
        parentId = parent.parent_id
      }
      const sortOrder = Number(draft.sort_order)
      if (!Number.isInteger(sortOrder) || sortOrder < 0 || sortOrder > 2147483647)
        throw new Error('errors.order')
      const saved = {
        id: current?.id ?? nextId(this.categories),
        name: requireText(draft.name, 150),
        parent_id: draft.parent_id,
        sort_order: sortOrder,
      }
      this.logChange(
        current ? 'update' : 'create',
        'category',
        saved.id,
        saved.name,
        current,
        saved,
      )
      if (current) Object.assign(current, saved)
      else this.categories.push(saved)
    },
    deleteCategory(id) {
      if (
        this.categories.some((item) => item.parent_id === id) ||
        this.products.some((item) => item.category_id === id)
      )
        throw new Error('errors.categoryInUse')
      const index = this.categories.findIndex((item) => item.id === id)
      if (index === -1) throw new Error('errors.required')
      const [category] = this.categories.splice(index, 1)
      this.logChange('delete', 'category', id, category.name, category)
    },
    saveWarehouse(draft) {
      this.requireAdmin()
      const current = this.warehouses.find((item) => item.id === draft.id)
      const name = requireText(draft.name, 150)
      if (
        this.warehouses.some(
          (item) => item.id !== draft.id && item.name.toLowerCase() === name.toLowerCase(),
        )
      ) {
        throw new Error('errors.nameExists')
      }
      const saved = {
        id: current?.id ?? nextId(this.warehouses),
        name,
        address: String(draft.address ?? '')
          .trim()
          .slice(0, 255),
        is_active: Boolean(draft.is_active),
        show_on_site: Boolean(draft.show_on_site),
      }
      this.logChange(current ? 'update' : 'create', 'warehouse', saved.id, name, current, saved)
      if (current) Object.assign(current, saved)
      else this.warehouses.push(saved)
    },
    saveEmployee(draft) {
      this.requireAdmin()
      const current = this.employees.find((item) => item.id === draft.id)
      const username = current?.username ?? requireText(draft.username, 50)
      if (draft.role !== 'admin' && draft.role !== 'staff') throw new Error('errors.required')
      if (current?.id === this.actorId && (draft.role !== 'admin' || !draft.is_active)) {
        throw new Error('errors.ownAccount')
      }
      if (
        this.employees.some(
          (item) => item.id !== draft.id && item.username.toLowerCase() === username.toLowerCase(),
        )
      ) {
        throw new Error('errors.usernameExists')
      }
      const saved = {
        id: current?.id ?? nextId(this.employees),
        first_name: requireText(draft.first_name, 100),
        last_name: requireText(draft.last_name, 100),
        username,
        role: draft.role,
        is_active: Boolean(draft.is_active),
      }
      this.logChange(
        current ? 'update' : 'create',
        'employee',
        saved.id,
        employeeName(saved),
        current,
        saved,
      )
      if (current) Object.assign(current, saved)
      else this.employees.push(saved)
    },
  },
})

export function employeeName(employee) {
  return employee ? employee.first_name + ' ' + employee.last_name : '—'
}
