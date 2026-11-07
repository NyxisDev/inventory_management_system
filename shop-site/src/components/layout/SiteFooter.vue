<template>
  <footer class="site-footer">
    <div class="container">
      <div class="site-footer__grid">
        <div class="site-footer__brand">
          <SiteLogo />
          <p class="site-footer__about">{{ t('footer.about') }}</p>
        </div>

        <nav class="site-footer__col" :aria-label="t('footer.catalog')">
          <h2 class="site-footer__title">{{ t('footer.catalog') }}</h2>
          <ul>
            <li v-for="cat in catalog.categories" :key="cat.slug">
              <router-link :to="{ name: 'category', params: { categorySlug: cat.slug } }">{{ cat.name }}</router-link>
            </li>
          </ul>
        </nav>

        <div class="site-footer__col">
          <h2 class="site-footer__title">{{ t('footer.contacts') }}</h2>
          <ul class="site-footer__contacts">
            <li>
              <q-icon :name="mdiPhone" aria-hidden="true" />
              <a :href="config.phoneHref" class="site-footer__strong">{{ config.phone }}</a>
            </li>
            <li>
              <q-icon :name="mdiEmailOutline" aria-hidden="true" />
              <a :href="config.emailHref">{{ config.email }}</a>
            </li>
            <li>
              <q-icon :name="mdiMapMarkerOutline" aria-hidden="true" />
              <span>{{ config.address }}</span>
            </li>
          </ul>
        </div>

        <div class="site-footer__col">
          <h2 class="site-footer__title">{{ t('contacts.hours') }}</h2>
          <ul class="site-footer__hours">
            <li v-for="line in config.hours" :key="line">
              <q-icon :name="mdiClockOutline" aria-hidden="true" />
              <span>{{ line }}</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="site-footer__bottom">
        <p>{{ t('footer.rights', { year, name: config.siteName }) }}</p>
        <p v-if="config.mock" class="site-footer__demo">{{ t('footer.sampleData') }}</p>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { mdiClockOutline, mdiEmailOutline, mdiMapMarkerOutline, mdiPhone } from '@quasar/extras/mdi-v7'
import { useConfigStore } from '@/stores/config'
import { useCatalogStore } from '@/stores/catalog'
import SiteLogo from './SiteLogo.vue'

const { t } = useI18n()
const config = useConfigStore()
const catalog = useCatalogStore()
const year = new Date().getFullYear()
</script>

<style lang="scss" scoped>
.site-footer {
  background: $color-page;
  border-top: 1px solid $color-border;
  padding: 64px 0 28px;
  color: $color-text-muted;

  &__grid {
    display: grid;
    gap: 40px;
    grid-template-columns: 1fr;

    @media (min-width: 640px) {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    @media (min-width: 1024px) {
      grid-template-columns: 1.4fr 1fr 1.3fr 1fr;
    }
  }

  &__about {
    margin-top: 16px;
    max-width: 320px;
    font-size: 0.9375rem;
  }

  &__title {
    margin-bottom: 16px;
    font-family: $font-heading;
    font-size: 1.0625rem;
    color: $color-text;
  }

  ul {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  a {
    color: $color-text-muted;

    &:hover {
      color: $primary;
    }
  }

  &__contacts li,
  &__hours li {
    display: flex;
    align-items: flex-start;
    gap: 10px;

    .q-icon {
      flex: none;
      margin-top: 4px;
      color: $primary;
      font-size: 18px;
    }
  }

  &__strong {
    color: $color-text !important;
    font-weight: 600;

    &:hover {
      color: $primary !important;
    }
  }

  &__bottom {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    gap: 8px 24px;
    margin-top: 48px;
    padding-top: 24px;
    border-top: 1px solid $color-border;
    font-size: 0.875rem;
  }

  &__demo {
    color: #fbbf24;
  }
}
</style>
