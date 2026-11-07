<template>
  <div>
    <HeroSection
      :products="catalog.productTotal"
      :categories="catalog.flatCategories.length"
      :warehouses="catalog.warehouses.length"
    />

    <!-- Benefits -->
    <section class="section section--panel" aria-labelledby="benefits-title">
      <div class="container">
        <div class="benefits">
          <h2 id="benefits-title" v-reveal class="benefits__title">{{ t('home.benefitsTitle') }}</h2>
          <ul class="benefits__list">
            <li v-for="benefit in benefits" :key="benefit.title" class="benefit">
              <h3 class="benefit__title">{{ benefit.title }}</h3>
              <p class="benefit__text">{{ benefit.text }}</p>
            </li>
          </ul>
        </div>
      </div>
    </section>

    <!-- Categories -->
    <section class="section section--page" aria-labelledby="categories-title">
      <div class="container">
        <div v-reveal class="section-head">
          <div class="section-head__text">
            <h2 id="categories-title">{{ t('home.categoriesTitle') }}</h2>
            <p>{{ t('home.categoriesText') }}</p>
          </div>
          <q-btn
            outline
            no-caps
            class="btn btn--outline"
            :to="{ name: 'catalog' }"
            :label="t('home.allCategories')"
            :icon-right="mdiArrowRight"
          />
        </div>
        <ul class="categories-grid">
          <li v-for="(category, i) in catalog.categories" :key="category.slug" v-reveal="(i % 3) * 80">
            <CategoryTile :category="category" />
          </li>
        </ul>
      </div>
    </section>

    <!-- New arrivals -->
    <section class="section section--panel" aria-labelledby="new-title">
      <div class="container">
        <div v-reveal class="section-head">
          <div class="section-head__text">
            <h2 id="new-title">{{ t('home.newTitle') }}</h2>
            <p>{{ t('home.newText') }}</p>
          </div>
          <q-btn
            outline
            no-caps
            class="btn btn--outline"
            :to="{ name: 'catalog' }"
            :label="t('home.seeAllProducts')"
            :icon-right="mdiArrowRight"
          />
        </div>
        <ProductGrid :products="catalog.newArrivals" :loading="!catalog.homeLoaded" reveal class="new-grid" />
      </div>
    </section>

    <!-- Call to action -->
    <section class="section section--page" aria-labelledby="cta-title">
      <div class="container">
        <div v-reveal class="cta">
          <div class="cta__text">
            <h2 id="cta-title">{{ t('home.ctaTitle') }}</h2>
            <p>{{ t('home.ctaText') }}</p>
          </div>
          <div class="cta__actions">
            <q-btn
              unelevated
              no-caps
              class="btn btn--primary"
              :href="config.phoneHref"
              :icon="mdiPhone"
              :label="config.phone"
            />
            <q-btn outline no-caps class="btn btn--outline" :href="config.emailHref" :icon="mdiEmailOutline" :label="config.email" />
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  mdiArrowRight,
  mdiEmailOutline,
  mdiPhone,
} from '@quasar/extras/mdi-v7'
import { useCatalogStore } from '@/stores/catalog'
import { useConfigStore } from '@/stores/config'
import { usePageMeta } from '@/composables/use-page-meta'
import HeroSection from '@/components/home/HeroSection.vue'
import CategoryTile from '@/components/home/CategoryTile.vue'
import ProductGrid from '@/components/ProductGrid.vue'

defineOptions({
  name: 'IndexPage',
  async preFetch({ store }) {
    const catalog = useCatalogStore(store)
    await Promise.all([catalog.loadHome(), catalog.loadWarehouses()])
  },
})

const { t, tm, rt } = useI18n()
const catalog = useCatalogStore()
const config = useConfigStore()

const benefits = computed(() => tm('home.benefits').map((b) => ({ title: rt(b.title), text: rt(b.text) })))

usePageMeta(() => ({
  title: t('meta.homeTitle'),
  description: t('meta.homeDescription'),
  path: '/',
  jsonLd: {
    '@context': 'https://schema.org',
    '@type': 'HardwareStore',
    name: config.siteName,
    url: config.siteUrl,
    telephone: config.phone,
    email: config.email,
    address: config.address,
    openingHours: config.hours,
  },
}))
</script>

<style lang="scss" scoped>
// Heading on the left, four short points on the right; no card boxes.
.benefits {
  display: grid;
  gap: 32px;

  @media (min-width: 1024px) {
    grid-template-columns: minmax(0, 5fr) minmax(0, 7fr);
    gap: 64px;
    align-items: start;
  }

  &__title {
    max-width: 16ch;
    text-wrap: balance;
  }

  &__list {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 0 40px;

    @media (min-width: 640px) {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }
}

.benefit {
  padding: 20px 0 28px;
  border-top: 1px solid $color-border-strong;

  &:first-child {
    border-top-color: $primary;
  }

  &__title {
    font-size: 1.1875rem;
    margin-bottom: 8px;
  }

  &__text {
    color: $color-text-muted;
    font-size: 0.9375rem;
    max-width: 44ch;
  }
}

.categories-grid {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 20px;
  grid-template-columns: 1fr;

  @media (min-width: 640px) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  @media (min-width: 1024px) {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

// Product cards sit on a panel section, so they use the page colour.
.new-grid :deep(.card) {
  background: $color-page;
}

.cta {
  display: flex;
  flex-direction: column;
  gap: 28px;
  padding: 32px 20px;
  border: 1px solid rgba(255, 138, 0, 0.35);
  border-radius: $radius-card;
  background: $color-panel;

  @media (min-width: 480px) {
    padding: 40px 28px;
  }

  @media (min-width: 900px) {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    padding: 56px;
  }

  &__text {
    max-width: 620px;

    p {
      margin-top: 12px;
      color: #cbd5e1;
    }
  }

  &__actions {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    min-width: 0;

    @media (min-width: 900px) {
      flex: none;
      flex-direction: column;
    }

    .btn {
      max-width: 100%;

      @media (max-width: 479px) {
        width: 100%;
      }

      :deep(.q-btn__content) {
        flex-wrap: nowrap;
        min-width: 0;
      }

      :deep(.block) {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }
  }
}
</style>
