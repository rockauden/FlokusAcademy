import { test, expect } from '@playwright/test'
import { apiCall, login } from './helpers.js'

/**
 * The AI tutor's off switch.
 *
 * Ask Floki ships switched off (FLOKI_ENABLED in backend/app/config.py). The
 * reason is not technical: Google's Gemini API terms forbid an API client
 * "directed towards or ... likely to be accessed by individuals under the age
 * of 18", and on the unpaid tier submitted prompts train Google's models and
 * may be read by human reviewers. The feature is kept whole behind a flag so
 * it can come back on a paid key rather than being rebuilt.
 *
 * The end-to-end harness turns it ON (see scripts/run_test_api.py) because the
 * safety and stuck-flag specs are the most important in the repo and need the
 * feature reachable. So the switched-off experience is tested from the client
 * side, by intercepting the status call — which is exactly the surface the
 * child sees, and does not need a second API process with a different
 * environment.
 */
test.describe('Ask Floki, switched off', () => {
  test('the status endpoint reports whether the tutor is reachable', async ({ page }) => {
    await login(page, 'student')
    const status = await apiCall(page, 'get', '/ai/status')
    expect(status).toHaveProperty('enabled')
    // True in this harness; false is what production ships.
    expect(typeof status.enabled).toBe('boolean')
  })

  test('the student sees a calm resting card, not an error', async ({ page }) => {
    await page.route('**/api/ai/status', (route) =>
      route.fulfill({ json: { enabled: false } }),
    )

    await login(page, 'student')
    await page.goto('/student/floki')

    await expect(page.getByText(/Floki is having a rest/i)).toBeVisible()
    await expect(page.getByText(/wake him up when he's ready/i)).toBeVisible()

    // The things that would make it read as a fault rather than a normal state.
    await expect(page.getByPlaceholder(/Ask Floki anything/i)).toHaveCount(0)
    await expect(page.getByRole('button', { name: /^Send$/ })).toHaveCount(0)
    await expect(page.getByText(/error|failed|something went wrong|503/i)).toHaveCount(0)

    // And a way back to the work, so the screen is not a dead end.
    await expect(page.getByRole('link', { name: /Back to my quests/i })).toBeVisible()
  })

  test('the sidebar does not offer a door that only leads to "resting"', async ({ page }) => {
    await page.route('**/api/ai/status', (route) =>
      route.fulfill({ json: { enabled: false } }),
    )

    await login(page, 'student')
    await page.goto('/student/quests')

    // Matched on href, not on the visible label: the sidebar collapses to
    // icon-only and drops its text, so a name-based locator finds nothing
    // either way and the assertion would pass while proving nothing.
    await expect(page.locator('a[href="/student/quests"]')).toHaveCount(1)
    await expect(page.locator('a[href="/student/floki"]')).toHaveCount(0)
  })

  test('with the tutor on, the sidebar does offer it', async ({ page }) => {
    // The counterpart to the test above. Without it, a bug that hid every nav
    // link would look like a pass.
    await login(page, 'student')
    await page.goto('/student/quests')

    await expect(page.locator('a[href="/student/quests"]')).toHaveCount(1)
    await expect(page.locator('a[href="/student/floki"]')).toHaveCount(1)
  })

  test('with the tutor on, the chat box is offered as normal', async ({ page }) => {
    await login(page, 'student')
    await page.goto('/student/floki')

    await expect(page.getByPlaceholder(/Ask Floki anything/i)).toBeVisible()
    await expect(page.getByText(/Floki is having a rest/i)).toHaveCount(0)
  })
})
