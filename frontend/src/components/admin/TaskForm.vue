<script setup>
import { ref } from 'vue'

const props = defineProps({
  courses: { type: Array, default: () => [] },
  initialData: { type: Object, default: () => null }
})
const emit = defineEmits(['submit', 'cancel'])

/**
 * The full editor for one piece of work — the details view behind a week
 * planner card, and the way anything is corrected after it is typed.
 *
 * Most work now enters through the planner, where a cell takes a title and
 * nothing else. This form exists for the rest: attaching a link, fixing the
 * minutes, marking something teacher-led. It lost its unit picker on
 * 2026-08-26 along with the importer and the rolling scheduler — a unit had
 * no meaning left once the year stopped being loaded in advance.
 */

/**
 * Local date as YYYY-MM-DD. Deliberately not toISOString().slice(0, 10),
 * which converts to UTC first and so returns the wrong day for anyone west of
 * Greenwich for part of the evening.
 */
function todayISO() {
  const now = new Date()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${now.getFullYear()}-${month}-${day}`
}

const form = ref(props.initialData || {
  title: '',
  course_id: '',
  task_type: 'lesson',
  dependency_mode: 'independent',
  priority: 'standard',
  sequence_order: 0,
  estimated_minutes: 15,
  resource_url: '',
  workbook_pages: '',
  xp_reward: 10,
  is_boss_fight: false,
  // Defaults to today so a quick-added task actually reaches the student.
  // The student's day selects on `scheduled_date <= today`, and in SQL
  // `NULL <= today` is NULL rather than true — so an undated assignment is
  // silently excluded from their list forever while still showing in every
  // admin view. Clearing the field is still allowed; it just is not the
  // default.
  scheduled_date: todayISO(),
  // Nothing in the app moves a dated assignment any more, so this no longer
  // defends against a scheduler. It is kept because it still records *why* a
  // date is what it is — a deliberate placement rather than a default — and
  // the week planner sets it on everything it creates.
  date_locked: false,
  medium: 'online'
})

const error = ref('')

// Blank inputs come out of the DOM as '', but the API types these as
// Optional[date] / Optional[int] — '' is not a valid empty value for either
// and fails validation with a 422.
const NULL_WHEN_BLANK = ['scheduled_date', 'school_day_offset', 'day_of_week_hint']

function submit() {
  // course_id is required by the API, and title is only marked required in
  // markup, which does nothing outside a real form submit. Catch both here so
  // the user gets a plain answer instead of a server validation error.
  if (!form.value.title || !String(form.value.title).trim()) {
    error.value = 'Give the task a title.'
    return
  }
  if (form.value.course_id === '' || form.value.course_id === null) {
    error.value = 'Choose a class for this task.'
    return
  }

  const payload = { ...form.value }
  for (const key of NULL_WHEN_BLANK) {
    if (payload[key] === '') payload[key] = null
  }

  error.value = ''
  emit('submit', payload)
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
        <label>Class</label>
        <select v-model="form.course_id">
          <option value="">Select Class</option>
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
        <select v-model="form.dependency_mode" class="dependency-mode">
          <option value="independent">Independent</option>
          <!-- Was `with_teacher`, which matched no branch in the scheduler: the
               lesson never got a date, yet still burned a slot in the sequence.
               The schema now rejects anything outside the three canonical
               values, so a drift like that becomes a 422 rather than silence. -->
          <option value="teacher_led">With Teacher (Dad)</option>
          <option value="live_scheduled">Live / Scheduled Session</option>
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

    <p v-if="error" class="form-error">{{ error }}</p>

    <div class="actions mt-lg">
      <button class="btn-primary" @click="submit">Save Task</button>
      <button class="btn-ghost" @click="$emit('cancel')">Cancel</button>
    </div>
  </div>
</template>

<style scoped>
.form-error {
  color: var(--color-danger, #e05252);
  margin-top: var(--space-md);
}
.hint {
  font-size: 0.8125rem;
  margin-top: var(--space-sm);
}

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
