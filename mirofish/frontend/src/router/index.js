import { createRouter, createWebHistory } from 'vue-router'
import Landing from '../views/Landing.vue'
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import Process from '../views/MainView.vue'
import SimulationView from '../views/SimulationView.vue'
import SimulationRunView from '../views/SimulationRunView.vue'
import ReportView from '../views/ReportView.vue'
import InteractionView from '../views/InteractionView.vue'
import NeuroSimUpload from '../views/NeuroSimUpload.vue'
import NeuroSimDashboard from '../views/NeuroSimDashboard.vue'
import NeuroSimAnalysis from '../views/NeuroSimAnalysis.vue'
import CrisisUpload from '../views/CrisisUpload.vue'
import CrisisProgress from '../views/CrisisProgress.vue'
import CrisisReport from '../views/CrisisReport.vue'

const routes = [
  {
    path: '/',
    name: 'Landing',
    component: Landing
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/dashboard',
    name: 'Home',
    component: Home,
    meta: { requiresAuth: true }
  },
  {
    path: '/analyze',
    name: 'NeuroSimAnalysis',
    component: NeuroSimAnalysis,
    meta: { requiresAuth: true }
  },
  {
    path: '/process/:projectId',
    name: 'Process',
    component: Process,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/simulation/:simulationId',
    name: 'Simulation',
    component: SimulationView,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/simulation/:simulationId/start',
    name: 'SimulationRun',
    component: SimulationRunView,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/report/:reportId',
    name: 'Report',
    component: ReportView,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/interaction/:reportId',
    name: 'Interaction',
    component: InteractionView,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/neurosim',
    name: 'NeuroSimUpload',
    component: NeuroSimUpload,
    meta: { requiresAuth: true }
  },
  {
    path: '/neurosim/results/:experimentId',
    name: 'NeuroSimDashboard',
    component: NeuroSimDashboard,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/crisis/upload',
    name: 'CrisisUpload',
    component: CrisisUpload,
    meta: { requiresAuth: true }
  },
  {
    path: '/crisis/progress/:simulationId',
    name: 'CrisisProgress',
    component: CrisisProgress,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/crisis/report/:simulationId',
    name: 'CrisisReport',
    component: CrisisReport,
    props: true,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const auth = window.__AUTH__
  if (!auth || auth.loading) {
    next()
    return
  }
  if (to.meta.requiresAuth && !auth.isSignedIn) {
    next({ name: 'Login' })
  } else {
    next()
  }
})

export default router
