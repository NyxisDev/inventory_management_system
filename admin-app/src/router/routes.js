const demoRoutes = [
  {
    path: '/demo',
    component: () => import('../layouts/DemoLayout.vue'),
    children: [
      { path: '', name: 'demo-dashboard', component: () => import('../pages/DashboardPage.vue') },
      {
        path: 'products',
        name: 'demo-products',
        component: () => import('../pages/ProductsPage.vue'),
      },
      {
        path: 'products/new',
        name: 'demo-product-new',
        component: () => import('../pages/ProductFormPage.vue'),
      },
      {
        path: 'products/:id(\\d+)',
        name: 'demo-product',
        component: () => import('../pages/ProductFormPage.vue'),
      },
      { path: 'stock', name: 'demo-stock', component: () => import('../pages/StockPage.vue') },
      {
        path: 'movements',
        name: 'demo-movements',
        component: () => import('../pages/MovementsPage.vue'),
      },
      {
        path: 'categories',
        name: 'demo-categories',
        component: () => import('../pages/DirectoryPage.vue'),
        props: { kind: 'categories' },
      },
      {
        path: 'warehouses',
        name: 'demo-warehouses',
        component: () => import('../pages/DirectoryPage.vue'),
        props: { kind: 'warehouses' },
      },
      {
        path: 'employees',
        name: 'demo-employees',
        component: () => import('../pages/DirectoryPage.vue'),
        props: { kind: 'employees' },
        meta: { demoAdmin: true },
      },
      {
        path: 'audit',
        name: 'demo-audit',
        component: () => import('../pages/AuditPage.vue'),
        meta: { demoAdmin: true },
      },
    ],
  },
]

export default [
  { path: '/', redirect: { name: 'login' } },
  {
    path: '/login',
    component: () => import('../layouts/AuthLayout.vue'),
    children: [{ path: '', name: 'login', component: () => import('../pages/LoginPage.vue') }],
  },
  ...(import.meta.env.DEV ? demoRoutes : []),
  { path: '/:catchAll(.*)*', component: () => import('../pages/ErrorNotFound.vue') },
]
