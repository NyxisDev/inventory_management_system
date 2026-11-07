<template>
  <!-- Categories for phones and tablets: chips wrap onto new lines, so nothing scrolls sideways. -->
  <nav class="cat-chips" :aria-label="t('catalog.categories')">
    <ul class="cat-chips__row">
      <li>
        <router-link
          :to="{ name: 'catalog', query: carryQuery }"
          class="cat-chip"
          :class="{ 'is-active': !activeSlug }"
          :aria-current="!activeSlug ? 'page' : undefined"
        >
          {{ t('catalog.allProducts') }}
        </router-link>
      </li>
      <li v-for="cat in categories" :key="cat.slug">
        <router-link
          :to="{ name: 'category', params: { categorySlug: cat.slug }, query: carryQuery }"
          class="cat-chip"
          :class="{ 'is-active': activeSlug === cat.slug, 'is-parent': openParent?.slug === cat.slug }"
          :aria-current="activeSlug === cat.slug ? 'page' : undefined"
        >
          <q-icon :name="categoryIcon(cat.slug)" size="18px" aria-hidden="true" />
          {{ cat.name }}
        </router-link>
      </li>
    </ul>

    <ul v-if="openParent?.children?.length" class="cat-chips__row cat-chips__row--sub">
      <li v-for="child in openParent.children" :key="child.slug">
        <router-link
          :to="{ name: 'category', params: { categorySlug: child.slug }, query: carryQuery }"
          class="cat-chip cat-chip--sub"
          :class="{ 'is-active': activeSlug === child.slug }"
          :aria-current="activeSlug === child.slug ? 'page' : undefined"
        >
          {{ child.name }}
          <span v-if="child.product_count !== undefined" class="cat-chip__count">{{ child.product_count }}</span>
        </router-link>
      </li>
    </ul>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { categoryIcon } from '@/composables/category-icons'
import { toCatalogQuery } from '@/composables/catalog-query'

const props = defineProps({
  categories: { type: Array, default: () => [] },
  activeSlug: { type: String, default: '' },
  filters: { type: Object, required: true },
})

const { t } = useI18n()

const carryQuery = computed(() => toCatalogQuery({ ...props.filters, page: 1 }))

// The top-level category that is selected or holds the selected subcategory.
const openParent = computed(() =>
  props.categories.find(
    (cat) => cat.slug === props.activeSlug || (cat.children ?? []).some((c) => c.slug === props.activeSlug),
  ),
)
</script>

<style lang="scss" scoped>
.cat-chips {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;

  &__row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    list-style: none;
    margin: 0;
    padding: 0;

    @media (max-width: 599px) {
      gap: 6px;
    }

    > li {
      min-width: 0;
      max-width: 100%;
    }

    &--sub {
      padding: 10px 0 0;
      border-top: 1px solid $color-border;
    }
  }
}

.cat-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  max-width: 100%;
  min-height: 44px;
  padding: 0 14px;
  border: 1px solid $color-border-strong;
  border-radius: $radius-button;
  color: #cbd5e1;
  font-size: 0.9375rem;
  font-weight: 500;
  line-height: 1.25;
  transition:
    border-color $transition,
    background-color $transition,
    color $transition;

  .q-icon {
    flex: none;
    color: $color-text-muted;
  }

  &:hover {
    border-color: rgba(255, 255, 255, 0.32);
    color: $color-text;
  }

  &.is-parent {
    border-color: rgba(255, 138, 0, 0.45);
    color: $color-text;
  }

  &.is-active {
    border-color: $primary;
    background: $color-primary-soft;
    color: $primary;

    .q-icon {
      color: $primary;
    }
  }

  &--sub {
    min-height: 40px;
    font-size: 0.875rem;
  }

  // Phones: smaller chips without icons, so the list stays a few lines high.
  @media (max-width: 599px) {
    gap: 6px;
    min-height: 40px;
    padding: 0 12px;
    font-size: 0.875rem;

    .q-icon {
      display: none;
    }

    &--sub {
      min-height: 36px;
    }
  }

  &__count {
    font-size: 0.75rem;
    color: $color-text-muted;
    font-variant-numeric: tabular-nums;
  }
}
</style>
