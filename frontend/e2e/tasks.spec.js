import { test, expect } from '@playwright/test'
import { login, logout, quickAddTask, todayISO } from './helpers.js'

test.describe('task creation reaches the student', () => {
  test('quick add defaults the scheduled date to today', async ({ page }) => {
    // Regression: the field defaulted to '', which became a NULL
    // scheduled_date. The student's day filters on `scheduled_date <= today`,
    // and NULL <= today is NULL rather than true in SQL, so undated work was
    // invisible to the student while still listed for the teacher.
    await login(page, 'teacher')
    await page.goto('/admin/tasks')
    await page.getByRole('button', { name: 'Quick Add' }).click()

    const dateField = page.locator('.task-form input[type="date"]')
    await expect(dateField).toHaveValue(todayISO())
  })

  test('a task created by the teacher appears in the student day', async ({ page }) => {
    await login(page, 'teacher')
    const title = await quickAddTask(page, 'Beast Academy')

    // The teacher sees it.
    await page.goto('/admin/tasks')
    await page.getByRole('button', { name: 'Task List' }).click()
    await expect(page.getByText(title)).toBeVisible()

    // And so does the student -- the half that was broken.
    await logout(page)
    await login(page, 'student')
    await expect(page.getByText(title)).toBeVisible()
  })

  test('the student day counts the new task', async ({ page }) => {
    await login(page, 'teacher')
    await quickAddTask(page, 'Counted task')
    await logout(page)

    await login(page, 'student')
    const day = await page.evaluate(async () => {
      const response = await fetch('/api/tasks/today', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      })
      return response.json()
    })

    expect(day.date).toBe(new Date().toISOString().slice(0, 10))
    expect(day.tasks.length).toBeGreaterThan(0)
  })
})

test.describe('task form validation', () => {
  test('a blank title is rejected without contacting the server', async ({ page }) => {
    await login(page, 'teacher')
    await page.goto('/admin/tasks')
    await page.getByRole('button', { name: 'Quick Add' }).click()

    let posted = 0
    page.on('request', (request) => {
      if (request.method() === 'POST' && request.url().includes('/api/tasks')) posted += 1
    })

    await page.locator('.task-form select').first().selectOption('1')
    await page.getByRole('button', { name: 'Save Task' }).click()

    await expect(page.locator('.form-error')).toHaveText(/title/i)
    expect(posted).toBe(0)
  })

  test('a missing course is rejected without contacting the server', async ({ page }) => {
    await login(page, 'teacher')
    await page.goto('/admin/tasks')
    await page.getByRole('button', { name: 'Quick Add' }).click()

    let posted = 0
    page.on('request', (request) => {
      if (request.method() === 'POST' && request.url().includes('/api/tasks')) posted += 1
    })

    await page.locator('.task-form input[type="text"]').first().fill('No course chosen')
    await page.getByRole('button', { name: 'Save Task' }).click()

    await expect(page.locator('.form-error')).toHaveText(/course/i)
    expect(posted).toBe(0)
  })

  test('a server validation error is readable, not [object Object]', async ({ page }) => {
    await login(page, 'teacher')

    const message = await page.evaluate(async () => {
      const { api } = await import('/src/api/client.js')
      try {
        await api.post('/tasks/', { title: 'x', course_id: 1, scheduled_date: 'not-a-date' })
        return null
      } catch (error) {
        return error.message
      }
    })

    expect(message).toContain('scheduled_date')
    expect(message).not.toContain('[object Object]')
  })
})
