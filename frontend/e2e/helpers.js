import { expect } from '@playwright/test'

// Matches backend/scripts/run_test_api.py, which seeds these two accounts into
// a database created fresh for each run.
export const TEACHER_PIN = '1234'
export const STUDENT_PIN = '4321'

/** Local date as YYYY-MM-DD, matching what the task form defaults to. */
export function todayISO() {
  const now = new Date()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${now.getFullYear()}-${month}-${day}`
}

/** Sign in through the real login screen, not by injecting a token. */
export async function login(page, role) {
  const card = role === 'teacher' ? "Dad's Dashboard" : "Sonny's Hub"
  const pin = role === 'teacher' ? TEACHER_PIN : STUDENT_PIN

  await page.goto('/login')
  await page.getByRole('button', { name: new RegExp(card, 'i') }).click()

  await page.locator('input[type="password"]').fill(pin)
  await page.getByRole('button', { name: 'Login', exact: true }).click()

  await expect(page).toHaveURL(new RegExp(role === 'teacher' ? '/admin' : '/student'))
}

export async function logout(page) {
  await page.evaluate(async () => {
    const { useAuthStore } = await import('/src/stores/auth.js')
    await useAuthStore().logout()
  })
  await expect(page).toHaveURL(/\/login/)
}

/**
 * Create a task through the Quick Add form. Returns the title used, which is
 * unique per call so specs can assert on their own row.
 */
export async function quickAddTask(page, titlePrefix = 'E2E task') {
  const title = `${titlePrefix} ${Date.now()}`

  await page.goto('/admin/tasks')
  await page.getByRole('button', { name: 'Quick Add' }).click()

  const form = page.locator('.task-form')
  await expect(form).toBeVisible()

  await form.locator('input[type="text"]').first().fill(title)
  // The first select is the course picker; option "1" is the seeded Math
  // program. Selecting by index would silently pass if the order changed.
  await form.locator('select').first().selectOption('1')
  await form.getByRole('button', { name: 'Save Task' }).click()

  return title
}
