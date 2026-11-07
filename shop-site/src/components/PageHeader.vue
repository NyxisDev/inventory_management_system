<template>
  <section class="page-header">
    <div class="container">
      <q-breadcrumbs v-if="crumbs.length" :separator-color="'grey-6'" class="page-header__crumbs" :aria-label="t('common.breadcrumbs')">
        <template #separator>
          <q-icon :name="mdiChevronRight" size="16px" />
        </template>
        <q-breadcrumbs-el v-for="(crumb, i) in crumbs" :key="i" :label="crumb.label" :to="i < crumbs.length - 1 ? crumb.to : undefined" />
      </q-breadcrumbs>
      <h1 class="page-header__title">{{ title }}</h1>
      <p v-if="subtitle" class="page-header__subtitle">{{ subtitle }}</p>
      <slot />
    </div>
  </section>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { mdiChevronRight } from '@quasar/extras/mdi-v7'

defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  crumbs: { type: Array, default: () => [] },
})

const { t } = useI18n()
</script>

<style lang="scss" scoped>
.page-header {
  padding: 36px 0 40px;
  background: $color-panel;
  border-bottom: 1px solid $color-border;

  @media (min-width: 1024px) {
    padding: 48px 0 52px;
  }

  &__crumbs {
    margin-bottom: 20px;
  }

  &__title {
    font-size: clamp(2rem, 5vw, 2.75rem);
    line-height: 1.1;
    letter-spacing: -0.02em;
    overflow-wrap: anywhere;
    text-wrap: balance;
  }

  &__subtitle {
    max-width: 68ch;
    margin-top: 10px;
    color: $color-text-muted;
  }
}
</style>
