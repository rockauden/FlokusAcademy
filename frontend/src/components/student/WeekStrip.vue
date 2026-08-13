<script setup>
import { computed } from 'vue'

const props = defineProps({
  weekDates: { type: Array, default: () => [] }, // array of date strings for Mon-Thu
  taskCounts: { type: Object, default: () => ({}) } // { 'YYYY-MM-DD': { total, completed } }
})

const days = ['Mon', 'Tue', 'Wed', 'Thu']
const todayStr = new Date().toISOString().split('T')[0]

const mappedDays = computed(() => {
  return days.map((name, i) => {
    const dStr = props.weekDates[i]
    const counts = props.taskCounts[dStr] || { total: 0, completed: 0 }
    return {
      name,
      dateStr: dStr,
      isToday: dStr === todayStr,
      total: counts.total,
      completed: counts.completed,
      status: counts.total === 0 ? 'empty' : (counts.completed >= counts.total ? 'done' : 'partial')
    }
  })
})
</script>

<template>
  <div class="week-strip">
    <div 
      v-for="day in mappedDays" 
      :key="day.name" 
      class="day-cell"
      :class="{ 'is-today': day.isToday, 'is-done': day.status === 'done' }"
    >
      <div class="day-name">{{ day.name }}</div>
      <div class="indicator">
        <span v-if="day.status === 'empty'">—</span>
        <span v-else-if="day.status === 'done'">✓</span>
        <span v-else>{{ day.completed }}/{{ day.total }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.week-strip {
  display: flex;
  gap: var(--space-sm);
  background: var(--bg-card);
  padding: var(--space-sm);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
}
.day-cell {
  flex: 1;
  text-align: center;
  padding: var(--space-sm);
  border-radius: var(--radius-sm);
  background: var(--bg-input);
  transition: all var(--transition-fast);
}
.day-cell.is-today {
  border: 1px solid var(--accent-blue);
  box-shadow: var(--shadow-glow-blue);
}
.day-cell.is-done {
  background: rgba(34, 197, 94, 0.1);
  color: var(--accent-green);
}
.day-name {
  font-size: 0.75rem;
  text-transform: uppercase;
  color: var(--text-muted);
  font-weight: bold;
  margin-bottom: 4px;
}
.indicator {
  font-weight: 600;
}
</style>
