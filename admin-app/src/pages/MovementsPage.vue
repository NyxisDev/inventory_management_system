<template>
  <q-page class="admin-page">
    <div class="admin-heading">
      <div>
        <h1>{{ $t('nav.movements') }}</h1>
        <p>{{ $t('movements.subtitle') }}</p>
      </div>
    </div>
    <div class="admin-panel admin-filter-grid q-pa-md q-mb-md">
      <q-select
        v-model="filters.product"
        :options="inventory.products"
        option-value="id"
        option-label="name"
        emit-value
        map-options
        outlined
        clearable
        :label="$t('common.product')"
      />
      <q-select
        v-model="filters.warehouse"
        :options="inventory.warehouses"
        option-value="id"
        option-label="name"
        emit-value
        map-options
        outlined
        clearable
        :label="$t('common.warehouse')"
      />
      <q-select
        v-model="filters.type"
        :options="typeOptions"
        emit-value
        map-options
        outlined
        clearable
        :label="$t('common.type')"
      />
      <q-select
        v-model="filters.employee"
        :options="employeeOptions"
        emit-value
        map-options
        outlined
        clearable
        :label="$t('common.employee')"
      />
      <q-input
        v-model="filters.from"
        type="date"
        outlined
        stack-label
        :label="$t('common.startDate')"
      />
      <q-input
        v-model="filters.to"
        type="date"
        outlined
        stack-label
        :label="$t('common.endDate')"
      />
    </div>
    <p v-if="invalidDates" class="admin-alert" role="status">{{ $t('errors.dateRange') }}</p>
    <MovementTable :rows="rows" />
  </q-page>
</template>

<script setup>
import { computed, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import MovementTable from '../components/MovementTable.vue'
import { dateKey, movementTypes } from '../lib/inventory-format.js'
import { employeeName, useInventory } from '../stores/inventory.js'

const inventory = useInventory()
const { t } = useI18n()
const filters = reactive({
  product: null,
  warehouse: null,
  employee: null,
  type: null,
  from: '',
  to: '',
})
const typeOptions = computed(() =>
  movementTypes.map((value) => ({ value, label: t('stock.' + value) })),
)
const employeeOptions = computed(() =>
  inventory.employees.map((item) => ({ value: item.id, label: employeeName(item) })),
)
const invalidDates = computed(() => filters.from && filters.to && filters.from > filters.to)
const rows = computed(() =>
  invalidDates.value
    ? []
    : inventory.movements.filter((item) => {
        const date = dateKey(new Date(item.created_at))
        return (
          (!filters.product || item.product_id === filters.product) &&
          (!filters.warehouse || item.warehouse_id === filters.warehouse) &&
          (!filters.employee || item.employee_id === filters.employee) &&
          (!filters.type || item.type === filters.type) &&
          (!filters.from || date >= filters.from) &&
          (!filters.to || date <= filters.to)
        )
      }),
)
</script>
