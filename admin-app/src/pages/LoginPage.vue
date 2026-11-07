<template>
  <q-page class="flex flex-center q-pa-md">
    <q-card flat bordered class="login-card q-pa-lg">
      <img :src="budmasterLogo" alt="Budmaster" class="login-logo" />
      <h1 class="text-h5 q-mt-none q-mb-lg">{{ $t('login.title') }}</h1>

      <q-form
        v-if="isDemoAvailable"
        class="q-gutter-y-md"
        @submit="submitPreview"
        @validation-error="submitted = false"
      >
        <q-input
          v-model="username"
          :label="$t('login.username')"
          :rules="[(value) => Boolean(value?.trim()) || $t('login.usernameRequired')]"
          autocomplete="username"
          outlined
          lazy-rules
          @update:model-value="submitted = false"
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
            @update:model-value="submitted = false"
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
          unelevated
          no-caps
        />

        <p v-if="submitted" class="q-mb-none" role="status">
          {{ $t('login.previewSuccess') }}
        </p>
      </q-form>
      <p v-else class="admin-muted">{{ $t('login.pending') }}</p>
      <q-separator v-if="isDemoAvailable" class="q-my-lg" />
      <q-btn
        v-if="isDemoAvailable"
        class="full-width admin-action"
        :to="{ name: 'demo-dashboard' }"
        :label="$t('login.openDemo')"
        icon="dashboard"
        outline
        no-caps
      />
    </q-card>
  </q-page>
</template>

<script setup>
import { ref } from 'vue'
import budmasterLogo from '../assets/budmaster-logo-dark.svg'

const isDemoAvailable = import.meta.env.DEV
const username = ref('')
const password = ref('')
const isPasswordVisible = ref(false)
const submitted = ref(false)

function hidePasswordOnExit(event) {
  if (!event.currentTarget.contains(event.relatedTarget)) {
    isPasswordVisible.value = false
  }
}

function submitPreview() {
  isPasswordVisible.value = false
  password.value = ''
  submitted.value = true
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

.login-submit {
  min-height: $admin-control-height;
  border-radius: $admin-control-radius;
  font-size: 1rem;
  font-weight: 600;
}
</style>
