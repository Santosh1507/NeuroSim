<template>
  <div class="login-container">
    <div class="login-card">
      <h1 class="login-title">MiroFish Offline</h1>
      <p class="login-subtitle">Sign in to continue</p>

      <button class="oauth-btn google-btn" @click="handleGoogleSignIn">
        <span class="btn-icon">G</span>
        Sign in with Google
      </button>

      <div class="divider"><span>or</span></div>

      <form @submit.prevent="handleEmailSignIn">
        <input v-model="email" type="email" placeholder="Email" class="input" required />
        <input v-model="password" type="password" placeholder="Password" class="input" required />
        <p v-if="error" class="error-msg">{{ error }}</p>
        <button type="submit" class="submit-btn" :disabled="submitting">
          {{ submitting ? 'Signing in...' : 'Sign In' }}
        </button>
      </form>

      <p class="signup-link">
        No account?
        <a href="#" @click.prevent="mode = 'signup'">Sign up</a>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { injectAuth } from '../lib/auth'

const router = useRouter()
const { signIn, signUp, signInWithOAuth } = injectAuth()

const email = ref('')
const password = ref('')
const error = ref('')
const submitting = ref(false)
const mode = ref('signin')

async function handleGoogleSignIn() {
  try {
    error.value = ''
    await signInWithOAuth('google')
  } catch (e) {
    error.value = e.message
  }
}

async function handleEmailSignIn() {
  submitting.value = true
  error.value = ''
  try {
    if (mode.value === 'signup') {
      await signUp(email.value, password.value)
      error.value = 'Check your email for the confirmation link'
    } else {
      await signIn(email.value, password.value)
      router.push('/')
    }
  } catch (e) {
    error.value = e.message
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000;
  font-family: 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
}
.login-card {
  background: #fff;
  padding: 48px;
  width: 400px;
  max-width: 90vw;
}
.login-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 8px 0;
}
.login-subtitle {
  color: #666;
  margin: 0 0 32px 0;
  font-size: 0.9rem;
}
.oauth-btn {
  width: 100%;
  padding: 14px;
  border: 1px solid #ddd;
  background: #fff;
  cursor: pointer;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  transition: background 0.2s;
}
.oauth-btn:hover { background: #f5f5f5; }
.btn-icon { font-weight: 700; font-size: 1.1rem; }
.divider {
  display: flex;
  align-items: center;
  margin: 24px 0;
  color: #bbb;
  font-size: 0.8rem;
}
.divider::before, .divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #eee;
}
.divider span { padding: 0 12px; }
.input {
  width: 100%;
  padding: 12px;
  margin-bottom: 12px;
  border: 1px solid #ddd;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9rem;
  outline: none;
  box-sizing: border-box;
}
.input:focus { border-color: #000; }
.submit-btn {
  width: 100%;
  padding: 14px;
  background: #000;
  color: #fff;
  border: none;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  cursor: pointer;
  font-size: 0.9rem;
}
.submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.error-msg { color: #e00; font-size: 0.85rem; margin-bottom: 12px; }
.signup-link { margin-top: 20px; font-size: 0.85rem; color: #666; text-align: center; }
.signup-link a { color: #000; font-weight: 600; }
</style>
