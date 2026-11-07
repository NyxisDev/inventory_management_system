<template>
  <q-layout class="login-layout">
    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { useQuasar } from 'quasar'

const quasar = useQuasar()
quasar.dark.set(true)
</script>

<style scoped>
.login-layout {
  --q-dark-page: #0b1121;
  --q-dark: #151d30;
  --q-negative: #ff6b75;

  background: var(--q-dark-page);
}
</style>