<template>
  <router-link to="/" class="site-logo" :aria-label="`${config.siteName}, ${t('nav.home')}`">
    <svg class="site-logo__mark" viewBox="0 0 40 40" aria-hidden="true">
      <rect width="40" height="40" rx="10" fill="#ff8a00" />
      <path d="M9 29V17l11-6 11 6v12" fill="none" stroke="#0b1121" stroke-width="3.2" stroke-linejoin="round" />
      <rect x="15" y="20" width="10" height="9" rx="1.5" fill="#0b1121" />
    </svg>
    <span class="site-logo__name">{{ config.siteName }}</span>
  </router-link>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { useConfigStore } from '@/stores/config'

const config = useConfigStore()
const { t } = useI18n()
</script>

<style lang="scss" scoped>
.site-logo {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  color: $color-text;
  flex: none;

  &:hover {
    color: $color-text;
  }

  &__mark {
    width: 40px;
    height: 40px;
    flex: none;
  }

  &__name {
    font-family: $font-heading;
    font-weight: 700;
    font-size: 1.375rem;
    letter-spacing: -0.02em;
  }
}
</style>
