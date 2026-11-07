<template>
  <NotFoundBlock v-if="catalog.listStatus === 'not-found'" :title="t('notFound.categoryTitle')" />

  <div v-else>
    <PageHeader :title="title" :crumbs="crumbs" :subtitle="t('catalog.resultsCount', catalog.list.total)" />

    <section class="section section--page catalog">
      <div class="container catalog__layout">
        <aside class="catalog__sidebar gt-sm" :aria-label="t('catalog.filters')">
          <CatalogFilters :categories="catalog.categories" :active-slug="categorySlug" :filters="filters" @change="applyFilters" />
        </aside>

        <div ref="resultsRef" class="catalog__results">
          <div class="catalog__toolbar">
            <q-btn
              outline
              no-caps
              class="btn btn--outline btn--sm lt-md"
              :icon="mdiTune"
              :label="t('catalog.showFilters')"
              @click="filtersOpen = true"
            >
              <q-badge v-if="activeCount" color="primary" floating rounded>{{ activeCount }}</q-badge>
            </q-btn>

            <div class="catalog__chips">
              <q-chip
                v-if="filters.priceMin !== null || filters.priceMax !== null"
                removable
                class="catalog__chip"
                :remove-aria-label="t('catalog.resetFilters')"
                @remove="applyFilters({ priceMin: null, priceMax: null, page: 1 })"
              >
                {{ priceChip }}
              </q-chip>
              <q-chip v-if="filters.inStock" removable class="catalog__chip" @remove="applyFilters({ inStock: false, page: 1 })">
                {{ t('catalog.inStockOnly') }}
              </q-chip>
            </div>

            <q-select
              :model-value="filters.sort"
              :options="sortOptions"
              emit-value
              map-options
              outlined
              dense
              options-dense
              class="field-dark catalog__sort"
              :label="t('catalog.sortBy')"
              @update:model-value="(sort) => applyFilters({ sort, page: 1 })"
            />
          </div>

          <div v-if="catalog.listStatus === 'error'" class="catalog__state card card--panel">
            <q-icon :name="mdiAlertCircleOutline" size="40px" color="primary" />
            <p>{{ t('catalog.loadError') }}</p>
            <q-btn unelevated no-caps class="btn btn--primary btn--sm" :label="t('catalog.retry')" @click="reload" />
          </div>

          <div v-else-if="catalog.listStatus === 'ready' && catalog.list.items.length === 0" class="catalog__state card card--panel">
            <q-icon :name="mdiPackageVariant" size="44px" class="text-muted" />
            <h2 class="catalog__state-title">{{ t('catalog.empty') }}</h2>
            <p>{{ t('catalog.emptyHint') }}</p>
            <q-btn
              v-if="activeCount"
              outline
              no-caps
              class="btn btn--outline btn--sm"
              :label="t('catalog.resetFilters')"
              @click="applyFilters({ priceMin: null, priceMax: null, inStock: false, page: 1 })"
            />
          </div>

          <ProductGrid
            v-else
            :products="catalog.list.items"
            :loading="catalog.listStatus === 'loading'"
            :skeletons="6"
            :columns="3"
          />

          <nav v-if="pages > 1" class="catalog__pagination" :aria-label="t('catalog.pagination')">
            <q-pagination
              :model-value="filters.page"
              :max="pages"
              :max-pages="5"
              :to-fn="pageLink"
              direction-links
              boundary-links
              color="grey-5"
              active-color="primary"
              active-text-color="white"
              :icon-prev="mdiChevronLeft"
              :icon-next="mdiChevronRight"
              :icon-first="mdiChevronDoubleLeft"
              :icon-last="mdiChevronDoubleRight"
            />
          </nav>
        </div>
      </div>
    </section>

    <q-dialog v-model="filtersOpen" position="right" full-height>
      <div class="filters-sheet">
        <div class="filters-sheet__head">
          <h2 class="filters-sheet__title">{{ t('catalog.filters') }}</h2>
          <q-btn flat round :icon="mdiClose" :aria-label="t('nav.closeMenu')" @click="filtersOpen = false" />
        </div>
        <div class="filters-sheet__body">
          <CatalogFilters :categories="catalog.categories" :active-slug="categorySlug" :filters="filters" @change="applyFilters" />
        </div>
        <div class="filters-sheet__foot">
          <q-btn
            unelevated
            no-caps
            class="btn btn--primary full-width"
            :loading="catalog.listStatus === 'loading'"
            :label="`${t('catalog.applyFilters')} (${catalog.list.total})`"
            @click="filtersOpen = false"
          />
        </div>
      </div>
    </q-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  mdiAlertCircleOutline,
  mdiChevronDoubleLeft,
  mdiChevronDoubleRight,
  mdiChevronLeft,
  mdiChevronRight,
  mdiClose,
  mdiPackageVariant,
  mdiTune,
} from '@quasar/extras/mdi-v7'
import { useCatalogStore } from '@/stores/catalog'
import { useFormat } from '@/composables/use-format'
import { usePageMeta } from '@/composables/use-page-meta'
import { PAGE_SIZE, parseCatalogQuery, toCatalogQuery } from '@/composables/catalog-query'
import PageHeader from '@/components/PageHeader.vue'
import NotFoundBlock from '@/components/NotFoundBlock.vue'
import ProductGrid from '@/components/ProductGrid.vue'
import CatalogFilters from '@/components/catalog/CatalogFilters.vue'

