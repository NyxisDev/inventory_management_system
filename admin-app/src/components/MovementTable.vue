<template>
  <q-table
    flat
    wrap-cells
    row-key="id"
    :rows="rows"
    :columns="columns"
    :no-data-label="$t('movements.empty')"
    :rows-per-page-options="[10, 25, 50]"
    :hide-bottom="compact"
  >
    <template #body-cell-quantity_change="props">
      <q-td :props="props">
        <span :class="props.row.quantity_change.startsWith('-') ? 'admin-alert' : ''">
          {{ props.value }}
        </span>
      </q-td>
    </template>
  </q-table>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { formatDate, formatQuantity } from '../lib/inventory-format.js'
import { employeeName, useInventory } from '../stores/inventory.js'

defineProps({ rows: { type: Array, required: true }, compact: Boolean })
const { t } = useI18n()
const inventory = useInventory()
const columns = computed(() => [
  {
    name: 'created_at',
    label: t('common.date'),
    field: 'created_at',
    format: formatDate,
    align: 'left',
  },
  {
    name: 'product',
    label: t('common.product'),
    field: (row) => inventory.products.find((product) => product.id === row.product_id)?.name,
    align: 'left',
  },
  {
    name: 'warehouse',
    label: t('common.warehouse'),
    field: (row) =>
      inventory.warehouses.find((warehouse) => warehouse.id === row.warehouse_id)?.name,
    align: 'left',
  },
  { name: 'type', label: t('common.type'), field: (row) => t('stock.' + row.type), align: 'left' },
  {
    name: 'quantity_change',
    label: t('stock.quantityChange'),
    field: 'quantity_change',
    format: (value) => (value.startsWith('-') ? '' : '+') + formatQuantity(value),
  },
  {
    name: 'quantity_after',
    label: t('stock.postBalance'),
    field: 'quantity_after',
    format: (value) => formatQuantity(value),
  },
  {
    name: 'employee',
    label: t('common.employee'),
    field: (row) =>
      employeeName(inventory.employees.find((employee) => employee.id === row.employee_id)),
    align: 'left',
  },
  { name: 'comment', label: t('common.comment'), field: 'comment', align: 'left' },
])
</script>
