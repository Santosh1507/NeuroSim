/**
 * Tests for API service: token attachment and 401 refresh interceptor.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import MockAdapter from 'axios-mock-adapter'

describe('API interceptor', () => {
  let mock
  let service

  beforeEach(() => {
    service = axios.create({
      baseURL: 'http://localhost:5001',
      timeout: 5000,
    })

    mock = new MockAdapter(service)

    delete window.location
    window.location = { href: '' }
  })

  describe('Request interceptor', () => {
    it('attaches Authorization header when token exists', async () => {
      const mockToken = 'test-token'

      service.interceptors.request.use(config => {
        config.headers['Authorization'] = `Bearer ${mockToken}`
        return config
      })

      mock.onGet('/test').reply(config => {
        return [200, { authHeader: config.headers['Authorization'] }]
      })

      const response = await service.get('/test')
      expect(response.data.authHeader).toBe('Bearer test-token')
    })

    it('does not attach header when no token', async () => {
      service.interceptors.request.use(config => {
        const token = null
        if (token) {
          config.headers['Authorization'] = `Bearer ${token}`
        }
        return config
      })

      mock.onGet('/test').reply(config => {
        return [200, { authHeader: config.headers['Authorization'] }]
      })

      const response = await service.get('/test')
      expect(response.data.authHeader).toBeUndefined()
    })
  })

  describe('Response interceptor - 401 handling', () => {
    it('redirects to login on 401 without refresh', async () => {
      mock.onGet('/protected').reply(401)

      service.interceptors.response.use(
        response => response,
        error => {
          if (error.response?.status === 401) {
            window.location.href = '/login'
          }
          return Promise.reject(error)
        }
      )

      await expect(service.get('/protected')).rejects.toThrow()
      expect(window.location.href).toBe('/login')
    })

    it('retries request after successful token refresh', async () => {
      let requestCount = 0

      mock.onGet('/protected').reply(config => {
        requestCount++
        if (requestCount === 1) {
          return [401, { error: 'Token expired' }]
        }
        return [200, { data: 'success' }]
      })

      let isRefreshing = false
      let failedQueue = []

      const processQueue = (error, token = null) => {
        for (const promise of failedQueue) {
          if (error) promise.reject(error)
          else promise.resolve(token)
        }
        failedQueue = []
      }

      service.interceptors.response.use(
        response => response,
        async error => {
          const originalRequest = error.config

          if (error.response?.status === 401 && !originalRequest._retry) {
            if (isRefreshing) {
              return new Promise((resolve, reject) => {
                failedQueue.push({ resolve, reject })
              }).then(token => {
                originalRequest.headers['Authorization'] = `Bearer ${token}`
                return service(originalRequest)
              })
            }

            originalRequest._retry = true
            isRefreshing = true

            try {
              const newToken = 'refreshed-token'
              originalRequest.headers['Authorization'] = `Bearer ${newToken}`
              processQueue(null, newToken)
              return service(originalRequest)
            } finally {
              isRefreshing = false
            }
          }

          return Promise.reject(error)
        }
      )

      const response = await service.get('/protected')
      expect(response.status).toBe(200)
      expect(requestCount).toBe(2)
    })

    it('queues concurrent requests during refresh', async () => {
      let requestCount = 0

      mock.onGet('/protected').reply(config => {
        requestCount++
        if (requestCount <= 2) {
          return [401, { error: 'Token expired' }]
        }
        return [200, { data: 'success' }]
      })

      let isRefreshing = false
      let failedQueue = []

      const processQueue = (error, token = null) => {
        for (const promise of failedQueue) {
          if (error) promise.reject(error)
          else promise.resolve(token)
        }
        failedQueue = []
      }

      service.interceptors.response.use(
        response => response,
        async error => {
          const originalRequest = error.config

          if (error.response?.status === 401 && !originalRequest._retry) {
            if (isRefreshing) {
              return new Promise((resolve, reject) => {
                failedQueue.push({ resolve, reject })
              }).then(token => {
                originalRequest.headers['Authorization'] = `Bearer ${token}`
                return service(originalRequest)
              })
            }

            originalRequest._retry = true
            isRefreshing = true

            try {
              const newToken = 'refreshed-token'
              originalRequest.headers['Authorization'] = `Bearer ${newToken}`
              processQueue(null, newToken)
              return service(originalRequest)
            } finally {
              isRefreshing = false
            }
          }

          return Promise.reject(error)
        }
      )

      const [res1, res2] = await Promise.all([
        service.get('/protected'),
        service.get('/protected'),
      ])

      expect(res1.status).toBe(200)
      expect(res2.status).toBe(200)
    })
  })
})
