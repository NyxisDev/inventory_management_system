<template>
  <NotFoundBlock />
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { usePageMeta } from '@/composables/use-page-meta'
import NotFoundBlock from '@/components/NotFoundBlock.vue'

defineOptions({
  name: 'ErrorNotFound',
  preFetch({ ssrContext }) {
    // Real 404 status for search engines.
    if (ssrContext) ssrContext.httpStatus = 404
  },
})

const { t } = useI18n()
const route = useRoute()

usePageMeta(() => ({ title: t('meta.notFoundTitle'), path: route.path, noindex: true }))
</script>
