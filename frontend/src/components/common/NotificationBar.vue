<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api/client'

const events = ref([])

onMounted(async () => {
  try {
    const data = await api.get('/events/upcoming')
    if (data) events.value = data
  } catch (e) {
    console.error(e)
  }
})

/**
 * The API returns event_date; it has never returned a days_until field, so the
 * template rendered a blank and the bar read "First Day of School (In  days)".
 * Counting whole days locally also avoids a timezone shift: both sides are
 * pinned to local midnight before subtracting.
 */
function countdown(eventDate) {
  if (!eventDate) return ''

  const [year, month, day] = String(eventDate).slice(0, 10).split('-').map(Number)
  if (!year || !month || !day) return ''

  const target = new Date(year, month - 1, day)
  const today = new Date()
  const midnight = new Date(today.getFullYear(), today.getMonth(), today.getDate())

  const days = Math.round((target - midnight) / 86400000)

  if (days < 0) return 'past'
  if (days === 0) return 'today'
  if (days === 1) return 'tomorrow'
  return `in ${days} days`
}
</script>

<template>
  <div v-if="events.length > 0" class="notification-bar">
    <div class="content">
      <strong>🔔 Upcoming:</strong>
      <span v-for="ev in events" :key="ev.id" class="event-item">
        {{ ev.title }} ({{ countdown(ev.event_date) }})
      </span>
    </div>
  </div>
</template>

<style scoped>
.notification-bar {
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-default);
  padding: var(--space-sm) var(--space-lg);
  border-left: 4px solid var(--accent-orange);
  margin-bottom: var(--space-md);
  border-radius: var(--radius-sm);
}
.content {
  display: flex;
  gap: var(--space-md);
  align-items: center;
  overflow-x: auto;
  white-space: nowrap;
}
.event-item {
  color: var(--text-secondary);
  font-size: 0.875rem;
}
</style>
