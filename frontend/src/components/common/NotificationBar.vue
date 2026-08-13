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
</script>

<template>
  <div v-if="events.length > 0" class="notification-bar">
    <div class="content">
      <strong>🔔 Upcoming:</strong>
      <span v-for="ev in events" :key="ev.id" class="event-item">
        {{ ev.title }} (In {{ ev.days_until }} days)
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
