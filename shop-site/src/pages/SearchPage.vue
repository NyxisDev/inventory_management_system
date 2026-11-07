<template>
  <div>
    <PageHeader
      :title="filters.q ? t('search.resultsFor', { q: filters.q }) : t('search.label')"
      :crumbs="[{ label: t('nav.home'), to: '/' }, { label: t('search.submit') }]"
    >
      <div class="search-page__box">
        <SearchBox large :initial="filters.q" />
      </div>
    </PageHeader>

    <section class="section section--page search-page">
      <div class="container">
        <p v-if="!filters.q" class="search-page__hint">{{ t('search.emptyQuery') }}</p>

        <template v-else>
          <div class="search-page__bar">
            <p class="search-page__count" aria-live="polite">
              {{ catalog.searchStatus === 'loading' ? t('common.loading') : t('search.resultsCount', catalog.search.total) }}
            </p>
          </div>

          <div v-if="catalog.searchStatus === 'error'" class="search-page__empty card card--panel">
            <p>{{ t('catalog.loadError') }}</p>
          </div>

          <div
            v-else-if="catalog.searchStatus === 'ready' && catalog.search.items.length === 0"
            class="search-page__empty card card--panel"
          >
            <q-icon :name="mdiMagnifyClose" size="44px" class="text-muted" />
            <h2>{{ t('search.noResults', { q: filters.q }) }}</h2>
            <p>{{ t('search.noResultsHint') }}</p>
            <q-btn unelevated no-caps class="btn btn--primary btn--sm" :to="{ name: 'catalog' }" :label="t('home.viewCatalog')" />
          </div>

          <ProductGrid v-else :products="catalog.search.items" :loading="catalog.searchStatus === 'loading'" />

          <nav v-if="pages > 1" class="search-page__pagination" :aria-label="t('catalog.pagination')">
            <q-pagination
              :model-value="filters.page"
              :max="pages"
              :max-pages="5"
              :to-fn="pageLink"
              direction-links
              color="grey-5"
              active-color="primary"
              active-text-color="white"
              :icon-prev="mdiChevronLeft"
              :icon-next="mdiChevronRight"
            />
          </nav>
        </template>

        <div v-if="!filters.q || (catalog.searchStatus === 'ready' && catalog.search.items.length === 0)" class="search-page__cats">
          <h2 class="search-page__cats-title">{{ t('home.categoriesTitle') }}</h2>
          <div class="search-page__cat-list">
            <router-link
              v-for="cat in catalog.categories"
              :key="cat.slug"
              :to="{ name: 'category', params: { categorySlug: cat.slug } }"
              class="search-page__cat"
            >
              <q-icon :name="categoryIcon(cat.slug)" size="18px" />
              {{ cat.name }}
            </router-link>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { mdiChevronLeft, mdiChevronRight, mdiMagnifyClose } from '@quasar/extras/mdi-v7'
import { useCatalogStore } from '@/stores/catalog'
import { usePageMeta } from '@/composables/use-page-meta'
import { categoryIcon } from '@/composables/category-icons'
import { PAGE_SIZE, parseCatalogQuery, toCatalogQuery } from '@/composables/catalog-query'
import PageHeader from '@/components/PageHeader.vue'
import ProductGrid from '@/components/ProductGrid.vue'
import SearchBox from '@/components/layout/SearchBox.vue'

defineOptions({
  name: 'SearchPage',
  async preFetch({ store, currentRoute }) {
    await useCatalogStore(store).loadSearch(parseCatalogQuery(currentRoute.query))
  },
})

const { t } = useI18n()
const route = useRoute()
const catalog = useCatalogStore()

const filters = computed(() => parseCatalogQuery(route.query))
const pages = computed(() => Math.max(1, Math.ceil(catalog.search.total / (catalog.search.page_size || PAGE_SIZE))))

function pageLink(page) {
  return { query: toCatalogQuery({ ...filters.value, page }) }
}

watch(
  () => route.fullPath,
  () => {
    if (route.name === 'search') catalog.loadSearch(filters.value)
  },
)

usePageMeta(() => ({
  title: filters.value.q ? t('meta.searchTitle', { q: filters.value.q }) : t('meta.searchTitleEmpty'),
  description: t('meta.catalogDescription'),
  path: '/search',
  noindex: true,
}))
</script>

<style lang="scss" scoped>
.search-page {
  padding-top: 40px;

  &__box {
    max-width: 640px;
    margin-top: 24px;
  }

  &__hint {
    color: $color-text-muted;
  }

  &__bar {
    margin-bottom: 20px;
  }

  &__count {
    color: $color-text-muted;
  }

  &__empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    padding: 56px 24px;
    text-align: center;
    color: $color-text-muted;

    h2 {
      font-size: 1.25rem;
    }
  }

  &__pagination {
    display: flex;
    justify-content: center;
    margin-top: 40px;
  }

  &__cats {
    margin-top: 48px;
  }

  &__cats-title {
    font-size: 1.25rem;
    margin-bottom: 16px;
  }

  &__cat-list {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }

  &__cat {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    min-height: 44px;
    padding: 8px 16px;
    border: 1px solid $color-border;
    border-radius: 999px;
    color: $color-text;
    background: $color-panel;

    .q-icon {
      color: $primary;
    }

    &:hover {
      border-color: $primary;
      color: $color-text;
    }
  }
}
</style>
