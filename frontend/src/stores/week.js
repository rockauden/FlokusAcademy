import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api/client'

/**
 * The week planner — hand-entered planning, one week at a time, and since
 * 2026-08-26 the only way work enters the app.
 *
 * No trailing slash issues to inherit: `/week/` is a collection and keeps its
 * slash, the entry paths are actions and do not have one, matching what the
 * backend declares. See stores/tasks.js:60 for what the mismatch costs.
 */
export const useWeekStore = defineStore('week', () => {
  const week = ref(null)
  const loading = ref(false)
  const saving = ref(false)

  async function fetchWeek(startDate = null) {
    loading.value = true
    try {
      const query = startDate ? `?start=${startDate}` : ''
      week.value = await api.get(`/week/${query}`)
      return week.value
    } finally {
      loading.value = false
    }
  }

  async function addEntry(entry) {
    saving.value = true
    try {
      return await api.post('/week/entries', entry)
    } finally {
      saving.value = false
    }
  }

  async function moveEntry(id, scheduledDate) {
    return await api.put(`/week/entries/${id}/move`, { scheduled_date: scheduledDate })
  }

  async function removeEntry(id) {
    return await api.delete(`/week/entries/${id}`)
  }

  return { week, loading, saving, fetchWeek, addEntry, moveEntry, removeEntry }
})
