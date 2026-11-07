<template>
  <div class="no-photo" role="img" :aria-label="t('product.noPhoto')">
    <svg viewBox="0 0 120 90" aria-hidden="true">
      <path d="M30 62V40l30-16 30 16v22" fill="none" stroke="currentColor" stroke-width="3" stroke-linejoin="round" />
      <rect x="48" y="46" width="24" height="16" rx="2" fill="currentColor" opacity="0.5" />
      <path d="M20 62h80" stroke="currentColor" stroke-width="3" stroke-linecap="round" />
    </svg>
    <span v-if="!compact">{{ t('product.noPhoto') }}</span>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

defineProps({ compact: { type: Boolean, default: false } })
const { t } = useI18n()
</script>

<style lang="scss" scoped>
.no-photo {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: rgba(148, 163, 184, 0.75);
  font-size: 0.8125rem;
  font-weight: 500;
  background:
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px) 0 0 / 24px 24px,
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px) 0 0 / 24px 24px,
    linear-gradient(160deg, #1b2540, #111a2e);

  svg {
    width: 38%;
    max-width: 120px;
  }
}
</style>
