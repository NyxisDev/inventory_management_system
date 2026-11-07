<template>
  <q-page class="admin-page">
    <div class="admin-heading">
      <div>
        <h1>{{ $t('nav.stock') }}</h1>
        <p>{{ $t('stock.subtitle') }}</p>
      </div>
      <q-btn
        flat
        no-caps
        class="admin-action"
        icon="history"
        :label="$t('nav.movements')"
        :to="{ name: 'app-movements' }"
      />
    </div>
    <q-tabs
      v-model="draft.operation"
      align="left"
      no-caps
      class="q-mb-md"
      @update:model-value="draft.quantity = ''"
    >
      <q-tab
        v-for="operation in stockOperations"
        :key="operation"
        :name="operation"
        :label="$t('stock.' + operation)"
      />
    </q-tabs>

    <q-form class="admin-panel q-pa-md" @submit="submit">
      <div class="admin-form-grid">
        <q-select
          v-model="draft.product_id"
          :options="productOptions"
          emit-value
          map-options
          outlined
          :label="$t('common.product')"
          :rules="[required]"
        />
        <q-select
          v-model="draft.warehouse_id"
          :options="inventory.activeWarehouses"
          option-label="name"
          option-value="id"
          emit-value
          map-options
          outlined
          :label="$t(draft.operation === 'transfer' ? 'stock.from' : 'common.warehouse')"
          :rules="[required]"
        />
        <q-select
          v-if="draft.operation === 'transfer'"
          v-model="draft.to_warehouse_id"
          :options="destinationOptions"
          option-label="name"
          option-value="id"
          emit-value
          map-options
          outlined
          :label="$t('stock.to')"
          :rules="[required]"
        />
        <q-input
          v-model="draft.quantity"
          outlined
          inputmode="decimal"
          :label="$t(draft.operation === 'adjustment' ? 'stock.newQuantity' : 'common.quantity')"
          :suffix="product?.unit"
          :rules="[validAmount]"
        />
        <q-input
          v-model="draft.comment"
          outlined
          type="textarea"
          maxlength="500"
          :label="$t('common.comment')"
          class="admin-form-wide"
          :rules="draft.operation === 'adjustment' ? [required] : []"
        />
      </div>

      <section class="q-mt-lg q-mb-lg">
        <h2 class="admin-section-title">{{ $t('stock.preview') }}</h2>
        <q-list v-if="preview.lines.length" separator class="q-mt-sm">
          <q-item v-for="line in preview.lines" :key="line.warehouse_id" class="q-px-none">
            <q-item-section>
              <q-item-label>{{ warehouseName(line.warehouse_id) }}</q-item-label>
              <q-item-label caption>
                {{ $t('stock.current') }} {{ formatQuantity(line.quantity_before, product?.unit) }}
              </q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-item-label>{{ formatQuantity(line.quantity_after, product?.unit) }}</q-item-label>
              <q-item-label caption>{{ $t('stock.after') }}</q-item-label>
            </q-item-section>
          </q-item>
        </q-list>
        <p v-else-if="preview.error" class="admin-alert q-mt-sm q-mb-none" role="status">
          {{ preview.error }}
        </p>
        <p v-else class="admin-muted q-mt-sm q-mb-none">{{ $t('stock.previewHelp') }}</p>
      </section>

      <q-btn
        class="admin-action admin-primary"
        type="submit"
        color="primary"
        text-color="dark"
        unelevated
        no-caps
        :label="$t('stock.record')"
      />
    </q-form>
  </q-page>
</template>

<script setup>
import { computed, reactive, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useInventoryActions } from '../composables/use-inventory-actions.js'
import {
  formatQuantity,
  parseQuantity,
  queryValue,
  stockOperations,
} from '../lib/inventory-format.js'
import { useInventory } from '../stores/inventory.js'

const route = useRoute()
const { t, te } = useI18n()
const inventory = useInventory()
const { attempt, confirm } = useInventoryActions()
const draft = reactive({
  operation: 'income',
  product_id: Number(queryValue(route.query.product)) || null,
  warehouse_id: null,
  to_warehouse_id: null,
  quantity: '',
  comment: '',
})
const product = computed(() =>
  inventory.availableProducts.find((item) => item.id === draft.product_id),
)
const productOptions = computed(() =>
  inventory.availableProducts.map((item) => ({
    value: item.id,
    label: item.sku + ' · ' + item.name,
  })),
)
const destinationOptions = computed(() =>
  inventory.activeWarehouses.filter((item) => item.id !== draft.warehouse_id),
)

watch(
  () => draft.warehouse_id,
  (value) => {
    if (value === draft.to_warehouse_id) draft.to_warehouse_id = null
  },
)

const preview = computed(() => {
  if (
    !product.value ||
    !draft.warehouse_id ||
    !draft.quantity ||
    (draft.operation === 'transfer' && !draft.to_warehouse_id)
  )
    return { lines: [], error: '' }
  try {
    return { lines: inventory.planStock(draft, false), error: '' }
  } catch (error) {
    return { lines: [], error: te(error.message) ? t(error.message) : t('errors.generic') }
  }
})

const required = (value) => Boolean(String(value ?? '').trim()) || t('common.required')
const validAmount = (value) => {
  const parsed = parseQuantity(value)
  return (
    (parsed !== null && (parsed > 0n || draft.operation === 'adjustment')) || t('errors.quantity')
  )
}

function warehouseName(id) {
  return inventory.warehouses.find((item) => item.id === id)?.name
}

async function submit() {
  const details = { ...draft }
  if (!(await attempt(() => inventory.planStock(details)))) return

  const save = async () => {
    if (await attempt(() => inventory.recordStock(details), 'stock.recorded')) {
      draft.quantity = ''
      draft.comment = ''
    }
  }
  if (draft.operation === 'income') save()
  else
    confirm(
      t('stock.confirm', { operation: t('stock.' + draft.operation), name: product.value.name }),
      save,
    )
}
</script>
