<script setup>
import { ref, onMounted, computed } from 'vue'
import { api } from '../../api/client'
import EventCard from '../../components/common/EventCard.vue'

const events = ref([])
const nextMajor = ref(null)

onMounted(async () => {
  events.value = await api.get('/events') || []
  nextMajor.value = await api.get('/events/next-major') || null
})

const sortedEvents = computed(() => {
  return [...events.value].sort((a, b) => new Date(a.date) - new Date(b.date))
})
</script>

<template>
  <div class="calendar-view">
    <header class="hero mb-lg">
      <h1>School Calendar 📅</h1>
    </header>

    <div v-if="nextMajor" class="major-event-hero mb-lg">
      <div class="countdown-block">
        <span class="days">{{ nextMajor.days_until }}</span>
        <span class="label">Days Until</span>
      </div>
      <div class="event-info">
        <h2>{{ nextMajor.title }}</h2>
        <p>{{ new Date(nextMajor.date).toLocaleDateString() }}</p>
      </div>
    </div>

    <div class="events-list">
      <h3>Upcoming Events</h3>
      <div v-if="sortedEvents.length === 0" class="text-muted mt-md">No events scheduled.</div>
      <EventCard v-for="ev in sortedEvents" :key="ev.id" :event="ev" />
    </div>
  </div>
</template>

<style scoped>
.major-event-hero {
  background: linear-gradient(135deg, var(--bg-card), var(--accent-purple));
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
  display: flex;
  align-items: center;
  gap: var(--space-lg);
  box-shadow: var(--shadow-glow-purple);
}
.countdown-block {
  background: rgba(0,0,0,0.3);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  text-align: center;
}
.countdown-block .days {
  display: block;
  font-size: 3rem;
  font-weight: 800;
  color: #fff;
  line-height: 1;
}
.countdown-block .label {
  font-size: 0.875rem;
  color: rgba(255,255,255,0.8);
  text-transform: uppercase;
}
.event-info h2 {
  color: #fff;
  margin: 0 0 var(--space-xs);
}
.event-info p {
  color: rgba(255,255,255,0.9);
  margin: 0;
}
</style>
