// meta.requiresAuth: signed-in employees only; meta.requiresAdmin: admins only.
// The backend checks permissions on every request; these flags only shape the UI.
const appRoutes = [
  {
    path: '/',
    component: () => import('../layouts/DemoLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', name: 'app-dashboard', component: () => import('../pages/DashboardPage.vue') },
      {
        path: 'products',
        name: 'app-products',
        component: () => import('../pages/ProductsPage.vue'),
      },
      {
        path: 'products/new',
        name: 'app-product-new',
        component: () => import('../pages/ProductFormPage.vue'),
      },
      {
        path: 'products/:id(\\d+)',
        name: 'app-product',
        component: () => import('../pages/ProductFormPage.vue'),
      },
      { path: 'stock', name: 'app-stock', component: () => import('../pages/StockPage.vue') },
      {
        path: 'movements',
        name: 'app-movements',
        component: () => import('../pages/MovementsPage.vue'),
      },
      {
        path: 'categories',
        name: 'app-categories',
        component: () => import('../pages/DirectoryPage.vue'),
        props: { kind: 'categories' },
      },
      {
        path: 'warehouses',
        name: 'app-warehouses',
        component: () => import('../pages/DirectoryPage.vue'),
        props: { kind: 'warehouses' },
      },
      {
        path: 'employees',
        name: 'app-employees',
        component: () => import('../pages/DirectoryPage.vue'),
        props: { kind: 'employees' },
        meta: { requiresAdmin: true },
      },
      {
        path: 'audit',
        name: 'app-audit',
        component: () => import('../pages/AuditPage.vue'),
        meta: { requiresAdmin: true },
      },
    ],
  },
]

export default [
  {
    path: '/login',
    component: () => import('../layouts/AuthLayout.vue'),
    children: [{ path: '', name: 'login', component: () => import('../pages/LoginPage.vue') }],
  },
  ...appRoutes,
  { path: '/:catchAll(.*)*', component: () => import('../pages/ErrorNotFound.vue') },
]
