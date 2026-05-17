import { ref, computed, provide, inject } from 'vue'
import { supabase } from './supabase'

const AUTH_KEY = 'auth'
const DEV_MODE = import.meta.env.VITE_DEV_AUTH === 'true'

const user = ref(null)
const session = ref(null)
const loading = ref(true)

export function useAuth() {
  const isSignedIn = computed(() => !!user.value)
  const currentUser = computed(() => user.value)

  async function init() {
    if (DEV_MODE) {
      const devUser = JSON.parse(localStorage.getItem('dev_user') || 'null')
      if (devUser) {
        user.value = devUser
        session.value = { access_token: 'dev-token' }
      }
      loading.value = false
      return
    }
    if (!supabase) {
      loading.value = false
      return
    }
    const { data: { session: s } } = await supabase.auth.getSession()
    session.value = s
    user.value = s?.user ?? null
    loading.value = false

    supabase.auth.onAuthStateChange((_event, s) => {
      session.value = s
      user.value = s?.user ?? null
    })
  }

  async function signIn(email, password) {
    if (DEV_MODE) {
      const devUser = { id: 'dev-user-123', email, email_confirmed_at: new Date().toISOString() }
      user.value = devUser
      session.value = { access_token: 'dev-token' }
      localStorage.setItem('dev_user', JSON.stringify(devUser))
      return
    }
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) throw error
  }

  async function signUp(email, password) {
    if (DEV_MODE) {
      const devUser = { id: 'dev-user-123', email, email_confirmed_at: new Date().toISOString() }
      user.value = devUser
      session.value = { access_token: 'dev-token' }
      localStorage.setItem('dev_user', JSON.stringify(devUser))
      return
    }
    const { error } = await supabase.auth.signUp({ email, password })
    if (error) throw error
  }

  async function signInWithOAuth(provider = 'google') {
    if (DEV_MODE) {
      const devUser = { id: 'dev-user-123', email: `dev@${provider}.com`, email_confirmed_at: new Date().toISOString() }
      user.value = devUser
      session.value = { access_token: 'dev-token' }
      localStorage.setItem('dev_user', JSON.stringify(devUser))
      return
    }
    const { error } = await supabase.auth.signInWithOAuth({ provider })
    if (error) throw error
  }

  async function signOut() {
    if (DEV_MODE) {
      user.value = null
      session.value = null
      localStorage.removeItem('dev_user')
      return
    }
    const { error } = await supabase.auth.signOut()
    if (error) throw error
  }

  return { user, session, loading, isSignedIn, currentUser, init, signIn, signUp, signInWithOAuth, signOut }
}

export function provideAuth() {
  const auth = useAuth()
  provide(AUTH_KEY, auth)
  return auth
}

export function injectAuth() {
  const auth = inject(AUTH_KEY)
  if (!auth) throw new Error('Auth not provided — wrap app with provideAuth')
  return auth
}

export function getAccessToken() {
  return session.value?.access_token ?? null
}
