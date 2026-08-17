<script setup>
import { computed } from 'vue'

/**
 * Sonny's week: what is done, what is left, and where today sits.
 *
 * The version this replaces showed four unlabelled cells reading
 * "0/2, —, 0/2, —", which is genuinely hard to interpret. Three things were
 * wrong with it, and each is fixed here.
 *
 * No dates. "MON" alone does not tell you which Monday, and nothing connects
 * a cell to a date you are planning around. Every cell now carries its date.
 *
 * A future day showed "0 of 2 done". Wednesday has not happened yet, so
 * counting its completions reads as failure rather than as work waiting. A day
 * still to come now shows how much is on it, and nothing about completion.
 *
 * An empty day showed a bare dash, indistinguishable from missing data --
 * which is exactly how it was read. A day with no work now says so.
 */
const props = defineProps({
  weekDates: { type: Array, default: () => [] },     // ['YYYY-MM-DD', ...]
  taskCounts: { type: Object, default: () => ({}) }, // { 'YYYY-MM-DD': { total, completed } }
})

const NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

function localToday() {
  const now = new Date()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${now.getFullYear()}-${month}-${day}`
}

const days = computed(() => {
  const today = localToday()

  return props.weekDates.map((dateStr) => {
    const counts = props.taskCounts[dateStr] || { total: 0, completed: 0 }
    const { total, completed } = counts

    // Parsed as local parts rather than new Date(dateStr), which treats a bare
    // date as UTC and lands on the previous day for anyone behind Greenwich.
    const [year, month, dayOfMonth] = dateStr.split('-').map(Number)
    const parsed = new Date(year, month - 1, dayOfMonth)

    const isToday = dateStr === today
    const isPast = dateStr < today
    const done = total > 0 && completed >= total

    let status
    if (total === 0) status = 'rest'
    else if (done) status = 'done'
    else if (isToday) status = 'today'
    else if (isPast) status = 'missed'
    else status = 'upcoming'

    return {
      dateStr,
      name: NAMES[parsed.getDay() === 0 ? 6 : parsed.getDay() - 1],
      dayOfMonth,
      isToday,
      total,
      completed,
      status,
      label: describe(status, completed, total, isToday),
    }
  })
})

function describe(status, completed, total, isToday) {
  if (status === 'rest') return isToday ? 'Nothing scheduled today' : 'No work scheduled'
  if (status === 'done') return `All ${total} done`
  if (status === 'upcoming') return `${total} to come`
  return `${completed} of ${total} done`
}
</script>

<template>
  <div class="week-strip" role="list">
    <div
      v-for="day in days"
      :key="day.dateStr"
      class="day"
      :class="[`is-${day.status}`, { 'is-today': day.isToday }]"
      role="listitem"
      :aria-label="`${day.name} ${day.dayOfMonth}: ${day.label}`"
    >
      <div class="head">
        <span class="name">{{ day.name }}</span>
        <span class="date">{{ day.dayOfMonth }}</span>
      </div>

      <div class="mark">
        <!-- Done: the tick alone. A count next to it just dilutes it. -->
        <span v-if="day.status === 'done'" class="tick" aria-hidden="true">✓</span>

        <!-- Still to come: how much is waiting, and nothing about completion,
             because none of it could have been done yet. -->
        <span v-else-if="day.status === 'upcoming'" class="count">{{ day.total }}</span>

        <!-- Nothing scheduled -- said in words, so it cannot be mistaken for
             data that failed to load. -->
        <span v-else-if="day.status === 'rest'" class="rest">Free</span>

        <!-- Today, or a past day with work left on it. -->
        <span v-else class="progress">{{ day.completed }}<span class="of">/{{ day.total }}</span></span>
      </div>

      <span v-if="day.isToday" class="today-tag">Today</span>
    </div>
  </div>
</template>

<style scoped>
.week-strip {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: var(--space-sm);
  background: var(--bg-card);
  padding: var(--space-sm);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
}

.day {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.35rem;
  padding: var(--space-sm) 0.35rem 0.6rem;
  border-radius: var(--radius-sm);
  background: var(--bg-input);
  border: 1px solid transparent;
  min-height: 5.25rem;
  position: relative;
}

.head {
  display: flex;
  align-items: baseline;
  gap: 0.3rem;
}
.name {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 700;
  color: var(--text-muted);
}
.date {
  font-size: 0.8rem;
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
}

.mark {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  font-weight: 700;
  font-size: 1.15rem;
  font-variant-numeric: tabular-nums;
}
.of { color: var(--text-muted); font-weight: 600; }

.tick { color: var(--accent-green); font-size: 1.35rem; }
.count { color: var(--text-secondary); }
.rest {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: var(--text-muted);
  opacity: 0.75;
}

/* A finished day should be the one that catches the eye. */
.is-done { background: rgb(34 197 94 / 10%); }
.is-done .name, .is-done .date { color: var(--accent-green); }

/* A past day with work left is worth noticing, but this is a nine-year-old's
   screen -- it is a nudge, not a telling-off. No red, no warning icon. */
.is-missed .progress { color: var(--accent-orange, #fb923c); }

.is-rest { opacity: 0.6; }

.is-today {
  border-color: var(--accent-blue);
  background: var(--bg-card-hover, var(--bg-input));
  box-shadow: var(--shadow-glow-blue);
}
.is-today .name, .is-today .date { color: var(--text-primary); }

.today-tag {
  position: absolute;
  bottom: -0.55rem;
  font-size: 0.6rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 700;
  color: var(--accent-blue);
  background: var(--bg-card);
  padding: 0 0.35rem;
}

@media (max-width: 30rem) {
  .day { min-height: 4.5rem; padding-top: 0.5rem; }
  .mark { font-size: 1rem; }
  .rest { font-size: 0.65rem; }
}
</style>
