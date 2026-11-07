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
          <router-link :to="{ name: 'app-dashboard' }" class="brand-link">
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
        <q-btn flat no-caps class="admin-action" icon="account_circle">
          <span class="gt-xs q-ml-sm">{{ auth.fullName }}</span>
          <q-menu anchor="bottom right" self="top right">
            <q-list style="min-width: 220px">
              <q-item>
                <q-item-section>
                  <q-item-label>{{ auth.fullName }}</q-item-label>
                  <q-item-label caption>{{ $t('demo.' + auth.employee?.role) }}</q-item-label>
                </q-item-section>
              </q-item>
              <q-separator />
              <q-item v-close-popup clickable @click="passwordDialog = true">
                <q-item-section avatar><q-icon name="key" /></q-item-section>
                <q-item-section>{{ $t('account.changePassword') }}</q-item-section>
              </q-item>
              <q-item v-close-popup clickable @click="signOut">
                <q-item-section avatar><q-icon name="logout" /></q-item-section>
                <q-item-section>{{ $t('account.signOut') }}</q-item-section>
              </q-item>
            </q-list>
          </q-menu>
        </q-btn>
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
            :to="{ name: 'app-' + item.key }"
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
      <router-view />
      <q-dialog v-model="passwordDialog" persistent>
        <q-card class="q-pa-sm" style="width: 420px; max-width: 92vw">
          <q-form @submit="changePassword">
            <q-card-section>
              <h2 class="admin-section-title q-my-none">{{ $t('account.changePassword') }}</h2>
            </q-card-section>
            <q-card-section class="q-pt-none q-gutter-y-md">
              <q-input
                v-model="passwords.old"
                type="password"
                outlined
                autocomplete="current-password"
                :label="$t('account.currentPassword')"
                :rules="[(v) => Boolean(v) || $t('common.required')]"
              />
              <q-input
                v-model="passwords.new"
                type="password"
                outlined
                autocomplete="new-password"
                maxlength="72"
                :label="$t('directory.newPassword')"
                :hint="$t('directory.passwordHint')"
                :rules="[strongPassword]"
              />
            </q-card-section>
            <q-card-actions align="right">
              <q-btn v-close-popup flat no-caps :label="$t('common.cancel')" />
              <q-btn
                type="submit"
                color="primary"
                text-color="dark"
                unelevated
                no-caps
                :loading="savingPassword"
                :label="$t('common.save')"
              />
            </q-card-actions>
          </q-form>
        </q-card>
      </q-dialog>
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useQuasar } from 'quasar'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import brandIcon from '../assets/budmaster-icon.svg'
import { api } from '../boot/axios.js'
import { useInventoryActions } from '../composables/use-inventory-actions.js'
import { useAuthStore } from '../stores/auth.js'
import { useInventory } from '../stores/inventory.js'

const quasar = useQuasar()
const inventory = useInventory()
const auth = useAuthStore()
const { attempt } = useInventoryActions()
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
const passwordDialog = ref(false)
const savingPassword = ref(false)
const passwords = ref({ old: '', new: '' })
const strongPassword = (value) =>
  (String(value ?? '').length >= 10 && /\p{L}/u.test(value) && /\d/.test(value)) ||
  t('directory.passwordHint')

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

async function signOut() {
  await auth.logout()
  inventory.reset()
  router.replace({ name: 'login' })
}

// After a password change all other sessions end; this one gets fresh tokens
async function changePassword() {
  savingPassword.value = true
  const ok = await attempt(async () => {
    try {
      const { data } = await api.post('/auth/change-password', {
        old_password: passwords.value.old,
        new_password: passwords.value.new,
      })
      auth.setSession(data)
    } catch (error) {
      const detail = error?.response?.data?.detail
      throw new Error(detail ? 'api:' + detail : 'errors.generic', { cause: error })
    }
  }, 'common.saved')
  savingPassword.value = false
  if (ok) {
    passwords.value = { old: '', new: '' }
    passwordDialog.value = false
  }
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
