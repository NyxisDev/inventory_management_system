<template>
  <ul class="product-grid" :class="`product-grid--${columns}`">
    <template v-if="loading">
      <li v-for="n in skeletons" :key="`s${n}`"><ProductCardSkeleton /></li>
    </template>
    <template v-else>
      <li v-for="(product, i) in products" :key="product.slug" v-reveal="reveal ? (i % 4) * 70 : 0">
        <ProductCard :product="product" />
      </li>
    </template>
  </ul>
</template>

<script setup>
import ProductCard from './ProductCard.vue'
import ProductCardSkeleton from './ProductCardSkeleton.vue'

defineProps({
  products: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  skeletons: { type: Number, default: 8 },
  columns: { type: Number, default: 4, validator: (v) => [3, 4].includes(v) },
  reveal: { type: Boolean, default: false },
})
</script>

<style lang="scss" scoped>
.product-grid {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;

  @media (min-width: 560px) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  @media (min-width: 900px) {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  &--4 {
    @media (min-width: 1100px) {
      grid-template-columns: repeat(4, minmax(0, 1fr));
    }
  }

  &--3 {
    @media (min-width: 1024px) and (max-width: 1179px) {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }

  > li {
    min-width: 0;
  }
}
</style>
