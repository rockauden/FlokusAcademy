import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api/client'

export const useScheduleStore = defineStore('schedule', () => {
  const nonSchoolDays = ref([])
  const loading = ref(false)

  async function fetchCalendar(start, end) {
    loading.value = true
    try {
      const query = new URLSearchParams({ start_date: start, end_date: end })
      const data = await api.get(`/schedule/calendar?${query}`)
      nonSchoolDays.value = Array.isArray(data) ? data : []
    } finally {
      loading.value = false
    }
  }

  // The schedule endpoints take their arguments as query parameters, not a
  // JSON body. The date parameter is named `date_val` on the API.
  //
  // These return what unfinished work falls on the day — marking a day off no
  // longer moves anything, it reports. The caller decides.
  async function addSickDay(date) {
    const query = new URLSearchParams({ date_val: date })
    return await api.post(`/schedule/sick-day?${query}`)
  }

  async function addHoliday(date, label = 'Holiday') {
    const query = new URLSearchParams({ date_val: date, label })
    return await api.post(`/schedule/holiday?${query}`)
  }

  async function removeNonSchoolDay(id) {
    // This is a school_calendar entry, not a school_event. Deleting via
    // /events/{id} silently destroyed an unrelated calendar event instead.
    await api.delete(`/schedule/calendar/${id}`)
  }

  return { nonSchoolDays, loading, fetchCalendar, addSickDay, addHoliday, removeNonSchoolDay }
})
