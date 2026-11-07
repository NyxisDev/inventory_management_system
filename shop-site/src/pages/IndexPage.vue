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
        <div v-reveal class="section-head">
          <div class="section-head__text">
            <p class="eyebrow">{{ t('home.benefitsEyebrow') }}</p>
            <h2 id="benefits-title">{{ t('home.benefitsTitle') }}</h2>
          </div>
        </div>
        <ul class="benefits">
          <li v-for="(benefit, i) in benefits" :key="benefit.title" v-reveal="i * 80" class="benefit card">
            <span class="benefit__icon" aria-hidden="true"><q-icon :name="benefitIcons[i]" size="26px" /></span>
            <h3 class="benefit__title">{{ benefit.title }}</h3>
            <p class="benefit__text">{{ benefit.text }}</p>
          </li>
        </ul>
      </div>
    </section>

    <!-- Categories -->
    <section class="section section--page" aria-labelledby="categories-title">
      <div class="container">
        <div v-reveal class="section-head">
          <div class="section-head__text">
            <p class="eyebrow">{{ t('home.categoriesEyebrow') }}</p>
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
            <p class="eyebrow">{{ t('home.newEyebrow') }}</p>
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
  mdiHardHat,
  mdiMapMarkerMultipleOutline,
  mdiPhone,
  mdiTagOutline,
  mdiWarehouse,
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

const benefitIcons = [mdiWarehouse, mdiTagOutline, mdiMapMarkerMultipleOutline, mdiHardHat]
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
.benefits {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 20px;
  grid-template-columns: 1fr;

  @media (min-width: 640px) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  @media (min-width: 1100px) {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

.benefit {
  padding: 28px 24px;

  &__icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 52px;
    height: 52px;
    margin-bottom: 20px;
    border-radius: 12px;
    border: 1px solid rgba(255, 138, 0, 0.35);
    color: $primary;
    background: $color-primary-soft;
  }

  &__title {
    font-size: 1.1875rem;
    margin-bottom: 10px;
  }

  &__text {
    color: $color-text-muted;
    font-size: 0.9375rem;
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
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 28px;
  padding: 40px 28px;
  border: 1px solid rgba(255, 138, 0, 0.35);
  border-radius: $radius-card;
  overflow: hidden;
  background:
    radial-gradient(circle at 100% 0%, rgba(255, 138, 0, 0.22), transparent 55%),
    linear-gradient(135deg, $color-panel, $color-panel-raised);

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
    flex: none;
  }
}
</style>
