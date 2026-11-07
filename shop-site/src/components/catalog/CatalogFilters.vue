<template>
  <div class="filters">
    <section class="filters__group" aria-labelledby="f-categories">
      <h2 id="f-categories" class="filters__title">{{ t('catalog.categories') }}</h2>
      <ul class="filters__tree">
        <li>
          <router-link
            :to="{ name: 'catalog', query: carryQuery }"
            class="filters__cat"
            :class="{ 'is-active': !activeSlug }"
            :aria-current="!activeSlug ? 'page' : undefined"
          >
            <span>{{ t('catalog.allProducts') }}</span>
          </router-link>
        </li>
        <li v-for="cat in categories" :key="cat.slug">
          <router-link
            :to="{ name: 'category', params: { categorySlug: cat.slug }, query: carryQuery }"
            class="filters__cat"
            :class="{ 'is-active': activeSlug === cat.slug, 'is-open': isOpen(cat) }"
            :aria-current="activeSlug === cat.slug ? 'page' : undefined"
          >
            <q-icon :name="categoryIcon(cat.slug)" size="18px" class="filters__cat-icon" />
            <span>{{ cat.name }}</span>
            <span v-if="cat.product_count !== undefined" class="filters__count">{{ cat.product_count }}</span>
          </router-link>
          <ul v-if="cat.children?.length && isOpen(cat)" class="filters__sub">
            <li v-for="child in cat.children" :key="child.slug">
              <router-link
                :to="{ name: 'category', params: { categorySlug: child.slug }, query: carryQuery }"
                class="filters__cat filters__cat--child"
                :class="{ 'is-active': activeSlug === child.slug }"
                :aria-current="activeSlug === child.slug ? 'page' : undefined"
              >
                <span>{{ child.name }}</span>
                <span v-if="child.product_count !== undefined" class="filters__count">{{ child.product_count }}</span>
              </router-link>
            </li>
          </ul>
        </li>
      </ul>
    </section>

    <section class="filters__group" aria-labelledby="f-price">
      <h2 id="f-price" class="filters__title">{{ t('catalog.price') }}</h2>
      <q-range
        v-model="range"
        :min="0"
        :max="sliderMax"
        :step="1"
        color="primary"
        track-color="grey-8"
        class="filters__range"
        :aria-label="t('catalog.priceRange')"
        @change="applyRange"
      />
      <div class="filters__inputs">
        <q-input
          v-model.number="minInput"
          type="number"
          inputmode="decimal"
          min="0"
          outlined
          dense
          class="field-dark"
          :label="t('catalog.priceFrom')"
          :suffix="currencySymbol"
          @change="applyInputs"
          @keyup.enter="applyInputs"
        />
        <span class="filters__dash" aria-hidden="true">–</span>
        <q-input
          v-model.number="maxInput"
          type="number"
          inputmode="decimal"
          min="0"
          outlined
          dense
          class="field-dark"
          :label="t('catalog.priceTo')"
          :suffix="currencySymbol"
          @change="applyInputs"
          @keyup.enter="applyInputs"
        />
      </div>
    </section>

    <section class="filters__group" aria-labelledby="f-stock">
      <h2 id="f-stock" class="filters__title">{{ t('catalog.availability') }}</h2>
      <q-toggle
        :model-value="filters.inStock"
        color="primary"
        :label="t('catalog.inStockOnly')"
        class="filters__toggle"
        @update:model-value="(v) => emitChange({ inStock: v })"
      />
    </section>

    <q-btn
      v-if="hasActive"
      flat
      no-caps
      class="filters__reset"
      :icon="mdiRefresh"
      :label="t('catalog.resetFilters')"
      @click="emitChange({ priceMin: null, priceMax: null, inStock: false })"
    />
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { mdiRefresh } from '@quasar/extras/mdi-v7'
import { useConfigStore } from '@/stores/config'
import { categoryIcon } from '@/composables/category-icons'
import { hasActiveFilters, PRICE_SLIDER_MAX, toCatalogQuery } from '@/composables/catalog-query'

