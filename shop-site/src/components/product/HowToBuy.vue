<template>
  <section class="buy card" aria-labelledby="buy-title">
    <h2 id="buy-title" class="buy__title">{{ t('product.howToBuy') }}</h2>
    <p class="buy__text">{{ t('product.howToBuyText') }}</p>

    <q-btn
      unelevated
      no-caps
      class="btn btn--primary full-width buy__call"
      :href="config.phoneHref"
      :icon="mdiPhone"
      :label="t('product.call', { phone: config.phone })"
    />
    <q-btn
      outline
      no-caps
      class="btn btn--outline full-width"
      :href="config.emailHref"
      :icon="mdiEmailOutline"
      :label="t('product.email')"
    />

    <dl class="buy__info">
      <div>
        <dt><q-icon :name="mdiMapMarkerOutline" aria-hidden="true" /> {{ t('contacts.address') }}</dt>
        <dd>{{ config.address }}</dd>
      </div>
      <div>
        <dt><q-icon :name="mdiClockOutline" aria-hidden="true" /> {{ t('product.hours') }}</dt>
        <dd>
          <span v-for="line in config.hours" :key="line" class="buy__hours">{{ line }}</span>
        </dd>
      </div>
    </dl>
  </section>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { mdiClockOutline, mdiEmailOutline, mdiMapMarkerOutline, mdiPhone } from '@quasar/extras/mdi-v7'
import { useConfigStore } from '@/stores/config'

const { t } = useI18n()
const config = useConfigStore()
</script>

<style lang="scss" scoped>
.buy {
  padding: 24px;
  border-color: rgba(255, 138, 0, 0.35);
  background:
    radial-gradient(circle at 100% 0%, rgba(255, 138, 0, 0.14), transparent 50%),
    $color-panel;

  &__title {
    font-size: 1.25rem;
  }

  &__text {
    margin: 8px 0 20px;
    font-size: 0.9375rem;
    color: #cbd5e1;
  }

  &__call {
    margin-bottom: 10px;
  }

  &__info {
    display: grid;
    gap: 16px;
    margin: 24px 0 0;
    padding-top: 20px;
    border-top: 1px solid $color-border;

    dt {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.75rem;
      font-weight: 600;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: $color-text-muted;

      .q-icon {
        font-size: 16px;
        color: $primary;
      }
    }

    dd {
      margin: 4px 0 0 24px;
      font-size: 0.9375rem;
    }
  }

  &__hours {
    display: block;
  }
}
</style>
