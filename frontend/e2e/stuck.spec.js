import { test, expect } from '@playwright/test'
import { login } from './helpers.js'

/**
 * Raising a real flag needs Gemini to choose to call the tool, which cannot be
 * made deterministic without a live key. The backend mechanism is covered
 * separately; these cover what the parent actually sees, with the list stubbed.
 */
const FLAGS = [
  { id: 1, student_id: 2, session_id: 's1', topic: 'dividing fractions by whole numbers', created_at: new Date().toISOString(), resolved_at: null },
  { id: 2, student_id: 2, session_id: 's1', topic: 'long division', created_at: new Date().toISOString(), resolved_at: null },
]

async function stubFlags(page, flags = FLAGS) {
  await page.route('**/api/students/stuck-flags*', async (route) => {
    if (route.request().method() !== 'GET') return route.continue()
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(flags),
    })
  })
}

test.describe('stuck flags reach the parent', () => {
  test('unresolved flags appear on the admin screen', async ({ page }) => {
    await login(page, 'teacher')
    await stubFlags(page)
    await page.goto('/admin/week')

    const strip = page.locator('.stuck-strip')
    await expect(strip).toBeVisible()
    await expect(strip).toContainText('dividing fractions by whole numbers')
    await expect(strip).toContainText('long division')
  })

  test('the strip is visually distinct from a safety alert', async ({ page }) => {
    // If getting stuck on fractions looked like a distress disclosure, the red
    // banner would stop meaning anything -- which is how a safety layer fails
    // without anyone noticing.
    await login(page, 'teacher')
    await stubFlags(page)
    await page.goto('/admin/week')

    const stuckBorder = await page.locator('.stuck').first()
      .evaluate((el) => getComputedStyle(el).borderLeftColor)

    // The safety banner's rail is red; this one must not be.
    expect(stuckBorder).not.toBe('rgb(224, 82, 82)')
    expect(stuckBorder).toBeTruthy()
  })

  test('marking one helped removes it from the strip', async ({ page }) => {
    await login(page, 'teacher')
    await stubFlags(page)
    await page.route('**/api/students/stuck-flags/*/resolve', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ...FLAGS[0], resolved_at: new Date().toISOString() }) }),
    )
    await page.goto('/admin/week')

    const strip = page.locator('.stuck-strip')
    await expect(strip).toContainText('dividing fractions')

    await strip.getByRole('button', { name: 'Helped' }).first().click()

    await expect(strip).not.toContainText('dividing fractions')
    await expect(strip).toContainText('long division')
  })

  test('nothing is shown when there is nothing to report', async ({ page }) => {
    await login(page, 'teacher')
    await stubFlags(page, [])
    await page.goto('/admin/week')

    await expect(page.locator('.admin-layout')).toBeVisible()
    await expect(page.locator('.stuck-strip')).toHaveCount(0)
  })

  test('a student cannot read them', async ({ page }) => {
    await login(page, 'student')

    const status = await page.evaluate(async () => {
      const response = await fetch('/api/students/stuck-flags', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      })
      return response.status
    })

    expect(status).toBe(403)
  })
})
