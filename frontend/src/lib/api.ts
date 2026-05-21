/**
 * Centralized Axios API client.
 *
 * All components should import `apiClient` from here instead of
 * creating their own axios instances or hardcoding API_URL.
 *
 * Handles:
 *   - Base URL from NEXT_PUBLIC_API_URL env var (falls back to localhost)
 *   - Automatic Authorization header injection from Supabase session
 *   - Consistent error messages for 4xx/5xx responses
 *   - 10-second default timeout
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { supabase } from './supabase'

export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 30_000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ─── Request interceptor: attach auth token ───────────────────────────────

apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    if (supabase) {
      const { data: { session } } = await supabase.auth.getSession()
      if (session?.access_token) {
        config.headers.set('Authorization', `Bearer ${session.access_token}`)
      }
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ─── Response interceptor: normalize errors ──────────────────────────────

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    const serverMessage = error.response?.data?.detail
    const status = error.response?.status

    if (status === 429) {
      return Promise.reject(new Error('Rate limit exceeded. Please wait a moment and try again.'))
    }
    if (status === 403) {
      return Promise.reject(new Error(serverMessage || 'Free tier limit reached. Upgrade to Pro for unlimited analyses.'))
    }
    if (status === 401) {
      return Promise.reject(new Error('Authentication required. Please sign in.'))
    }
    if (serverMessage) {
      return Promise.reject(new Error(serverMessage))
    }
    if (!error.response) {
      return Promise.reject(new Error('Cannot reach the NeuroSim API. Check your connection.'))
    }
    return Promise.reject(error)
  }
)

export default apiClient
