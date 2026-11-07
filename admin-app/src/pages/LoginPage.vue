<template>
  <q-page class="flex flex-center q-pa-md">
    <q-card flat bordered class="login-card q-pa-lg">
      <img :src="budmasterLogo" alt="Budmaster" class="login-logo" />
      <h1 class="text-h5 q-mt-none q-mb-lg">{{ $t('login.title') }}</h1>

      <p v-if="route.query.reason === 'idle'" class="admin-muted" role="status">
        {{ $t('login.idle') }}
      </p>
      <q-form class="q-gutter-y-md" @submit="submit">
        <q-input
          v-model="username"
          :label="$t('login.username')"
          :rules="[(value) => Boolean(value?.trim()) || $t('login.usernameRequired')]"
          autocomplete="username"
          outlined
          lazy-rules
          @update:model-value="error = ''"
        />

        <div class="password-control" @focusout="hidePasswordOnExit">
          <q-input
            v-model="password"
            :label="$t('login.password')"
            :rules="[(value) => Boolean(value) || $t('login.passwordRequired')]"
            :type="isPasswordVisible ? 'text' : 'password'"
            autocomplete="current-password"
            outlined
            lazy-rules
            @update:model-value="error = ''"
          >
            <template #append>
              <q-btn
                class="password-toggle"
                type="button"
                flat
                round
                :icon="isPasswordVisible ? 'visibility_off' : 'visibility'"
                :aria-label="$t(isPasswordVisible ? 'login.hidePassword' : 'login.showPassword')"
                @click="isPasswordVisible = !isPasswordVisible"
              />
            </template>
          </q-input>
        </div>

        <q-btn
          class="login-submit full-width"
          type="submit"
          color="primary"
          text-color="dark"
          :label="$t('login.submit')"
          :loading="loading"
          unelevated
          no-caps
        />
        <p v-if="error" class="login-error q-mb-none" role="alert">{{ error }}</p>
      </q-form>
    </q-card>
  </q-page>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import budmasterLogo from '../assets/budmaster-logo-dark.svg'
import { apiErrorMessage } from '../boot/axios.js'
import { useAuthStore } from '../stores/auth.js'
import { useInventory } from '../stores/inventory.js'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const auth = useAuthStore()
const inventory = useInventory()

const username = ref('')
const password = ref('')
const isPasswordVisible = ref(false)
const loading = ref(false)
const error = ref('')

function hidePasswordOnExit(event) {
  if (!event.currentTarget.contains(event.relatedTarget)) {
    isPasswordVisible.value = false
  }
}

async function submit() {
  isPasswordVisible.value = false
  loading.value = true
  error.value = ''
  try {
    await auth.login(username.value.trim(), password.value)
    inventory.reset()
    const redirect = String(route.query.redirect || '')
    // Only internal paths, never an external URL
    router.replace(redirect.startsWith('/') && !redirect.startsWith('//') ? redirect : '/')
  } catch (err) {
    error.value = apiErrorMessage(err) || t('errors.generic')
  } finally {
    password.value = ''
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-card {
  width: 100%;
  max-width: 400px;
  border-radius: $admin-radius;
}

.login-logo {
  display: block;
  width: 220px;
  max-width: 100%;
  height: auto;
  margin-bottom: 24px;
}

.password-toggle {
  min-width: $admin-control-height;
  min-height: $admin-control-height;
}

.password-control :deep(input::-ms-reveal) {
  display: none;
}

.login-error {
  color: var(--q-negative);
}

.login-submit {
  min-height: $admin-control-height;
  border-radius: $admin-control-radius;
  font-size: 1rem;
  font-weight: 600;
}
</style>
