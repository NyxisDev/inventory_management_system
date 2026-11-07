<template>
  <section class="hero" aria-labelledby="hero-title">
    <div class="hero__bg" aria-hidden="true" />
    <div class="hero__overlay" aria-hidden="true" />

    <div class="container hero__inner">
      <p class="eyebrow hero__eyebrow">{{ t('home.heroEyebrow') }}</p>
      <h1 id="hero-title" class="hero__title">
        <span>{{ t('home.heroTitleLine1') }}</span>
        <span class="text-orange">{{ t('home.heroTitleLine2') }}</span>
      </h1>
      <p class="hero__subtitle">
        <template v-for="(point, i) in points" :key="point">
          <span v-if="i > 0" class="hero__dot" aria-hidden="true">•</span>
          <span>{{ point }}</span>
        </template>
      </p>
      <div class="hero__actions">
        <q-btn
          unelevated
          no-caps
          class="btn btn--primary"
          :to="{ name: 'catalog' }"
          :label="t('home.viewCatalog')"
          :icon-right="mdiArrowRight"
        />
        <q-btn outline no-caps class="btn btn--outline" :to="{ name: 'contacts' }" :label="t('home.contactUs')" />
      </div>
    </div>

    <div class="container hero__stats-wrap">
      <dl class="hero__stats">
        <div v-for="stat in stats" :key="stat.label" class="hero__stat">
          <dt>{{ stat.label }}</dt>
          <dd>{{ stat.value }}</dd>
        </div>
      </dl>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { mdiArrowRight } from '@quasar/extras/mdi-v7'

const props = defineProps({
  warehouses: { type: Number, default: 0 },
  products: { type: Number, default: 0 },
  categories: { type: Number, default: 0 },
})

const { t, tm, rt } = useI18n()

const points = computed(() => tm('home.heroPoints').map((p) => rt(p)))

const stats = computed(() =>
  [
    { value: props.products, label: t('home.statsProducts') },
    { value: props.categories, label: t('home.statsCategories') },
    { value: props.warehouses, label: t('home.statsWarehouses') },
    { value: t('home.statsLive'), label: t('home.statsUpdated') },
  ].filter((s) => s.value),
)
</script>

<style lang="scss" scoped>
.hero {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: calc(100vh - #{$header-height});
  min-height: calc(100svh - #{$header-height});
  overflow: hidden;
  isolation: isolate;
  // Pull the hero under the sticky header so the image reaches the top.
  margin-top: -$header-height;
  padding-top: $header-height;

  &__bg {
    position: absolute;
    inset: 0;
    z-index: -2;
    background: #0b1121 url('/images/hero-site.svg') center bottom / cover no-repeat;
    transform: scale(1.02);
  }

  &__overlay {
    position: absolute;
    inset: 0;
    z-index: -1;
    background:
      linear-gradient(180deg, rgba(11, 17, 33, 0.55) 0%, rgba(11, 17, 33, 0) 30%),
      linear-gradient(0deg, #0b1121 0%, rgba(11, 17, 33, 0) 28%),
      rgba(11, 17, 33, 0.7);
  }

  &__inner {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding-top: 72px;
    padding-bottom: 48px;
    animation: hero-in 0.8s ease-out both;
  }

  &__eyebrow {
    &::after {
      content: '';
      width: 24px;
      height: 2px;
      background: $primary;
      border-radius: 2px;
    }
  }

  &__title {
    display: flex;
    flex-direction: column;
    max-width: 900px;
    font-size: clamp(2.4rem, 7vw, 4.25rem);
    line-height: 1.04;
  }

  &__subtitle {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 6px 14px;
    max-width: 680px;
    margin-top: 24px;
    font-size: clamp(1rem, 2.2vw, 1.1875rem);
    color: #cbd5e1;
  }

  &__dot {
    color: $primary;
  }

  &__actions {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 14px;
    margin-top: 40px;

    .btn {
      min-height: 54px;
      padding: 0 28px;
    }
  }

  &__stats-wrap {
    padding-bottom: 40px;
  }

  &__stats {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    margin: 0;
    border: 1px solid $color-border;
    border-radius: $radius-card;
    background: rgba(21, 29, 48, 0.72);
    backdrop-filter: blur(10px);
    overflow: hidden;

    @media (min-width: 768px) {
      grid-template-columns: repeat(4, minmax(0, 1fr));
    }
  }

  &__stat {
    display: flex;
    flex-direction: column-reverse;
    gap: 2px;
    padding: 18px 20px;
    border-right: 1px solid $color-border;
    border-bottom: 1px solid $color-border;

    dt {
      font-size: 0.875rem;
      color: $color-text-muted;
    }

    dd {
      margin: 0;
      font-family: $font-heading;
      font-weight: 700;
      font-size: clamp(1.5rem, 3vw, 2rem);
      color: $color-text;
      line-height: 1.1;
    }

    @media (min-width: 768px) {
      border-bottom: 0;

      &:last-child {
        border-right: 0;
      }
    }
  }
}

@keyframes hero-in {
  from {
    opacity: 0;
    transform: translateY(24px);
  }

  to {
    opacity: 1;
    transform: none;
  }
}
</style>
