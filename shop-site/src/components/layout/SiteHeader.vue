<template>
  <header class="site-header" :class="{ 'is-scrolled': scrolled }">
    <div class="container site-header__row">
      <SiteLogo />

      <nav class="site-header__nav" :aria-label="t('nav.mainNavigation')">
        <router-link :to="{ name: 'catalog' }" class="site-header__link" :class="{ 'is-active': inCatalog }">
          {{ t('nav.catalog') }}
        </router-link>
        <router-link :to="{ name: 'contacts' }" class="site-header__link" active-class="is-active">
          {{ t('nav.contacts') }}
        </router-link>
      </nav>

      <div class="site-header__search">
        <SearchBox :initial="currentQuery" />
      </div>

      <div class="site-header__actions">
        <a :href="config.phoneHref" class="site-header__phone">
          <q-icon :name="mdiPhone" size="18px" aria-hidden="true" />
          <span>{{ config.phone }}</span>
        </a>

        <LanguageSwitcher class="site-header__lang" />

        <q-btn
          flat
          round
          class="site-header__icon-btn lt-md"
          :icon="mdiMagnify"
          :aria-label="t('search.label')"
          :aria-expanded="mobileSearch ? 'true' : 'false'"
          @click="toggleMobileSearch"
        />
        <q-btn
          flat
          round
          class="site-header__icon-btn lt-md"
          :icon="mdiPhone"
          :href="config.phoneHref"
          :aria-label="`${t('nav.callUs')}: ${config.phone}`"
        />
        <q-btn
          flat
          round
          class="site-header__icon-btn lt-md"
          :icon="mdiMenu"
          :aria-label="t('nav.openMenu')"
          @click="$emit('open-menu')"
        />
      </div>
    </div>

    <q-slide-transition>
      <div v-show="mobileSearch" class="site-header__mobile-search lt-md">
        <div class="container">
          <SearchBox ref="mobileSearchRef" :initial="currentQuery" @done="mobileSearch = false" />
        </div>
      </div>
    </q-slide-transition>
  </header>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { mdiMagnify, mdiMenu, mdiPhone } from '@quasar/extras/mdi-v7'
import { useConfigStore } from '@/stores/config'
import SiteLogo from './SiteLogo.vue'
import SearchBox from './SearchBox.vue'
import LanguageSwitcher from './LanguageSwitcher.vue'

defineEmits(['open-menu'])

const { t } = useI18n()
const config = useConfigStore()
const route = useRoute()

const scrolled = ref(false)
const mobileSearch = ref(false)
const mobileSearchRef = ref(null)

const inCatalog = computed(() => ['catalog', 'category', 'product'].includes(route.name))
const currentQuery = computed(() => (route.name === 'search' ? String(route.query.q ?? '') : ''))

watch(
  () => route.fullPath,
  () => {
    mobileSearch.value = false
  },
)

async function toggleMobileSearch() {
  mobileSearch.value = !mobileSearch.value
  if (mobileSearch.value) {
    await nextTick()
    mobileSearchRef.value?.focus()
  }
}

function onScroll() {
  scrolled.value = window.scrollY > 8
}

onMounted(() => {
  onScroll()
  window.addEventListener('scroll', onScroll, { passive: true })
})

onBeforeUnmount(() => window.removeEventListener('scroll', onScroll))
</script>

<style lang="scss" scoped>
.site-header {
  position: sticky;
  top: 0;
  z-index: 2000;
  background: rgba(11, 17, 33, 0.82);
  backdrop-filter: saturate(140%) blur(14px);
  -webkit-backdrop-filter: saturate(140%) blur(14px);
  border-bottom: 1px solid transparent;
  transition:
    border-color $transition,
    background-color $transition;

  &.is-scrolled {
    background: rgba(11, 17, 33, 0.94);
    border-bottom-color: $color-border;
  }

  &__row {
    display: flex;
    align-items: center;
    gap: 12px;
    height: $header-height;

    @media (min-width: 1024px) {
      gap: 24px;
    }
  }

  &__nav {
    display: none;
    gap: 4px;

    @media (min-width: 1024px) {
      display: flex;
    }
  }

  &__link {
    position: relative;
    padding: 10px 14px;
    border-radius: $radius-button;
    font-weight: 500;
    color: $color-text-muted;

    &:hover {
      color: $color-text;
    }

    &.is-active {
      color: $color-text;

      &::after {
        content: '';
        position: absolute;
        left: 14px;
        right: 14px;
        bottom: 2px;
        height: 2px;
        border-radius: 2px;
        background: $primary;
      }
    }
  }

  &__search {
    display: none;
    flex: 1;
    max-width: 440px;
    margin-left: auto;

    @media (min-width: 1024px) {
      display: block;
    }
  }

  &__actions {
    display: flex;
    flex: none;
    align-items: center;
    gap: 4px;
    margin-left: auto;

    @media (max-width: 379px) {
      gap: 0;
    }

    @media (min-width: 1024px) {
      margin-left: 0;
    }
  }

  &__phone {
    display: none;
    align-items: center;
    gap: 8px;
    height: 48px;
    padding: 0 16px;
    border: 1px solid $color-border-strong;
    border-radius: $radius-button;
    color: $color-text;
    font-weight: 600;
    white-space: nowrap;
    transition:
      border-color $transition,
      color $transition;

    .q-icon {
      color: $primary;
    }

    &:hover {
      border-color: $primary;
      color: $color-text;
    }

    @media (min-width: 1024px) {
      display: inline-flex;
    }
  }

  // Small phones get the language switch in the menu instead.
  &__lang {
    display: none;

    @media (min-width: 480px) {
      display: inline-flex;
    }
  }

  &__icon-btn {
    width: 44px;
    height: 44px;
    color: $color-text;
  }

  &__mobile-search {
    padding: 0 0 16px;
  }
}
</style>
