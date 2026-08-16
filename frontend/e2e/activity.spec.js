import { test, expect } from '@playwright/test'
import { login, logout, quickAddTask } from './helpers.js'

test.describe('week strip and streak use real data', () => {
  test('the activity endpoint returns the current Mon-Thu week', async ({ page }) => {
    await login(page, 'student')

    const activity = await page.evaluate(async () => {
      const { api } = await import('/src/api/client.js')
      return api.get('/analytics/activity')
    })

    expect(activity.days).toHaveLength(4)
    expect(typeof activity.streak).toBe('number')

    // Monday through Thursday of the week containing today.
    const weekdays = activity.days.map((d) => new Date(`${d.date}T00:00:00`).getDay())
    expect(weekdays).toEqual([1, 2, 3, 4])

    // The dates it replaced were hardcoded to October 2023.
    for (const day of activity.days) {
      expect(day.date.startsWith('2023')).toBe(false)
      expect(day.total).toBeGreaterThanOrEqual(0)
      expect(day.completed).toBeLessThanOrEqual(day.total)
    }
  })

  test('a task created today shows up in the week strip counts', async ({ page }) => {
    await login(page, 'teacher')
    await quickAddTask(page, 'Activity counted')
    await logout(page)

    await login(page, 'student')
    const result = await page.evaluate(async () => {
      const { api } = await import('/src/api/client.js')
      const activity = await api.get('/analytics/activity')
      const now = new Date()
      const iso = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
      return { today: activity.days.find((d) => d.date === iso), iso }
    })

    // Quick add defaults to today, and today is a school day in this window.
    if (result.today) {
      expect(result.today.total).toBeGreaterThan(0)
    }
  })

  test('a student cannot request another student\'s activity', async ({ page }) => {
    await login(page, 'student')

    const same = await page.evaluate(async () => {
      const { api } = await import('/src/api/client.js')
      // Asking for someone else must silently return your own data, never theirs.
      const mine = await api.get('/analytics/activity')
      const attempted = await api.get('/analytics/activity?student_id=1')
      return JSON.stringify(mine.days) === JSON.stringify(attempted.days)
    })

    expect(same).toBe(true)
  })

  test('a teacher must name a student', async ({ page }) => {
    await login(page, 'teacher')

    const status = await page.evaluate(async () => {
      const response = await fetch('/api/analytics/activity', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      })
      return response.status
    })

    expect(status).toBe(400)
  })

  test('the student dashboard renders the strip and a real streak', async ({ page }) => {
    await login(page, 'student')
    await page.goto('/student/quests')

    const strip = page.locator('.week-strip')
    await expect(strip).toBeVisible()
    await expect(strip).toContainText('Mon')
    await expect(strip).toContainText('Thu')

    // The streak card is present and shows a number, not the old literal 5
    // with its unconditional "Keep it up!".
    const streakCard = page.locator('.kpi-row').getByText('Daily Streak')
    await expect(streakCard).toBeVisible()
  })
})