const props = defineProps({
  categories: { type: Array, default: () => [] },
  activeSlug: { type: String, default: '' },
  filters: { type: Object, required: true },
})
const emit = defineEmits(['change'])

const { t } = useI18n()
const config = useConfigStore()

const sliderMax = computed(() => Math.max(PRICE_SLIDER_MAX, Math.ceil(props.filters.priceMax ?? 0)))
const hasActive = computed(() => hasActiveFilters(props.filters))

const currencySymbol = computed(() => {
  const parts = new Intl.NumberFormat('en', { style: 'currency', currency: config.currency }).formatToParts(0)
  return parts.find((p) => p.type === 'currency')?.value ?? config.currency
})

// Changing the category keeps price and stock filters, but starts at page 1.
const carryQuery = computed(() => toCatalogQuery({ ...props.filters, page: 1 }))

const range = ref({ min: 0, max: PRICE_SLIDER_MAX })
const minInput = ref(null)
const maxInput = ref(null)

watch(
  () => [props.filters.priceMin, props.filters.priceMax],
  ([min, max]) => {
    range.value = { min: min ?? 0, max: max ?? sliderMax.value }
    minInput.value = min
    maxInput.value = max
  },
  { immediate: true },
)

function isOpen(cat) {
  if (props.activeSlug === cat.slug) return true
  return (cat.children ?? []).some((c) => c.slug === props.activeSlug)
}

function normalize(value) {
  if (value === '' || value === null || value === undefined) return null
  const n = Number(value)
  if (!Number.isFinite(n) || n < 0) return null
  return Math.round(n * 100) / 100
}

function applyRange(value) {
  emitChange({
    priceMin: value.min > 0 ? value.min : null,
    priceMax: value.max < sliderMax.value ? value.max : null,
  })
}

function applyInputs() {
  let min = normalize(minInput.value)
  let max = normalize(maxInput.value)
  if (min !== null && max !== null && min > max) [min, max] = [max, min]
  if (min === props.filters.priceMin && max === props.filters.priceMax) return
  emitChange({ priceMin: min, priceMax: max })
}

function emitChange(patch) {
  emit('change', { ...patch, page: 1 })
}
</script>

<style lang="scss" scoped>
.filters {
  display: flex;
  flex-direction: column;
  gap: 8px;

  &__group {
    padding: 20px 0;
    border-bottom: 1px solid $color-border;

    &:first-child {
      padding-top: 0;
    }
  }

  &__title {
    margin-bottom: 12px;
    font-family: $font-body;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: $color-text-muted;
  }

  &__tree,
  &__sub {
    list-style: none;
    margin: 0;
    padding: 0;
  }

  &__sub {
    margin: 2px 0 6px 20px;
    padding-left: 12px;
    border-left: 1px solid $color-border;
  }

  &__cat {
    display: flex;
    align-items: center;
    gap: 10px;
    min-height: 40px;
    padding: 6px 10px;
    border-radius: $radius-button;
    color: #cbd5e1;
    font-size: 0.9375rem;
    font-weight: 500;

    &:hover {
      background: rgba(255, 255, 255, 0.05);
      color: $color-text;
    }

    &.is-active {
      background: $color-primary-soft;
      color: $primary;

      .filters__count {
        color: $primary;
      }
    }

    &--child {
      min-height: 36px;
      font-size: 0.875rem;
    }
  }

  &__cat-icon {
    color: $color-text-muted;
    flex: none;
  }

  &__cat.is-active &__cat-icon {
    color: $primary;
  }

  &__count {
    margin-left: auto;
    font-size: 0.75rem;
    color: $color-text-muted;
  }

  &__range {
    margin: 4px 8px 16px;
  }

  &__inputs {
    display: flex;
    align-items: center;
    gap: 8px;

    .q-input {
      flex: 1;
    }
  }

  &__dash {
    color: $color-text-muted;
  }

  &__toggle {
    margin-left: -10px;
    color: $color-text;
  }

  &__reset {
    align-self: flex-start;
    margin-top: 8px;
    color: $primary;
    font-weight: 600;
    border-radius: $radius-button;
  }
}
</style>
