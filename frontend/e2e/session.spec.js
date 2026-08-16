import { test, expect } from '@playwright/test'
import { login } from './helpers.js'

test.describe('session handling', () => {
  test('an expired access token is refreshed silently, once', async ({ page }) => {
    // Regression: the server rotates the refresh token on every use and treats
    // a replay as a compromised session, clearing refresh_token_id outright.
    // Several requests failing at once must therefore share a single refresh --
    // independent ones would spend the same token twice and end the session.
    await login(page, 'teacher')

    const result = await page.evaluate(async () => {
      const { api } = await import('/src/api/client.js')
      const calls = []
      const originalFetch = window.fetch
      window.fetch = (...args) => {
        calls.push(String(args[0]))
        return originalFetch(...args)
      }

      localStorage.setItem('token', 'eyJhbGciOiJIUzI1NiJ9.expired.signature')

      const outcomes = await Promise.allSettled([
        api.get('/tasks/'),
        api.get('/events/'),
        api.get('/projects/'),
        api.get('/expenses/'),
      ])

      window.fetch = originalFetch
      return {
        refreshCalls: calls.filter((url) => url.includes('/auth/refresh')).length,
        rejected: outcomes.filter((o) => o.status === 'rejected').length,
        stillAuthenticated: !!localStorage.getItem('token'),
      }
    })

    expect(result.refreshCalls).toBe(1)
    expect(result.rejected).toBe(0)
    expect(result.stillAuthenticated).toBe(true)
    await expect(page).not.toHaveURL(/\/login/)
  })

  test('an unrecoverable session ends cleanly instead of looping', async ({ page }) => {
    await login(page, 'teacher')

    const result = await page.evaluate(async () => {
      const { api } = await import('/src/api/client.js')
      const { useAuthStore } = await import('/src/stores/auth.js')

      // Logout clears refresh_token_id server-side, so no refresh can succeed.
      await useAuthStore().logout()
      localStorage.setItem('token', 'eyJhbGciOiJIUzI1NiJ9.stale.signature')

      const calls = []
      const originalFetch = window.fetch
      window.fetch = (...args) => {
        calls.push(String(args[0]))
        return originalFetch(...args)
      }

      let message = null
      try {
        await api.get('/tasks/')
      } catch (error) {
        message = error.message
      }

      window.fetch = originalFetch
      return {
        totalCalls: calls.length,
        message,
        tokenCleared: !localStorage.getItem('token'),
      }
    })

    // Exactly two: the original request, then one failed refresh. No retry
    // storm, no infinite loop.
    expect(result.totalCalls).toBe(2)
    expect(result.message).toMatch(/session has expired/i)
    expect(result.tokenCleared).toBe(true)
  })

  test('logging out invalidates the refresh cookie server-side', async ({ page }) => {
    // Regression: logout only cleared localStorage, leaving the HttpOnly
    // refresh cookie valid for its full 7 days.
    await login(page, 'teacher')

    const status = await page.evaluate(async () => {
      const { useAuthStore } = await import('/src/stores/auth.js')
      await useAuthStore().logout()

      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      })
      return response.status
    })

    expect(status).toBe(401)
  })
})

test.describe('API routing', () => {
  test('collection routes do not redirect', async ({ page }) => {
    // Regression (C-07): the client called /api/tasks without the trailing
    // slash, FastAPI answered 307 to an absolute URL, and behind a
    // TLS-terminating proxy that came back as http:// and was blocked as mixed
    // content. Calling the declared path means there is no redirect at all.
    await login(page, 'teacher')

    const results = await page.evaluate(async () => {
      const token = localStorage.getItem('token')
      const paths = ['/api/tasks/', '/api/events/', '/api/projects/', '/api/expenses/', '/api/courses/']
      const out = []
      for (const path of paths) {
        const response = await fetch(path, { headers: { Authorization: `Bearer ${token}` } })
        out.push({ path, status: response.status, redirected: response.redirected })
      }
      return out
    })

    for (const result of results) {
      expect(result.status, `${result.path} should succeed`).toBe(200)
      expect(result.redirected, `${result.path} should not redirect`).toBe(false)
    }
  })
})
