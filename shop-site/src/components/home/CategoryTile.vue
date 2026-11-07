<template>
  <article class="category-tile card card--panel card--interactive">
    <div class="category-tile__top">
      <span class="category-tile__icon" aria-hidden="true">
        <q-icon :name="categoryIcon(category.slug)" size="28px" />
      </span>
      <q-icon :name="mdiArrowTopRight" class="category-tile__arrow" size="22px" aria-hidden="true" />
    </div>
    <h3 class="category-tile__title">
      <router-link :to="{ name: 'category', params: { categorySlug: category.slug } }" class="category-tile__link">
        {{ category.name }}
      </router-link>
    </h3>
    <p v-if="category.product_count !== undefined" class="category-tile__count">
      {{ t('home.productsCount', category.product_count) }}
    </p>
    <ul v-if="category.children?.length" class="category-tile__children">
      <li v-for="child in category.children" :key="child.slug">
        <router-link :to="{ name: 'category', params: { categorySlug: child.slug } }" class="category-tile__child">
          {{ child.name }}
        </router-link>
      </li>
    </ul>
  </article>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { mdiArrowTopRight } from '@quasar/extras/mdi-v7'
import { categoryIcon } from '@/composables/category-icons'

defineProps({
  category: { type: Object, required: true },
})

const { t } = useI18n()
</script>

<style lang="scss" scoped>
.category-tile {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 24px;

  &__top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 28px;
  }

  &__icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 56px;
    height: 56px;
    border-radius: 14px;
    background: $color-primary-soft;
    color: $primary;
    transition:
      background-color $transition,
      color $transition;
  }

  &:hover &__icon {
    background: $primary;
    color: #fff;
  }

  &__arrow {
    color: $color-text-muted;
    transition:
      color $transition,
      transform $transition;
  }

  &:hover &__arrow {
    color: $primary;
    transform: translate(2px, -2px);
  }

  &__title {
    font-size: 1.25rem;
  }

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

  &__count {
    margin-top: 4px;
    font-size: 0.875rem;
    color: $color-text-muted;
  }

  &__children {
    position: relative;
    z-index: 1; // above the stretched title link
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    list-style: none;
    margin: 20px 0 0;
    padding: 0;
  }

  &__child {
    display: inline-flex;
    align-items: center;
    min-height: 32px;
    padding: 4px 12px;
    border: 1px solid $color-border;
    border-radius: 999px;
    font-size: 0.8125rem;
    color: #cbd5e1;
    background: rgba(255, 255, 255, 0.02);

    &:hover {
      border-color: $primary;
      color: $primary;
    }
  }
}
</style>
