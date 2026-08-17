import { test, expect } from '@playwright/test'
import { login, logout, quickAddTask } from './helpers.js'

test.describe('week strip and streak use real data', () => {
  test('the activity endpoint returns the current Mon-Fri week', async ({ page }) => {
    await login(page, 'student')

    const activity = await page.evaluate(async () => {
      const { api } = await import('/src/api/client.js')
      return api.get('/analytics/activity')
    })

    expect(activity.days).toHaveLength(5)
    expect(typeof activity.streak).toBe('number')

    // Monday through Friday of the week containing today. Friday is included
    // even though the scheduler will not place work there by itself: a week
    // with a day missing just reads as truncated.
    const weekdays = activity.days.map((d) => new Date(`${d.date}T00:00:00`).getDay())
    expect(weekdays).toEqual([1, 2, 3, 4, 5])

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
    await expect(strip).toContainText('Fri')
    await expect(strip.locator('.day')).toHaveCount(5)

    // Every cell carries its date; without one, "MON" does not say which
    // Monday and the row cannot be tied to anything being planned.
    const dates = await strip.locator('.day .date').allTextContents()
    expect(dates).toHaveLength(5)
    for (const d of dates) expect(Number(d)).toBeGreaterThan(0)

    const streakCard = page.locator('.kpi-row').getByText('Daily Streak')
    await expect(streakCard).toBeVisible()
  })

  test('today is unmistakable', async ({ page }) => {
    await login(page, 'student')
    await page.goto('/student/quests')

    const today = page.locator('.week-strip .day.is-today')
    // Only marked when today is a weekday; at a weekend nothing should claim it.
    const isWeekday = await page.evaluate(() => {
      const d = new Date().getDay()
      return d >= 1 && d <= 5
    })

    if (isWeekday) {
      await expect(today).toHaveCount(1)
      await expect(today).toContainText('Today')
    } else {
      await expect(today).toHaveCount(0)
    }
  })

  test('a day with no work says so instead of showing a bare dash', async ({ page }) => {
    // The dash was read as missing data, which is exactly what it looked like.
    await login(page, 'student')
    await page.goto('/student/quests')
    await expect(page.locator('.week-strip')).toBeVisible()

    const restCells = page.locator('.week-strip .day.is-rest')
    if (await restCells.count() > 0) {
      await expect(restCells.first()).toContainText('Free')
      await expect(restCells.first()).not.toContainText('—')
    }
  })

  test('a future day shows what is waiting, not "0 done"', async ({ page }) => {
    // Wednesday reading "0/2" on Monday invited the reading that something had
    // already gone wrong, when the day simply had not happened.
    await login(page, 'student')
    await page.goto('/student/quests')
    await expect(page.locator('.week-strip')).toBeVisible()

    const upcoming = page.locator('.week-strip .day.is-upcoming')
    for (let i = 0; i < await upcoming.count(); i += 1) {
      await expect(upcoming.nth(i)).not.toContainText('/')
    }
  })
})
