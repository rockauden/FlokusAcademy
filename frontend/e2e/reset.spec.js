import { test, expect } from '@playwright/test'
import { login, apiCall, apiError, isoDate } from './helpers.js'

/**
 * The reset: one button, irreversible, and the only thing in the app that can
 * destroy a year of records. Both halves of its guard are worth a test - that
 * the wrong phrase does nothing at all, and that the right one leaves behind
 * the things it promised to keep.
 */
test.describe('starting over', () => {
  test('the wrong phrase deletes nothing', async ({ page }) => {
    await login(page, 'teacher')
    const created = await apiCall(page, 'post', '/week/entries', {
      course_id: 1,
      scheduled_date: isoDate(new Date()),
      title: `Survivor ${Date.now()}`,
    })

    // Right words, wrong case. An almost-match must be as inert as nonsense.
    const message = await apiError(page, 'post', '/maintenance/reset-curriculum', {
      confirm: 'delete all work',
    })
    expect(message).toContain('DELETE ALL WORK')

    expect((await apiCall(page, 'get', `/tasks/${created.id}`)).id).toBe(created.id)
  })

  test('the right phrase clears the work and keeps the classes', async ({ page }) => {
    await login(page, 'teacher')
    await apiCall(page, 'post', '/week/entries', {
      course_id: 1,
      scheduled_date: isoDate(new Date()),
      title: `Doomed ${Date.now()}`,
    })

    const classesBefore = (await apiCall(page, 'get', '/courses/?include_inactive=true')).length
    expect(classesBefore).toBeGreaterThan(0)

    const result = await apiCall(page, 'post', '/maintenance/reset-curriculum', {
      confirm: 'DELETE ALL WORK',
    })
    expect(result.lessons).toBeGreaterThan(0)

    // Work gone...
    const week = await apiCall(page, 'get', '/week/')
    expect(week.entries).toHaveLength(0)
    expect(week.behind).toHaveLength(0)
    expect(await apiCall(page, 'get', '/tasks/')).toHaveLength(0)

    // ...classes kept, because a clean slate is not a blank app.
    expect((await apiCall(page, 'get', '/courses/?include_inactive=true')).length).toBe(classesBefore)
  })
})
