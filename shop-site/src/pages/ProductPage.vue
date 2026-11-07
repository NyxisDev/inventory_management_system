<template>
  <NotFoundBlock
    v-if="catalog.productStatus === 'not-found'"
    :title="t('notFound.productTitle')"
    :text="t('notFound.productText')"
  />

  <div v-else-if="catalog.productStatus === 'error'" class="container product-error">
    <p>{{ t('catalog.loadError') }}</p>
    <q-btn unelevated no-caps class="btn btn--primary btn--sm" :label="t('catalog.retry')" @click="reload" />
  </div>

  <div v-else-if="product" class="product-page">
    <div class="container">
      <q-breadcrumbs class="product-page__crumbs" :aria-label="t('common.breadcrumbs')">
        <template #separator><q-icon :name="mdiChevronRight" size="16px" /></template>
        <q-breadcrumbs-el v-for="(crumb, i) in crumbs" :key="i" :label="crumb.label" :to="crumb.to" />
      </q-breadcrumbs>

      <div class="product-page__top">
        <div class="product-page__gallery">
          <ProductGallery :images="product.images ?? []" :name="product.name" />
        </div>

        <div class="product-page__info">
          <router-link
            v-if="product.category"
            :to="{ name: 'category', params: { categorySlug: product.category.slug } }"
            class="product-page__category"
          >
            <q-icon :name="categoryIcon(product.category.slug)" size="16px" />
            {{ product.category.name }}
          </router-link>

          <h1 class="product-page__title">{{ product.name }}</h1>

          <p class="product-page__sku">
            {{ t('product.sku') }}: <span class="product-page__sku-value">{{ product.sku }}</span>
          </p>

          <div class="product-page__price">
            <PriceTag :price="product.price" :unit="product.unit" size="lg" />
            <StockBadge :quantity="product.total_quantity" :unit="product.unit" />
          </div>

          <WarehouseStock :rows="product.stock ?? []" :total="product.total_quantity" :unit="product.unit" />
        </div>
      </div>

      <div class="product-page__bottom">
        <section class="product-page__description card card--panel" aria-labelledby="desc-title">
          <h2 id="desc-title" class="product-page__h2">{{ t('product.description') }}</h2>
          <!-- eslint-disable-next-line vue/no-v-html -- description is sanitized with DOMPurify (services/sanitize.js) -->
          <div v-if="descriptionHtml" class="rich-text" v-html="descriptionHtml" />
          <p v-else class="text-muted">{{ t('product.noDescription') }}</p>
        </section>

        <aside class="product-page__aside">
          <HowToBuy />
        </aside>
      </div>
    </div>

    <section v-if="catalog.similar.length" class="section section--panel product-page__similar" aria-labelledby="similar-title">
      <div class="container">
        <div class="section-head">
          <h2 id="similar-title">{{ t('product.similar') }}</h2>
          <q-btn
            v-if="product.category"
            outline
            no-caps
            class="btn btn--outline btn--sm"
            :to="{ name: 'category', params: { categorySlug: product.category.slug } }"
            :label="product.category.name"
            :icon-right="mdiArrowRight"
          />
        </div>
        <ProductGrid :products="catalog.similar" class="similar-grid" />
      </div>
    </section>
  </div>

  <div v-else class="container product-page product-page--loading">
    <q-skeleton type="text" width="40%" />
    <div class="product-page__top">
      <q-skeleton class="product-page__skeleton-img" />
      <div>
        <q-skeleton type="text" width="30%" />
        <q-skeleton type="text" height="56px" />
        <q-skeleton type="text" width="50%" height="48px" />
        <q-skeleton height="220px" class="q-mt-lg" style="border-radius: 16px" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { mdiArrowRight, mdiChevronRight } from '@quasar/extras/mdi-v7'
import { useCatalogStore } from '@/stores/catalog'
import { useConfigStore } from '@/stores/config'
import { usePageMeta, absoluteUrl } from '@/composables/use-page-meta'
import { categoryIcon } from '@/composables/category-icons'
import { sanitizeHtml } from '@/services/sanitize'
import NotFoundBlock from '@/components/NotFoundBlock.vue'
import PriceTag from '@/components/PriceTag.vue'
import StockBadge from '@/components/StockBadge.vue'
import ProductGrid from '@/components/ProductGrid.vue'
import ProductGallery from '@/components/product/ProductGallery.vue'
import WarehouseStock from '@/components/product/WarehouseStock.vue'
import HowToBuy from '@/components/product/HowToBuy.vue'

defineOptions({
  name: 'ProductPage',
  async preFetch({ store, currentRoute, ssrContext }) {
    const catalog = useCatalogStore(store)
    await catalog.loadProduct(String(currentRoute.params.slug))
    if (ssrContext && catalog.productStatus === 'not-found') ssrContext.httpStatus = 404
  },
})

const { t } = useI18n()
const route = useRoute()
const catalog = useCatalogStore()
const config = useConfigStore()

const product = computed(() => (catalog.productSlug === route.params.slug ? catalog.product : null))
const descriptionHtml = computed(() => sanitizeHtml(product.value?.description))

