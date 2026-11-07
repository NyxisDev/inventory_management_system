<template>
  <section class="page-header">
    <div class="page-header__glow" aria-hidden="true" />
    <div class="container">
      <q-breadcrumbs v-if="crumbs.length" :separator-color="'grey-6'" class="page-header__crumbs" :aria-label="t('common.breadcrumbs')">
        <template #separator>
          <q-icon :name="mdiChevronRight" size="16px" />
        </template>
        <q-breadcrumbs-el v-for="(crumb, i) in crumbs" :key="i" :label="crumb.label" :to="i < crumbs.length - 1 ? crumb.to : undefined" />
      </q-breadcrumbs>
      <p v-if="eyebrow" class="eyebrow">{{ eyebrow }}</p>
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
  eyebrow: { type: String, default: '' },
  crumbs: { type: Array, default: () => [] },
})

const { t } = useI18n()
</script>

<style lang="scss" scoped>
.page-header {
  position: relative;
  overflow: hidden;
  padding: 36px 0 40px;
  background:
    linear-gradient(rgba(255, 255, 255, 0.025) 1px, transparent 1px) 0 0 / 40px 40px,
    linear-gradient(90deg, rgba(255, 255, 255, 0.025) 1px, transparent 1px) 0 0 / 40px 40px,
    $color-panel;
  border-bottom: 1px solid $color-border;

  @media (min-width: 1024px) {
    padding: 48px 0 52px;
  }

  &__glow {
    position: absolute;
    right: -120px;
    top: -160px;
    width: 480px;
    height: 480px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(255, 138, 0, 0.16), transparent 65%);
    pointer-events: none;
  }

  .container {
    position: relative;
  }

  &__crumbs {
    margin-bottom: 20px;
  }

  &__title {
    font-size: clamp(2rem, 5vw, 2.75rem);
    line-height: 1.1;
    letter-spacing: -0.02em;
  }

  &__subtitle {
    margin-top: 10px;
    color: $color-text-muted;
  }
}
</style>
