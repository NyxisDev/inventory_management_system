<template>
  <section class="stock card card--panel" aria-labelledby="stock-title">
    <div class="stock__head">
      <h2 id="stock-title" class="stock__title">{{ t('product.availability') }}</h2>
      <StockBadge :quantity="total" :unit="unit" short />
    </div>

    <p v-if="rows.length === 0" class="stock__empty">{{ t('product.noWarehouses') }}</p>

    <table v-else class="stock__table">
      <thead>
        <tr>
          <th scope="col">{{ t('product.warehouse') }}</th>
          <th scope="col" class="num">{{ t('product.quantity') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.warehouse_name" :class="{ 'is-out': !isInStock(row.quantity) }">
          <td>
            <span class="stock__name">
              <span class="stock__dot" aria-hidden="true" />
              {{ row.warehouse_name }}
            </span>
            <span v-if="row.address" class="stock__address">{{ row.address }}</span>
          </td>
          <td class="num stock__qty">
            {{ isInStock(row.quantity) ? formatQty(row.quantity, unit) : t('product.outOfStock') }}
          </td>
        </tr>
      </tbody>
      <tfoot>
        <tr>
          <th scope="row">{{ t('product.total') }}</th>
          <td class="num stock__total">{{ formatQty(total, unit) }}</td>
        </tr>
      </tfoot>
    </table>

    <p class="stock__note">
      <q-icon :name="mdiInformationOutline" size="16px" aria-hidden="true" />
      {{ t('product.stockUpdated') }}
    </p>
  </section>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { mdiInformationOutline } from '@quasar/extras/mdi-v7'
import { useFormat } from '@/composables/use-format'
import StockBadge from '../StockBadge.vue'

defineProps({
  rows: { type: Array, default: () => [] },
  total: { type: [String, Number], default: '0' },
  unit: { type: String, default: '' },
})

const { t } = useI18n()
const { formatQty, isInStock } = useFormat()
</script>

<style lang="scss" scoped>
.stock {
  padding: 24px;

  &__head {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 16px;
  }

  &__title {
    font-size: 1.25rem;
  }

  &__empty {
    color: $color-text-muted;
  }

  &__table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9375rem;

    th,
    td {
      padding: 14px 0;
      text-align: left;
      vertical-align: top;
      border-bottom: 1px solid $color-border;
    }

    thead th {
      padding-top: 0;
      font-size: 0.75rem;
      font-weight: 600;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: $color-text-muted;
    }

    .num {
      text-align: right;
      white-space: nowrap;
      padding-left: 16px;
    }

    tfoot th,
    tfoot td {
      border-bottom: 0;
      padding-bottom: 0;
      font-weight: 600;
    }
  }

  &__name {
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 600;
  }

  &__dot {
    width: 8px;
    height: 8px;
    flex: none;
    border-radius: 50%;
    background: $color-stock-in;
  }

  &__address {
    display: block;
    margin: 2px 0 0 18px;
    font-size: 0.8125rem;
    color: $color-text-muted;
  }

  &__qty {
    font-weight: 600;
    color: $color-stock-in;
  }

  tr.is-out &__dot {
    background: $color-stock-out;
  }

  tr.is-out &__qty {
    font-weight: 500;
    color: $color-stock-out;
  }

  &__total {
    font-family: $font-heading;
    font-size: 1.125rem;
    color: $color-text;
  }

  &__note {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 16px;
    font-size: 0.8125rem;
    color: $color-text-muted;
  }
}
</style>
