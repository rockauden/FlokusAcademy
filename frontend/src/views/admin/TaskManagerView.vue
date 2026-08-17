<script setup>
import { ref, onMounted, computed } from 'vue'
import { useTasksStore } from '../../stores/tasks'
import { useCoursesStore } from '../../stores/courses'
import TaskForm from '../../components/admin/TaskForm.vue'
import { api } from '../../api/client'

const tasksStore = useTasksStore()
const coursesStore = useCoursesStore()
const activeTab = ref('quick') // quick, list, bulk

const bulkText = ref('')
const bulkPreview = ref(null)

onMounted(async () => {
  await tasksStore.fetchAllTasks()
  await coursesStore.fetchCourses()
})

const pendingCount = computed(() => tasksStore.allTasks.filter(t => !t.is_completed).length)

async function handleCreateTask(taskData) {
  await tasksStore.createTask(taskData)
  alert('Task created!')
  // Reset form could be handled by v-if on TaskForm
}

async function handleDelete(id) {
  if (confirm('Delete this task?')) {
    await tasksStore.deleteTask(id)
  }
}

function parseBulk() {
  try {
    const data = JSON.parse(bulkText.value)
    bulkPreview.value = Array.isArray(data) ? data : [data]
  } catch (e) {
    alert('Invalid JSON formatting: ' + e.message + '\n\nCheck for missing commas, extra commas at the end, or missing quotes.')
  }
}

async function submitBulk() {
  if (!bulkPreview.value) return
  await api.post('/tasks/bulk', bulkPreview.value)
  alert('Imported!')
  bulkText.value = ''
  bulkPreview.value = null
  await tasksStore.fetchAllTasks()
}
</script>

<template>
  <div class="task-manager">
    <header class="page-header">
      <h1>Task Manager</h1>
      <div class="badge badge-blue">Pending Tasks: {{ pendingCount }}</div>
    </header>

    <div class="tabs mb-lg">
      <button :class="{ active: activeTab === 'quick' }" @click="activeTab = 'quick'">Quick Add</button>
      <button :class="{ active: activeTab === 'list' }" @click="activeTab = 'list'">Task List</button>
      <button :class="{ active: activeTab === 'bulk' }" @click="activeTab = 'bulk'">Bulk Import</button>
    </div>

    <div v-if="activeTab === 'quick'" class="tab-content">
      <TaskForm :courses="coursesStore.courses" @submit="handleCreateTask" />
    </div>

    <div v-if="activeTab === 'list'" class="tab-content">
      <div class="list-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Course</th>
              <th>Date</th>
              <th>Type</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="task in tasksStore.allTasks" :key="task.id">
              <td>{{ task.title }}</td>
              <td>{{ task.course?.title }}</td>
              <td>{{ task.scheduled_date || 'Unscheduled' }}</td>
              <td>{{ task.task_type }}</td>
              <td>
                <button class="btn-ghost" @click="handleDelete(task.id)">🗑️</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="activeTab === 'bulk'" class="tab-content">
      <div class="form-group">
        <label>Paste JSON Array of Tasks</label>
        <textarea v-model="bulkText" rows="10" placeholder="[{ title: '...' }]"></textarea>
      </div>
      <button class="btn-ghost mt-md" @click="parseBulk">Preview</button>
      
      <div v-if="bulkPreview" class="mt-lg">
        <h3>Preview ({{ bulkPreview.length }} tasks)</h3>
        
        <div class="list-container mt-md">
          <table class="data-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Course ID</th>
                <th>Type</th>
                <th>Min</th>
                <th>XP</th>
                <th>Day Hint</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(task, idx) in bulkPreview" :key="idx">
                <td>{{ task.title }}</td>
                <td>{{ coursesStore.courses.find(c => c.id === task.course_id)?.title || task.course_id }}</td>
                <td>{{ task.task_type }}</td>
                <td>{{ task.estimated_minutes }}</td>
                <td>{{ task.xp_reward }}</td>
                <!-- All seven days: the hint widened from 0..3 to 0..6 when
                     Fri/Sat/Sun became optional days rather than forbidden
                     ones, and a truncated list rendered a Saturday as "None". -->
                <td>{{ ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][task.day_of_week_hint] || 'None' }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <button class="btn-primary mt-md" @click="submitBulk">Confirm Import</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-lg);
}
.tabs {
  display: flex;
  gap: var(--space-sm);
  border-bottom: 1px solid var(--border-default);
  padding-bottom: var(--space-sm);
}
.tabs button {
  background: transparent;
  border: none;
  color: var(--text-muted);
  padding: var(--space-sm) var(--space-md);
}
.tabs button.active {
  color: var(--accent-blue);
  border-bottom: 2px solid var(--accent-blue);
}
.data-table {
  width: 100%;
  border-collapse: collapse;
}
.data-table th, .data-table td {
  padding: var(--space-sm);
  text-align: left;
  border-bottom: 1px solid var(--border-subtle);
}
.preview-box {
  background: var(--bg-input);
  padding: var(--space-md);
  border-radius: var(--radius-sm);
  max-height: 300px;
  overflow: auto;
  font-size: 0.875rem;
}
</style>
