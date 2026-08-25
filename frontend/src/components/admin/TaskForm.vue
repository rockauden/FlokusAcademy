<script setup>
import { ref, computed, watch } from 'vue'
import { useUnitsStore } from '../../stores/units'

const props = defineProps({
  courses: { type: Array, default: () => [] },
  initialData: { type: Object, default: () => null }
})
const emit = defineEmits(['submit', 'cancel'])

/**
 * Units for the unit picker.
 *
 * Every lesson authored through this form used to arrive with unit_id = NULL,
 * because the form had no field for it. That is not a cosmetic gap:
 * rolling_scheduler.py groups by (student_id, lesson.unit_id), so every
 * unit-less lesson across every subject collapsed into a single group, and the
 * scheduler advances one school day per lesson within a group. Quick-add five
 * tasks, press Recalculate, and they spread across five consecutive school
 * days regardless of subject. The grouping is correct when units are
 * populated; it was silently destructive in the only state the UI could
 * produce.
 */
const unitsStore = useUnitsStore()

// Fetched per program rather than all at once. The picker only ever shows one
// program's units, and the store is shared with the unit manager — narrowing
// the fetch keeps the two screens from overwriting each other's list.
const unitsForCourse = computed(() => {
  if (!form.value.course_id) return []
  return unitsStore.units.filter(u => u.course_id === Number(form.value.course_id))
})

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
  // The API still says module_id; internally it is Lesson.unit_id.
  module_id: '',
  task_type: 'lesson',
  dependency_mode: 'independent',
  // 'core' | 'standard' | 'optional'. How pace changes without curriculum
  // changing — accelerating releases core only and leaves the rest.
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
  // admin view. Clearing the field is still allowed and still means
  // "authored but not scheduled yet"; it just is not the default.
  scheduled_date: todayISO(),
  // Off by default, and deliberately separate from the date above. The date
  // defaults to today for convenience, which is not the same as the teacher
  // saying "this belongs on today" — so the scheduler stays free to move it.
  // Ticking the box is what turns the date into a promise.
  date_locked: false,
  medium: 'online'
})

const error = ref('')

// A unit belongs to exactly one program, so a unit chosen under the old
// program is wrong the moment the program changes. Clearing it is the honest
// outcome — silently keeping it would attach the lesson to another subject's
// unit, and the scheduler would pace it there.
watch(() => form.value.course_id, (next, previous) => {
  if (previous !== undefined && next !== previous) form.value.module_id = ''
  if (next !== '' && next !== null && next !== undefined) unitsStore.fetchUnits(next)
}, { immediate: true })

const selectedUnit = computed(() => {
  if (!form.value.module_id) return null
  return unitsForCourse.value.find(u => u.id === Number(form.value.module_id)) || null
})

// "Staged" here means the unit is not released: planned, completed or
// abandoned. The scheduler already refuses to date lessons in such units —
// but the scheduler is only one of two doors a date can come through. This
// form is the other, and its date field defaults to today.
const stagedUnit = computed(() => selectedUnit.value !== null && selectedUnit.value.status !== 'active')

// Picking an unreleased unit blanks the date. The default-to-today exists so
// a quick add actually reaches the student — but for a lesson going into a
// planned unit, "reaches the student" is precisely the wrong outcome: it
// walks around the unit-status gate and lands in the student's day while the
// unit it belongs to is still invisible. Found in the wild on the first
// pilot run (2026-08-25): Vols 2–3 were planned, the form dated their
// lessons anyway, and the student's day showed them.
//
// Clear, never fill: switching back to an active unit does not restore
// today's date, because the teacher may have blanked it on purpose and a
// watcher that re-fills a field the user emptied is how forms get called
// untrustworthy. And this watcher only runs on a *change* of unit — not on
// mount — so opening an existing lesson for editing never silently strips
// the date it already has.
watch(() => form.value.module_id, (next, previous) => {
  if (next === previous) return
  if (stagedUnit.value) {
    form.value.scheduled_date = ''
    // An undated lesson cannot be pinned — the scheduler skips locked rows
    // and would never place an undated locked one. Same rule submit()
    // applies; clearing it here keeps the checkbox from lying.
    form.value.date_locked = false
  }
})

// Blank inputs come out of the DOM as '', but the API types these as
// Optional[date] / Optional[int] — '' is not a valid empty value for either
// and fails validation with a 422. Leaving the date blank is the normal case
// for a quick add, so this has to be normalised before sending. module_id is
// on the list for the same reason: "no unit" is a legitimate quick-add.
const NULL_WHEN_BLANK = ['scheduled_date', 'school_day_offset', 'day_of_week_hint', 'module_id']

function submit() {
  // course_id is required by the API, and title is only marked required in
  // markup, which does nothing outside a real form submit. Catch both here so
  // the user gets a plain answer instead of a server validation error.
  if (!form.value.title || !String(form.value.title).trim()) {
    error.value = 'Give the task a title.'
    return
  }
  if (form.value.course_id === '' || form.value.course_id === null) {
    error.value = 'Choose a course for this task.'
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
        <label>Course</label>
        <select v-model="form.course_id">
          <option value="">Select Course</option>
          <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.emoji }} {{ c.title }}</option>
        </select>
      </div>

      <div class="form-group">
        <label>Unit</label>
        <select v-model="form.module_id" class="unit-picker" :disabled="!form.course_id">
          <option value="">No unit (quick add)</option>
          <option v-for="u in unitsForCourse" :key="u.id" :value="u.id">{{ u.title }}</option>
        </select>
        <p v-if="form.course_id && unitsForCourse.length === 0" class="text-muted hint">
          This program has no units yet — create them under Programs &amp; Units.
        </p>
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
        <label>Priority</label>
        <select v-model="form.priority">
          <option value="core">Core — always released</option>
          <option value="standard">Standard — normal pace</option>
          <option value="optional">Optional — only if pace allows</option>
        </select>
      </div>

      <div class="form-group">
        <label>Sequence Order</label>
        <input type="number" v-model.number="form.sequence_order" />
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
        <p v-if="stagedUnit && !form.scheduled_date" class="text-muted hint staged-hint">
          This unit is {{ selectedUnit.status }}, so the date was cleared: the
          lesson stays staged — invisible to the student — until you activate
          the unit and recalculate the schedule.
        </p>
        <p v-else-if="stagedUnit && form.scheduled_date" class="form-warning hint staged-warning">
          This unit is {{ selectedUnit.status }}, but a date set here still
          puts the lesson in the student's day. Leave the date blank unless
          that is what you mean.
        </p>
      </div>
    </div>

    <div class="form-group mt-md checkbox">
      <label>
        <input type="checkbox" v-model="form.date_locked" class="pin-date" :disabled="!form.scheduled_date" />
        📌 Pin to this date
      </label>
      <p class="text-muted hint">
        Recalculating the schedule — which also happens when you add a sick day
        or a holiday — moves unpinned work. Pin a date you have promised, like a
        Saturday co-op.
      </p>
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
.form-warning {
  color: var(--color-warning, #d99a2b);
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
