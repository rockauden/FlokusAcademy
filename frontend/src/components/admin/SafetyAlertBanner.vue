<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api/client'

/**
 * Unacknowledged safety alerts from Ask Floki, shown above every admin screen.
 *
 * Deliberately not dismissible in one click from here: acknowledging is an
 * explicit "I have seen this and spoken to him" action, so the button says so.
 * There is no push or email channel in this deployment, which means this
 * banner is the only way a parent finds out -- so it sits on every page rather
 * than on a dashboard they might not open.
 */
const events = ref([])
const loading = ref(true)

const LABELS = {
  self_harm: 'Something serious',
  abuse: 'Something serious',
  distress: 'Feeling low',
}

async function load() {
  try {
    const data = await api.get('/students/safety-events?unacknowledged_only=true')
    events.value = Array.isArray(data) ? data : []
  } catch {
    // A failure here must never take the admin UI down with it.
    events.value = []
  } finally {
    loading.value = false
  }
}

async function acknowledge(id) {
  try {
    await api.post(`/students/safety-events/${id}/acknowledge`, {})
    events.value = events.value.filter((e) => e.id !== id)
  } catch {
    await load()
  }
}

function when(value) {
  if (!value) return ''
  return new Date(value).toLocaleString(undefined, {
    weekday: 'short', hour: 'numeric', minute: '2-digit',
  })
}

onMounted(load)
</script>

<template>
  <div v-if="!loading && events.length" class="safety-banner">
    <div v-for="event in events" :key="event.id" class="alert">
      <div class="body">
        <strong>{{ LABELS[event.category] || 'Needs your attention' }}</strong>
        <span class="meta">Sonny said this to Floki - {{ when(event.created_at) }}</span>
        <blockquote>{{ event.excerpt }}</blockquote>
        <p class="advice">Floki did not reply to this beyond pointing him to you. Please check in with him.</p>
      </div>
      <button class="ack" @click="acknowledge(event.id)">I've spoken to him</button>
    </div>
  </div>
</template>

<style scoped>
.safety-banner {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}

.alert {
  display: flex;
  gap: var(--space-md);
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  background: var(--bg-card);
  border: 1px solid var(--accent-red, #e05252);
  border-left: 4px solid var(--accent-red, #e05252);
  border-radius: var(--radius-sm);
  padding: var(--space-md);
}

.body { display: flex; flex-direction: column; gap: 0.25rem; min-width: 16rem; flex: 1; }
.meta { color: var(--text-secondary); font-size: 0.8125rem; }

blockquote {
  margin: 0.35rem 0 0;
  padding-left: var(--space-sm);
  border-left: 2px solid var(--border-default);
  color: var(--text-primary);
}

.advice { margin: 0.35rem 0 0; color: var(--text-secondary); font-size: 0.875rem; }

.ack {
  background: transparent;
  border: 1px solid var(--border-default);
  color: var(--text-secondary);
  border-radius: var(--radius-sm);
  padding: 0.4rem 0.75rem;
  cursor: pointer;
  white-space: nowrap;
}
.ack:hover { color: var(--text-primary); border-color: var(--text-secondary); }
</style>
