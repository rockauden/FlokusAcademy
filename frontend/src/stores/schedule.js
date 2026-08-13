import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api/client'

export const useScheduleStore = defineStore('schedule', () => {
  const nonSchoolDays = ref([])
  const loading = ref(false)

  async function fetchCalendar(start, end) {
    loading.value = true
    try {
      const data = await api.get(`/schedule/calendar?start=${start}&end=${end}`)
      if (data) nonSchoolDays.value = data
    } finally {
      loading.value = false
    }
  }

  async function addSickDay(date, label) {
    await api.post('/schedule/sick-day', { date, label })
  }

  async function addHoliday(date, label) {
    await api.post('/schedule/holiday', { date, label })
  }

  async function recalculate(moduleId = null) {
    const payload = moduleId ? { module_id: moduleId } : {}
    await api.post('/schedule/recalculate', payload)
  }

  async function removeNonSchoolDay(id) {
    // Delete event using event id if possible (backend support needed)
    // Assume events can be deleted via /events/{id} for now.
    await api.delete(`/events/${id}`)
  }

  return { nonSchoolDays, loading, fetchCalendar, addSickDay, addHoliday, recalculate, removeNonSchoolDay }
})
