import { test, expect } from '@playwright/test'
import { login, apiCall, apiError, nextWeekday } from './helpers.js'

const SATURDAY = 6
const TUESDAY = 2

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
    // A pin needs a date to pin to. An undated pinned row claims a placement
    // it does not have, which is exactly the kind of quiet inconsistency the
    // week planner would then have to render.
    expect(cleared.date_locked).toBe(false)
  })
})

test.describe('one dependency_mode vocabulary', () => {
  test('the form offers only values the API accepts', async ({ page }) => {
    // B6. The form offered `with_teacher` while every other layer said
    // `teacher_led`, and the schema typed it as a bare string, so nothing
    // caught the mismatch. The scheduler that used to mis-handle it is gone;
    // the vocabulary still has to agree, and the Literal is what enforces it.
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

test.describe('marking a day off reports, and never reschedules', () => {
  test('a sick day names what falls on it and moves nothing', async ({ page }) => {
    // The behaviour that replaced the rolling scheduler. Adding a sick day
    // used to fire reschedule_from_today across the whole tenant, rewriting
    // the date of every incomplete assignment — including ones the teacher
    // had placed by hand. Now it reports and leaves them alone: the week
    // planner shows what was hit and he decides.
    await login(page, 'teacher')
    const sickDay = nextWeekday(TUESDAY, { skip: 3 })
    const untouched = nextWeekday(SATURDAY, { skip: 2 })

    const onTheDay = await apiCall(page, 'post', '/tasks/', {
      title: `Falls on the sick day ${Date.now()}`,
      course_id: 1,
      scheduled_date: sickDay,
    })
    const elsewhere = await apiCall(page, 'post', '/tasks/', {
      title: `Elsewhere that week ${Date.now()}`,
      course_id: 1,
      scheduled_date: untouched,
    })

    const result = await apiCall(page, 'post', `/schedule/sick-day?date_val=${sickDay}`)

    expect(result.day_type).toBe('sick_day')
    expect(result.affected.map(a => a.id)).toContain(onTheDay.id)

    // Reported, not moved — both dates are exactly where the teacher put them.
    expect((await apiCall(page, 'get', `/tasks/${onTheDay.id}`)).scheduled_date).toBe(sickDay)
    expect((await apiCall(page, 'get', `/tasks/${elsewhere.id}`)).scheduled_date).toBe(untouched)
  })

  test('there is no recalculate endpoint left to move work', async ({ page }) => {
    // Belt and braces on the decision: if a rescheduler is ever reintroduced,
    // this fails and someone has to think about it first.
    await login(page, 'teacher')
    const message = await apiError(page, 'post', '/schedule/recalculate', {})
    expect(message).toBeTruthy()
  })
})

test.describe('the school week stays configuration', () => {
  test('a nonsense school week is refused rather than absorbed', async ({ page }) => {
    // get_school_days searches day by day for a match, so a week that parses
    // to no days at all is an infinite loop that hangs the worker. Refusing it
    // at write time is the only place that failure is cheap.
    await login(page, 'teacher')
    const message = await apiError(page, 'put', '/config/school_days', { value: 'Blursday' })
    expect(message).toBeTruthy()

    const config = await apiCall(page, 'get', '/config/')
    expect(config.school_days).not.toBe('Blursday')
  })
})
