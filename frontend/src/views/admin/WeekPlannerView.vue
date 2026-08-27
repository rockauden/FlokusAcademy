<script setup>
import { ref, computed, onMounted } from 'vue'
import { useWeekStore } from '../../stores/week'
import { useCoursesStore } from '../../stores/courses'
import { useScheduleStore } from '../../stores/schedule'

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
const scheduleStore = useScheduleStore()

const error = ref('')
const notice = ref('')
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

// Deactivated classes are fetched too but shown only on request: a class you
// stopped teaching should be out of the way, not gone — its completed work
// still has to count toward the UFA record, and un-hiding has to be possible
// without a screen of its own, because there is no longer a screen of its own.
const sortClasses = list =>
  [...list].sort((a, b) => a.sort_order - b.sort_order || a.title.localeCompare(b.title))

const classes = computed(() => sortClasses(coursesStore.courses.filter(c => c.is_active)))
const hiddenClasses = computed(() => sortClasses(coursesStore.courses.filter(c => !c.is_active)))

const showHidden = ref(false)
const addingClass = ref(false)
const newClass = ref({ emoji: '📘', title: '' })

async function addClass() {
  const title = newClass.value.title.trim()
  if (!title) { addingClass.value = false; return }
  error.value = ''
  try {
    // subject_area and platform are required by the API and are not worth a
    // question here — a household knows its classes by one name. Both default
    // to the title and stay editable through the API if that ever matters.
    await coursesStore.createCourse({
      title,
      subject_area: title,
      platform: title,
      emoji: newClass.value.emoji || '📘',
      sort_order: coursesStore.courses.length,
    })
    newClass.value = { emoji: '📘', title: '' }
    addingClass.value = false
    await coursesStore.fetchCourses({ includeInactive: true })
  } catch (e) {
    error.value = e.message
  }
}

const editingClass = ref(null)
const classDraft = ref({ emoji: '', title: '' })

function startRenameClass(klass) {
  editingClass.value = klass.id
  classDraft.value = { emoji: klass.emoji, title: klass.title }
}

async function saveClassName(klass) {
  const title = classDraft.value.title.trim()
  editingClass.value = null
  if (!title || (title === klass.title && classDraft.value.emoji === klass.emoji)) return
  error.value = ''
  try {
    // subject_area and platform follow the title *only* when they were derived
    // from it — which is what happens for a class added here, where one name is
    // all a household has for it. The seeded classes are different: "Tuttle
    // Twins" has subject_area "Social Studies", and renaming the class to
    // "American History" should not overwrite the subject the analytics group
    // by. Matching on the old title is what tells the two cases apart.
    const derived = field => (klass[field] === klass.title ? title : klass[field])
    await coursesStore.updateCourse(klass.id, {
      ...klass,
      title,
      emoji: classDraft.value.emoji || klass.emoji,
      subject_area: derived('subject_area'),
      platform: derived('platform'),
    })
    await coursesStore.fetchCourses({ includeInactive: true })
  } catch (e) {
    error.value = e.message
  }
}

async function hideClass(klass) {
  error.value = ''
  try {
    await coursesStore.deactivateCourse(klass.id)
    await coursesStore.fetchCourses({ includeInactive: true })
    notice.value = `${klass.title} hidden. Its finished work still counts.`
  } catch (e) {
    error.value = e.message
  }
}

async function restoreClass(klass) {
  error.value = ''
  try {
    await coursesStore.updateCourse(klass.id, { ...klass, is_active: true })
    await coursesStore.fetchCourses({ includeInactive: true })
  } catch (e) {
    error.value = e.message
  }
}

function entriesFor(courseId, date) {
  if (!weekStore.week) return []
  return weekStore.week.entries.filter(e => e.course_id === courseId && e.scheduled_date === date)
}

