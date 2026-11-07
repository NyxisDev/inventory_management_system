<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { useMeta } from 'quasar'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { localeInfo, rememberLocale } from '@/i18n/locales.js'

defineOptions({ name: 'App' })

const { locale } = useI18n({ useScope: 'global' })
const route = useRoute()

useMeta(() => ({ htmlAttr: { lang: localeInfo(locale.value).tag } }))

// A shared link with ?lang= also sets the language for the next visits.
onMounted(() => {
  if (route.query.lang !== undefined) rememberLocale(locale.value)
})
</script>
