import { test, expect } from '@playwright/test'
import { apiCall, apiError, login, quickAddTask, todayISO } from './helpers.js'

/**
 * Removing work from the plan.
 *
 * Before this, one click on any card's Remove button deleted the lesson and
 * cascaded to every assignment hanging off it — completed ones included. A
 * misclick on a finished card erased the completion, the focus minutes and the
 * notes, and reversed XP the student had genuinely earned. That is a hole in
 * the school record, so it is guarded in two independent places and both are
 * asserted here: the server refuses outright, and the button needs two clicks.
 *
 * The server half is the one that matters. A UI guard can be bypassed by any
 * stale tab or hand-made request; the 409 cannot.
 */
test.describe('removing an item from the plan', () => {
  test('the server refuses to delete work that has been marked done', async ({ page }) => {
    await login(page, 'teacher')

    const title = await quickAddTask(page, 'Completed and precious')
    const before = await apiCall(page, 'get', `/tasks/?scheduled_date=${todayISO()}`)
    const entry = before.find((t) => t.title === title)
    expect(entry, 'the entry we just created should be in the list').toBeTruthy()

    await apiCall(page, 'post', `/tasks/${entry.id}/complete`, {
      completion_notes: 'Finished it',
      focus_minutes: 20,
    })

    const message = await apiError(page, 'delete', `/week/entries/${entry.id}`)
    expect(message, 'deleting completed work must fail').not.toBeNull()
    // The refusal has to name the item, or the teacher cannot tell which of a
    // week's cards refused to go.
    expect(message).toContain(title)
    expect(message).toMatch(/marked done|school record/i)

    // And it is genuinely still there, with its completion intact — a 409 that
    // deleted anyway would be worse than no guard at all.
    const after = await apiCall(page, 'get', `/tasks/?scheduled_date=${todayISO()}`)
    const survivor = after.find((t) => t.id === entry.id)
    expect(survivor, 'the completed entry must survive the refused delete').toBeTruthy()
    expect(survivor.is_completed).toBe(true)
    expect(survivor.focus_minutes).toBe(20)
    expect(survivor.completion_notes).toBe('Finished it')
  })

  test('unfinished work can still be removed', async ({ page }) => {
    await login(page, 'teacher')

    const title = await quickAddTask(page, 'Planned then reconsidered')
    const before = await apiCall(page, 'get', `/tasks/?scheduled_date=${todayISO()}`)
    const entry = before.find((t) => t.title === title)
    expect(entry).toBeTruthy()

    await apiCall(page, 'delete', `/week/entries/${entry.id}`)

    const after = await apiCall(page, 'get', `/tasks/?scheduled_date=${todayISO()}`)
    expect(after.find((t) => t.id === entry.id), 'it should be gone').toBeFalsy()
  })

  test('marking it not done again releases it for removal', async ({ page }) => {
    await login(page, 'teacher')

    const title = await quickAddTask(page, 'Done then undone')
    const listed = await apiCall(page, 'get', `/tasks/?scheduled_date=${todayISO()}`)
    const entry = listed.find((t) => t.title === title)

    await apiCall(page, 'post', `/tasks/${entry.id}/complete`, {
      completion_notes: '',
      focus_minutes: 5,
    })
    expect(await apiError(page, 'delete', `/week/entries/${entry.id}`)).not.toBeNull()

    // This is the documented escape hatch: an explicit decision, not a
    // force flag hidden in a query string.
    await apiCall(page, 'post', `/tasks/${entry.id}/uncomplete`)
    await apiCall(page, 'delete', `/week/entries/${entry.id}`)

    const after = await apiCall(page, 'get', `/tasks/?scheduled_date=${todayISO()}`)
    expect(after.find((t) => t.id === entry.id)).toBeFalsy()
  })

  test('the Remove button needs a second click before anything goes', async ({ page }) => {
    await login(page, 'teacher')
    const title = await quickAddTask(page, 'Two clicks to go')

    await page.goto('/admin/week')
    // quickAddTask puts the work on today; from Friday onward the planner opens
    // on next week, so navigate back until the card is on screen.
    const card = page.getByText(title, { exact: false }).first()
    if (!(await card.isVisible().catch(() => false))) {
      await page.getByRole('button', { name: 'Previous week' }).click()
    }
    await expect(card).toBeVisible()
    await card.click()

    const removeButton = page.getByTestId('remove-entry')
    await expect(removeButton).toHaveText(/^Remove$/)

    // First click arms it and says so, and must not delete.
    await removeButton.click()
    await expect(removeButton).toHaveText(/Really remove\?/i)
    await expect(page.getByTestId('cancel-remove')).toBeVisible()

    const stillThere = await apiCall(page, 'get', `/tasks/?scheduled_date=${todayISO()}`)
    expect(
      stillThere.find((t) => t.title === title),
      'one click must never delete',
    ).toBeTruthy()

    // Backing out leaves it alone.
    await page.getByTestId('cancel-remove').click()
    await expect(removeButton).toHaveText(/^Remove$/)
  })
})
