import { defineRouter } from '#q-app'
import { createMemoryHistory, createRouter, createWebHistory } from 'vue-router'
import routes from './routes'

export default defineRouter(function (/* { store, ssrContext } */) {
  const createHistory = import.meta.env.SSR ? createMemoryHistory : createWebHistory

  return createRouter({
    routes,
    history: createHistory(),
    scrollBehavior(to, from, savedPosition) {
      if (savedPosition) return savedPosition
      // Filter, sort and page changes on the same page keep the scroll position
      // near the results instead of jumping to the very top.
      if (to.path === from.path) return false
      return { left: 0, top: 0 }
    },
  })
})
