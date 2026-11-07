import { defineRouter } from '#q-app'
import {
  createMemoryHistory,
  createRouter,
  createWebHashHistory,
  createWebHistory,
} from 'vue-router'

import routes from './routes.js'
import { Notify } from 'quasar'
import { useAuthStore } from '../stores/auth.js'
import { useInventory } from '../stores/inventory.js'

/*
 * If not building with SSR mode, you can
 * directly export the Router instantiation;
 *
 * The function below can be async too; either use
 * async/await or return a Promise which resolves
 * with the Router instance.
 */

export default defineRouter(({ store }) => {
  const createHistory = import.meta.env.QUASAR_SERVER
    ? createMemoryHistory
    : import.meta.env.QUASAR_VUE_ROUTER_MODE === 'history'
      ? createWebHistory
      : createWebHashHistory

  const Router = createRouter({
    scrollBehavior: () => ({ left: 0, top: 0 }),
    routes,

    // Leave this as is and make changes in quasar.conf.js instead!
    // quasar.conf.js -> build -> vueRouterMode
    // quasar.conf.js -> build -> publicPath
    history: createHistory(import.meta.env.QUASAR_VUE_ROUTER_BASE),
  })

  Router.beforeEach(async (to) => {
    const auth = useAuthStore(store)
    // First navigation: try to restore the session from the refresh cookie
    if (!auth.restored) await auth.restore()

    if (to.name === 'login') {
      return auth.isAuthenticated ? { name: 'app-dashboard' } : true
    }
    if (to.matched.some((record) => record.meta.requiresAuth) && !auth.isAuthenticated) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }
    if (to.matched.some((record) => record.meta.requiresAdmin) && !auth.isAdmin) {
      Notify.create({ message: 'This page is available to administrators only.', color: 'warning' })
      return { name: 'app-dashboard' }
    }
    if (auth.isAuthenticated) await useInventory(store).ensureLoaded()
    return true
  })

  return Router
})
