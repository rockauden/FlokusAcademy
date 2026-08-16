import { test, expect } from '@playwright/test'
import { login } from './helpers.js'

test.describe('errors are visible, not silent', () => {
  test('every response carries a request id', async ({ page }) => {
    await login(page, 'teacher')

    const header = await page.evaluate(async () => {
      const response = await fetch('/api/tasks/', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      })
      return response.headers.get('X-Request-ID')
    })

    expect(header).toBeTruthy()
    expect(header.length).toBeGreaterThan(8)
  })

  test('an inbound request id is echoed back, so calls can be correlated', async ({ page }) => {
    await login(page, 'teacher')

    const header = await page.evaluate(async () => {
      const response = await fetch('/api/tasks/', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
          'X-Request-ID': 'trace-me-12345',
        },
      })
      return response.headers.get('X-Request-ID')
    })

    expect(header).toBe('trace-me-12345')
  })

  test('a failed API call carries the request id on the error', async ({ page }) => {
    await login(page, 'teacher')

    const details = await page.evaluate(async () => {
      const { api } = await import('/src/api/client.js')
      try {
        await api.post('/tasks/', { title: 'x', course_id: 1, scheduled_date: 'nonsense' })
        return null
      } catch (error) {
        return { message: error.message, requestId: error.requestId, status: error.status }
      }
    })

    expect(details.status).toBe(422)
    expect(details.requestId).toBeTruthy()
    expect(details.message).toContain('scheduled_date')
  })

  test('an unhandled rejection surfaces as a visible toast', async ({ page }) => {
    await login(page, 'teacher')
    await page.goto('/admin/tasks')

    // Exactly the shape of failure that went unnoticed all week: a fire and
    // forget API call from a handler, rejecting with nobody awaiting it.
    await page.evaluate(async () => {
      const { api } = await import('/src/api/client.js')
      api.post('/tasks/', { title: 'x', course_id: 1, scheduled_date: 'nonsense' })
    })

    const toasts = page.locator('.error-toasts')
    await expect(toasts).toBeVisible()
    await expect(toasts).toContainText(/scheduled_date/i)
  })

  test('a toast can be dismissed', async ({ page }) => {
    await login(page, 'teacher')
    await page.goto('/admin/tasks')

    await page.evaluate(async () => {
      const { useErrorsStore } = await import('/src/stores/errors.js')
      useErrorsStore().report('Something specific went wrong', { requestId: 'abc123' })
    })

    const toasts = page.locator('.error-toasts')
    await expect(toasts).toContainText('Something specific went wrong')
    await expect(toasts).toContainText('abc123')

    await toasts.getByRole('button', { name: 'Dismiss' }).first().click()
    await expect(page.locator('.error-toasts')).toHaveCount(0)
  })

  test('an API failure does not blank the page', async ({ page }) => {
    // Regression guard: the boundary originally treated a rejected fetch from
    // a child's onMounted as a render failure and replaced the whole screen,
    // which turns a network blip into "the app is broken".
    await login(page, 'teacher')
    await page.goto('/admin/tasks')

    await page.evaluate(async () => {
      const { api } = await import('/src/api/client.js')
      try {
        await api.get('/definitely-not-a-real-endpoint')
      } catch {
        // Swallowed here; the point is what the boundary does with it.
      }
      const error = new Error('simulated API failure')
      error.requestId = 'abc123'
      error.status = 500
      throw error
    }).catch(() => {})

    await expect(page.locator('.crash')).toHaveCount(0)
    await expect(page.locator('.task-form, .admin-layout')).not.toHaveCount(0)
  })

  test('an expired session shows no crash screen and no toast', async ({ page }) => {
    // Regression: the session-expired error was thrown bare, so the boundary
    // could not tell it from a render failure and put the crash screen over an
    // entirely ordinary redirect to the login page. Caught as a flake first --
    // it only surfaced when the expiry happened to land during a render.
    await login(page, 'teacher')
    await page.goto('/admin/tasks')

    await page.evaluate(async () => {
      const { api } = await import('/src/api/client.js')
      const { useAuthStore } = await import('/src/stores/auth.js')
      await useAuthStore().logout()
      localStorage.setItem('token', 'eyJhbGciOiJIUzI1NiJ9.stale.sig')
      try { await api.get('/tasks/') } catch { /* expected */ }
    })

    await expect(page).toHaveURL(/\/login/)
    await expect(page.locator('.crash')).toHaveCount(0)
    await expect(page.locator('.error-toasts')).toHaveCount(0)
  })

  test('repeated identical failures collapse instead of stacking', async ({ page }) => {
    await login(page, 'teacher')
    await page.goto('/admin/tasks')

    const count = await page.evaluate(async () => {
      const { useErrorsStore } = await import('/src/stores/errors.js')
      const errors = useErrorsStore()
      errors.clear()
      errors.report('Network unavailable')
      errors.report('Network unavailable')
      errors.report('Network unavailable')
      return errors.items.length
    })

    expect(count).toBe(1)
    await expect(page.locator('.error-toasts')).toContainText('x3')
  })
})
