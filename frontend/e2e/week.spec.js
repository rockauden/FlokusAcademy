import { test, expect } from '@playwright/test'
import { login, logout, apiCall, isoDate } from './helpers.js'

/**
 * The week planner — the Sunday screen, and since 2026-08-26 the only way
 * work enters the app.
 *
 * The specs that matter most here are the two promises the screen makes:
 * typing a cell creates work on that day, and nothing the app does afterwards
 * moves it. The second is easy to break silently and expensive when it
 * breaks, because the failure looks like the teacher misremembering.
 */

function mondayOf(d) {
  const copy = new Date(d)
  const day = copy.getDay()
  // getDay() is 0=Sun; shift so Monday starts the week.
  copy.setDate(copy.getDate() - ((day + 6) % 7))
  return copy
}

/**
 * The Monday the planner opens on: this week Mon–Thu, next week from Friday.
 * Mirrors get_week's rule — planning happens at the end of a week for the one
 * after it, and opening on a week already spent wastes the teacher's first
 * click.
 */
function plannedMonday() {
  const today = new Date()
  const monday = mondayOf(today)
  // getDay(): 0=Sun, 5=Fri, 6=Sat.
  const day = today.getDay()
  if (day === 5 || day === 6 || day === 0) monday.setDate(monday.getDate() + 7)
  return isoDate(monday)
}

function dayInPlannedWeek(offset) {
  const [y, m, d] = plannedMonday().split('-').map(Number)
  const date = new Date(y, m - 1, d + offset)
  return isoDate(date)
}

