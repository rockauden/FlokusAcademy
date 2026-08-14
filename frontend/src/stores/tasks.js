import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '../api/client'

export const useTasksStore = defineStore('tasks', () => {
  const todayTasks = ref([])
  const todayDate = ref(null)
  const allTasks = ref([])
  const loading = ref(false)

  // Guarded so a shape change in the API degrades to an empty list instead of
  // throwing inside a computed and blanking the whole view.
  const pendingTasks = computed(() =>
    Array.isArray(todayTasks.value) ? todayTasks.value.filter(t => !t.is_completed) : []
  )
  const completedTasks = computed(() =>
    Array.isArray(todayTasks.value) ? todayTasks.value.filter(t => t.is_completed) : []
  )

  const tasksBySubject = computed(() => {
    const grouped = {}
    if (!Array.isArray(todayTasks.value)) return grouped
    todayTasks.value.forEach(task => {
      const course = task.course?.title || 'Other'
      if (!grouped[course]) grouped[course] = []
      grouped[course].push(task)
    })
    return grouped
  })

  async function fetchTodayTasks() {
    loading.value = true
    try {
      // GET /api/tasks/today returns a StudentDayView: { date, tasks: [...] }
      const data = await api.get('/tasks/today')
      todayTasks.value = Array.isArray(data?.tasks) ? data.tasks : []
      todayDate.value = data?.date ?? null
    } finally {
      loading.value = false
    }
  }

  async function fetchAllTasks(filters = {}) {
    loading.value = true
    try {
      const query = new URLSearchParams(filters).toString()
      const data = await api.get(`/tasks?${query}`)
      allTasks.value = Array.isArray(data) ? data : []
    } finally {
      loading.value = false
    }
  }

  async function createTask(data) {
    await api.post('/tasks', data)
    await fetchTodayTasks()
  }

  async function completeTask(id, notes, minutes) {
    await api.post(`/tasks/${id}/complete`, { completion_notes: notes, focus_minutes: minutes })
    await fetchTodayTasks()
  }

  async function deleteTask(id) {
    await api.delete(`/tasks/${id}`)
    await fetchAllTasks()
  }

  return { todayTasks, todayDate, allTasks, loading, pendingTasks, completedTasks, tasksBySubject, fetchTodayTasks, fetchAllTasks, createTask, completeTask, deleteTask }
})
