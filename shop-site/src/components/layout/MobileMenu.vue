<template>
  <q-dialog v-model="model" position="right" full-height class="side-sheet-dialog">
    <div class="mobile-menu" role="navigation" :aria-label="t('nav.mainNavigation')">
      <div class="mobile-menu__head">
        <SiteLogo />
        <q-btn flat round :icon="mdiClose" :aria-label="t('nav.closeMenu')" @click="model = false" />
      </div>

      <div class="mobile-menu__links">
        <router-link to="/" class="mobile-menu__link" exact-active-class="is-active">{{ t('nav.home') }}</router-link>
        <router-link :to="{ name: 'catalog' }" class="mobile-menu__link" exact-active-class="is-active">
          {{ t('nav.catalog') }}
        </router-link>
        <router-link :to="{ name: 'contacts' }" class="mobile-menu__link" exact-active-class="is-active">
          {{ t('nav.contacts') }}
        </router-link>
      </div>

      <p class="mobile-menu__label">{{ t('catalog.categories') }}</p>
      <ul class="mobile-menu__cats">
        <li v-for="cat in catalog.categories" :key="cat.slug">
          <router-link :to="{ name: 'category', params: { categorySlug: cat.slug } }" class="mobile-menu__cat">
            {{ cat.name }}
          </router-link>
        </li>
      </ul>

      <LanguageSwitcher variant="segmented" class="mobile-menu__lang" />

      <div class="mobile-menu__contact">
        <q-btn
          unelevated
          no-caps
          class="btn btn--primary full-width"
          :href="config.phoneHref"
          :icon="mdiPhone"
          :label="config.phone"
        />
        <p v-if="config.hours.length" class="mobile-menu__hours">
          <span v-for="line in config.hours" :key="line">{{ line }}</span>
        </p>
      </div>
    </div>
  </q-dialog>
</template>

<script setup>
import { watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { mdiClose, mdiPhone } from '@quasar/extras/mdi-v7'
import { useConfigStore } from '@/stores/config'
import { useCatalogStore } from '@/stores/catalog'
import SiteLogo from './SiteLogo.vue'
import LanguageSwitcher from './LanguageSwitcher.vue'

const model = defineModel({ type: Boolean, default: false })

const { t } = useI18n()
const route = useRoute()
const config = useConfigStore()
const catalog = useCatalogStore()

watch(
  () => route.fullPath,
  () => {
    model.value = false
  },
)
</script>

<style lang="scss" scoped>
.mobile-menu {
  width: min(360px, 88vw);
  height: 100%;
  max-height: 100% !important;
  // Scrolls only on very short screens; the bar itself stays hidden.
  overflow-y: auto;
  scrollbar-width: none;
  overscroll-behavior: contain;
  padding: 16px 20px 28px;

  &::-webkit-scrollbar {
    display: none;
  }

  background: $color-panel;
  border-left: 1px solid $color-border;
  border-radius: 0 !important;

  &__head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 56px;
    margin-bottom: 8px;
  }

  &__links {
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding-bottom: 12px;
    border-bottom: 1px solid $color-border;
  }

  &__link {
    display: flex;
    align-items: center;
    min-height: 46px;
    padding: 0 12px;
    border-radius: $radius-button;
    font-family: $font-heading;
    font-size: 1.1875rem;
    font-weight: 700;
    color: $color-text;

    &.is-active {
      background: $color-primary-soft;
      color: $primary;
    }
  }

  &__label {
    margin: 16px 4px 8px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: $color-text-muted;
  }

  // Categories wrap as compact chips, so the whole menu fits on most phones.
  &__cats {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    list-style: none;
    margin: 0 4px;
    padding: 0;

    > li {
      max-width: 100%;
    }
  }

  &__cat {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    max-width: 100%;
    min-height: 40px;
    padding: 0 12px;
    border: 1px solid $color-border;
    border-radius: $radius-button;
    color: $color-text;
    font-size: 0.9375rem;
    line-height: 1.25;

    &:hover {
      background: rgba(255, 255, 255, 0.05);
      color: $color-text;
    }
  }

  &__lang {
    margin: 16px 4px 0;
  }

  &__contact {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid $color-border;
  }

  &__hours {
    display: flex;
    flex-wrap: wrap;
    gap: 0 12px;
    margin-top: 10px;
    font-size: 0.8125rem;
    line-height: 1.5;
    color: $color-text-muted;
  }
}
</style>
