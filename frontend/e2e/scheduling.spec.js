import { test, expect } from '@playwright/test'
import { login, apiCall, apiError, isoDate, nextWeekday, weekdayOf } from './helpers.js'

const SATURDAY = 6
const FRIDAY = 5
const TUESDAY = 2

const CORE_SCHOOL_DAYS = 'Mon,Tue,Wed,Thu'

/** A lesson with no date and no unit: staged, unlocked, and the scheduler's to place. */
async function stageLesson(page, title, extra = {}) {
  return await apiCall(page, 'post', '/tasks/', {
    title: `${title} ${Date.now()}`,
    course_id: 1,
    scheduled_date: null,
    ...extra,
  })
}

test.describe('a partial update leaves the rest of the lesson alone', () => {
  test('sending only a title does not reset xp, duration or date', async ({ page }) => {
    // Regression, B5. TaskUpdate used to inherit TaskBase, where every field
    // but `title` has a default, and update_task called model_dump() — which
    // returns those defaults for fields the client never sent. Renaming a
    // lesson therefore reset its XP to 10, its duration to 30, its type to
    // "reading", and its scheduled_date to None. That last one removed the
    // assignment from the student's day outright.
    await login(page, 'teacher')
    const scheduled = nextWeekday(TUESDAY, { skip: 4 })

    const created = await apiCall(page, 'post', '/tasks/', {
      title: `Partial update ${Date.now()}`,
      course_id: 1,
      xp_reward: 50,
      estimated_minutes: 45,
      task_type: 'quiz',
      scheduled_date: scheduled,
    })
    expect(created.xp_reward).toBe(50)

    const updated = await apiCall(page, 'put', `/tasks/${created.id}`, { title: 'Renamed only' })

    expect(updated.title).toBe('Renamed only')
    expect(updated.xp_reward).toBe(50)
    expect(updated.estimated_minutes).toBe(45)
    expect(updated.task_type).toBe('quiz')
    expect(updated.scheduled_date).toBe(scheduled)
  })

  test('an explicit null still clears the date', async ({ page }) => {
    // exclude_unset on its own cannot tell "field absent" from "field set to
    // null", and clearing a date deliberately has to stay possible — that is
    // how a lesson goes back to being staged rather than scheduled.
    await login(page, 'teacher')

    const created = await apiCall(page, 'post', '/tasks/', {
      title: `Clearable date ${Date.now()}`,
      course_id: 1,
      scheduled_date: nextWeekday(TUESDAY, { skip: 4 }),
      date_locked: true,
    })
    expect(created.scheduled_date).not.toBeNull()
    expect(created.date_locked).toBe(true)

    const cleared = await apiCall(page, 'put', `/tasks/${created.id}`, { scheduled_date: null })
    expect(cleared.scheduled_date).toBeNull()
    // A pin needs a date to pin to. Clearing the date releases the assignment
    // back to the scheduler; leaving the flag set would strand it, since the
    // scheduler skips locked rows and would never place an undated one.
    expect(cleared.date_locked).toBe(false)
  })
})

test.describe('one dependency_mode vocabulary', () => {
  test('the form value the UI sends is one the scheduler handles', async ({ page }) => {
    // B6. The form offered `with_teacher`; the scheduler branched on
    // `teacher_led`. A lesson saved as `with_teacher` matched no branch, never
    // got a date, and still burned a slot in the sequence.
    await login(page, 'teacher')
    await page.goto('/admin/tasks')
    await page.getByRole('button', { name: 'Quick Add' }).click()

    // By class, not by index: this form grows a select or two in the same
    // phase, and an index-based locator would start asserting on the wrong one
    // while still passing.
    const dependency = page.locator('.task-form .dependency-mode')
    await expect(dependency.locator('option[value="teacher_led"]')).toHaveCount(1)
    await expect(dependency.locator('option[value="with_teacher"]')).toHaveCount(0)
  })

  test('an unknown mode is a 422, not a silent no-op', async ({ page }) => {
    await login(page, 'teacher')

    const message = await apiError(page, 'post', '/tasks/', {
      title: 'Bad dependency mode',
      course_id: 1,
      dependency_mode: 'with_teacher',
    })

    expect(message).toContain('dependency_mode')
  })
})

