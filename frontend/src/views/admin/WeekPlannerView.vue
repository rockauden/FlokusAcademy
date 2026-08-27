<script setup>
import { ref, computed, onMounted } from 'vue'
import { useWeekStore } from '../../stores/week'
import { useCoursesStore } from '../../stores/courses'

/**
 * The Sunday screen: classes down the side, days across the top, type in a
 * cell. This replaced the rolling-schedule control and the curriculum
 * importer both — the app no longer places work, so a screen for supervising
 * placement had nothing left to supervise.
 *
 * The design rule throughout: one line of typing per item. A cell takes a
 * title and Enter; minutes, XP and type have defaults, and the card opens for
 * the times they are wrong. Anything that would send the teacher to a second
 * screen on a Sunday evening has failed.
 */
const weekStore = useWeekStore()
const coursesStore = useCoursesStore()

const error = ref('')
// Which cell is currently accepting typing, as `${courseId}:${date}`. Only
// one at a time — this is a form, not a spreadsheet.
const typingIn = ref(null)
const draft = ref('')
const expanded = ref(null)

const DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

/** Local YYYY-MM-DD. Never toISOString(), which converts to UTC first and
 *  hands back yesterday for anyone west of Greenwich after late afternoon —
 *  the bug the old WeeklyGrid shipped with. */
