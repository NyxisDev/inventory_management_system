<template>
  <section class="not-found">
    <div class="container not-found__inner">
      <p class="not-found__code" aria-hidden="true">{{ t('notFound.code') }}</p>
      <h1 class="not-found__title">{{ title || t('notFound.title') }}</h1>
      <p class="not-found__text">{{ text || t('notFound.text') }}</p>
      <div class="not-found__actions">
        <q-btn unelevated no-caps class="btn btn--primary" :to="{ name: 'catalog' }" :label="t('notFound.goCatalog')" />
        <q-btn outline no-caps class="btn btn--outline" to="/" :label="t('notFound.goHome')" />
      </div>
    </div>
  </section>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

defineProps({
  title: { type: String, default: '' },
  text: { type: String, default: '' },
})

const { t } = useI18n()
</script>

<style lang="scss" scoped>
.not-found {
  padding: 96px 0 120px;

  &__inner {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  &__code {
    font-family: $font-heading;
    font-weight: 700;
    font-size: clamp(6rem, 22vw, 11rem);
    line-height: 1;
    letter-spacing: -0.04em;
    color: $primary;
  }

  &__title {
    margin-top: 16px;
    font-size: clamp(1.75rem, 4vw, 2.5rem);
  }

  &__text {
    max-width: 520px;
    margin-top: 12px;
    color: $color-text-muted;
  }

  &__actions {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 12px;
    margin-top: 32px;
  }
}
</style>