defineOptions({
  name: 'CatalogPage',
  async preFetch({ store, currentRoute, ssrContext }) {
    const catalog = useCatalogStore(store)
    const slug = String(currentRoute.params.categorySlug ?? '')
    await catalog.loadList(parseCatalogQuery(currentRoute.query), slug)
    if (ssrContext && catalog.listStatus === 'not-found') ssrContext.httpStatus = 404
  },
})

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const catalog = useCatalogStore()
const { formatPrice } = useFormat()

const filtersOpen = ref(false)
const resultsRef = ref(null)

const categorySlug = computed(() => String(route.params.categorySlug ?? ''))
const filters = computed(() => parseCatalogQuery(route.query))
const category = computed(() => (categorySlug.value ? catalog.categoryBySlug(categorySlug.value) : null))
const title = computed(() => category.value?.name ?? t('catalog.title'))
const pages = computed(() => Math.max(1, Math.ceil(catalog.list.total / (catalog.list.page_size || PAGE_SIZE))))

const activeCount = computed(
  () => (filters.value.priceMin !== null || filters.value.priceMax !== null ? 1 : 0) + (filters.value.inStock ? 1 : 0),
)

const priceChip = computed(() => {
  const { priceMin, priceMax } = filters.value
  if (priceMin !== null && priceMax !== null) return `${formatPrice(priceMin)} – ${formatPrice(priceMax)}`
  if (priceMin !== null) return `${t('catalog.priceFrom')} ${formatPrice(priceMin)}`
  return `${t('catalog.priceTo')} ${formatPrice(priceMax)}`
})

const sortOptions = computed(() => [
  { value: '-created_at', label: t('catalog.sort.newest') },
  { value: 'price', label: t('catalog.sort.priceAsc') },
  { value: '-price', label: t('catalog.sort.priceDesc') },
  { value: 'name', label: t('catalog.sort.name') },
])

const crumbs = computed(() => {
  const list = [
    { label: t('nav.home'), to: '/' },
    { label: t('catalog.title'), to: { name: 'catalog' } },
  ]
  const cat = category.value
  if (cat?.parent) list.push({ label: cat.parent.name, to: { name: 'category', params: { categorySlug: cat.parent.slug } } })
  if (cat) list.push({ label: cat.name })
  return list
})

function pageLink(page) {
  return { query: toCatalogQuery({ ...filters.value, page }) }
}

function applyFilters(patch) {
  router.push({ query: toCatalogQuery({ ...filters.value, ...patch }) })
}

function reload() {
  catalog.listKey = ''
  catalog.loadList(filters.value, categorySlug.value)
}

// Same page component, new query or category: load on the client.
watch(
  () => route.fullPath,
  async (to, from) => {
    if (!['catalog', 'category'].includes(route.name)) return
    const pageChanged = new URL(to, 'http://x').searchParams.get('page') !== new URL(from, 'http://x').searchParams.get('page')
    await catalog.loadList(filters.value, categorySlug.value)
    if (pageChanged && resultsRef.value) {
      await nextTick()
      const top = resultsRef.value.getBoundingClientRect().top + window.scrollY - 100
      window.scrollTo({ top, behavior: 'smooth' })
    }
  },
)

usePageMeta(() => {
  const cat = category.value
  const query = toCatalogQuery({ ...filters.value, page: 1, q: '' })
  return {
    title: cat ? cat.name : t('meta.catalogTitle'),
    description: cat
      ? `${cat.name}: ${t('meta.catalogDescription')}`
      : t('meta.catalogDescription'),
    path: route.path + (filters.value.page > 1 ? `?page=${filters.value.page}` : ''),
    // Filtered views are not separate pages for search engines.
    noindex: Object.keys(query).length > 0 || catalog.listStatus === 'not-found',
  }
})
</script>

<style lang="scss" scoped>
.catalog {
  padding-top: 40px;

  &__layout {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 40px;

    @media (min-width: 1024px) {
      grid-template-columns: 260px minmax(0, 1fr);
    }
  }

  &__sidebar {
    position: sticky;
    top: calc(#{$header-height} + 24px);
    align-self: start;
    max-height: calc(100vh - #{$header-height} - 48px);
    overflow-y: auto;
    padding-right: 8px;
    scrollbar-width: thin;
    scrollbar-color: rgba(255, 255, 255, 0.15) transparent;
  }

  &__toolbar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
  }

  &__chips {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    flex: 1;
  }

  &__chip {
    background: $color-primary-soft;
    color: $primary;
    border: 1px solid rgba(255, 138, 0, 0.35);
    font-weight: 500;
  }

  &__sort {
    width: 100%;
    margin-left: auto;

    @media (min-width: 480px) {
      width: 220px;
    }
  }

  &__state {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    padding: 56px 24px;
    text-align: center;
    color: $color-text-muted;
  }

  &__state-title {
    font-size: 1.25rem;
    color: $color-text;
  }

  &__pagination {
    display: flex;
    justify-content: center;
    margin-top: 40px;

    :deep(.q-btn) {
      min-width: 40px;
      min-height: 40px;
      border-radius: $radius-button;
      font-weight: 600;
    }
  }
}

.filters-sheet {
  display: flex;
  flex-direction: column;
  width: min(380px, 92vw);
  height: 100%;
  max-height: 100% !important;
  background: $color-panel;
  border-left: 1px solid $color-border;
  border-radius: 0 !important;

  &__head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 16px 8px 20px;
  }

  &__title {
    font-size: 1.25rem;
  }

  &__body {
    flex: 1;
    overflow-y: auto;
    padding: 8px 20px 20px;
  }

  &__foot {
    padding: 16px 20px;
    border-top: 1px solid $color-border;
  }
}
</style>
