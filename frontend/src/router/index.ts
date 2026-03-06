import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'
import Login from '@/views/Login.vue'
import { useUserStore } from '@/stores/user'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { title: '登录' }
  },
  {
    path: '/',
    component: MainLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '经营总览', icon: 'dashboard', requiresAuth: true }
      },
      {
        path: 'production',
        name: 'Production',
        component: () => import('@/views/ProductionQuery.vue'),
        meta: { title: '生产', icon: 'bar-chart', requiresAuth: true }
      },
      {
        path: 'inventory',
        name: 'Inventory',
        component: () => import('@/views/InventoryQuery.vue'),
        meta: { title: '库存', icon: 'database', requiresAuth: true }
      },
      {
        path: 'sales',
        name: 'Sales',
        component: () => import('@/views/SalesQuery.vue'),
        meta: { title: '销售', icon: 'shopping', requiresAuth: true }
      },
      {
        path: 'sales-forecast',
        name: 'SalesForecast',
        component: () => import('@/views/SalesForecast.vue'),
        meta: { title: '销售预测', icon: 'line-chart', requiresAuth: true }
      },
      {
        path: 'balance',
        name: 'Balance',
        component: () => import('@/views/BalanceOptimize.vue'),
        meta: { title: '产销平衡', icon: 'aim', requiresAuth: true }
      },
      {
        path: 'optimizer',
        name: 'Optimizer',
        component: () => import('@/views/BalanceOptimizeV2.vue'),
        meta: { title: '运筹优化引擎', icon: 'experiment', requiresAuth: true }
      },
      {
        path: 'data',
        name: 'DataManagement',
        component: () => import('@/views/DataManagement.vue'),
        meta: { title: '后台配置', icon: 'cloud-upload', requiresAuth: true }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!userStore.token) {
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
