<script setup>
import { ref } from 'vue'
import FocusTimer from './FocusTimer.vue'

const props = defineProps({
  task: { type: Object, required: true }
})

const emit = defineEmits(['complete'])
const expanded = ref(false)
const notes = ref('')

function handleComplete(minutes) {
  emit('complete', { id: props.task.id, notes: notes.value, minutes })
  expanded.value = false
}
</script>

<template>
  <div class="task-card" :class="{ 'boss': task.is_boss_fight, 'completed': task.is_completed }">
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
        <button class="btn-success mt-md" style="width: 100%" @click="handleComplete(task.estimated_minutes)">
          Mark Complete (+{{ task.xp_reward }} XP)
        </button>
      </div>
    </div>

    <div v-if="task.is_completed" class="completed-badge">
      ✓ Done (+{{ task.xp_reward }} XP)
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
</style>
