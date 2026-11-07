<template>
  <div>
    <PageHeader
      :title="t('contacts.title')"
      :eyebrow="t('contacts.eyebrow')"
      :subtitle="t('contacts.text')"
      :crumbs="[{ label: t('nav.home'), to: '/' }, { label: t('nav.contacts') }]"
    />

    <section class="section section--page contacts">
      <div class="container">
        <ul class="contacts__cards">
          <li v-reveal class="contact-card card card--panel">
            <span class="contact-card__icon"><q-icon :name="mdiPhone" size="24px" /></span>
            <h2 class="contact-card__label">{{ t('contacts.phone') }}</h2>
            <a :href="config.phoneHref" class="contact-card__value contact-card__value--big">{{ config.phone }}</a>
          </li>
          <li v-reveal="80" class="contact-card card card--panel">
            <span class="contact-card__icon"><q-icon :name="mdiEmailOutline" size="24px" /></span>
            <h2 class="contact-card__label">{{ t('contacts.email') }}</h2>
            <a :href="config.emailHref" class="contact-card__value">{{ config.email }}</a>
          </li>
          <li v-reveal="160" class="contact-card card card--panel">
            <span class="contact-card__icon"><q-icon :name="mdiMapMarkerOutline" size="24px" /></span>
            <h2 class="contact-card__label">{{ t('contacts.address') }}</h2>
            <p class="contact-card__value">{{ config.address }}</p>
          </li>
          <li v-reveal="240" class="contact-card card card--panel">
            <span class="contact-card__icon"><q-icon :name="mdiClockOutline" size="24px" /></span>
            <h2 class="contact-card__label">{{ t('contacts.hours') }}</h2>
            <p class="contact-card__value">
              <span v-for="line in config.hours" :key="line" class="contact-card__line">{{ line }}</span>
            </p>
          </li>
        </ul>
      </div>
    </section>

    <section class="section section--panel" aria-labelledby="warehouses-title">
      <div class="container">
        <div v-reveal class="section-head">
          <div class="section-head__text">
            <h2 id="warehouses-title">{{ t('contacts.warehousesTitle') }}</h2>
            <p>{{ t('contacts.warehousesText') }}</p>
          </div>
        </div>

        <p v-if="catalog.warehouses.length === 0" class="text-muted">{{ t('contacts.noWarehouses') }}</p>

        <ul v-else class="warehouses">
          <li v-for="(w, i) in catalog.warehouses" :key="w.name" v-reveal="(i % 3) * 80" class="warehouse card">
            <div class="warehouse__map" aria-hidden="true">
              <svg viewBox="0 0 320 140" preserveAspectRatio="xMidYMid slice">
                <rect width="320" height="140" fill="#0f172a" />
                <path :d="mapRoads[i % mapRoads.length]" stroke="#1e2a47" stroke-width="10" fill="none" stroke-linecap="round" />
                <path :d="mapRoads[(i + 1) % mapRoads.length]" stroke="#1a2440" stroke-width="5" fill="none" stroke-linecap="round" />
                <circle cx="160" cy="66" r="26" fill="rgba(255,138,0,0.18)" />
                <path d="M160 40c-11 0-19 8-19 18 0 14 19 32 19 32s19-18 19-32c0-10-8-18-19-18z" fill="#ff8a00" />
                <circle cx="160" cy="58" r="6" fill="#0b1121" />
              </svg>
            </div>
            <div class="warehouse__body">
              <span class="warehouse__num">{{ String(i + 1).padStart(2, '0') }}</span>
              <h3 class="warehouse__name">{{ w.name }}</h3>
              <p class="warehouse__address">{{ w.address }}</p>
              <a
                v-if="w.address"
                class="warehouse__link"
                :href="mapLink(w.address)"
                target="_blank"
                rel="noopener noreferrer"
              >
                {{ t('contacts.showOnMap') }}
                <q-icon :name="mdiOpenInNew" size="16px" />
              </a>
            </div>
          </li>
        </ul>
      </div>
    </section>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { mdiClockOutline, mdiEmailOutline, mdiMapMarkerOutline, mdiOpenInNew, mdiPhone } from '@quasar/extras/mdi-v7'
import { useCatalogStore } from '@/stores/catalog'
import { useConfigStore } from '@/stores/config'
import { usePageMeta } from '@/composables/use-page-meta'
import PageHeader from '@/components/PageHeader.vue'

defineOptions({
  name: 'ContactsPage',
  async preFetch({ store }) {
    await useCatalogStore(store).loadWarehouses()
  },
})

const { t } = useI18n()
const catalog = useCatalogStore()
const config = useConfigStore()

// Decorative street lines behind the pin (not a real map).
const mapRoads = [
  'M-10 100 C80 80 140 120 330 60 M90 -10 L120 150',
  'M-10 40 L330 90 M220 -10 C200 60 240 100 210 150',
  'M-10 120 C100 40 200 140 330 30 M40 -10 L70 150',
]

function mapLink(address) {
  return `https://www.openstreetmap.org/search?query=${encodeURIComponent(address)}`
}

usePageMeta(() => ({
  title: t('meta.contactsTitle'),
  description: t('meta.contactsDescription'),
  path: '/contacts',
}))
</script>

<style lang="scss" scoped>
.contacts {
  &__cards {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 20px;
    grid-template-columns: 1fr;

    @media (min-width: 640px) {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    @media (min-width: 1100px) {
      grid-template-columns: repeat(4, minmax(0, 1fr));
    }
  }
}

.contact-card {
  padding: 28px 24px;

  &__icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 52px;
    height: 52px;
    margin-bottom: 20px;
    border-radius: 12px;
    background: $color-primary-soft;
    color: $primary;
  }

  &__label {
    font-family: $font-body;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: $color-text-muted;
    margin-bottom: 8px;
  }

  &__value {
    display: block;
    color: $color-text;
    font-weight: 500;
    word-break: break-word;

    &--big {
      font-family: $font-heading;
      font-size: 1.375rem;
      font-weight: 700;
    }
  }

  a.contact-card__value:hover {
    color: $primary;
  }

  &__line {
    display: block;
  }
}

.warehouses {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 20px;
  grid-template-columns: 1fr;

  @media (min-width: 640px) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  @media (min-width: 1024px) {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

.warehouse {
  overflow: hidden;
  background: $color-page;

  &__map {
    height: 140px;
    border-bottom: 1px solid $color-border;

    svg {
      width: 100%;
      height: 100%;
      display: block;
    }
  }

  &__body {
    position: relative;
    padding: 24px;
  }

  &__num {
    position: absolute;
    top: 20px;
    right: 24px;
    font-family: $font-heading;
    font-weight: 700;
    font-size: 1.75rem;
    color: rgba(255, 255, 255, 0.08);
  }

  &__name {
    font-size: 1.25rem;
  }

  &__address {
    margin-top: 6px;
    color: $color-text-muted;
  }

  &__link {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    min-height: 44px;
    margin-top: 8px;
    font-weight: 600;
  }
}
</style>
