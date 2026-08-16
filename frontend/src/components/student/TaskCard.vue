<script setup>
import { computed, onUnmounted, ref } from 'vue'
import FocusTimer from './FocusTimer.vue'
import { taskXp } from '../../utils/xp'

const props = defineProps({
  task: { type: Object, required: true }
})

const emit = defineEmits(['complete'])
const expanded = ref(false)
const notes = ref('')

// Acknowledges the tap immediately, rather than leaving the card inert until
// the request returns and the list happens to re-render. On a slow tablet
// connection that gap is long enough to make a child tap again.
const settling = ref(false)

// What the ledger will actually award — doubled for boss fights.
const xpValue = computed(() => taskXp(props.task))

let recovery = null

function handleComplete(minutes) {
  if (settling.value) return   // A second tap must not award twice.

  settling.value = true
  // Deliberately stays expanded. Collapsing here unmounts the button along
  // with the rest of the body, so the acknowledgement would never be seen --
  // the card would just go quiet. It is about to leave the list anyway.
  emit('complete', { id: props.task.id, notes: notes.value, minutes })

  // If the card is still mounted a few seconds later, the completion did not
  // land. The failure itself surfaces as a toast; this is what stops the card
  // sitting permanently disabled with no way to try again.
  clearTimeout(recovery)
  recovery = setTimeout(() => { settling.value = false }, 6000)
}

onUnmounted(() => clearTimeout(recovery))
</script>

<template>
  <div
    class="task-card"
    :class="{ 'boss': task.is_boss_fight, 'completed': task.is_completed, 'settling': settling }"
  >
    <div class="task-header" @click="!task.is_completed && (expanded = !expanded)">
      <div class="title-section">
        <span class="emoji">{{ task.course?.emoji || '📝' }}</span>
        <h4>{{ task.title }}</h4>
        <span v-if="task.is_boss_fight" class="boss-badge">👑 Boss Fight</span>
      </div>
      <div class="meta-section">
        <span class="badge badge-blue">{{ task.estimated_minutes }}m</span>
        <span class="badge" :class="task.medium === 'offline' ? 'badge-orange' : 'badge-purple'">
          {{ task.medium === 'offline' ? '📖' : '💻' }}
        </span>
        <span v-if="task.dependency_mode === 'with_teacher'" class="badge badge-orange">Wait for Dad</span>
      </div>
    </div>
    
    <div v-if="expanded && !task.is_completed" class="task-body">
      <div v-if="task.workbook_pages" class="resource-info mb-md">
        Pages: {{ task.workbook_pages }}
      </div>
      <div v-if="task.resource_url" class="resource-info mb-md">
        <a :href="task.resource_url" target="_blank" class="btn-ghost" style="display:inline-block; text-decoration:none;">Open Lesson</a>
      </div>
      
      <div class="completion-area">
        <FocusTimer :task-id="task.id" :default-minutes="task.estimated_minutes" @complete="handleComplete" />
        <div class="form-group mt-md">
          <label>Notes (optional)</label>
          <textarea v-model="notes" rows="2" placeholder="What did you learn?"></textarea>
        </div>
        <button
          class="btn-success mt-md"
          style="width: 100%"
          :disabled="settling"
          @click="handleComplete(task.estimated_minutes)"
        >
          {{ settling ? 'Nice work!' : `Mark Complete (+${xpValue} XP)` }}
        </button>
      </div>
    </div>

    <div v-if="task.is_completed" class="completed-badge">
      ✓ Done (+{{ xpValue }} XP)
    </div>
  </div>
</template>

<style scoped>
.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
}
.title-section {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}
.emoji { font-size: 1.25rem; }
.title-section h4 { margin: 0; color: var(--text-primary); }
.meta-section {
  display: flex;
  gap: var(--space-xs);
}
.boss-badge {
  background: var(--accent-purple);
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: bold;
}
.task-body {
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: 1px solid var(--border-subtle);
  animation: fadeIn var(--transition-default);
}
.completed-badge {
  margin-top: var(--space-sm);
  color: var(--accent-green);
  font-weight: 600;
  font-size: 0.875rem;
}

/* The settle: a single confirming pulse, not a bounce. The card is about to
   leave the list, so this reads as "received" rather than as an effect. */
.task-card.settling {
  border-color: var(--accent-green);
  box-shadow: 0 0 0 1px var(--accent-green), 0 0 22px rgb(34 197 94 / 22%);
}

@media (prefers-reduced-motion: no-preference) {
  .task-card.settling {
    animation: settle 420ms ease-out;
  }

  @keyframes settle {
    0%   { transform: scale(1); }
    35%  { transform: scale(1.015); }
    100% { transform: scale(1); }
  }
}
</style>
