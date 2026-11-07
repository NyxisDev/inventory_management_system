<template>
  <q-page class="admin-page">
    <div class="admin-heading">
      <div>
        <h1>{{ product?.name || $t(isNew ? 'products.add' : 'products.edit') }}</h1>
        <p v-if="product">{{ product.sku }}</p>
      </div>
      <q-btn
        flat
        no-caps
        class="admin-action"
        icon="arrow_back"
        :label="$t('common.back')"
        :to="{ name: 'demo-products' }"
      />
    </div>

    <p v-if="!isNew && !product" class="admin-panel q-pa-md">{{ $t('errors.productMissing') }}</p>
    <template v-else>
      <q-banner v-if="product?.is_archived" class="admin-panel q-mb-md">{{
        $t('products.archivedNote')
      }}</q-banner>
      <q-tabs
        v-if="product"
        :model-value="activeTab"
        align="left"
        no-caps
        class="q-mb-md"
        @update:model-value="setTab"
      >
        <q-tab name="details" :label="$t('products.details')" />
        <q-tab name="photos" :label="$t('products.photos')" />
        <q-tab name="stock" :label="$t('products.stock')" />
        <q-tab name="history" :label="$t('products.history')" />
      </q-tabs>

      <q-form
        v-if="activeTab === 'details'"
        class="admin-panel admin-form-grid q-pa-md"
        @submit="save"
      >
        <q-input
          v-model="draft.name"
          :readonly="product?.is_archived"
          outlined
          :label="$t('common.name')"
          maxlength="255"
          :rules="[required]"
        />
        <q-input
          v-model="draft.sku"
          :readonly="product?.is_archived"
          outlined
          :label="$t('common.sku')"
          maxlength="64"
          :rules="[required]"
        />
        <q-select
          v-model="draft.category_id"
          :readonly="product?.is_archived"
          :options="inventory.categories"
          option-label="name"
          option-value="id"
          emit-value
          map-options
          clearable
          outlined
          :label="$t('common.category')"
        />
        <q-select
          v-model="draft.unit"
          :readonly="product?.is_archived || hasStockHistory"
          :options="units"
          outlined
          :label="$t('common.unit')"
          :rules="[required]"
        />
        <q-input
          v-model="draft.price"
          :readonly="product?.is_archived"
          outlined
          inputmode="decimal"
          :label="$t('common.price') + ' (€)'"
          :rules="[validPrice]"
        />
        <q-toggle
          v-model="draft.is_published"
          :disable="product?.is_archived"
          :label="$t('common.published')"
        />
        <q-input
          v-model="draft.description"
          :readonly="product?.is_archived"
          outlined
          type="textarea"
          class="admin-form-wide"
          :label="$t('common.description')"
          maxlength="2000"
        />
        <div v-if="!product?.is_archived" class="admin-form-wide">
          <q-btn
            class="admin-action admin-primary"
            type="submit"
            color="primary"
            text-color="dark"
            unelevated
            no-caps
            :label="$t('common.save')"
          />
        </div>
      </q-form>

      <div v-if="activeTab === 'photos'" class="admin-panel q-pa-lg">
        <q-icon name="image" size="36px" class="admin-muted" />
        <p class="q-mt-md q-mb-none">{{ $t('products.photosNote') }}</p>
      </div>

      <div v-if="activeTab === 'stock'" class="admin-panel q-pa-md">
        <q-list separator>
          <q-item
            v-for="warehouse in inventory.warehouses"
            :key="warehouse.id"
            class="stock-row q-px-none q-py-md"
          >
            <q-item-section>
              <q-item-label>{{ warehouse.name }}</q-item-label>
              <q-item-label caption>{{
                formatQuantity(
                  inventory.stockAt(product.id, warehouse.id)?.quantity ?? '0',
                  product.unit,
                )
              }}</q-item-label>
            </q-item-section>
            <q-item-section side v-if="!product.is_archived && warehouse.is_active">
              <q-form class="minimum-form" @submit="saveMinimum(warehouse.id)">
                <q-input
                  v-model="minimums[warehouse.id]"
                  outlined
                  inputmode="decimal"
                  :label="$t('products.minimum')"
                  :aria-label="$t('products.minimumFor', { name: warehouse.name })"
                  :rules="[validQuantity]"
                  hide-bottom-space
                />
                <q-btn flat no-caps class="admin-action" type="submit" :label="$t('common.save')" />
              </q-form>
            </q-item-section>
          </q-item>
        </q-list>
        <q-btn
          v-if="!product.is_archived"
          class="admin-action q-mt-md"
          color="primary"
          text-color="dark"
          unelevated
          no-caps
          :label="$t('products.openStock')"
          :to="{ name: 'demo-stock', query: { product: String(product.id) } }"
        />
      </div>

      <MovementTable v-if="activeTab === 'history'" :rows="history" />
    </template>
  </q-page>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { onBeforeRouteLeave, onBeforeRouteUpdate, useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import MovementTable from '../components/MovementTable.vue'
import { useDemoActions } from '../composables/use-demo-actions.js'
import { formatQuantity, parsePrice, parseQuantity, units } from '../lib/inventory-format.js'
import { useDemoInventory } from '../stores/demo-inventory.js'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const inventory = useDemoInventory()
const { attempt } = useDemoActions()
const tabs = ['details', 'photos', 'stock', 'history']
const isNew = computed(() => route.name === 'demo-product-new')
const product = computed(() =>
  isNew.value ? undefined : inventory.products.find((item) => item.id === Number(route.params.id)),
)
const activeTab = computed(() =>
  product.value && tabs.includes(route.query.tab) ? route.query.tab : 'details',
)
const history = computed(() =>
  inventory.movements.filter((movement) => movement.product_id === product.value?.id),
)
const hasStockHistory = computed(
  () =>
    history.value.length > 0 || inventory.stock.some((row) => row.product_id === product.value?.id),
)
const draft = reactive({})
const minimums = reactive({})
const snapshot = ref('')

watch(
  product,
  (value) => {
    Object.assign(
      draft,
      value || {
        id: null,
        sku: '',
        name: '',
        price: '',
        unit: 'pcs',
        category_id: null,
        is_published: false,
        description: '',
      },
    )
    for (const warehouse of inventory.warehouses)
      minimums[warehouse.id] = inventory.stockAt(value?.id, warehouse.id)?.min_quantity ?? '0'
    snapshot.value = JSON.stringify(draft)
  },
  { immediate: true },
)

const required = (value) => Boolean(String(value ?? '').trim()) || t('common.required')
const validPrice = (value) => parsePrice(value) !== null || t('errors.price')
const validQuantity = (value) => parseQuantity(value) !== null || t('errors.quantity')
const allowLeave = () =>
  JSON.stringify(draft) === snapshot.value || window.confirm(t('products.leave'))

onBeforeRouteLeave(allowLeave)
onBeforeRouteUpdate(
  (to, from) => (to.name === from.name && to.params.id === from.params.id) || allowLeave(),
)

function setTab(tab) {
  router.replace({ query: { ...route.query, tab } })
}

function save() {
  const id = attempt(() => inventory.saveProduct(draft), 'common.saved')
  if (id === null) return
  snapshot.value = JSON.stringify(draft)
  router.replace({ name: 'demo-product', params: { id } })
}

function saveMinimum(warehouseId) {
  attempt(
    () => inventory.setMinimum(product.value.id, warehouseId, minimums[warehouseId]),
    'common.saved',
  )
}
</script>

<style scoped>
.minimum-form {
  display: flex;
  align-items: center;
  gap: 8px;
}

@media (max-width: 599px) {
  .stock-row {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .stock-row :deep(.q-item__section--side) {
    padding: 0;
  }
}
</style>
