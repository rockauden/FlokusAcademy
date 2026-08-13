<script setup>
import { computed } from 'vue'

const props = defineProps({
  event: { type: Object, required: true }
})

const urgencyClass = computed(() => {
  const imp = props.event.importance || 'normal'
  if (imp === 'high') return 'urgent'
  if (imp === 'medium') return 'important'
  return 'normal'
})

const formattedDate = computed(() => {
  return new Date(props.event.date).toLocaleDateString(undefined, {
    weekday: 'short', month: 'short', day: 'numeric'
  })
})
</script>

<template>
  <div class="event-card" :class="urgencyClass">
    <div class="event-header">
      <h4>{{ event.title }}</h4>
      <span class="date">{{ formattedDate }}</span>
    </div>
    <div v-if="event.description" class="description">
      {{ event.description }}
    </div>
    <div class="footer">
      <span class="category">{{ event.category }}</span>
      <span v-if="event.days_until !== undefined" class="countdown">
        In {{ event.days_until }} days
      </span>
    </div>
  </div>
</template>

<style scoped>
.event-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-xs);
}
.event-header h4 {
  color: var(--text-primary);
  margin: 0;
}
.date {
  font-size: 0.875rem;
  color: var(--text-secondary);
}
.description {
  color: var(--text-muted);
  font-size: 0.875rem;
  margin-bottom: var(--space-sm);
}
.footer {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: var(--text-muted);
}
.countdown {
  font-weight: 600;
  color: var(--accent-orange);
}
</style>
