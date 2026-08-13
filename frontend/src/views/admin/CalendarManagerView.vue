<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api/client'

const events = ref([])
const showForm = ref(false)
const form = ref({
  title: '',
  date: '',
  category: '📌 General',
  importance: 'normal',
  reminder_days: 7,
  description: ''
})

const categories = [
  '🎓 School Start / Term', '💰 UFA Milestone', '🛠️ Kit Delivery / Project', 
  '🎥 Live Class (Outschool)', '📌 General', '🏔️ Field Trip', '🏃 Sports / Co-op'
]

async function fetchEvents() {
  events.value = await api.get('/events') || []
}

onMounted(fetchEvents)

async function submitEvent() {
  await api.post('/events', form.value)
  showForm.value = false
  await fetchEvents()
}

async function deleteEvent(id) {
  if (confirm('Delete event?')) {
    await api.delete(`/events/${id}`)
    await fetchEvents()
  }
}
</script>

<template>
  <div class="calendar-manager">
    <header class="page-header mb-lg">
      <h1>Calendar Manager</h1>
      <button class="btn-primary" @click="showForm = true">Add Event</button>
    </header>

    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal-content">
        <h3>New Event</h3>
        <div class="form-group mt-md">
          <label>Title</label>
          <input type="text" v-model="form.title" />
        </div>
        <div class="form-group">
          <label>Date</label>
          <input type="date" v-model="form.date" />
        </div>
        <div class="form-group">
          <label>Category</label>
          <select v-model="form.category">
            <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
          </select>
        </div>
        <div class="form-group">
          <label>Importance</label>
          <select v-model="form.importance">
            <option value="normal">Normal</option>
            <option value="medium">Medium / Important</option>
            <option value="high">High / Urgent</option>
          </select>
        </div>
        <div class="actions mt-md">
          <button class="btn-primary" @click="submitEvent">Save</button>
          <button class="btn-ghost" @click="showForm = false">Cancel</button>
        </div>
      </div>
    </div>

    <div class="events-list">
      <table class="data-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Title</th>
            <th>Category</th>
            <th>Urgency</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ev in events" :key="ev.id">
            <td>{{ new Date(ev.date).toLocaleDateString() }}</td>
            <td>{{ ev.title }}</td>
            <td>{{ ev.category }}</td>
            <td>{{ ev.importance }}</td>
            <td>
              <button class="btn-ghost" @click="deleteEvent(ev.id)">🗑️</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.data-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--bg-card);
  border-radius: var(--radius-md);
  overflow: hidden;
}
.data-table th, .data-table td {
  padding: var(--space-md);
  text-align: left;
  border-bottom: 1px solid var(--border-subtle);
}
</style>
