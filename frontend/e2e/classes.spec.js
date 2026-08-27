import { test, expect } from '@playwright/test'
import { login, apiCall } from './helpers.js'

test.describe('class manager', () => {
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

  test('clearing unstarted work keeps what was actually finished', async ({ page }) => {
    // The escape hatch for an abandoned plan — and the line it must not cross.
    // Deleting a lesson cascades to its assignments, which is the right thing
    // for work nobody ever did and a data-loss bug for work someone did. The
    // server decides that per lesson; the button cannot override it.
    await login(page, 'teacher')
    const stamp = Date.now()
    const program = await apiCall(page, 'post', '/courses/', {
      title: `Clearable class ${stamp}`,
      subject_area: 'Test',
      platform: 'e2e',
    })

    const finished = await apiCall(page, 'post', '/tasks/', {
      title: `Actually done ${stamp}`,
      course_id: program.id,
    })
    await apiCall(page, 'post', `/tasks/${finished.id}/complete`, {
      completion_notes: 'Done before the clear-out',
      focus_minutes: 20,
    })
    await apiCall(page, 'post', '/tasks/', { title: `Never started ${stamp}`, course_id: program.id })
    await apiCall(page, 'post', '/tasks/', { title: `Also never started ${stamp}`, course_id: program.id })

    const result = await apiCall(page, 'post', `/courses/${program.id}/clear-unstarted`)
    expect(result.lessons_deleted).toBe(2)
    expect(result.completed_kept).toBe(1)

    const left = await apiCall(page, 'get', `/tasks/?course_id=${program.id}`)
    expect(left).toHaveLength(1)
    expect(left[0].is_completed).toBe(true)
    expect(left[0].completion_notes).toBe('Done before the clear-out')
  })
})
