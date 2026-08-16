<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api/client'

/**
 * Times Floki judged Sonny to be stuck and asked for a hand.
 *
 * Styled deliberately unlike SafetyAlertBanner. That one is bordered in red
 * because everything in it is serious; this is ordinary school news -- someone
 * found long division hard on a Tuesday. If the two looked alike, the red one
 * would stop meaning anything, which is the only way the safety layer fails
 * quietly.
 */
const flags = ref([])
const loading = ref(true)

async function load() {
  try {
    const data = await api.get('/students/stuck-flags?unresolved_only=true')
    flags.value = Array.isArray(data) ? data : []
  } catch {
    // Never take the admin UI down over a nice-to-have strip.
    flags.value = []
  } finally {
    loading.value = false
  }
}

async function resolve(id) {
  try {
    await api.post(`/students/stuck-flags/${id}/resolve`, {})
    flags.value = flags.value.filter((f) => f.id !== id)
  } catch {
    await load()
  }
}

function when(value) {
  if (!value) return ''
  const then = new Date(value)
  const minutes = Math.round((Date.now() - then.getTime()) / 60000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes} min ago`
  return then.toLocaleString(undefined, { weekday: 'short', hour: 'numeric', minute: '2-digit' })
}

onMounted(load)
</script>

<template>
  <div v-if="!loading && flags.length" class="stuck-strip">
    <div v-for="flag in flags" :key="flag.id" class="stuck">
      <span class="mark" aria-hidden="true">🙋</span>
      <span class="text">
        Sonny got stuck on <strong>{{ flag.topic }}</strong>
        <span class="when">{{ when(flag.created_at) }}</span>
      </span>
      <button class="done" @click="resolve(flag.id)">Helped</button>
    </div>
  </div>
</template>

<style scoped>
.stuck-strip {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs, 0.4rem);
  margin-bottom: var(--space-md);
}

.stuck {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-left: 3px solid var(--accent-blue, #60a5fa);
  border-radius: var(--radius-sm);
  padding: 0.6rem 0.85rem;
  font-size: 0.9rem;
}

.mark { font-size: 1.05rem; }
.text { flex: 1; color: var(--text-primary); }
.when { color: var(--text-secondary); margin-left: 0.5rem; font-size: 0.8125rem; }

.done {
  background: transparent;
  border: 1px solid var(--border-default);
  color: var(--text-secondary);
  border-radius: var(--radius-sm);
  padding: 0.3rem 0.7rem;
  cursor: pointer;
  white-space: nowrap;
}
.done:hover { color: var(--text-primary); border-color: var(--text-secondary); }
</style>
