import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  { path: '/login', component: () => import('../views/LoginView.vue') },
  {
    path: '/student',
    component: () => import('../layouts/StudentLayout.vue'),
    meta: { requiresAuth: true, role: 'student' },
    children: [
      { path: '', redirect: '/student/quests' },
      { path: 'quests', component: () => import('../views/student/DailyQuestsView.vue') },
      { path: 'calendar', component: () => import('../views/student/CalendarView.vue') },
      { path: 'creator', component: () => import('../views/student/CreatorBlockView.vue') },
      { path: 'floki', component: () => import('../views/student/AskFlokiView.vue') }
    ]
  },
  {
    path: '/admin',
    component: () => import('../layouts/AdminLayout.vue'),
    meta: { requiresAuth: true, role: 'teacher' },
    children: [
      { path: '', redirect: '/admin/week' },
      { path: 'week', component: () => import('../views/admin/WeekPlannerView.vue') },
      { path: 'programs', component: () => import('../views/admin/ProgramManagerView.vue') },
      { path: 'tasks', component: () => import('../views/admin/TaskManagerView.vue') },
      { path: 'calendar', component: () => import('../views/admin/CalendarManagerView.vue') },
      { path: 'projects', component: () => import('../views/admin/ProjectManagerView.vue') },
      { path: 'portfolio', component: () => import('../views/admin/PortfolioView.vue') },
      { path: 'analytics', component: () => import('../views/admin/AnalyticsView.vue') },
      { path: 'finances', component: () => import('../views/admin/FinancesView.vue') },
      { path: 'settings', component: () => import('../views/admin/SettingsView.vue') }
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/login' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (!auth.token) {
    auth.loadFromStorage()
  }

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    next('/login')
  } else if (to.path === '/login' && auth.isAuthenticated) {
    next(auth.isTeacher ? '/admin' : '/student')
  } else {
    next()
  }
})

export default router
