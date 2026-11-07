import { defineRouter } from '#q-app'
import { createMemoryHistory, createRouter, createWebHashHistory, createWebHistory } from 'vue-router'
import routes from './routes'

// SSR: memory history on the server, normal URLs in the browser.
// SPA build (static demo on GitHub Pages): hash URLs, because a static host
// cannot answer deep links like /product/x with the app.
function pickHistory() {
  if (import.meta.env.SSR) return createMemoryHistory()
  if (import.meta.env.QUASAR_MODE === 'spa') return createWebHashHistory()
  return createWebHistory()
}

export default defineRouter(function (/* { store, ssrContext } */) {
  return createRouter({
    routes,
    history: pickHistory(),
    scrollBehavior(to, from, savedPosition) {
      if (savedPosition) return savedPosition
      // Filter, sort and page changes on the same page keep the scroll position
      // near the results instead of jumping to the very top.
      if (to.path === from.path) return false
      return { left: 0, top: 0 }
    },
  })
})
