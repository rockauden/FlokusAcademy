import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api/client'

/**
 * Units — the middle tier of the curriculum model, and until now unreachable
 * from the client. `/api/modules` has been complete and fully functional for
 * as long as it has existed and had exactly zero frontend callers, which is
 * why every lesson authored through the UI carried a null unit_id and the
 * rolling scheduler collapsed every subject into one queue.
 *
 * The API says `module` and `course_id`; the UI says Unit and Program.
 */
export const useUnitsStore = defineStore('units', () => {
  const units = ref([])
  const loading = ref(false)

  async function fetchUnits(courseId = null, { includeInactive = false } = {}) {
    loading.value = true
    try {
      const params = new URLSearchParams()
      if (courseId !== null && courseId !== '') params.set('course_id', courseId)
      if (includeInactive) params.set('include_inactive', 'true')
      const query = params.toString()
      // Trailing slash before the query string, for the same 307 reason the
      // courses and tasks stores document.
      const data = await api.get(`/modules/${query ? `?${query}` : ''}`)
      units.value = Array.isArray(data) ? data : []
    } finally {
      loading.value = false
    }
  }

  async function createUnit(data) {
    return await api.post('/modules/', data)
  }

  async function updateUnit(id, data) {
    return await api.put(`/modules/${id}`, data)
  }

  return { units, loading, fetchUnits, createUnit, updateUnit }
})
