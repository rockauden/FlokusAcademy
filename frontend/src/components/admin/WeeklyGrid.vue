<script setup>
import { computed } from 'vue'

const props = defineProps({
  tasks: { type: Array, default: () => [] },
  startDate: { type: String, required: true } // Monday date
})

const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday']

const grid = computed(() => {
  const start = new Date(props.startDate)
  return days.map((dayName, idx) => {
    const d = new Date(start)
    d.setDate(d.getDate() + idx)
    const dateStr = d.toISOString().split('T')[0]
    
    return {
      name: dayName,
      date: dateStr,
      tasks: props.tasks.filter(t => t.scheduled_date === dateStr)
    }
  })
})
</script>

<template>
  <div class="weekly-grid">
    <div v-for="day in grid" :key="day.date" class="grid-column">
      <div class="col-header">
        <h4>{{ day.name }}</h4>
        <span class="text-muted">{{ day.date }}</span>
      </div>
      <div class="col-body">
        <div v-for="task in day.tasks" :key="task.id" class="grid-task">
          <span class="emoji">{{ task.course?.emoji }}</span>
          <span class="title">{{ task.title }}</span>
          <span class="time">{{ task.estimated_minutes }}m</span>
        </div>
        <div v-if="day.tasks.length === 0" class="empty-state">
          No tasks
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.weekly-grid {
  display: flex;
  gap: var(--space-md);
  overflow-x: auto;
  padding-bottom: var(--space-sm);
}
.grid-column {
  flex: 1;
  min-width: 200px;
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
}
.col-header {
  padding: var(--space-md);
  border-bottom: 1px solid var(--border-subtle);
  background: rgba(0,0,0,0.2);
}
.col-header h4 { margin: 0 0 4px; }
.col-header span { font-size: 0.75rem; }

.col-body {
  padding: var(--space-sm);
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}
.grid-task {
  background: var(--bg-input);
  padding: var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}
.grid-task .title { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.grid-task .time { color: var(--accent-blue); font-weight: 600; font-size: 0.75rem; }
.empty-state {
  text-align: center;
  padding: var(--space-md);
  color: var(--text-muted);
  font-size: 0.875rem;
  font-style: italic;
}
</style>
