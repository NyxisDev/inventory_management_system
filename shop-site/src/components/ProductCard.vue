<template>
  <article class="product-card card card--interactive">
    <div class="product-card__media">
      <q-img
        v-if="imageUrl"
        :src="imageUrl"
        :ratio="4 / 3"
        :alt="product.name"
        loading="lazy"
        fit="cover"
        no-spinner
        class="product-card__img"
        sizes="(min-width: 1024px) 280px, (min-width: 560px) 45vw, 92vw"
      />
      <div v-else class="product-card__ratio"><NoPhoto /></div>
      <StockBadge class="product-card__badge" :quantity="product.total_quantity" :unit="product.unit" short />
    </div>

    <div class="product-card__body">
      <p v-if="product.category" class="product-card__category">{{ product.category.name }}</p>
      <h3 class="product-card__title">
        <router-link :to="{ name: 'product', params: { slug: product.slug } }" class="product-card__link">
          {{ product.name }}
        </router-link>
      </h3>
      <p class="product-card__sku">{{ t('product.sku') }} {{ product.sku }}</p>

      <div class="product-card__footer">
        <PriceTag :price="product.price" :unit="product.unit" />
        <p class="product-card__stock" :class="{ 'is-out': !inStock }">
          {{ inStock ? t('product.inStock', { qty: formatQty(product.total_quantity, product.unit) }) : t('product.outOfStock') }}
        </p>
      </div>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useFormat } from '@/composables/use-format'
import StockBadge from './StockBadge.vue'
import PriceTag from './PriceTag.vue'
import NoPhoto from './NoPhoto.vue'

const props = defineProps({
  product: { type: Object, required: true },
})

const { t } = useI18n()
const { formatQty, isInStock } = useFormat()

const imageUrl = computed(() => props.product.main_image?.thumb_url || props.product.main_image?.url || '')
const inStock = computed(() => isInStock(props.product.total_quantity))
</script>

<style lang="scss" scoped>
.product-card {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;

  &__media {
    position: relative;
    margin: 8px 8px 0;
    border-radius: 12px;
    overflow: hidden;
    background: $color-panel-raised;
  }

  &__img {
    transition: transform 0.5s ease-in-out;
  }

  &:hover &__img {
    transform: scale(1.04);
  }

  &__ratio {
    position: relative;
    aspect-ratio: 4 / 3;
  }

  &__badge {
    position: absolute;
    top: 10px;
    left: 10px;
    backdrop-filter: blur(6px);
    background-color: rgba(11, 17, 33, 0.78);
  }

  &__body {
    display: flex;
    flex-direction: column;
    flex: 1;
    padding: 16px 18px 18px;
  }

  &__category {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: $color-text-muted;
    margin-bottom: 6px;
  }

  &__title {
    font-family: $font-body;
    font-size: 1rem;
    font-weight: 600;
    line-height: 1.4;
    margin: 0;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    min-height: 2.8em;
  }

  // The whole card is clickable through the title link.
  &__link {
    color: $color-text;

    &::after {
      content: '';
      position: absolute;
      inset: 0;
      border-radius: inherit;
    }

    &:hover {
      color: $color-text;
    }

    &:focus-visible {
      outline: none;

      &::after {
        outline: 2px solid $primary;
        outline-offset: -2px;
        border-radius: $radius-card;
      }
    }
  }

  &__sku {
    margin-top: 4px;
    font-size: 0.8125rem;
    color: $color-text-muted;
  }

  &__footer {
    margin-top: auto;
    padding-top: 14px;
  }

  &__stock {
    margin-top: 4px;
    font-size: 0.8125rem;
    font-weight: 500;
    color: $color-stock-in;

    &.is-out {
      color: $color-stock-out;
    }
  }
}
</style>
