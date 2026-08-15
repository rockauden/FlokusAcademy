<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api/client'

const selectedDate = ref(new Date().toISOString().split('T')[0])
const completedTasks = ref([])

async function fetchPortfolio() {
  // Use filter endpoint. Trailing slash avoids the 307 on /api/tasks/.
  const data = await api.get(`/tasks/?is_completed=true&scheduled_date=${selectedDate.value}`)
  completedTasks.value = data || []
}

onMounted(fetchPortfolio)
</script>

<template>
  <div class="portfolio-view">
    <header class="page-header mb-lg">
      <h1>Compliance Portfolio</h1>
      <div class="actions">
        <input type="date" v-model="selectedDate" @change="fetchPortfolio" />
        <button class="btn-ghost">Export CSV</button>
      </div>
    </header>

    <div class="portfolio-content">
      <div v-if="completedTasks.length === 0" class="text-muted">
        No completed tasks found for {{ selectedDate }}.
      </div>
      <div v-for="task in completedTasks" :key="task.id" class="portfolio-item">
        <h4>{{ task.title }} ({{ task.course?.title }})</h4>
        <div class="meta text-muted">Completed on: {{ new Date(task.completed_at).toLocaleString() }} | Focus: {{ task.focus_minutes }}m</div>
        <div v-if="task.completion_notes" class="notes mt-sm">
          <strong>Notes:</strong> {{ task.completion_notes }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.actions {
  display: flex;
  gap: var(--space-sm);
}
.portfolio-item {
  background: var(--bg-card);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  border-left: 4px solid var(--accent-green);
  margin-bottom: var(--space-md);
}
.notes {
  background: var(--bg-input);
  padding: var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
}
</style>