test.describe('core, optional and blocked days', () => {
  test('a pinned Saturday survives a sick day', async ({ page }) => {
    // B6/B10, and the reason date_locked exists. routers/schedule.py fires a
    // full-tenant reschedule_from_today on add-sick-day, not only on the
    // Recalculate button, and the scheduler assigned scheduled_date
    // unconditionally for `independent` — the default mode. So a Saturday
    // catch-up used to survive exactly until the next sick day.
    await login(page, 'teacher')
    const saturday = nextWeekday(SATURDAY, { skip: 2 })
    const sickDay = nextWeekday(TUESDAY, { skip: 3 })

    const created = await apiCall(page, 'post', '/tasks/', {
      title: `Saturday catch-up ${Date.now()}`,
      course_id: 1,
      scheduled_date: saturday,
      date_locked: true,
    })
    expect(created.scheduled_date).toBe(saturday)
    expect(created.date_locked).toBe(true)

    await apiCall(page, 'post', `/schedule/sick-day?date_val=${sickDay}`)

    const after = await apiCall(page, 'get', `/tasks/${created.id}`)
    expect(after.scheduled_date).toBe(saturday)
  })

  test('an unpinned quick add is the scheduler\'s to move', async ({ page }) => {
    // The other half of the pin, and the one that is easy to break silently.
    // An earlier cut inferred date_locked from "a scheduled_date was sent",
    // and since the task form defaults that date to today, every quick add
    // came out pinned — the scheduler could never place any of it, and the
    // whole rolling schedule quietly stopped applying to new work.
    //
    // Driven through the real form rather than the API, because the form's
    // default is the thing that made the inference wrong.
    await login(page, 'teacher')
    const today = isoDate(new Date())

    await page.goto('/admin/tasks')
    await page.getByRole('button', { name: 'Quick Add' }).click()
    const form = page.locator('.task-form')

    const title = `Unpinned quick add ${Date.now()}`
    await form.locator('input[type="text"]').first().fill(title)
    await form.locator('select').first().selectOption('1')

    // The date is today's by default and the pin is off by default. Both
    // matter: this is exactly the state a hurried quick add leaves behind.
    await expect(form.locator('input[type="date"]')).toHaveValue(today)
    await expect(form.locator('.pin-date')).not.toBeChecked()

    const posted = page.waitForResponse(
      r => r.url().includes('/api/tasks/') && r.request().method() === 'POST'
    )
    await form.getByRole('button', { name: 'Save Task' }).click()
    const created = await (await posted).json()

    expect(created.scheduled_date).toBe(today)
    expect(created.date_locked).toBe(false)

    // Block today, which is what a sick day does. The assignment is unpinned,
    // so it has to move off a day that no longer exists.
    let entryId = null
    try {
      await apiCall(page, 'post', `/schedule/sick-day?date_val=${today}`)

      const after = await apiCall(page, 'get', `/tasks/${created.id}`)
      expect(after.scheduled_date).not.toBe(today)
      expect(after.scheduled_date).not.toBeNull()
      expect(after.date_locked).toBe(false)
    } finally {
      const calendar = await apiCall(
        page, 'get', `/schedule/calendar?start_date=${today}&end_date=${today}`
      )
      entryId = calendar.find(e => e.calendar_date === today)?.id
      if (entryId) await apiCall(page, 'delete', `/schedule/calendar/${entryId}`)
    }
  })

  test('the auto-scheduler never picks a Fri, Sat or Sun on its own', async ({ page }) => {
    await login(page, 'teacher')
    const staged = await stageLesson(page, 'Unhinted lesson')
    expect(staged.scheduled_date).toBeNull()

    await apiCall(page, 'post', '/schedule/recalculate', {})

    const placed = await apiCall(page, 'get', `/tasks/${staged.id}`)
    expect(placed.scheduled_date).not.toBeNull()
    // 1=Mon … 4=Thu in JavaScript's numbering.
    expect(weekdayOf(placed.scheduled_date)).toBeGreaterThanOrEqual(1)
    expect(weekdayOf(placed.scheduled_date)).toBeLessThanOrEqual(4)
  })

  test('a Saturday day_of_week_hint is honoured, not rejected', async ({ page }) => {
    // day_of_week_hint used to be capped at 0..3 to match a scheduler that
    // treated weekday() >= 4 as weekend. A hint naming a weekend day is a
    // deliberate statement — "this lesson belongs on a Saturday".
    await login(page, 'teacher')

    // 5 = Saturday in Python's Mon-based numbering, which is what the API takes.
    const staged = await stageLesson(page, 'Saturday co-op', { day_of_week_hint: 5 })
    expect(staged.day_of_week_hint).toBe(5)

    await apiCall(page, 'post', '/schedule/recalculate', {})

    const placed = await apiCall(page, 'get', `/tasks/${staged.id}`)
    expect(placed.scheduled_date).not.toBeNull()
    expect(weekdayOf(placed.scheduled_date)).toBe(SATURDAY)
  })

  test('the school week is configuration: adding Friday changes where work lands', async ({ page }) => {
    await login(page, 'teacher')

    // Block every day between now and the next Friday, so that Friday is the
    // first unblocked day. Whether the scheduler will use it is then decided
    // by app_config.school_days alone — which is the thing under test.
    const friday = nextWeekday(FRIDAY)
    const blocked = []
    const cursor = new Date()
    cursor.setDate(cursor.getDate() + 1)
    while (isoDate(cursor) < friday) {
      blocked.push(isoDate(cursor))
      cursor.setDate(cursor.getDate() + 1)
    }
    // Today too: the scheduler starts its search from today, not tomorrow.
    blocked.unshift(isoDate(new Date()))

    const entryIds = []
    try {
      for (const day of blocked) {
        await apiCall(page, 'post', `/schedule/holiday?date_val=${day}&label=School week test`)
      }
      const calendar = await apiCall(
        page, 'get', `/schedule/calendar?start_date=${blocked[0]}&end_date=${friday}`
      )
      entryIds.push(...calendar.filter(e => e.label === 'School week test').map(e => e.id))

      // The probe gets a program and an active unit of its own. The scheduler
      // groups by (student, unit) and advances a day per lesson within a
      // group, so a probe sharing the unit-less pool with every other spec's
      // lessons would land wherever its turn in that queue fell rather than on
      // the first available day.
      const program = await apiCall(page, 'post', '/courses/', {
        title: `School week probe ${Date.now()}`,
        subject_area: 'Test',
        platform: 'e2e',
      })
      const unit = await apiCall(page, 'post', '/modules/', {
        title: 'Probe unit',
        course_id: program.id,
        status: 'active',
      })
      const staged = await stageLesson(page, 'Friday probe', {
        course_id: program.id,
        module_id: unit.id,
      })

      // Mon-Thu: Friday is not a school day, so the lesson goes past it.
      await apiCall(page, 'post', '/schedule/recalculate', {})
      const underCoreWeek = await apiCall(page, 'get', `/tasks/${staged.id}`)
      expect(underCoreWeek.scheduled_date).not.toBe(friday)
      expect(weekdayOf(underCoreWeek.scheduled_date)).toBeLessThanOrEqual(4)

      // The only change is a settings row. No deploy, no code.
      await apiCall(page, 'put', '/config/school_days', { value: 'Mon,Tue,Wed,Thu,Fri' })
      await apiCall(page, 'post', '/schedule/recalculate', {})

      const underFiveDayWeek = await apiCall(page, 'get', `/tasks/${staged.id}`)
      expect(underFiveDayWeek.scheduled_date).toBe(friday)

      // And /schedule/school-days answers from the same row, so the two never
      // describe different weeks.
      const days = await apiCall(page, 'get', `/schedule/school-days?start_date=${friday}&count=5`)
      expect(days.school_days).toContain(friday)
    } finally {
      await apiCall(page, 'put', '/config/school_days', { value: CORE_SCHOOL_DAYS })
      for (const id of entryIds) {
        await apiCall(page, 'delete', `/schedule/calendar/${id}`)
      }
    }
  })

  test('a nonsense school week is refused rather than absorbed', async ({ page }) => {
    // get_school_days searches day by day for a match, so a week with no days
    // in it is an infinite loop that hangs the worker. It has to be caught at
    // write time.
    await login(page, 'teacher')

    const message = await apiError(page, 'put', '/config/school_days', { value: 'Funday,Blursday' })
    expect(message).toMatch(/school_days/i)

    const config = await apiCall(page, 'get', '/config/')
    expect(config.school_days).toBe(CORE_SCHOOL_DAYS)
  })
})
