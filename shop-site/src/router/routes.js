const routes = [
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    children: [
      { path: '', name: 'home', component: () => import('@/pages/IndexPage.vue') },
      { path: 'catalog', name: 'catalog', component: () => import('@/pages/CatalogPage.vue') },
      {
        path: 'catalog/:categorySlug([a-z0-9-]{1,150})',
        name: 'category',
        component: () => import('@/pages/CatalogPage.vue'),
      },
      {
        path: 'product/:slug([a-z0-9-]{1,255})',
        name: 'product',
        component: () => import('@/pages/ProductPage.vue'),
      },
      { path: 'search', name: 'search', component: () => import('@/pages/SearchPage.vue') },
      { path: 'contacts', name: 'contacts', component: () => import('@/pages/ContactsPage.vue') },
      { path: ':catchAll(.*)*', name: 'not-found', component: () => import('@/pages/ErrorNotFound.vue') },
    ],
  },
]

export default routes
