import { test, expect } from '@playwright/test'
import { login, logout } from './helpers.js'

/**
 * The safety layer is the highest-consequence code in the app, and its
 * escalation path never calls the model -- so it is fully testable here, with
 * no API key and nothing leaving the machine.
 */
test.describe('Ask Floki safety layer', () => {
  test('a distress message escalates instead of reaching the model', async ({ page }) => {
    await login(page, 'student')

    const reply = await page.evaluate(async () => {
      const { api } = await import('/src/api/client.js')
      return api.post('/ai/chat', {
        session_id: 'safety-e2e',
        message: 'i want to kill myself',
        persona: 'Socratic Tutor',
      })
    })

    expect(reply.escalated).toBe(true)
    // Points at a person and a real service, and does not try to counsel.
    expect(reply.message).toContain('988')
    expect(reply.message).toMatch(/dad|grown-up/i)
  })

  test('the parent sees the alert and can acknowledge it', async ({ page }) => {
    await login(page, 'student')
    await page.evaluate(async () => {
      const { api } = await import('/src/api/client.js')
      await api.post('/ai/chat', {
        session_id: 'safety-e2e-2',
        message: 'my uncle hits me and i am scared to go home',
        persona: 'Socratic Tutor',
      })
    })
    await logout(page)

    await login(page, 'teacher')
    const result = await page.evaluate(async () => {
      const { api } = await import('/src/api/client.js')
      const before = await api.get('/students/safety-events?unacknowledged_only=true')
      // Select by session rather than position: other specs in this file raise
      // their own alerts, and asserting on before[0] would couple this test to
      // the order they happen to run in.
      const target = before.find((e) => e.session_id === 'safety-e2e-2')
      await api.post(`/students/safety-events/${target.id}/acknowledge`, {})
      const after = await api.get('/students/safety-events?unacknowledged_only=true')
      return {
        unreadBefore: before.length,
        category: target.category,
        unreadAfter: after.length,
        stillThere: after.some((e) => e.id === target.id),
      }
    })

    expect(result.unreadBefore).toBeGreaterThan(0)
    expect(result.category).toBe('abuse')
    expect(result.unreadAfter).toBe(result.unreadBefore - 1)
    expect(result.stillThere).toBe(false)
  })

  test('ordinary schoolwork questions do not escalate', async ({ page }) => {
    await login(page, 'student')

    // Phrases a child says constantly. A layer that fires on these would train
    // a parent to ignore the alerts, which is worse than having none.
    const escalations = await page.evaluate(async () => {
      const { api } = await import('/src/api/client.js')
      const innocuous = [
        'this homework is killing me',
        'can you help me with fractions?',
        'I hate long division',
      ]
      const results = []
      for (const message of innocuous) {
        const reply = await api.post('/ai/chat', {
          session_id: 'safety-e2e-3',
          message,
          persona: 'Socratic Tutor',
        })
        results.push(reply.escalated === true)
      }
      return results
    })

    expect(escalations).toEqual([false, false, false])
  })

  test('the alert is visible on the admin screen, not just the API', async ({ page }) => {
    // With no push or email channel, this banner is the whole notification
    // mechanism -- if it does not render, the parent is never told.
    await login(page, 'student')
    await page.evaluate(async () => {
      const { api } = await import('/src/api/client.js')
      await api.post('/ai/chat', {
        session_id: 'safety-e2e-banner',
        message: 'i wish i was dead',
        persona: 'Socratic Tutor',
      })
    })
    await logout(page)

    await login(page, 'teacher')
    await page.goto('/admin/week')

    const banner = page.locator('.safety-banner')
    await expect(banner).toBeVisible()
    await expect(banner).toContainText('i wish i was dead')
    await expect(banner.getByRole('button', { name: /spoken to him/i }).first()).toBeVisible()
  })

  test('safety alerts are teacher-only', async ({ page }) => {
    await login(page, 'student')

    const status = await page.evaluate(async () => {
      const response = await fetch('/api/students/safety-events', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      })
      return response.status
    })

    expect(status).toBe(403)
  })
})
