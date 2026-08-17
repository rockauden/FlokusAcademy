import { test, expect } from '@playwright/test'
import { login, apiCall } from './helpers.js'

/** A program with three units — one released, two not — and a lesson in each. */
async function seedProgramWithUnits(page) {
  const stamp = Date.now()
  const program = await apiCall(page, 'post', '/courses/', {
    title: `Gating program ${stamp}`,
    subject_area: 'Test',
    platform: 'e2e',
  })

  const units = {}
  for (const [key, status] of [['active', 'active'], ['plannedA', 'planned'], ['plannedB', 'planned']]) {
    units[key] = await apiCall(page, 'post', '/modules/', {
      title: `${key} unit ${stamp}`,
      course_id: program.id,
      status,
    })
  }

  const lessons = {}
  for (const [key, unit] of Object.entries(units)) {
    lessons[key] = await apiCall(page, 'post', '/tasks/', {
      title: `${key} lesson ${stamp}`,
      course_id: program.id,
      module_id: unit.id,
      // Staged, not scheduled: undated and therefore the scheduler's to place.
      scheduled_date: null,
    })
  }

  return { program, units, lessons }
}

test.describe('the scheduler paces only released units', () => {
  test('planned units stay undated while the active one is scheduled', async ({ page }) => {
    // The safety valve for the whole curriculum migration. A full-year import
    // creates hundreds of undated assignments across ~26 units, and one sick
    // day fires reschedule_from_today across the entire tenant. Without the
    // unit-status clause that single click dates every unit at once and hands
    // a nine-year-old every subject's next lesson on the same morning.
    await login(page, 'teacher')
    const { lessons } = await seedProgramWithUnits(page)

    // A quick add with no unit at all — the outer join has to keep this.
    const quickAdd = await apiCall(page, 'post', '/tasks/', {
      title: `Unit-less quick add ${Date.now()}`,
      course_id: 1,
      scheduled_date: null,
    })

    await apiCall(page, 'post', '/schedule/recalculate', {})

    const active = await apiCall(page, 'get', `/tasks/${lessons.active.id}`)
    const plannedA = await apiCall(page, 'get', `/tasks/${lessons.plannedA.id}`)
    const plannedB = await apiCall(page, 'get', `/tasks/${lessons.plannedB.id}`)
    const unitless = await apiCall(page, 'get', `/tasks/${quickAdd.id}`)

    expect(active.scheduled_date).not.toBeNull()
    expect(plannedA.scheduled_date).toBeNull()
    expect(plannedB.scheduled_date).toBeNull()
    // An inner join would have dropped this one silently.
    expect(unitless.scheduled_date).not.toBeNull()
  })

  test('activating a planned unit releases it', async ({ page }) => {
    await login(page, 'teacher')
    const { units, lessons } = await seedProgramWithUnits(page)

    await apiCall(page, 'post', '/schedule/recalculate', {})
    expect((await apiCall(page, 'get', `/tasks/${lessons.plannedA.id}`)).scheduled_date).toBeNull()

    const unit = await apiCall(page, 'get', `/modules/${units.plannedA.id}`)
    const { id, course_id, created_at, ...rest } = unit
    await apiCall(page, 'put', `/modules/${units.plannedA.id}`, { ...rest, status: 'active' })

    await apiCall(page, 'post', '/schedule/recalculate', {})
    expect((await apiCall(page, 'get', `/tasks/${lessons.plannedA.id}`)).scheduled_date).not.toBeNull()
    // Its sibling is still planned, and still unreleased.
    expect((await apiCall(page, 'get', `/tasks/${lessons.plannedB.id}`)).scheduled_date).toBeNull()
  })
})

