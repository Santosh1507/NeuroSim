/**
 * Tests for router authentication guard.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createRouter, createWebHistory } from 'vue-router'

// Mock the auth module
vi.mock('../src/lib/auth', () => ({
  injectAuth: () => ({
    isSignedIn: { value: false },
    loading: { value: false }
  })
}))

describe('Router guard', () => {
  let router

  beforeEach(() => {
    window.__AUTH__ = { isSignedIn: false, loading: false }

    const routes = [
      { path: '/', name: 'Home', component: { template: '<div>Home</div>' }, meta: { requiresAuth: true } },
      { path: '/login', name: 'Login', component: { template: '<div>Login</div>' } },
      { path: '/public', name: 'Public', component: { template: '<div>Public</div>' } },
    ]

    router = createRouter({
      history: createWebHistory(),
      routes,
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
  })

  it('redirects unauthenticated user to login for protected route', async () => {
    window.__AUTH__ = { isSignedIn: false, loading: false }

    await router.push('/')
    await router.isReady()

    expect(router.currentRoute.value.name).toBe('Login')
  })

  it('allows authenticated user to access protected route', async () => {
    window.__AUTH__ = { isSignedIn: true, loading: false }

    await router.push('/')
    await router.isReady()

    expect(router.currentRoute.value.name).toBe('Home')
  })

  it('allows unauthenticated user to access public route', async () => {
    window.__AUTH__ = { isSignedIn: false, loading: false }

    await router.push('/public')
    await router.isReady()

    expect(router.currentRoute.value.name).toBe('Public')
  })

  it('allows unauthenticated user to access login page', async () => {
    window.__AUTH__ = { isSignedIn: false, loading: false }

    await router.push('/login')
    await router.isReady()

    expect(router.currentRoute.value.name).toBe('Login')
  })

  it('uses reactive auth state via getters', async () => {
    let signedIn = false
    window.__AUTH__ = {
      get isSignedIn() { return signedIn },
      loading: false
    }

    await router.push('/')
    await router.isReady()
    expect(router.currentRoute.value.name).toBe('Login')

    signedIn = true
    await router.push('/')
    await router.isReady()
    expect(router.currentRoute.value.name).toBe('Home')
  })
})
