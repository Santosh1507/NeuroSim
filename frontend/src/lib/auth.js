import { ref, computed, provide, inject } from 'vue'
import { supabase } from './supabase'

const AUTH_KEY = 'auth'

const user = ref(null)
const session = ref(null)
const loading = ref(true)

export function useAuth() {
  const isSignedIn = computed(() => !!user.value)
  const currentUser = computed(() => user.value)

  async function init() {
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
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) throw error
  }

  async function signUp(email, password) {
    const { error } = await supabase.auth.signUp({ email, password })
    if (error) throw error
  }

  async function signInWithOAuth(provider = 'google') {
    const { error } = await supabase.auth.signInWithOAuth({ provider })
    if (error) throw error
  }

  async function signOut() {
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
