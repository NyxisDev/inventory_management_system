<template>
  <q-page class="admin-page">
    <div class="admin-heading">
      <div>
        <h1>{{ $t('nav.products') }}</h1>
        <p>{{ $t('products.subtitle') }}</p>
      </div>
      <q-btn
        class="admin-action admin-primary"
        color="primary"
        text-color="dark"
        unelevated
        no-caps
        icon="add"
        :label="$t('products.add')"
        :to="{ name: 'app-product-new' }"
      />
    </div>

    <div class="admin-panel q-pa-md q-mb-md">
      <div class="admin-filter-grid">
        <q-input
          :model-value="search"
          debounce="300"
          outlined
          clearable
          :label="$t('products.search')"
          @update:model-value="setFilter('q', $event)"
        />
        <q-select
          :model-value="categoryId"
          :options="inventory.categories"
          option-value="id"
          option-label="name"
          emit-value
          map-options
          outlined
          clearable
          :label="$t('common.category')"
          @update:model-value="setFilter('category', $event)"
        />
        <q-select
          :model-value="warehouseId"
          :options="inventory.warehouses"
          option-value="id"
          option-label="name"
          emit-value
          map-options
          outlined
          clearable
          :label="$t('common.warehouse')"
          @update:model-value="setFilter('warehouse', $event)"
        />
        <q-select
          :model-value="visibility"
          :options="visibilityOptions"
          emit-value
          map-options
          outlined
          :label="$t('products.visibility')"
          @update:model-value="setFilter('status', $event)"
        />
      </div>
      <div class="row items-center justify-between q-mt-sm">
        <q-checkbox
          :model-value="lowOnly"
          :label="$t('products.onlyLow')"
          @update:model-value="setFilter('low', $event ? '1' : '')"
        />
        <q-btn
          flat
          no-caps
          class="admin-action"
          :label="$t('common.resetFilters')"
          :to="{ name: 'app-products' }"
        />
      </div>
    </div>

    <q-table
      flat
      wrap-cells
      row-key="id"
      :rows="rows"
      :columns="columns"
      :grid="quasar.screen.lt.sm"
      :pagination="pagination"
      :rows-per-page-options="[10, 25, 50]"
      :no-data-label="$t('products.empty')"
      @update:pagination="setPagination"
    >
      <template #body-cell-total="props">
        <q-td :props="props">
          <span :class="{ 'admin-alert text-weight-bold': props.row.low }">{{
            formatQuantity(props.value, props.row.unit)
          }}</span>
        </q-td>
      </template>
      <template #body-cell-is_published="props">
        <q-td :props="props">
          <q-toggle
            v-if="!props.row.is_archived"
            :model-value="props.row.is_published"
            :aria-label="$t('common.published') + ' · ' + props.row.name"
            @update:model-value="publish(props.row, $event)"
          />
          <span v-else class="admin-muted">{{ $t('common.archived') }}</span>
        </q-td>
      </template>
      <template #body-cell-actions="props">
        <q-td :props="props">
          <q-btn
            flat
            no-caps
            class="admin-action"
            :label="$t(props.row.is_archived ? 'common.view' : 'common.edit')"
            :to="productLink(props.row.id)"
          />
          <q-btn
            v-if="!props.row.is_archived"
            flat
            no-caps
            class="admin-action admin-alert"
            :label="$t('products.archive')"
            @click="archive(props.row)"
          />
        </q-td>
      </template>
      <template #item="props">
        <div class="col-12 q-pa-sm">
          <q-card flat class="admin-panel q-pa-md">
            <div class="text-weight-bold">{{ props.row.name }}</div>
            <div class="admin-muted text-caption">
              {{ props.row.sku }} · {{ props.row.category || $t('common.none') }}
            </div>
            <div class="row justify-between q-mt-sm">
              <span>{{ formatPrice(props.row.price) }}</span>
              <span :class="{ 'admin-alert': props.row.low }">{{
                formatQuantity(props.row.total, props.row.unit)
              }}</span>
            </div>
            <div class="row items-center justify-between q-mt-sm">
              <q-toggle
                v-if="!props.row.is_archived"
                :model-value="props.row.is_published"
                :label="$t('common.published')"
                @update:model-value="publish(props.row, $event)"
              />
              <span v-else class="admin-muted">{{ $t('common.archived') }}</span>
              <q-btn
                flat
                no-caps
                class="admin-action"
                :label="$t(props.row.is_archived ? 'common.view' : 'common.edit')"
                :to="productLink(props.row.id)"
              />
              <q-btn
                v-if="!props.row.is_archived"
                flat
                no-caps
                class="admin-action admin-alert"
                :label="$t('products.archive')"
                @click="archive(props.row)"
              />
            </div>
          </q-card>
        </div>
      </template>
    </q-table>
  </q-page>
