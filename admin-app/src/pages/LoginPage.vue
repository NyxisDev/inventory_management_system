<template>
  <q-page class="flex flex-center q-pa-md">
    <q-card flat bordered class="login-card q-pa-lg">
      <img :src="budmasterLogo" alt="Budmaster" class="login-logo" />
      <h1 class="text-h5 q-mt-none q-mb-lg">{{ $t('login.title') }}</h1>

      <q-form
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
    </q-card>
  </q-page>
</template>

<script setup>
import { ref } from 'vue'
import budmasterLogo from '../assets/budmaster-logo-dark.svg'

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
  submitted.value = true
}
</script>

<style scoped>
.login-card {
  --q-primary: #ff8a00;

  width: 100%;
  max-width: 400px;
  border-radius: 16px;
}

.login-logo {
  display: block;
  width: 220px;
  max-width: 100%;
  height: auto;
  margin-bottom: 24px;
}

.password-toggle {
  min-width: 44px;
  min-height: 44px;
}

.password-control :deep(input::-ms-reveal) {
  display: none;
}

.login-submit {
  min-height: 44px;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
}
</style>