function isoDate(d) {
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${month}-${day}`
}

function parseISO(s) {
  const [y, m, d] = s.split('-').map(Number)
  return new Date(y, m - 1, d)
}

const days = computed(() => {
  const w = weekStore.week
  if (!w) return []
  const start = parseISO(w.week_start)
  // Mon–Fri. Saturday and Sunday are shown only when something is actually
  // on them, so an ordinary week is five columns rather than seven mostly
  // empty ones.
  const count = w.entries.some(e => {
    const wd = parseISO(e.scheduled_date).getDay()
    return wd === 0 || wd === 6
  }) ? 7 : 5

  return Array.from({ length: count }, (_, i) => {
    const d = new Date(start)
    d.setDate(d.getDate() + i)
    const date = isoDate(d)
    const entries = w.entries.filter(e => e.scheduled_date === date)
    const off = w.days_off.find(o => o.date === date)
    return {
      date,
      name: DAY_NAMES[i],
      label: `${d.getMonth() + 1}/${d.getDate()}`,
      entries,
      minutes: entries.reduce((sum, e) => sum + (e.estimated_minutes || 0), 0),
      off,
      overloaded: entries.length > (w.daily_task_cap || 6),
    }
  })
})

const classes = computed(() =>
  [...coursesStore.courses].sort((a, b) => a.sort_order - b.sort_order || a.title.localeCompare(b.title))
)

function entriesFor(courseId, date) {
  if (!weekStore.week) return []
  return weekStore.week.entries.filter(e => e.course_id === courseId && e.scheduled_date === date)
}

async function load(start = null) {
  error.value = ''
  try {
    await Promise.all([
      weekStore.fetchWeek(start),
      coursesStore.courses.length ? Promise.resolve() : coursesStore.fetchCourses(),
    ])
  } catch (e) {
    error.value = e.message
  }
}

function shiftWeek(deltaDays) {
  const d = parseISO(weekStore.week.week_start)
  d.setDate(d.getDate() + deltaDays)
  load(isoDate(d))
}

function startTyping(courseId, date) {
  typingIn.value = `${courseId}:${date}`
  draft.value = ''
}

async function commitDraft(courseId, date, { keepOpen = true } = {}) {
  const title = draft.value.trim()
  draft.value = ''
  if (!title) {
    if (!keepOpen) typingIn.value = null
    return
  }
  error.value = ''
  try {
    await weekStore.addEntry({ course_id: courseId, scheduled_date: date, title })
    await weekStore.fetchWeek(weekStore.week.week_start)
    // Enter keeps the cell open: a class usually gets several days' work in
    // one sitting, and reopening the cell each time is the difference between
    // typing a week and clicking through one.
    if (!keepOpen) typingIn.value = null
  } catch (e) {
    error.value = e.message
  }
}

async function move(entry, date) {
  error.value = ''
  try {
    await weekStore.moveEntry(entry.id, date)
    await weekStore.fetchWeek(weekStore.week.week_start)
  } catch (e) {
    error.value = e.message
  }
  expanded.value = null
}

async function remove(entry) {
  error.value = ''
  try {
    await weekStore.removeEntry(entry.id)
    await weekStore.fetchWeek(weekStore.week.week_start)
  } catch (e) {
    error.value = e.message
  }
  expanded.value = null
}

onMounted(() => load())
</script>

<template>
  <div class="week-planner">
    <header class="page-header">
      <div>
        <h1>Plan the Week</h1>
        <p class="text-muted" v-if="weekStore.week">
          Click a cell and type what Sonny does for that class that day. What you type stays
          where you put it — nothing here reshuffles on its own.
        </p>
      </div>
      <div class="week-nav" v-if="weekStore.week">
        <button class="btn-ghost" @click="shiftWeek(-7)" aria-label="Previous week">←</button>
        <span class="week-label">{{ weekStore.week.week_start }} → {{ weekStore.week.week_end }}</span>
        <button class="btn-ghost" @click="shiftWeek(7)" aria-label="Next week">→</button>
      </div>
    </header>

    <p v-if="error" class="form-error">{{ error }}</p>

    <div
      v-if="weekStore.week && weekStore.week.behind.length"
      class="behind-strip"
      data-testid="behind-strip"
    >
      <strong>{{ weekStore.week.behind.length }} unfinished from before today</strong>
      <div class="behind-items">
        <span v-for="b in weekStore.week.behind.slice(0, 8)" :key="b.id" class="behind-item">
          {{ b.title }}
          <em>{{ b.scheduled_date }}</em>
          <button class="link-btn" @click="move(b, days[0]?.date)" title="Move into this week">
            move up
          </button>
          <button class="link-btn danger" @click="remove(b)" title="Drop it">drop</button>
        </span>
      </div>
    </div>

    <div v-if="weekStore.loading && !weekStore.week" class="text-muted">Loading the week…</div>

    <div v-else-if="weekStore.week" class="grid-scroll">
      <table class="grid" data-testid="week-grid">
        <thead>
          <tr>
            <th class="class-col">Class</th>
            <th
              v-for="day in days"
              :key="day.date"
              :class="{ 'is-off': day.off, 'is-over': day.overloaded }"
            >
              <div class="day-name">{{ day.name }} <span class="day-date">{{ day.label }}</span></div>
              <div class="day-meta">
                <template v-if="day.off">{{ day.off.label }}</template>
                <template v-else-if="day.entries.length">
                  {{ day.entries.length }} · {{ day.minutes }}m
                </template>
                <template v-else>—</template>
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="klass in classes" :key="klass.id">
            <th class="class-col">
              <span class="emoji">{{ klass.emoji }}</span> {{ klass.title }}
            </th>
            <td
              v-for="day in days"
              :key="day.date"
              class="cell"
              :class="{ 'is-off': day.off }"
              @click="typingIn !== `${klass.id}:${day.date}` && startTyping(klass.id, day.date)"
            >
              <div
                v-for="entry in entriesFor(klass.id, day.date)"
                :key="entry.id"
                class="entry"
                :class="{ done: entry.is_completed }"
                @click.stop="expanded = expanded === entry.id ? null : entry.id"
              >
                <span class="entry-title">{{ entry.title }}</span>
                <span class="entry-min">{{ entry.estimated_minutes }}m</span>

                <div v-if="expanded === entry.id" class="entry-actions" @click.stop>
                  <label class="move-label">
                    Move to
                    <select @change="move(entry, $event.target.value)" :value="entry.scheduled_date">
                      <option v-for="d in days" :key="d.date" :value="d.date">
                        {{ d.name }} {{ d.label }}
                      </option>
                    </select>
                  </label>
                  <button class="link-btn danger" @click="remove(entry)">Remove</button>
                </div>
              </div>

              <input
                v-if="typingIn === `${klass.id}:${day.date}`"
                class="cell-input"
                :placeholder="`What's the ${klass.title} work?`"
                v-model="draft"
                autofocus
                @keyup.enter="commitDraft(klass.id, day.date)"
                @keyup.escape="typingIn = null; draft = ''"
                @blur="commitDraft(klass.id, day.date, { keepOpen: false })"
                @click.stop
              />
              <span
                v-else-if="!entriesFor(klass.id, day.date).length"
                class="add-hint"
                aria-hidden="true"
              >+</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <p class="text-muted footnote" v-if="weekStore.week">
      Days off are set on the Calendar screen. Marking one tells you what falls on it — it never
      moves the work for you.
    </p>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-md);
  flex-wrap: wrap;
  margin-bottom: var(--space-lg);
}
.page-header p { max-width: 62ch; margin: var(--space-sm) 0 0; }
.week-nav { display: flex; align-items: center; gap: var(--space-sm); }
.week-label { font-variant-numeric: tabular-nums; color: var(--text-secondary); font-size: 0.875rem; }