</template>

<script setup>
import { computed } from 'vue'
import { useQuasar } from 'quasar'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useInventory } from '../stores/inventory.js'
import { useInventoryActions } from '../composables/use-inventory-actions.js'
import { compareDecimal, formatPrice, formatQuantity, queryValue } from '../lib/inventory-format.js'

const quasar = useQuasar()
const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const inventory = useInventory()
const { attempt, confirm } = useInventoryActions()
const statuses = ['all', 'published', 'unpublished', 'archived']
const sortFields = ['name', 'sku', 'category', 'price', 'total']
const visibilityOptions = computed(() =>
  statuses.map((value) => ({ value, label: t('common.' + value) })),
)
const search = computed(() => queryValue(route.query.q))
const categoryId = computed(() => Number(queryValue(route.query.category)) || null)
const warehouseId = computed(() => Number(queryValue(route.query.warehouse)) || null)
const visibility = computed(() =>
  statuses.includes(route.query.status) ? route.query.status : 'all',
)
const lowOnly = computed(() => route.query.low === '1')

const rows = computed(() => {
  const query = search.value.trim().toLowerCase()
  return inventory.products
    .filter((product) => {
      if ((visibility.value === 'archived') !== product.is_archived) return false
      if (visibility.value === 'published' && !product.is_published) return false
      if (visibility.value === 'unpublished' && product.is_published) return false
      if (categoryId.value && product.category_id !== categoryId.value) return false
      if (warehouseId.value && !inventory.stockAt(product.id, warehouseId.value)) return false
      if (lowOnly.value && !inventory.isLow(product.id, warehouseId.value)) return false
      return (product.name + ' ' + product.sku).toLowerCase().includes(query)
    })
    .map((product) => ({
      ...product,
      category: inventory.categories.find((category) => category.id === product.category_id)?.name,
      total: inventory.totalFor(product.id, warehouseId.value),
      low: inventory.isLow(product.id, warehouseId.value),
    }))
})

const columns = computed(() => [
  { name: 'sku', field: 'sku', label: t('common.sku'), align: 'left', sortable: true },
  { name: 'name', field: 'name', label: t('common.name'), align: 'left', sortable: true },
  {
    name: 'category',
    field: 'category',
    label: t('common.category'),
    align: 'left',
    sortable: true,
  },
  {
    name: 'price',
    field: 'price',
    label: t('common.price'),
    sortable: true,
    sort: compareDecimal,
    format: formatPrice,
  },
  {
    name: 'total',
    field: 'total',
    label: t('common.quantity'),
    sortable: true,
    sort: compareDecimal,
  },
  { name: 'is_published', field: 'is_published', label: t('common.published') },
  { name: 'actions', field: 'id', label: t('common.actions') },
])

const pagination = computed(() => {
  const size = Number(queryValue(route.query.size))
  const rowsPerPage = [10, 25, 50].includes(size) ? size : 10
  const requestedPage = Number(queryValue(route.query.page))
  return {
    page:
      Number.isSafeInteger(requestedPage) && requestedPage > 0
        ? Math.min(requestedPage, Math.max(1, Math.ceil(rows.value.length / rowsPerPage)))
        : 1,
    rowsPerPage,
    sortBy: sortFields.includes(route.query.sort) ? route.query.sort : 'name',
    descending: route.query.desc === '1',
  }
})

function setFilter(key, value) {
  router.replace({
    query: { ...route.query, [key]: value ? String(value) : undefined, page: undefined },
  })
}

function setPagination(value) {
  router.replace({
    query: {
      ...route.query,
      page: String(value.page),
      size: String(value.rowsPerPage),
      sort: value.sortBy,
      desc: value.descending ? '1' : undefined,
    },
  })
}

function productLink(id) {
  return { name: 'app-product', params: { id } }
}

function publish(product, value) {
  attempt(() => inventory.setPublished(product.id, value), 'common.saved')
}

function archive(product) {
  confirm(t('products.archivePrompt', { name: product.name }), () => {
    attempt(() => inventory.archiveProduct(product.id), 'common.saved')
  })
}
</script>
