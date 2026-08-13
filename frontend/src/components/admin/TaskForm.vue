<script setup>
import { ref } from 'vue'

const props = defineProps({
  courses: { type: Array, default: () => [] },
  initialData: { type: Object, default: () => null }
})
const emit = defineEmits(['submit', 'cancel'])

const form = ref(props.initialData || {
  title: '',
  course_id: '',
  task_type: 'lesson',
  dependency_mode: 'independent',
  estimated_minutes: 15,
  resource_url: '',
  workbook_pages: '',
  xp_reward: 10,
  is_boss_fight: false,
  scheduled_date: '',
  medium: 'online'
})

function submit() {
  emit('submit', form.value)
}
</script>

<template>
  <div class="task-form">
    <div class="form-grid">
      <div class="form-group">
        <label>Title *</label>
        <input type="text" v-model="form.title" required />
      </div>
      <div class="form-group">
        <label>Course</label>
        <select v-model="form.course_id">
          <option value="">Select Course</option>
          <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.emoji }} {{ c.title }}</option>
        </select>
      </div>
      
      <div class="form-group">
        <label>Task Type</label>
        <select v-model="form.task_type">
          <option value="lesson">Lesson</option>
          <option value="quiz">Quiz</option>
          <option value="project">Project</option>
        </select>
      </div>
      
      <div class="form-group">
        <label>Dependency</label>
        <select v-model="form.dependency_mode">
          <option value="independent">Independent</option>
          <option value="with_teacher">With Teacher (Dad)</option>
        </select>
      </div>

      <div class="form-group">
        <label>Estimated Minutes</label>
        <input type="number" v-model="form.estimated_minutes" />
      </div>
      
      <div class="form-group">
        <label>XP Reward</label>
        <input type="number" v-model="form.xp_reward" />
      </div>
      
      <div class="form-group">
        <label>Resource URL</label>
        <input type="url" v-model="form.resource_url" />
      </div>
      
      <div class="form-group">
        <label>Workbook Pages</label>
        <input type="text" v-model="form.workbook_pages" />
      </div>

      <div class="form-group">
        <label>Medium</label>
        <select v-model="form.medium">
          <option value="online">Online 💻</option>
          <option value="offline">Offline 📖</option>
        </select>
      </div>

      <div class="form-group">
        <label>Scheduled Date</label>
        <input type="date" v-model="form.scheduled_date" />
      </div>
    </div>

    <div class="form-group mt-md checkbox">
      <label>
        <input type="checkbox" v-model="form.is_boss_fight" />
        👑 Is Boss Fight?
      </label>
    </div>

    <div class="actions mt-lg">
      <button class="btn-primary" @click="submit">Save Task</button>
      <button class="btn-ghost" @click="$emit('cancel')">Cancel</button>
    </div>
  </div>
</template>

<style scoped>
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-md);
}
@media (max-width: 600px) {
  .form-grid { grid-template-columns: 1fr; }
}
.checkbox label {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  color: var(--text-primary);
  font-weight: 600;
  cursor: pointer;
}
.actions {
  display: flex;
  gap: var(--space-sm);
}
</style>
