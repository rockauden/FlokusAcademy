import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * Errors that should be visible to the person using the app.
 *
 * Every failure this project has hit was silent: a button did nothing, a list
 * stayed empty, and the only signal was someone eventually saying the app felt
 * broken. Anything that reaches here gets shown.
 */
export const useErrorsStore = defineStore('errors', () => {
  const items = ref([])
  let nextId = 1

  function report(message, { requestId = null, fatal = false } = {}) {
    const text = String(message || 'Something went wrong.')

    // Repeated identical failures (a poll on a 30s timer, say) should not
    // stack up into a wall of the same message.
    const existing = items.value.find((item) => item.message === text)
    if (existing) {
      existing.count += 1
      return existing.id
    }

    const id = nextId++
    items.value.push({ id, message: text, requestId, fatal, count: 1 })
    return id
  }

  function dismiss(id) {
    items.value = items.value.filter((item) => item.id !== id)
  }

  function clear() {
    items.value = []
  }

  return { items, report, dismiss, clear }
})
