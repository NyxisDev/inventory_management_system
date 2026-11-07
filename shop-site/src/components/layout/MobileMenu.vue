<template>
  <q-dialog v-model="model" position="right" full-height class="mobile-menu-dialog">
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
            <q-icon :name="categoryIcon(cat.slug)" size="20px" />
            {{ cat.name }}
          </router-link>
        </li>
      </ul>

      <div class="mobile-menu__contact">
        <q-btn
          unelevated
          no-caps
          class="btn btn--primary full-width"
          :href="config.phoneHref"
          :icon="mdiPhone"
          :label="config.phone"
        />
        <p v-for="line in config.hours" :key="line" class="mobile-menu__hours">{{ line }}</p>
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
import { categoryIcon } from '@/composables/category-icons'
import SiteLogo from './SiteLogo.vue'

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
  overflow-y: auto;
  padding: 16px 20px 28px;
  background: $color-panel;
  border-left: 1px solid $color-border;
  border-radius: 0 !important;

  &__head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 56px;
    margin-bottom: 16px;
  }

  &__links {
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding-bottom: 16px;
    border-bottom: 1px solid $color-border;
  }

  &__link {
    display: flex;
    align-items: center;
    min-height: 48px;
    padding: 0 12px;
    border-radius: $radius-button;
    font-family: $font-heading;
    font-size: 1.25rem;
    font-weight: 700;
    color: $color-text;

    &.is-active {
      background: $color-primary-soft;
      color: $primary;
    }
  }

  &__label {
    margin: 20px 12px 8px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: $color-text-muted;
  }

  &__cats {
    list-style: none;
    margin: 0;
    padding: 0;
  }

  &__cat {
    display: flex;
    align-items: center;
    gap: 12px;
    min-height: 44px;
    padding: 0 12px;
    border-radius: $radius-button;
    color: $color-text;

    .q-icon {
      color: $primary;
    }

    &:hover {
      background: rgba(255, 255, 255, 0.05);
      color: $color-text;
    }
  }

  &__contact {
    margin-top: 24px;
    padding-top: 20px;
    border-top: 1px solid $color-border;
  }

  &__hours {
    margin-top: 10px;
    font-size: 0.875rem;
    color: $color-text-muted;
  }
}
</style>