test.describe('planning a week by hand', () => {
  test('typing in a cell puts work on that day, pinned', async ({ page }) => {
    await login(page, 'teacher')
    const stamp = Date.now()
    const title = `Chapter ${stamp}`
    const wednesday = dayInPlannedWeek(2)

    await page.goto('/admin/week')
    await expect(page.getByTestId('week-grid')).toBeVisible()

    // Row 1 is the first class; the cell for Wednesday of the planned week.
    const row = page.locator('tbody tr').first()
    await row.locator('td.cell').nth(2).click()
    await row.locator('.cell-input').fill(title)
    await row.locator('.cell-input').press('Enter')

    // Scoped to the grid: the same title can legitimately appear in the
    // behind-strip too, and an unscoped match is a strict-mode violation.
    await expect(page.getByTestId('week-grid').getByText(title)).toBeVisible()

    // The database, not just the screen: on the right day, and pinned —
    // the teacher typed a day, which is the strongest placement statement
    // the app can be given.
    const week = await apiCall(page, 'get', '/week/')
    const created = week.entries.find(e => e.title === title)
    expect(created).toBeTruthy()
    expect(created.scheduled_date).toBe(wednesday)
    expect(created.date_locked).toBe(true)
  })

  test('the week opens on the week being planned, not the one ending', async ({ page }) => {
    // A Sunday-evening planner that opens on the week just finished makes the
    // teacher navigate before he can start. It opens on the week containing
    // tomorrow, which on any Sunday is the one about to begin.
    await login(page, 'teacher')
    const week = await apiCall(page, 'get', '/week/')
    expect(week.week_start).toBe(plannedMonday())
  })

  test('an entry can be moved to another day and stays there', async ({ page }) => {
    await login(page, 'teacher')
    const stamp = Date.now()
    const monday = dayInPlannedWeek(0)
    const thursday = dayInPlannedWeek(3)

    const created = await apiCall(page, 'post', '/week/entries', {
      course_id: 1,
      scheduled_date: monday,
      title: `Movable ${stamp}`,
    })
    expect(created.scheduled_date).toBe(monday)

    const moved = await apiCall(page, 'put', `/week/entries/${created.id}/move`, {
      scheduled_date: thursday,
    })
    expect(moved.scheduled_date).toBe(thursday)
    expect(moved.date_locked).toBe(true)

    // And a day off does not undo the decision.
    await apiCall(page, 'post', `/schedule/sick-day?date_val=${thursday}`)
    expect((await apiCall(page, 'get', `/tasks/${created.id}`)).scheduled_date).toBe(thursday)
  })

  test('removing an entry takes its XP back out of the ledger', async ({ page }) => {
    // Hand-entered work is authored per week, so a lesson here has no reuse to
    // protect and removing it should really remove it. What must not vanish
    // quietly is XP already awarded: the balance has to come back down, and it
    // does so as a new negative row, never by deleting history.
    //
    // The balance is read as the student on purpose. /analytics/summary always
    // reports the calling user's own XP, and the teacher has none — reading it
    // as the teacher returns 0 both times and the assertion passes while
    // proving nothing.
    await login(page, 'teacher')
    const stamp = Date.now()

    const created = await apiCall(page, 'post', '/week/entries', {
      course_id: 1,
      scheduled_date: isoDate(new Date()),
      title: `Removable ${stamp}`,
      xp_reward: 25,
    })
    await apiCall(page, 'post', `/tasks/${created.id}/complete`, {
      completion_notes: 'done',
      focus_minutes: 5,
    })

    // logout before each switch: the router sends an authenticated visitor
    // straight from /login to their own dashboard, so login() would never see
    // the sign-in screen it is waiting for.
    await logout(page)
    await login(page, 'student')
    const before = (await apiCall(page, 'get', '/analytics/summary')).xp_balance

    await logout(page)
    await login(page, 'teacher')
    await apiCall(page, 'delete', `/week/entries/${created.id}`)
    const week = await apiCall(page, 'get', '/week/')
    expect(week.entries.find(e => e.id === created.id)).toBeUndefined()

    await logout(page)
    await login(page, 'student')
    const after = (await apiCall(page, 'get', '/analytics/summary')).xp_balance
    expect(after).toBe(before - 25)
  })

  test('a class can be added and hidden from the planner itself', async ({ page }) => {
    // The class manager and the task manager were both removed; whatever they
    // did that still matters has to be reachable from this one screen or it is
    // gone. Adding and retiring a class is the whole of what remained.
    await login(page, 'teacher')
    const name = `Latin ${Date.now()}`

    await page.goto('/admin/week')
    await page.getByTestId('add-class').click()
    await page.locator('.class-input').fill(name)
    await page.locator('.class-input').press('Enter')

    const row = page.locator('tbody tr', { hasText: name })
    await expect(row).toBeVisible()

    // Hiding is deactivation, not deletion: finished work under a class the
    // household stopped teaching still has to count toward the UFA record.
    await row.locator('.row-btn').click()
    await expect(page.locator('tbody tr', { hasText: name })).toHaveCount(0)

    const all = await apiCall(page, 'get', '/courses/?include_inactive=true')
    const hidden = all.find(c => c.title === name)
    expect(hidden).toBeTruthy()
    expect(hidden.is_active).toBe(false)
  })

  test('a card opens an editor, and saving keeps what it does not show', async ({ page }) => {
    // The task form is gone; this is where minutes, links and teacher-led live
    // now. The editor sends a partial update, so anything outside it - the
    // date, the pin, the XP - has to survive untouched.
    await login(page, 'teacher')
    const stamp = Date.now()
    const week = await apiCall(page, 'get', '/week/')

    const created = await apiCall(page, 'post', '/week/entries', {
      course_id: 1,
      scheduled_date: week.week_start,
      title: `Editable ${stamp}`,
    })

    await page.goto('/admin/week')
    await page.locator('.entry', { hasText: `Editable ${stamp}` }).click()

    const editor = page.locator('.entry-editor')
    await editor.locator('.edit-row input').first().fill('45')
    await editor.locator('.edit-url').fill('https://example.com/lesson')
    await page.getByTestId('save-entry').click()

    await expect(page.locator('.entry', { hasText: '45m' })).toBeVisible()

    const after = await apiCall(page, 'get', `/tasks/${created.id}`)
    expect(after.estimated_minutes).toBe(45)
    expect(after.resource_url).toBe('https://example.com/lesson')
    // Untouched by an edit that never mentioned them.
    expect(after.scheduled_date).toBe(week.week_start)
    expect(after.date_locked).toBe(true)
    expect(after.xp_reward).toBe(10)
  })

  test('unfinished work from before today is surfaced, not carried forward', async ({ page }) => {
    // The teacher's half of the day cap: the backlog is a decision an adult
    // makes, not something that silently accumulates on a nine-year-old's
    // morning. Nothing here moves it — it is listed so it can be dealt with.
    await login(page, 'teacher')
    const stamp = Date.now()
    const lastWeek = new Date()
    lastWeek.setDate(lastWeek.getDate() - 6)

    const stale = await apiCall(page, 'post', '/tasks/', {
      title: `Left behind ${stamp}`,
      course_id: 1,
      scheduled_date: isoDate(lastWeek),
    })

    const week = await apiCall(page, 'get', '/week/')
    expect(week.behind.map(b => b.id)).toContain(stale.id)
    // Still on its original day. Being behind is information, not an action.
    expect((await apiCall(page, 'get', `/tasks/${stale.id}`)).scheduled_date).toBe(isoDate(lastWeek))
  })
})