const mainImage = computed(() => {
  const images = product.value?.images ?? []
  return images.find((i) => i.is_main) ?? images[0] ?? null
})

const crumbs = computed(() => {
  const p = product.value
  const list = [
    { label: t('nav.home'), to: '/' },
    { label: t('catalog.title'), to: { name: 'catalog' } },
  ]
  if (p?.category?.parent) {
    list.push({ label: p.category.parent.name, to: { name: 'category', params: { categorySlug: p.category.parent.slug } } })
  }
  if (p?.category) list.push({ label: p.category.name, to: { name: 'category', params: { categorySlug: p.category.slug } } })
  return list
})

function plainText(html, max = 160) {
  const text = String(html ?? '')
    .replace(/<[^>]*>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
  return text.length > max ? `${text.slice(0, max - 1)}…` : text
}

function reload() {
  catalog.productSlug = ''
  catalog.loadProduct(String(route.params.slug))
}

// Another product opened from "Similar products": same component, new slug.
watch(
  () => route.params.slug,
  (slug) => {
    if (route.name === 'product' && slug) catalog.loadProduct(String(slug))
  },
)

usePageMeta(() => {
  const p = product.value
  if (!p) {
    return { title: t('notFound.productTitle'), path: route.path, noindex: true }
  }
  const description = plainText(p.description) || `${p.name}. ${t('product.sku')} ${p.sku}.`
  const image = mainImage.value?.url ?? ''
  return {
    title: p.name,
    description,
    path: `/product/${p.slug}`,
    image,
    ogType: 'product',
    jsonLd: {
      '@context': 'https://schema.org',
      '@type': 'Product',
      name: p.name,
      sku: p.sku,
      description,
      image: (p.images ?? []).map((i) => absoluteUrl(config.siteUrl, i.url)),
      category: p.category?.name,
      offers: {
        '@type': 'Offer',
        url: absoluteUrl(config.siteUrl, `/product/${p.slug}`),
        price: String(p.price),
        priceCurrency: config.currency,
        availability: Number(p.total_quantity) > 0 ? 'https://schema.org/InStock' : 'https://schema.org/OutOfStock',
      },
    },
  }
})
</script>

<style lang="scss" scoped>
.product-page {
  padding-top: 28px;

  &__crumbs {
    margin-bottom: 24px;
  }

  &__top {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 32px;

    @media (min-width: 1024px) {
      grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr);
      gap: 48px;
    }
  }

  &__gallery {
    @media (min-width: 1024px) {
      position: sticky;
      top: calc(#{$header-height} + 24px);
      align-self: start;
    }
  }

  &__category {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    border-radius: 999px;
    background: $color-primary-soft;
    color: $primary;
    font-size: 0.8125rem;
    font-weight: 600;

    &:hover {
      color: $color-primary-hover;
    }
  }

  &__title {
    margin-top: 16px;
    font-size: clamp(1.875rem, 4vw, 2.5rem);
    line-height: 1.12;
    letter-spacing: -0.02em;
  }

  &__sku {
    margin-top: 10px;
    color: $color-text-muted;
    font-size: 0.9375rem;
  }

  &__sku-value {
    color: $color-text;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
  }

  &__price {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 12px 20px;
    margin: 24px 0 28px;
    padding: 20px 0;
    border-top: 1px solid $color-border;
    border-bottom: 1px solid $color-border;
  }

  &__bottom {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 24px;
    margin: 48px 0 72px;

    @media (min-width: 1024px) {
      grid-template-columns: minmax(0, 1.6fr) minmax(0, 1fr);
      gap: 32px;
    }
  }

  &__description {
    padding: 28px;
  }

  &__h2 {
    font-size: 1.25rem;
    margin-bottom: 16px;
  }

  &__similar {
    padding-top: 64px;
  }

  &--loading {
    padding-bottom: 72px;
  }

  &__skeleton-img {
    aspect-ratio: 4 / 3;
    height: auto;
    border-radius: $radius-card;
  }
}

.similar-grid :deep(.card) {
  background: $color-page;
}

.product-error {
  padding: 96px 16px;
  text-align: center;
  color: $color-text-muted;

  .q-btn {
    margin-top: 16px;
  }
}

.rich-text {
  color: #cbd5e1;

  :deep(p) {
    margin: 0 0 12px;
  }

  :deep(ul),
  :deep(ol) {
    margin: 0 0 12px;
    padding-left: 20px;
  }

  :deep(li) {
    margin-bottom: 6px;
  }

  :deep(li::marker) {
    color: $primary;
  }

  :deep(h2),
  :deep(h3),
  :deep(h4) {
    margin: 20px 0 8px;
    font-size: 1.125rem;
  }

  :deep(a) {
    color: $color-link;
    text-decoration: underline;
  }

  :deep(table) {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 12px;
  }

  :deep(th),
  :deep(td) {
    padding: 8px 10px;
    border: 1px solid $color-border;
    text-align: left;
  }
}
</style>
