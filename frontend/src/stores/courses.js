import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api/client'

// The API vocabulary is `courses`; the UI says "Program". Deliberate — see
// routers/modules.py:14. Renaming the paths is its own migration, not a
// drive-by, so the store keeps the API's word and the views use the teacher's.
export const useCoursesStore = defineStore('courses', () => {
  const courses = ref([])
  const loading = ref(false)

  async function fetchCourses({ includeInactive = false } = {}) {
    loading.value = true
    try {
      const query = includeInactive ? '?include_inactive=true' : ''
      const data = await api.get(`/courses/${query}`)
      // Mirrors the tasks store. The API client falls back to {} when a body
      // cannot be parsed, and assigning that here hands an object to a prop
      // typed Array — which Vue warns about and the course picker renders as
      // empty. Surfaced by the end-to-end suite.
      courses.value = Array.isArray(data) ? data : []
    } finally {
      loading.value = false
    }
  }

  // Trailing slash on every collection path. Without it FastAPI answers with a
  // 307 whose Location is absolute, and behind the TLS-terminating proxy that
  // came back as http:// — which the browser blocked as mixed content, so the
  // request silently did nothing. See stores/tasks.js:60-66.
  async function createCourse(data) {
    return await api.post('/courses/', data)
  }

  async function updateCourse(id, data) {
    return await api.put(`/courses/${id}`, data)
  }

  // DELETE deactivates rather than deletes: a program's lessons, and the XP
  // earned against them, outlive the decision to stop teaching it.
  async function deactivateCourse(id) {
    return await api.delete(`/courses/${id}`)
  }

  return { courses, loading, fetchCourses, createCourse, updateCourse, deactivateCourse }
})