.form-error { color: var(--color-danger, #e05252); }

.behind-strip {
  background: rgba(217, 154, 43, 0.1);
  border: 1px solid rgba(217, 154, 43, 0.35);
  border-radius: var(--radius-md, 8px);
  padding: var(--space-md);
  margin-bottom: var(--space-md);
}
.behind-items { display: flex; flex-wrap: wrap; gap: var(--space-sm); margin-top: var(--space-sm); }
.behind-item {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 999px;
  padding: 3px 10px;
  font-size: 0.8125rem;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.behind-item em { color: var(--text-secondary); font-style: normal; font-variant-numeric: tabular-nums; }

.grid-scroll { overflow-x: auto; }
table.grid { border-collapse: collapse; width: 100%; min-width: 720px; }
.grid th, .grid td {
  border: 1px solid var(--border-subtle, rgba(255,255,255,0.08));
  vertical-align: top;
  padding: 6px;
}
.grid thead th { background: rgba(0,0,0,0.2); text-align: left; padding: 8px; }
.day-name { font-weight: 600; }
.day-date { color: var(--text-secondary); font-weight: 400; font-size: 0.8125rem; }
.day-meta { font-size: 0.75rem; color: var(--text-secondary); font-variant-numeric: tabular-nums; }
thead th.is-off { background: rgba(255,255,255,0.03); color: var(--text-secondary); }
thead th.is-over .day-meta { color: #d99a2b; font-weight: 600; }

.class-col { min-width: 150px; white-space: nowrap; background: rgba(0,0,0,0.12); }
tbody th.class-col { text-align: left; font-weight: 500; }

.cell { min-width: 130px; height: 62px; cursor: text; position: relative; }
.cell.is-off { background: rgba(255,255,255,0.02); }
.cell:hover .add-hint { opacity: 0.5; }
.add-hint { color: var(--text-secondary); opacity: 0; transition: opacity 0.12s; }

.entry {
  background: var(--bg-input, rgba(255,255,255,0.06));
  border-radius: 6px;
  padding: 4px 6px;
  margin-bottom: 4px;
  font-size: 0.8125rem;
  cursor: pointer;
  display: flex;
  gap: 6px;
  align-items: baseline;
  justify-content: space-between;
}
.entry.done { opacity: 0.55; text-decoration: line-through; }
.entry-title { overflow-wrap: anywhere; }
.entry-min { color: var(--text-secondary); font-size: 0.75rem; font-variant-numeric: tabular-nums; }
.entry-actions {
  position: absolute;
  z-index: 5;
  left: 6px;
  right: 6px;
  bottom: 4px;
  background: var(--bg-card);
  border: 1px solid var(--border-default, rgba(255,255,255,0.14));
  border-radius: 6px;
  padding: 6px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  cursor: default;
}
.move-label { font-size: 0.75rem; color: var(--text-secondary); display: flex; gap: 4px; align-items: center; }
.move-label select { flex: 1; }

.cell-input {
  width: 100%;
  font-size: 0.8125rem;
  padding: 4px 6px;
}
.link-btn {
  background: none;
  border: none;
  color: var(--color-primary, #63b3ed);
  cursor: pointer;
  font-size: 0.75rem;
  padding: 0;
}
.link-btn.danger { color: var(--color-danger, #e05252); }
.footnote { margin-top: var(--space-md); font-size: 0.8125rem; }
</style>
