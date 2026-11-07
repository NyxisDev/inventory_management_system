<template>
  <q-page class="admin-page">
    <div class="admin-heading">
      <div>
        <h1>{{ $t('nav.audit') }}</h1>
        <p>{{ $t('audit.subtitle') }}</p>
      </div>
      <q-btn
        class="admin-action"
        flat
        no-caps
        icon="download"
        :disable="!rows.length"
        :label="$t('audit.export')"
        @click="download"
      />
    </div>
    <div class="admin-panel admin-filter-grid q-pa-md q-mb-md">
      <q-input v-model="search" debounce="300" outlined clearable :label="$t('common.search')" />
      <q-select
        v-model="employeeId"
        :options="employeeOptions"
        emit-value
        map-options
        outlined
        clearable
        :label="$t('common.employee')"
      />
      <q-select
        v-model="action"
        :options="actionOptions"
        emit-value
        map-options
        outlined
        clearable
        :label="$t('audit.action')"
      />
      <q-select
        v-model="entity"
        :options="entityOptions"
        emit-value
        map-options
        outlined
        clearable
        :label="$t('audit.entity')"
      />
    </div>
    <q-table
      flat
      wrap-cells
      row-key="id"
      :rows="rows"
      :columns="columns"
      :no-data-label="$t('audit.empty')"
      :rows-per-page-options="[10, 25, 50]"
    >
      <template #body="props">
        <q-tr :props="props">
          <q-td v-for="column in props.cols" :key="column.name" :props="props">
            <q-btn
              v-if="column.name === 'expand'"
              class="admin-action"
              flat
              round
              :icon="props.expand ? 'expand_less' : 'expand_more'"
              :aria-label="$t('common.view')"
              :aria-expanded="props.expand"
              @click="props.expand = !props.expand"
            />
            <span v-else>{{ column.value }}</span>
          </q-td>
        </q-tr>
        <q-tr v-if="props.expand" :props="props">
          <q-td colspan="100%">
            <q-markup-table flat dense wrap-cells>
              <thead>
                <tr>
                  <th scope="col">{{ $t('audit.field') }}</th>
                  <th scope="col">{{ $t('audit.old') }}</th>
                  <th scope="col">{{ $t('audit.new') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="change in props.row.changes" :key="change.field">
                  <th scope="row">{{ change.field }}</th>
                  <td>{{ display(change.old) }}</td>
                  <td>{{ display(change.new) }}</td>
                </tr>
              </tbody>
            </q-markup-table>
          </q-td>
        </q-tr>
      </template>
    </q-table>
  </q-page>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { exportFile } from 'quasar'
import { useDemoActions } from '../composables/use-demo-actions.js'
import { formatDate } from '../lib/inventory-format.js'
import { employeeName, useDemoInventory } from '../stores/demo-inventory.js'

const { t } = useI18n()
const { attempt } = useDemoActions()
const inventory = useDemoInventory()
const search = ref('')
const employeeId = ref(null)
const action = ref(null)
const entity = ref(null)
const makeOptions = (values) => values.map((value) => ({ value, label: t('audit.' + value) }))
const actionOptions = computed(() =>
  makeOptions(['create', 'update', 'delete', 'archive', 'stock_change']),
)
const entityOptions = computed(() =>
  makeOptions(['product', 'category', 'warehouse', 'employee', 'stock']),
)
const employeeOptions = computed(() =>
  inventory.employees.map((item) => ({ value: item.id, label: employeeName(item) })),
)
const nameOf = (id) => employeeName(inventory.employees.find((item) => item.id === id))
const rows = computed(() =>
  inventory.audit.filter((entry) => {
    const query = (search.value || '').trim().toLowerCase()
    return (
      (!employeeId.value || entry.employee_id === employeeId.value) &&
      (!action.value || entry.action === action.value) &&
      (!entity.value || entry.entity === entity.value) &&
      (entry.label + ' ' + nameOf(entry.employee_id)).toLowerCase().includes(query)
    )
  }),
)

const columns = computed(() => [
  { name: 'expand', label: '', field: 'id', align: 'left' },
  {
    name: 'date',
    label: t('common.date'),
    field: (row) => formatDate(row.created_at),
    align: 'left',
  },
  {
    name: 'employee',
    label: t('common.employee'),
    field: (row) => nameOf(row.employee_id),
    align: 'left',
  },
  {
    name: 'action',
    label: t('audit.action'),
    field: (row) => t('audit.' + row.action),
    align: 'left',
  },
  {
    name: 'entity',
    label: t('audit.entity'),
    field: (row) => t('audit.' + row.entity),
    align: 'left',
  },
  { name: 'record', label: t('audit.record'), field: 'label', align: 'left' },
])

function display(value) {
  if (value === null) return '—'
  if (typeof value === 'boolean') return t(value ? 'common.yes' : 'common.no')
  return value
}

function csvCell(value) {
  const text = String(value ?? '')
  const safe = /^[\s\uFEFF]*[=+\-@＝＋－＠]|^[\t\r\n]/u.test(text) ? "'" + text : text
  return '"' + safe.replaceAll('"', '""') + '"'
}

function download() {
  const exportedColumns = columns.value.slice(1)
  const table = [
    exportedColumns.map((column) => column.label),
    ...rows.value.map((row) =>
      exportedColumns.map((column) =>
        typeof column.field === 'function' ? column.field(row) : row[column.field],
      ),
    ),
  ]
  const result = exportFile(
    'budmaster-demo-audit.csv',
    '\uFEFF' + table.map((row) => row.map(csvCell).join(';')).join('\r\n'),
    'text/csv;charset=utf-8;',
  )
  if (result !== true)
    attempt(() => {
      throw new Error('errors.generic')
    })
}
</script>
