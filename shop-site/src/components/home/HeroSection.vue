<template>
  <section class="hero" aria-labelledby="hero-title">
    <div class="hero__bg" aria-hidden="true" />
    <div class="hero__overlay" aria-hidden="true" />

    <div class="container hero__inner">
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
      <p v-if="facts.length" class="hero__facts">
        <template v-for="(fact, i) in facts" :key="fact">
          <span v-if="i > 0" class="hero__dot" aria-hidden="true">•</span>
          <span>{{ fact }}</span>
        </template>
      </p>
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

// Real counts from the catalog, shown as a quiet line under the buttons.
const facts = computed(() =>
  [
    props.products && t('home.factsProducts', props.products),
    props.categories && t('home.factsCategories', props.categories),
    props.warehouses && t('home.factsWarehouses', props.warehouses),
  ].filter(Boolean),
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

  &__title {
    display: flex;
    flex-direction: column;
    max-width: 900px;
    font-size: clamp(2.1rem, 7vw, 4.25rem);
    line-height: 1.06;
    overflow-wrap: anywhere;
    text-wrap: balance;
  }

  &__subtitle {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 6px 14px;
    max-width: 100%;
    margin-top: 24px;
    font-size: clamp(1rem, 2.2vw, 1.1875rem);
    color: #cbd5e1;
  }

  &__dot {
    color: $primary;
  }

  // Below 1100px the points stack, so a separator never hangs at the end of a line.
  @media (max-width: 1099px) {
    &__subtitle,
    &__facts {
      flex-direction: column;
      align-items: center;
    }

    &__dot {
      display: none;
    }
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

    @media (max-width: 479px) {
      flex-direction: column;
      align-self: stretch;
    }
  }

  &__facts {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 4px 12px;
    margin-top: 32px;
    font-size: 0.9375rem;
    font-weight: 500;
    color: $color-text-muted;
    font-variant-numeric: tabular-nums;
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
