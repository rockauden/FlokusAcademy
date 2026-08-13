import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '../api/client'

export const useTasksStore = defineStore('tasks', () => {
  const todayTasks = ref([])
  const allTasks = ref([])
  const loading = ref(false)

  const pendingTasks = computed(() => todayTasks.value.filter(t => !t.is_completed))
  const completedTasks = computed(() => todayTasks.value.filter(t => t.is_completed))

  const tasksBySubject = computed(() => {
    const grouped = {}
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
      const data = await api.get('/tasks/today')
      if (data) todayTasks.value = data
    } finally {
      loading.value = false
    }
  }

  async function fetchAllTasks(filters = {}) {
    loading.value = true
    try {
      const query = new URLSearchParams(filters).toString()
      const data = await api.get(`/tasks?${query}`)
      if (data) allTasks.value = data
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

  return { todayTasks, allTasks, loading, pendingTasks, completedTasks, tasksBySubject, fetchTodayTasks, fetchAllTasks, createTask, completeTask, deleteTask }
})
