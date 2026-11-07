<template>
  <span class="stock-badge" :class="inStock ? 'stock-badge--in' : 'stock-badge--out'">
    <span class="stock-badge__dot" aria-hidden="true" />
    <template v-if="inStock">
      {{ short ? t('product.inStockShort') : t('product.inStock', { qty: formatQty(quantity, unit) }) }}
    </template>
    <template v-else>{{ t('product.outOfStock') }}</template>
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useFormat } from '@/composables/use-format'

const props = defineProps({
  quantity: { type: [String, Number], default: '0' },
  unit: { type: String, default: '' },
  short: { type: Boolean, default: false },
})

const { t } = useI18n()
const { formatQty, isInStock } = useFormat()
const inStock = computed(() => isInStock(props.quantity))
</script>

<style lang="scss" scoped>
.stock-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 0.8125rem;
  font-weight: 600;
  line-height: 1.4;
  white-space: nowrap;

  &__dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: currentColor;
    flex: none;
  }

  &--in {
    color: $color-stock-in;
    background: $color-stock-in-bg;

    .stock-badge__dot {
      box-shadow: 0 0 0 3px rgba(74, 222, 128, 0.18);
    }
  }

  &--out {
    color: $color-stock-out;
    background: $color-stock-out-bg;
  }
}
</style>
