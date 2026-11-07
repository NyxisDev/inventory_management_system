<template>
  <div>
    <PageHeader
      :title="t('contacts.title')"
      :subtitle="t('contacts.text')"
      :crumbs="[{ label: t('nav.home'), to: '/' }, { label: t('nav.contacts') }]"
    />

    <section class="section section--page contacts">
      <div class="container">
        <ul class="contacts__cards">
          <li v-reveal class="contact-card card card--panel">
            <h2 class="contact-card__label">
              <q-icon :name="mdiPhone" size="20px" aria-hidden="true" />
              {{ t('contacts.phone') }}</h2>
            <a :href="config.phoneHref" class="contact-card__value contact-card__value--big">{{ config.phone }}</a>
          </li>
          <li v-reveal="80" class="contact-card card card--panel">
            <h2 class="contact-card__label">
              <q-icon :name="mdiEmailOutline" size="20px" aria-hidden="true" />
              {{ t('contacts.email') }}</h2>
            <a :href="config.emailHref" class="contact-card__value">{{ config.email }}</a>
          </li>
          <li v-reveal="160" class="contact-card card card--panel">
            <h2 class="contact-card__label">
              <q-icon :name="mdiMapMarkerOutline" size="20px" aria-hidden="true" />
              {{ t('contacts.address') }}</h2>
            <p class="contact-card__value">{{ config.address }}</p>
          </li>
          <li v-reveal="240" class="contact-card card card--panel">
            <h2 class="contact-card__label">
              <q-icon :name="mdiClockOutline" size="20px" aria-hidden="true" />
              {{ t('contacts.hours') }}</h2>
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
            <div class="warehouse__body">
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
  padding: 24px;

  &__label {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
    font-family: $font-body;
    font-size: 0.9375rem;
    font-weight: 600;
    color: $color-text-muted;

    .q-icon {
      color: $primary;
    }
  }

  &__value {
    display: block;
    color: $color-text;
    font-weight: 500;
    overflow-wrap: anywhere;

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

  &__body {
    padding: 24px;
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
