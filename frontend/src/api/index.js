import axios from 'axios'
import { getAccessToken } from '../lib/auth'
import { supabase } from '../lib/supabase'

const DEV_MODE = import.meta.env.VITE_DEV_AUTH === 'true'

// Create axios instance
const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001',
  timeout: 300000,
  headers: {
    'Content-Type': 'application/json'
  }
})

let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  for (const promise of failedQueue) {
    if (error) {
      promise.reject(error)
    } else {
      promise.resolve(token)
    }
  }
  failedQueue = []
}

// Request interceptor - attach JWT token
service.interceptors.request.use(
  config => {
    const token = getAccessToken()
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor - handle 401 with token refresh
service.interceptors.response.use(
  response => {
    const res = response.data

    if (!res.success && res.success !== undefined) {
      console.error('API Error:', res.error || res.message || 'Unknown error')
      return Promise.reject(new Error(res.error || res.message || 'Error'))
    }

    return res
  },
  async error => {
    console.error('Response error:', error)

    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (DEV_MODE) {
        // In dev mode, just redirect to login
        window.location.href = '/login'
        return Promise.reject(error)
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(token => {
          originalRequest.headers['Authorization'] = `Bearer ${token}`
          return service(originalRequest)
        }).catch(err => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const { data, error: refreshError } = await supabase.auth.refreshSession()
        if (refreshError) throw refreshError

        const newToken = data.session?.access_token
        if (!newToken) throw new Error('No access token after refresh')

        originalRequest.headers['Authorization'] = `Bearer ${newToken}`
        processQueue(null, newToken)
        return service(originalRequest)
      } catch (refreshErr) {
        processQueue(refreshErr, null)
        window.location.href = '/login'
        return Promise.reject(refreshErr)
      } finally {
        isRefreshing = false
      }
    }

    if (error.code === 'ECONNABORTED' && error.message.includes('timeout')) {
      console.error('Request timeout')
    }

    if (error.message === 'Network Error') {
      console.error('Network error - please check your connection')
    }

    return Promise.reject(error)
  }
)

// Request function with retry
export const requestWithRetry = async (requestFn, maxRetries = 3, delay = 1000) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await requestFn()
    } catch (error) {
      if (i === maxRetries - 1) throw error

      console.warn(`Request failed, retrying (${i + 1}/${maxRetries})...`)
      await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)))
    }
  }
}

export default service
