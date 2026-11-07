<template>
  <p class="price" :class="`price--${size}`">
    <span class="price__value">{{ formatPrice(price) }}</span>
    <span v-if="unit" class="price__unit">/ {{ unitLabel(unit) }}</span>
  </p>
</template>

<script setup>
import { useFormat } from '@/composables/use-format'

defineProps({
  price: { type: [String, Number], required: true },
  unit: { type: String, default: '' },
  size: { type: String, default: 'md', validator: (v) => ['md', 'lg'].includes(v) },
})

const { formatPrice, unitLabel } = useFormat()
</script>

<style lang="scss" scoped>
.price {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 6px;
  margin: 0;

  &__value {
    font-family: $font-heading;
    font-weight: 700;
    color: $primary;
    letter-spacing: -0.01em;
  }

  &__unit {
    color: $color-text-muted;
    font-size: 0.875rem;
    font-weight: 500;
  }

  &--md .price__value {
    font-size: 1.375rem;
  }

  &--lg .price__value {
    font-size: clamp(2rem, 5vw, 2.5rem);
  }

  &--lg .price__unit {
    font-size: 1rem;
  }
}
</style>
