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

test.describe('program manager', () => {
  test('a program created in the UI reaches the task form picker', async ({ page }) => {
    await login(page, 'teacher')
    const title = `Tuttle Twins ${Date.now()}`

    await page.goto('/admin/programs')
    await page.locator('.program-form input[type="text"]').first().fill(title)
    await page.locator('.program-form input[type="text"]').nth(1).fill('Social Studies')

    // Wait for the POST rather than the button click: the click returns as
    // soon as it is dispatched, and reloading before the request lands would
    // test nothing at all — intermittently.
    const posted = page.waitForResponse(
      r => r.url().includes('/api/courses/') && r.request().method() === 'POST'
    )
    await page.getByRole('button', { name: 'Create Program' }).click()
    await posted

    // Survives a reload — it is in the database, not just in the component.
    await page.reload()
    await expect(page.locator('.program-list').getByText(title)).toBeVisible()

    await page.goto('/admin/tasks')
    await page.getByRole('button', { name: 'Quick Add' }).click()
    await expect(
      page.locator('.task-form select').first().locator('option', { hasText: title })
    ).toHaveCount(1)
  })

  test('deactivating hides the program from the picker but keeps its lessons', async ({ page }) => {
    await login(page, 'teacher')
    const title = `Retired program ${Date.now()}`

    const program = await apiCall(page, 'post', '/courses/', {
      title,
      subject_area: 'Test',
      platform: 'e2e',
    })
    const lesson = await apiCall(page, 'post', '/tasks/', {
      title: `Lesson under ${title}`,
      course_id: program.id,
    })

    await page.goto('/admin/programs')
    const row = page.locator('.program-item', { hasText: title })
    await row.getByRole('button', { name: 'Deactivate' }).click()
    await expect(row.getByText('Deactivated')).toBeVisible()

    // Gone from the picker…
    await page.goto('/admin/tasks')
    await page.getByRole('button', { name: 'Quick Add' }).click()
    await expect(
      page.locator('.task-form select').first().locator('option', { hasText: title })
    ).toHaveCount(0)

    // …but the curriculum and the student's work under it are untouched.
    // Deactivating a program must never reach the XP ledger.
    const survivor = await apiCall(page, 'get', `/tasks/${lesson.id}`)
    expect(survivor.title).toBe(`Lesson under ${title}`)
    expect(survivor.course_id).toBe(program.id)
  })
})

test.describe('unit manager', () => {
  test('units can be created under a program, with a status', async ({ page }) => {
    await login(page, 'teacher')
    const programTitle = `Unit host ${Date.now()}`
    await apiCall(page, 'post', '/courses/', {
      title: programTitle,
      subject_area: 'Test',
      platform: 'e2e',
    })

    await page.goto('/admin/programs')
    const row = page.locator('.program-item', { hasText: programTitle })
    await row.getByRole('button', { name: 'Units', exact: true }).click()

    const panel = page.locator('.unit-manager')
    await expect(panel).toBeVisible()

    await panel.locator('.unit-form input[type="text"]').first().fill('Vol 1 — The Miraculous Pencil')
    // Authoring a unit and releasing it are separate acts: a new unit is
    // planned until someone turns it on.
    await expect(panel.locator('.unit-status-field')).toHaveValue('planned')
    await panel.getByRole('button', { name: 'Create Unit' }).click()

    const unitRow = panel.locator('.unit-item', { hasText: 'Vol 1 — The Miraculous Pencil' })
    // The badge, not the status <select> — both carry the same word.
    await expect(unitRow.locator('.badge')).toHaveText('planned')

    // Activating a unit is the release action — the scheduler paces only these.
    await unitRow.locator('select').selectOption('active')
    await expect(unitRow.locator('.badge')).toHaveText('active')
  })
})

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

test.describe('unit picker on the task form', () => {
  test('a lesson created through the form carries its unit', async ({ page }) => {
    // B2. Nothing in the frontend had ever set unit_id, so every lesson
    // authored through the UI landed in the unit-less pool — where the
    // scheduler groups every subject together and advances a school day per
    // lesson, spreading five unrelated quick-adds across five days.
    await login(page, 'teacher')
    const stamp = Date.now()
    const program = await apiCall(page, 'post', '/courses/', {
      title: `Picker program ${stamp}`,
      subject_area: 'Test',
      platform: 'e2e',
    })
    const unit = await apiCall(page, 'post', '/modules/', {
      title: `Picker unit ${stamp}`,
      course_id: program.id,
      status: 'active',
    })

    await page.goto('/admin/tasks')
    await page.getByRole('button', { name: 'Quick Add' }).click()

    const form = page.locator('.task-form')
    const title = `Lesson with a unit ${stamp}`
    await form.locator('input[type="text"]').first().fill(title)
    // Selecting by value rather than index: by index this would keep passing
    // if the picker's ordering changed underneath it.
    await form.locator('select').first().selectOption(String(program.id))
    await form.locator('.unit-picker').selectOption(String(unit.id))

    const posted = page.waitForResponse(
      r => r.url().includes('/api/tasks/') && r.request().method() === 'POST'
    )
    await form.getByRole('button', { name: 'Save Task' }).click()
    await posted

    const tasks = await apiCall(page, 'get', `/tasks/?course_id=${program.id}`)
    const created = tasks.find(t => t.title === title)
    expect(created).toBeTruthy()
    expect(created.module_id).toBe(unit.id)
  })

  test('changing the program clears a unit chosen under the old one', async ({ page }) => {
    // A unit belongs to exactly one program. Keeping the old selection would
    // attach the lesson to another subject's unit and pace it there.
    await login(page, 'teacher')
    const stamp = Date.now()
    const program = await apiCall(page, 'post', '/courses/', {
      title: `Reset program ${stamp}`,
      subject_area: 'Test',
      platform: 'e2e',
    })
    const unit = await apiCall(page, 'post', '/modules/', {
      title: `Reset unit ${stamp}`,
      course_id: program.id,
      status: 'active',
    })

    await page.goto('/admin/tasks')
    await page.getByRole('button', { name: 'Quick Add' }).click()

    const form = page.locator('.task-form')
    await form.locator('select').first().selectOption(String(program.id))
    await form.locator('.unit-picker').selectOption(String(unit.id))
    await expect(form.locator('.unit-picker')).not.toHaveValue('')

    await form.locator('select').first().selectOption('1')
    await expect(form.locator('.unit-picker')).toHaveValue('')
  })
})
