import { createRouter, createWebHistory } from 'vue-router'
import Profile from '../views/Profile.vue'
import Dashboard from '../views/Dashboard.vue'
import Login from '../views/Login.vue'
import Billing from '../views/Billing.vue'
import ResetPassword from '../views/ResetPassword.vue'
import AdminLayout from '../views/admin/AdminLayout.vue'
import AdminDashboard from '../views/admin/AdminDashboard.vue'
import AdminUsers from '../views/admin/AdminUsers.vue'
import AdminShops from '../views/admin/AdminShops.vue'
import AdminTokens from '../views/admin/AdminTokens.vue'
import AdminReturns from '../views/admin/AdminReturns.vue'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'profile',
      component: Profile,
      meta: { requiresAuth: true }
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: Dashboard,
      meta: { requiresAuth: true }
    },
    {
      path: '/login',
      name: 'login',
      component: Login
    },
    {
      path: '/reset-password',
      name: 'reset-password',
      component: ResetPassword
    },
    {
      path: '/billing',
      name: 'billing',
      component: Billing,
      meta: { requiresAuth: true }
    },
    {
      path: '/admin',
      component: AdminLayout,
      meta: { requiresAuth: true, requiresAdmin: true },
      children: [
        {
          path: '',
          name: 'admin-dashboard',
          component: AdminDashboard,
        },
        {
          path: 'users',
          name: 'admin-users',
          component: AdminUsers,
        },
        {
          path: 'shops',
          name: 'admin-shops',
          component: AdminShops,
        },
        {
          path: 'tokens',
          name: 'admin-tokens',
          component: AdminTokens,
        },
        {
          path: 'returns',
          name: 'admin-returns',
          component: AdminReturns,
        },
      ]
    }
  ]
})

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()
  await authStore.initialize()

  if (to.meta.requiresAuth && !authStore.user) {
    return next('/login')
  }
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    return next('/')
  }
  // Redirect authenticated users away from /login
  if (authStore.user && !authStore.isAdmin && to.name === 'login') {
    return next('/')
  }
  // Admins always go to admin panel — they have no regular user interface
  if (authStore.isAdmin && !to.meta.requiresAdmin && to.path !== '/login' && to.path !== '/reset-password') {
    return next('/admin')
  }
  next()
})

export default router
