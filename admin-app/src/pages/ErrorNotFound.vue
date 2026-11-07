<template>
  <main class="fullscreen flex flex-center q-pa-lg text-center">
    <div>
      <p class="text-h3 q-mb-sm">404</p>
      <h1 class="text-h5 q-mt-none">{{ $t('common.notFound') }}</h1>
      <q-btn
        class="admin-action"
        :to="{ name: 'login' }"
        :label="$t('common.goBack')"
        color="primary"
        text-color="dark"
        unelevated
        no-caps
      />
    </div>
  </main>
</template>
