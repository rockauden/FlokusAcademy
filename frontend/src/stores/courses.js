import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api/client'

export const useCoursesStore = defineStore('courses', () => {
  const courses = ref([])
  const loading = ref(false)

  async function fetchCourses() {
    loading.value = true
    try {
      const data = await api.get('/courses/')
      // Mirrors the tasks store. The API client falls back to {} when a body
      // cannot be parsed, and assigning that here hands an object to a prop
      // typed Array — which Vue warns about and the course picker renders as
      // empty. Surfaced by the end-to-end suite.
      courses.value = Array.isArray(data) ? data : []
    } finally {
      loading.value = false
    }
  }

  return { courses, loading, fetchCourses }
})
