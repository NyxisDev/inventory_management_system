<template>
  <q-layout view="hHh Lpr fFf" class="admin-layout">
    <q-header bordered class="admin-header">
      <q-toolbar class="admin-toolbar q-px-md">
        <q-btn
          flat
          round
          icon="menu"
          class="admin-action"
          :aria-label="$t('nav.menu')"
          :aria-expanded="drawerOpen"
          @click="drawerOpen = !drawerOpen"
        />
        <q-toolbar-title class="q-pa-none">
          <router-link :to="{ name: 'demo-dashboard' }" class="brand-link">
            <img :src="brandIcon" alt="" />
            <span>Bud<span class="brand-accent">master</span></span>
          </router-link>
        </q-toolbar-title>
        <q-btn
          flat
          round
          class="admin-action"
          :icon="quasar.dark.isActive ? 'light_mode' : 'dark_mode'"
          :aria-label="$t(quasar.dark.isActive ? 'nav.light' : 'nav.dark')"
          @click="toggleTheme"
        />
        <q-btn
          flat
          round
          class="admin-action"
          icon="exit_to_app"
          :aria-label="$t('nav.signIn')"
          :to="{ name: 'login' }"
        />
      </q-toolbar>
    </q-header>

    <q-drawer
      v-model="drawerOpen"
      class="admin-drawer"
      show-if-above
      bordered
      :width="240"
      :breakpoint="900"
    >
      <nav class="q-pa-md" :aria-label="$t('nav.menu')">
        <q-select
          :model-value="inventory.role"
          :options="roleOptions"
          :label="$t('nav.role')"
          outlined
          emit-value
          map-options
          class="q-mb-md"
          @update:model-value="changeRole"
        />
        <q-select
          v-model="locale"
          :options="localeOptions"
          :label="$t('nav.language')"
          emit-value
          map-options
          outlined
          class="q-mb-md"
        />
        <q-list>
          <q-item
            v-for="item in visibleLinks"
            :key="item.key"
            clickable
            :to="{ name: 'demo-' + item.key }"
            :exact="item.key === 'dashboard'"
          >
            <q-item-section avatar>
              <q-icon :name="item.icon" />
            </q-item-section>
            <q-item-section>{{ $t('nav.' + item.key) }}</q-item-section>
          </q-item>
        </q-list>
      </nav>
    </q-drawer>

    <q-page-container>
      <div class="demo-notice q-py-sm q-px-md">
        <strong>{{ $t('demo.title') }}</strong>
        <span>{{ $t('demo.message') }}</span>
      </div>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useQuasar } from 'quasar'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import brandIcon from '../assets/budmaster-icon.svg'
import { useDemoInventory } from '../stores/demo-inventory.js'

const quasar = useQuasar()
const inventory = useDemoInventory()
const route = useRoute()
const router = useRouter()
const { t, locale } = useI18n()
const localeOptions = [
  { value: 'en-US', label: 'English' },
  { value: 'sk-SK', label: 'Slovenčina' },
]
const drawerOpen = ref(false)
const themeKey = 'budmaster-theme'

const links = [
  { key: 'dashboard', icon: 'dashboard' },
  { key: 'products', icon: 'inventory_2' },
  { key: 'stock', icon: 'swap_horiz' },
  { key: 'movements', icon: 'history' },
  { key: 'categories', icon: 'category' },
  { key: 'warehouses', icon: 'warehouse' },
  { key: 'employees', icon: 'people', admin: true },
  { key: 'audit', icon: 'fact_check', admin: true },
]

const visibleLinks = computed(() => links.filter((item) => !item.admin || inventory.isAdmin))
const roleOptions = computed(() =>
  ['admin', 'staff'].map((value) => ({ value, label: t('demo.' + value) })),
)

try {
  quasar.dark.set(localStorage.getItem(themeKey) !== 'light')
} catch {
  quasar.dark.set(true)
}

function toggleTheme() {
  quasar.dark.toggle()
  try {
    localStorage.setItem(themeKey, quasar.dark.isActive ? 'dark' : 'light')
  } catch {
    // The theme still works in this tab when browser storage is unavailable.
  }
}

function changeRole(role) {
  inventory.setRole(role)
  if (!inventory.isAdmin && route.meta.demoAdmin) router.replace({ name: 'demo-dashboard' })
}
</script>

<style scoped>
.brand-link {
  display: inline-flex;
  max-width: 100%;
  align-items: center;
  gap: 7px;
  color: inherit;
  text-decoration: none;
  font-weight: 700;
  vertical-align: middle;
}

.brand-link img {
  width: 34px;
  max-width: 100%;
  height: auto;
}

.brand-accent {
  color: var(--admin-alert);
}

.demo-notice {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 2px 12px;
  border-bottom: 1px solid var(--admin-border);
  color: var(--admin-muted);
  font-size: 0.875rem;
}

.demo-notice strong {
  color: var(--admin-alert);
}
</style>
