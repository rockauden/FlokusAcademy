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
      if (data) courses.value = data
    } finally {
      loading.value = false
    }
  }

  return { courses, loading, fetchCourses }
})
