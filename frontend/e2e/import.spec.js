import { test, expect } from '@playwright/test'
import { login, apiCall, apiError } from './helpers.js'

/**
 * The Phase 2 importer. Two kinds of coverage here, on purpose:
 *
 * - The UI specs drive the real screen — file chosen, preview read, commit
 *   clicked — because the screen is the checkpoint the teacher trusts.
 * - The idempotency and rollback specs go through the API via the app's own
 *   client: they assert database truths (a no-op is a no-op, completion
 *   survives a corrected re-import) that no amount of UI reading can prove.
 */

const HEADER = 'program,unit,title,task_type,priority,estimated_minutes,xp_reward'

function csvFile(rows, name = 'import.csv') {
  // \r\n and a UTF-8 BOM, exactly as Excel exports — the parser must eat both.
  const text = '\uFEFF' + [HEADER, ...rows].join('\r\n') + '\r\n'
  return { name, mimeType: 'text/csv', buffer: Buffer.from(text, 'utf-8') }
}

function csvText(rows) {
  return '\uFEFF' + [HEADER, ...rows].join('\r\n') + '\r\n'
}

async function courseIdByTitle(page, title) {
  const courses = await apiCall(page, 'get', '/courses/?include_inactive=true')
  const course = courses.find((c) => c.title === title)
  expect(course).toBeTruthy()
  return course.id
}

test.describe('curriculum import', () => {
  test('a file previews, commits through the screen, and the year arrives staged', async ({ page }) => {
    await login(page, 'teacher')
    const stamp = Date.now()
    const program = `Imported program ${stamp}`

    await page.goto('/admin/import')
    await page.locator('input[type="file"]').setInputFiles(csvFile([
      `${program},Vol 1,Chapter One,reading,core,30,10`,
      `${program},Vol 1,Chapter Two,reading,standard,30,10`,
      `${program},Vol 2,Chapter Three,reading,standard,30,10`,
    ]))

    const summary = page.getByTestId('import-summary')
    await expect(summary).toContainText('3')
    await expect(summary).toContainText('0 errors')
    await expect(summary).toContainText(program)

    await page.getByTestId('commit-import').click()
    await expect(page.getByTestId('import-id')).toBeVisible()

    // The database truth behind the success message: the lessons exist, and
    // every assignment is staged — no dates, nothing in the student's day.
    // Importing never sets dates; release does.
    const courseId = await courseIdByTitle(page, program)
    const tasks = await apiCall(page, 'get', `/tasks/?course_id=${courseId}`)
    expect(tasks).toHaveLength(3)
    for (const task of tasks) {
      expect(task.scheduled_date).toBeNull()
      expect(task.date_locked).toBe(false)
    }
  })

  test('a malformed row blocks commit, names its row, and is fixable in place', async ({ page }) => {
    await login(page, 'teacher')
    const stamp = Date.now()
    const program = `Fixable program ${stamp}`

    await page.goto('/admin/import')
    await page.locator('input[type="file"]').setInputFiles(csvFile([
      `${program},Vol 1,Good row,reading,core,30,10`,
      // "reeding" — the typo the row-numbered error exists for. This is data
      // row 2 of the file, spreadsheet row 3.
      `${program},Vol 1,Bad row,reeding,core,30,10`,
    ]))

    const errors = page.getByTestId('import-errors')
    await expect(errors).toContainText('Row 3')
    await expect(errors).toContainText('task_type')
    await expect(page.getByTestId('commit-import')).toBeDisabled()

    // Fix the raw line in place and re-check — the server, not the client,
    // decides the row is now fine.
    await errors.locator('.line-edit').fill(`${program},Vol 1,Bad row,reading,core,30,10`)
    await errors.getByRole('button', { name: 'Re-check file' }).click()

    await expect(page.getByTestId('import-summary')).toContainText('0 errors')
    await expect(page.getByTestId('commit-import')).toBeEnabled()
  })

  test('re-importing an unchanged file is a no-op', async ({ page }) => {
    await login(page, 'teacher')
    const stamp = Date.now()
    const program = `Idempotent program ${stamp}`
    const text = csvText([
      `${program},Vol 1,Lesson A,reading,core,30,10`,
      `${program},Vol 1,Lesson B,reading,standard,30,10`,
    ])

    const first = await apiCall(page, 'post', '/curriculum/commit', { csv_text: text })
    expect(first.new).toBe(2)
    expect(first.import_id).toBeTruthy()

    const second = await apiCall(page, 'post', '/curriculum/commit', { csv_text: text })
    expect(second.new).toBe(0)
    expect(second.updated).toBe(0)
    expect(second.unchanged).toBe(2)

    // Identical state, not just identical counts: still exactly two lessons.
    const courseId = await courseIdByTitle(page, program)
    expect(await apiCall(page, 'get', `/tasks/?course_id=${courseId}`)).toHaveLength(2)
  })

  test('a corrected re-import updates the lesson without touching completion history', async ({ page }) => {
    await login(page, 'teacher')
    const stamp = Date.now()
    const program = `Corrected program ${stamp}`
    const row = (xp) => `${program},Vol 1,Lesson A,reading,core,30,${xp}`

    await apiCall(page, 'post', '/curriculum/commit', { csv_text: csvText([row(10)]) })

    const courseId = await courseIdByTitle(page, program)
    const [task] = await apiCall(page, 'get', `/tasks/?course_id=${courseId}`)
    await apiCall(page, 'post', `/tasks/${task.id}/complete`, {
      completion_notes: 'Done before the correction',
      focus_minutes: 12,
    })

    // The teacher fixes the XP value in the workbook and re-imports.
    const report = await apiCall(page, 'post', '/curriculum/commit', { csv_text: csvText([row(25)]) })
    expect(report.updated).toBe(1)
    expect(report.new).toBe(0)

    // The lesson took the correction; the student's history took nothing.
    const refreshed = await apiCall(page, 'get', `/tasks/${task.id}`)
    expect(refreshed.xp_reward).toBe(25)
    expect(refreshed.is_completed).toBe(true)
    expect(refreshed.completion_notes).toBe('Done before the correction')
    expect(refreshed.focus_minutes).toBe(12)
  })

  test('rollback undoes a fresh import, refuses completed work, reverses XP under force', async ({ page }) => {
    await login(page, 'teacher')
    const stamp = Date.now()
    const program = `Rollback program ${stamp}`
    const text = csvText([
      `${program},Vol 1,Lesson A,reading,core,30,10`,
      `${program},Vol 1,Lesson B,reading,standard,30,10`,
    ])

    const { import_id } = await apiCall(page, 'post', '/curriculum/commit', { csv_text: text })
    const courseId = await courseIdByTitle(page, program)
    const tasks = await apiCall(page, 'get', `/tasks/?course_id=${courseId}`)
    await apiCall(page, 'post', `/tasks/${tasks[0].id}/complete`, {
      completion_notes: 'Earned before the rollback',
      focus_minutes: 5,
    })

    // Completed work blocks the plain rollback, and says so.
    const refusal = await apiError(page, 'post', '/curriculum/rollback', { import_id })
    expect(refusal).toContain('Completed work')

    // Forcing reverses the earned XP through the ledger, then deletes.
    const result = await apiCall(page, 'post', '/curriculum/rollback', { import_id, force: true })
    expect(result.lessons_deleted).toBe(2)
    expect(result.xp_reversed).toBeGreaterThan(0)

    expect(await apiCall(page, 'get', `/tasks/?course_id=${courseId}`)).toHaveLength(0)
  })
})
