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
 * Call the API as the signed-in user, through the app's own client.
 *
 * Going via `api` rather than a bare fetch means the request carries the same
 * headers, trailing slashes and error handling the real client uses — a spec
 * that hand-rolled the request could pass while the app was broken.
 *
 * Throws on a non-2xx, so use `apiError` when the failure is the thing under
 * test.
 */
export async function apiCall(page, method, path, body = undefined) {
  return await page.evaluate(async ({ method, path, body }) => {
    const { api } = await import('/src/api/client.js')
    return await api[method](path, body)
  }, { method, path, body })
}

/** The message from a failed API call. Returns null if the call succeeded. */
export async function apiError(page, method, path, body = undefined) {
  return await page.evaluate(async ({ method, path, body }) => {
    const { api } = await import('/src/api/client.js')
    try {
      await api[method](path, body)
      return null
    } catch (error) {
      return error.message
    }
  }, { method, path, body })
}

/** Local date as YYYY-MM-DD for a Date, matching todayISO's timezone handling. */
export function isoDate(date) {
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${date.getFullYear()}-${month}-${day}`
}

/**
 * The first date strictly after today falling on `jsWeekday`
 * (0=Sun … 6=Sat), as YYYY-MM-DD.
 *
 * Specs use this rather than a fixed date so they do not start failing on a
 * particular day of the week, or once the hardcoded date is in the past.
 */
export function nextWeekday(jsWeekday, { from = new Date(), skip = 0 } = {}) {
  const date = new Date(from.getFullYear(), from.getMonth(), from.getDate() + 1)
  while (date.getDay() !== jsWeekday) {
    date.setDate(date.getDate() + 1)
  }
  date.setDate(date.getDate() + 7 * skip)
  return isoDate(date)
}

/** 0=Sun … 6=Sat for a YYYY-MM-DD string, parsed as a local date. */
export function weekdayOf(isoString) {
  const [year, month, day] = isoString.split('-').map(Number)
  return new Date(year, month - 1, day).getDay()
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