async function load(start = null) {
  error.value = ''
  // Notices are about the week on screen. Carrying "8 items still sit on Thu"
  // into a different week is worse than saying nothing.
  notice.value = ''
  try {
    await Promise.all([
      weekStore.fetchWeek(start),
      coursesStore.fetchCourses({ includeInactive: true }),
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

/**
 * Days off, marked from the day they belong to.
 *
 * They used to live on the schedule screen, which was deleted with the
 * scheduler — and the calendar screen is a different thing entirely (school
 * events, a separate table), so for a while there was no way to mark or clear
 * one at all. Here is where the teacher actually learns about a day off:
 * looking at the week.
 *
 * Since nothing reschedules any more, a day off is a marker rather than a
 * mechanism. It greys the column and says why, and the work sitting on it
 * stays exactly where it is for the teacher to move or leave.
 */
const dayMenu = ref(null)
const dayLabel = ref('')

function openDayMenu(day) {
  dayMenu.value = dayMenu.value === day.date ? null : day.date
  dayLabel.value = ''
}

async function markDayOff(day, kind) {
  error.value = ''
  try {
    const label = dayLabel.value.trim()
    const result = kind === 'sick'
      ? await scheduleStore.addSickDay(day.date)
      : await scheduleStore.addHoliday(day.date, label || 'Day off')
    await load(weekStore.week.week_start)
    notice.value = result.affected && result.affected.length
      ? `${result.affected.length} item(s) still sit on ${day.name}. Move them if you want them elsewhere.`
      : ''
  } catch (e) {
    error.value = e.message
  }
  dayMenu.value = null
}

async function clearDayOff(day) {
  error.value = ''
  try {
    await scheduleStore.removeNonSchoolDay(day.off.id)
    await load(weekStore.week.week_start)
    notice.value = ''
  } catch (e) {
    error.value = e.message
  }
  dayMenu.value = null
}

// The details behind a card. This is what the task manager used to be for;
// folding it in here is what let that page go. Only the fields a week's
// planning actually touches — the rest keep their defaults.
const editDraft = ref(null)

function openEditor(entry) {
  expanded.value = entry.id
  editDraft.value = {
    title: entry.title,
    estimated_minutes: entry.estimated_minutes,
    xp_reward: entry.xp_reward,
    task_type: entry.task_type,
    dependency_mode: entry.dependency_mode,
    resource_url: entry.resource_url || '',
    description: entry.description || '',
  }
}

async function saveEdit(entry) {
  error.value = ''
  try {
    // A partial PUT: exclude_unset on the API means the fields not sent keep
    // their values, so this cannot quietly reset anything it does not show.
    await weekStore.updateEntry(entry.id, editDraft.value)
    await weekStore.fetchWeek(weekStore.week.week_start)
    expanded.value = null
    editDraft.value = null
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
  editDraft.value = null
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
              <button class="day-head" @click="openDayMenu(day)" :aria-expanded="dayMenu === day.date">
                <span class="day-name">{{ day.name }} <span class="day-date">{{ day.label }}</span></span>
                <span class="day-meta">
                  <template v-if="day.off">{{ day.off.label }}</template>
                  <template v-else-if="day.entries.length">
                    {{ day.entries.length }} · {{ day.minutes }}m
                  </template>
                  <template v-else>—</template>
                </span>
              </button>

              <div v-if="dayMenu === day.date" class="day-menu" @click.stop>
                <template v-if="day.off">
                  <p class="day-menu-note">{{ day.name }} is marked “{{ day.off.label }}”.</p>
                  <button class="link-btn" data-testid="clear-day-off" @click="clearDayOff(day)">
                    Back to a school day
                  </button>
                </template>
                <template v-else>
                  <input
                    v-model="dayLabel"
                    class="day-label-input"
                    placeholder="Reason (optional)"
                    @keyup.enter="markDayOff(day, 'off')"
                  />
                  <div class="day-menu-actions">
                    <button class="link-btn" data-testid="mark-day-off" @click="markDayOff(day, 'off')">Day off</button>
                    <button class="link-btn" @click="markDayOff(day, 'sick')">Sick day</button>
                  </div>
                </template>
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="klass in classes" :key="klass.id">
            <th class="class-col">
              <template v-if="editingClass === klass.id">
                <input
                  class="emoji-input"
                  v-model="classDraft.emoji"
                  maxlength="2"
                  aria-label="Emoji"
                  @keyup.enter="saveClassName(klass)"
                />
                <input
                  class="class-input rename"
                  v-model="classDraft.title"
                  autofocus
                  aria-label="Class name"
                  @keyup.enter="saveClassName(klass)"
                  @keyup.escape="editingClass = null"
                  @blur="saveClassName(klass)"
                />
              </template>
              <template v-else>
                <button
                  class="class-name"
                  data-testid="rename-class"
                  :title="`Rename ${klass.title}`"
                  @click="startRenameClass(klass)"
                >
                  <span class="emoji">{{ klass.emoji }}</span> {{ klass.title }}
                </button>
                <button
                  class="row-btn"
                  :title="`Hide ${klass.title}`"
                  :aria-label="`Hide ${klass.title}`"
                  @click="hideClass(klass)"
                >−</button>
              </template>
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
                @click.stop="expanded === entry.id ? (expanded = null) : openEditor(entry)"
              >
                <span class="entry-title">{{ entry.title }}</span>
                <span class="entry-min">{{ entry.estimated_minutes }}m</span>

                <div v-if="expanded === entry.id && editDraft" class="entry-editor" @click.stop>
                  <input class="edit-title" v-model="editDraft.title" aria-label="Title" />

                  <div class="edit-row">
                    <label>Minutes <input type="number" v-model.number="editDraft.estimated_minutes" /></label>
                    <label>XP <input type="number" v-model.number="editDraft.xp_reward" /></label>
                  </div>

                  <div class="edit-row">
                    <label>Type
                      <select v-model="editDraft.task_type">
                        <option value="lesson">Lesson</option>
                        <option value="reading">Reading</option>
                        <option value="practice">Practice</option>
                        <option value="project">Project</option>
                        <option value="quiz">Quiz</option>
                        <option value="review">Review</option>
                      </select>
                    </label>
                    <label>With
                      <select v-model="editDraft.dependency_mode" class="dependency-mode">
                        <option value="independent">On his own</option>
                        <option value="teacher_led">Dad</option>
                        <option value="live_scheduled">Live class</option>
                      </select>
                    </label>
                  </div>

                  <input class="edit-url" v-model="editDraft.resource_url" placeholder="Link (optional)" />
                  <textarea
                    class="edit-notes"
                    v-model="editDraft.description"
                    rows="2"
                    placeholder="Notes for Sonny (optional)"
                  ></textarea>

                  <label class="move-label">
                    Move to
                    <select @change="move(entry, $event.target.value)" :value="entry.scheduled_date">
                      <option v-for="d in days" :key="d.date" :value="d.date">
                        {{ d.name }} {{ d.label }}
                      </option>
                    </select>
                  </label>

                  <div class="edit-actions">
                    <button class="btn-primary sm" data-testid="save-entry" @click="saveEdit(entry)">Save</button>
                    <button class="link-btn danger" @click="remove(entry)">Remove</button>
                  </div>
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
        <tfoot>
          <tr class="add-row">
            <th class="class-col">
              <template v-if="addingClass">
                <input class="emoji-input" v-model="newClass.emoji" maxlength="2" aria-label="Emoji" />
                <input
                  class="class-input"
                  v-model="newClass.title"
                  placeholder="Class name"
                  autofocus
                  @keyup.enter="addClass"
                  @keyup.escape="addingClass = false; newClass.title = ''"
                  @blur="addClass"
                />
              </template>
              <button v-else class="row-btn add" data-testid="add-class" @click="addingClass = true">
                + Add a class
              </button>
            </th>
            <td :colspan="days.length"></td>
          </tr>
        </tfoot>
      </table>
    </div>

    <p v-if="notice" class="text-muted footnote">{{ notice }}</p>

    <div v-if="hiddenClasses.length" class="hidden-classes">
      <button class="link-btn" @click="showHidden = !showHidden">
        {{ showHidden ? 'Hide' : `${hiddenClasses.length} hidden class${hiddenClasses.length === 1 ? '' : 'es'}` }}
      </button>
      <span v-if="showHidden" class="hidden-list">
        <span v-for="k in hiddenClasses" :key="k.id" class="hidden-item">
          {{ k.emoji }} {{ k.title }}
          <button class="link-btn" @click="restoreClass(k)">bring back</button>
        </span>
      </span>
    </div>

    <p class="text-muted footnote" v-if="weekStore.week">
      Click a day's heading to mark it off, or to make it a school day again. Marking one tells you
      what already sits on it — it never moves the work for you.
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

thead th { position: relative; }
.day-head {
  background: none;
  border: none;
  padding: 2px 4px;
  margin: -2px -4px;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
  /* Column, not block: the name and the day's tally are separate lines. As
     inline spans inside the button they ran together — "Thu 8/278 - 240m" —
     which is what block-level divs were quietly doing before this became a
     control. */
  display: flex;
  flex-direction: column;
  gap: 2px;
  width: 100%;
  border-radius: 4px;
}
.day-head:hover { background: rgba(255,255,255,0.06); }
.day-menu {
  position: absolute;
  z-index: 7;
  top: calc(100% - 4px);
  left: 4px;
  min-width: 190px;
  background: var(--bg-card);
  border: 1px solid var(--border-default, rgba(255,255,255,0.16));
  border-radius: 8px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.4);
  font-weight: 400;
}
.day-menu-note { margin: 0; font-size: 0.75rem; color: var(--text-secondary); }
.day-menu-actions { display: flex; gap: var(--space-md); }
.day-label-input { width: 100%; font-size: 0.8125rem; padding: 3px 6px; }

tbody th.class-col { display: flex; align-items: center; justify-content: space-between; gap: 6px; }
/* A button that reads as the label it edits: the affordance is the hover, not
   a permanent control, because this row is read far more often than renamed. */
.class-name {
  background: none;
  border: none;
  padding: 2px 4px;
  margin: -2px -4px;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
  border-radius: 4px;
  overflow-wrap: anywhere;
  flex: 1;
  min-width: 0;
}
.class-name:hover, .class-name:focus-visible { background: rgba(255,255,255,0.08); }
.class-input.rename { width: auto; flex: 1; min-width: 0; }
.row-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.95rem;
  line-height: 1;
  padding: 2px 5px;
  border-radius: 4px;
  opacity: 0;
  transition: opacity 0.12s;
}
tbody th.class-col:hover .row-btn { opacity: 0.7; }
.row-btn:hover, .row-btn:focus-visible { opacity: 1; background: rgba(255,255,255,0.08); }
.row-btn.add { opacity: 0.75; font-size: 0.8125rem; }
.row-btn.add:hover { opacity: 1; }

.add-row th { background: transparent; }
.emoji-input { width: 3ch; text-align: center; margin-right: 6px; }
.class-input { width: calc(100% - 4ch); font-size: 0.875rem; }

.hidden-classes { margin-top: var(--space-md); font-size: 0.8125rem; }
.hidden-list { display: inline-flex; flex-wrap: wrap; gap: var(--space-sm); margin-left: var(--space-sm); }
.hidden-item { color: var(--text-secondary); display: inline-flex; gap: 5px; align-items: center; }

.entry-editor {
  position: absolute;
  z-index: 6;
  left: 4px;
  right: 4px;
  top: 4px;
  width: 240px;
  background: var(--bg-card);
  border: 1px solid var(--border-default, rgba(255,255,255,0.16));
  border-radius: 8px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  cursor: default;
  box-shadow: 0 8px 24px rgba(0,0,0,0.4);
}
.entry-editor input, .entry-editor select, .entry-editor textarea {
  width: 100%;
  font-size: 0.8125rem;
  padding: 3px 6px;
}
.edit-title { font-weight: 600; }
.edit-row { display: flex; gap: 6px; }
.edit-row label {
  flex: 1;
  font-size: 0.7rem;
  color: var(--text-secondary);
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.edit-notes { resize: vertical; font-family: inherit; }
.edit-actions { display: flex; align-items: center; justify-content: space-between; gap: 6px; margin-top: 2px; }
.btn-primary.sm { padding: 4px 12px; font-size: 0.8125rem; }
</style>
