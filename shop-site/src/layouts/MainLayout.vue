<template>
  <div class="main-layout">
    <a href="#main" class="skip-link">{{ t('nav.skipToContent') }}</a>
    <SiteHeader @open-menu="menuOpen = true" />
    <main id="main" class="main-layout__content" tabindex="-1">
      <router-view />
    </main>
    <SiteFooter />
    <MobileMenu v-model="menuOpen" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useCatalogStore } from '@/stores/catalog'
import SiteHeader from '@/components/layout/SiteHeader.vue'
import SiteFooter from '@/components/layout/SiteFooter.vue'
import MobileMenu from '@/components/layout/MobileMenu.vue'

defineOptions({
  name: 'MainLayout',
  // Categories are used in the footer and the menu on every page.
  async preFetch({ store }) {
    await useCatalogStore(store).loadCategories()
  },
})

const { t } = useI18n()
const menuOpen = ref(false)
</script>

<style lang="scss" scoped>
.main-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;

  &__content {
    flex: 1;
    outline: none;
  }
}
</style>
