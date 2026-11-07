<template>
  <q-page class="admin-page">
    <div class="admin-heading">
      <div>
        <h1>{{ $t('nav.dashboard') }}</h1>
        <p>{{ $t('dashboard.subtitle') }}</p>
      </div>
      <q-btn
        class="admin-action admin-primary"
        color="primary"
        text-color="dark"
        unelevated
        no-caps
        icon="add"
        :label="$t('dashboard.newReceipt')"
        :to="{ name: 'app-stock' }"
      />
    </div>

    <div class="admin-form-grid q-mb-xl">
      <q-card v-for="metric in metrics" :key="metric.key" flat class="admin-panel q-pa-md">
        <div class="row items-center justify-between q-mb-md">
          <span class="admin-muted">{{ $t('dashboard.' + metric.key) }}</span>
          <q-icon :name="metric.icon" size="22px" class="admin-alert" />
        </div>
        <div class="text-h4 text-weight-bold">{{ metric.value }}</div>
      </q-card>
    </div>

    <section class="q-mb-xl">
      <div class="row items-center justify-between q-mb-sm">
        <h2 class="admin-section-title">{{ $t('dashboard.attention') }}</h2>
        <q-btn
          flat
          no-caps
          class="admin-action"
          :label="$t('dashboard.allProducts')"
          :to="{ name: 'app-products', query: { low: '1' } }"
        />
      </div>
      <q-list class="admin-panel" separator v-if="lowProducts.length">
        <q-item
          v-for="product in lowProducts"
          :key="product.id"
          :to="{ name: 'app-product', params: { id: product.id }, query: { tab: 'stock' } }"
        >
          <q-item-section>
            <q-item-label>{{ product.name }}</q-item-label>
            <q-item-label caption>{{ product.sku }}</q-item-label>
          </q-item-section>
          <q-item-section side>
            <span class="admin-alert">{{
              formatQuantity(inventory.totalFor(product.id), product.unit)
            }}</span>
          </q-item-section>
        </q-item>
      </q-list>
      <p v-else class="admin-panel q-pa-md">{{ $t('dashboard.noLow') }}</p>
    </section>

    <section>
      <div class="row items-center justify-between q-mb-sm">
        <h2 class="admin-section-title">{{ $t('dashboard.recent') }}</h2>
        <q-btn
          flat
          no-caps
          class="admin-action"
          :label="$t('dashboard.allMovements')"
          :to="{ name: 'app-movements' }"
        />
      </div>
      <MovementTable :rows="inventory.movements.slice(0, 10)" compact />
    </section>
  </q-page>
</template>

<script setup>
import { computed } from 'vue'
import MovementTable from '../components/MovementTable.vue'
import { formatQuantity } from '../lib/inventory-format.js'
import { useInventory } from '../stores/inventory.js'

const inventory = useInventory()
const lowProducts = computed(() =>
  inventory.availableProducts.filter((product) => inventory.isLow(product.id)),
)
const metrics = computed(() => [
  { key: 'totalProducts', icon: 'inventory_2', value: inventory.availableProducts.length },
  { key: 'lowProducts', icon: 'warning_amber', value: lowProducts.value.length },
  {
    key: 'unpublishedProducts',
    icon: 'visibility_off',
    value: inventory.availableProducts.filter((product) => !product.is_published).length,
  },
])
</script>
