import { test, expect } from '@playwright/test'
import { login } from './helpers.js'

/** Hold the day's tasks open for `ms` so the loading state can be observed. */
async function delayTodayTasks(page, ms) {
  await page.route('**/api/tasks/today', async (route) => {
    await new Promise((resolve) => setTimeout(resolve, ms))
    await route.continue()
  })
}

test.describe('loading skeletons', () => {
  test('a slow load shows skeletons, never "0 tasks left today"', async ({ page }) => {
    // The blank flash this replaces was not merely empty -- it stated, for a
    // beat, that there was no work today, which is a wrong and deflating
    // thing to tell a child before the answer is known.
    await login(page, 'student')
    await delayTodayTasks(page, 1500)
    await page.goto('/student/quests')

    await expect(page.locator('.task-lists[aria-busy="true"]')).toBeVisible()
    await expect(page.locator('.skeleton').first()).toBeVisible()
    await expect(page.getByText('You have 0 tasks left today')).toHaveCount(0)
  })

  test('skeletons give way to the real content', async ({ page }) => {
    await login(page, 'student')
    await delayTodayTasks(page, 900)
    await page.goto('/student/quests')

    await expect(page.locator('.task-lists[aria-busy="true"]')).toBeVisible()
    await expect(page.locator('.task-lists[aria-busy="true"]')).toHaveCount(0, { timeout: 10_000 })
    await expect(page.locator('.hero .subtitle')).toBeVisible()
  })

  test('a fast load shows no skeleton at all', async ({ page }) => {
    // Under the 200ms delay nothing should appear: a placeholder that comes
    // and goes within two frames reads as a glitch, not as loading.
    await login(page, 'student')

    let sawSkeleton = false
    await page.goto('/student/quests')
    // Sample immediately; the local API answers well inside the delay window.
    for (let i = 0; i < 6; i += 1) {
      if (await page.locator('.task-lists[aria-busy="true"]').count() > 0) {
        sawSkeleton = true
        break
      }
      await page.waitForTimeout(25)
    }

    expect(sawSkeleton).toBe(false)
    await expect(page.locator('.hero .subtitle')).toBeVisible()
  })

  test('the 30-second poll does not replace the list with skeletons', async ({ page }) => {
    // Swapping real content the child is reading for placeholders twice a
    // minute would be worse than the flash this feature removes.
    await login(page, 'student')
    await page.goto('/student/quests')
    await expect(page.locator('.hero .subtitle')).toBeVisible()

    const reappeared = await page.evaluate(async () => {
      const { useTasksStore } = await import('/src/stores/tasks.js')
      const store = useTasksStore()
      await store.fetchTodayTasks()          // exactly what the poll does
      await new Promise((r) => setTimeout(r, 500))
      return document.querySelectorAll('.task-lists[aria-busy="true"]').length
    })

    expect(reappeared).toBe(0)
  })

  test('a failed first load shows the real view, not endless skeletons', async ({ page }) => {
    await login(page, 'student')
    await page.route('**/api/tasks/today', (route) => route.abort())
    await page.goto('/student/quests')

    await expect(page.locator('.task-lists[aria-busy="true"]')).toHaveCount(0, { timeout: 10_000 })
    await expect(page.locator('.hero .subtitle')).toBeVisible()
  })

  test('skeletons match the real card box', async ({ page }) => {
    // A placeholder of the wrong size causes the layout jump it exists to
    // prevent, so it reuses the real .task-card class rather than its own box.
    await login(page, 'student')
    await delayTodayTasks(page, 1500)
    await page.goto('/student/quests')

    const skeletonCard = page.locator('.task-card').first()
    await expect(skeletonCard).toBeVisible()

    const box = await skeletonCard.evaluate((el) => {
      const style = getComputedStyle(el)
      return { padding: style.padding, radius: style.borderTopLeftRadius, left: style.borderLeftWidth }
    })

    expect(box.left).toBe('4px')          // the accent rail every task card has
    expect(parseFloat(box.radius)).toBeGreaterThan(0)
  })
})
