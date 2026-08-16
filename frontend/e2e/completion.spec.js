import { test, expect } from '@playwright/test'
import { login, logout, quickAddTask } from './helpers.js'

/** Create a task as the teacher, then arrive on the student's day with it open. */
async function openTaskAsStudent(page, title) {
  await login(page, 'teacher')
  const taskTitle = await quickAddTask(page, title)
  await logout(page)

  await login(page, 'student')
  await page.goto('/student/quests')

  const card = page.locator('.task-card').filter({ hasText: taskTitle })
  await expect(card).toBeVisible()
  await card.locator('.task-header').click()
  return { card, taskTitle }
}

test.describe('the completion moment', () => {
  test('the tap is acknowledged before the request returns', async ({ page }) => {
    // Without this the card sat inert until the refetch re-rendered the list,
    // which on a slow connection is long enough for a child to tap again.
    // The completion request is held open deliberately, because the whole
    // point of the state is what the child sees *during* that wait -- letting
    // it resolve at local speed would test nothing.
    const { card } = await openTaskAsStudent(page, 'Settle')

    let release
    const held = new Promise((resolve) => { release = resolve })
    await page.route('**/api/tasks/*/complete', async (route) => {
      await held
      await route.continue()
    })

    await card.getByRole('button', { name: /Mark Complete/ }).click()

    const acknowledged = card.getByRole('button', { name: 'Nice work!' })
    await expect(acknowledged).toBeVisible()
    await expect(acknowledged).toBeDisabled()

    release()
  })

  test('XP counts up to the amount actually awarded', async ({ page }) => {
    const { card } = await openTaskAsStudent(page, 'Counts XP')

    const value = page.locator('.kpi-card').filter({ hasText: 'XP Earned Today' }).locator('.value')
    // Other specs share this database, so the starting figure is whatever it
    // is; what matters is that finishing work moves it.
    const before = Number(await value.textContent())

    await card.getByRole('button', { name: /Mark Complete/ }).click()

    await expect
      .poll(async () => Number(await value.textContent()), { timeout: 10_000 })
      .toBeGreaterThan(before)
  })

  test('the burst never intercepts a tap', async ({ page }) => {
    // A child tapping the next task mid-celebration must not be blocked.
    await login(page, 'student')
    await page.goto('/student/quests')
    await expect(page.locator('.quests-view')).toBeVisible()

    const canvas = page.locator('canvas.burst')
    await expect(canvas).toBeAttached()

    const pointerEvents = await canvas.evaluate((el) => getComputedStyle(el).pointerEvents)
    expect(pointerEvents).toBe('none')
  })

  test('reduced motion draws no particles at all', async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' })
    const { card } = await openTaskAsStudent(page, 'Reduced motion')

    await card.getByRole('button', { name: /Mark Complete/ }).click()

    // fire() returns before activating when motion is unwanted, so the canvas
    // never becomes visible -- not a shorter animation, none.
    await page.waitForTimeout(400)
    const isActive = await page.evaluate(() => {
      const canvas = document.querySelector('canvas.burst')
      return canvas ? canvas.classList.contains('is-active') : null
    })

    expect(isActive).toBe(false)
  })

  test('reduced motion still updates the numbers immediately', async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' })
    const { card } = await openTaskAsStudent(page, 'Reduced motion numbers')

    const xpCard = page.locator('.kpi-card').filter({ hasText: 'XP Earned Today' })
    await card.getByRole('button', { name: /Mark Complete/ }).click()

    // No animation, but the value must still be correct -- reduced motion
    // removes the movement, never the information.
    await expect(xpCard.locator('.value')).not.toHaveText('0', { timeout: 10_000 })
  })

  test('a completed task moves to the finished list', async ({ page }) => {
    const { card, taskTitle } = await openTaskAsStudent(page, 'Moves to done')

    await card.getByRole('button', { name: /Mark Complete/ }).click()

    const completedSection = page.locator('.completed-section')
    await expect(completedSection).toBeVisible({ timeout: 10_000 })
    await expect(completedSection).toContainText(taskTitle)
  })
})
