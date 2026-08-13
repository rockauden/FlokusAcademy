<script setup>
import { ref, onMounted } from 'vue'
import { useTasksStore } from '../../stores/tasks'
import { useScheduleStore } from '../../stores/schedule'
import WeeklyGrid from '../../components/admin/WeeklyGrid.vue'

const tasksStore = useTasksStore()
const scheduleStore = useScheduleStore()

const newDate = ref('')
const newLabel = ref('')

onMounted(async () => {
  await tasksStore.fetchAllTasks({ pending_only: true })
})

// Calculate the current Monday
function getMonday(d) {
  d = new Date(d);
  var day = d.getDay(),
      diff = d.getDate() - day + (day == 0 ? -6 : 1);
  return new Date(d.setDate(diff)).toISOString().split('T')[0];
}

const currentMonday = ref(getMonday(new Date()))

async function addSickDay() {
  if (!newDate.value) return
  await scheduleStore.addSickDay(newDate.value, newLabel.value || 'Sick Day')
  alert('Added Sick Day')
  newDate.value = ''
  newLabel.value = ''
}

async function addHoliday() {
  if (!newDate.value) return
  await scheduleStore.addHoliday(newDate.value, newLabel.value || 'Holiday')
  alert('Added Holiday')
  newDate.value = ''
  newLabel.value = ''
}

async function recalculate() {
  if(confirm('Trigger rolling reschedule? This will shift all incomplete tasks.')) {
    await scheduleStore.recalculate()
    await tasksStore.fetchAllTasks({ pending_only: true })
    alert('Schedule recalculated!')
  }
}
</script>

<template>
  <div class="schedule-view">
    <header class="page-header mb-lg">
      <h1>Rolling Schedule Control</h1>
      <button class="btn-primary" @click="recalculate">🔄 Recalculate Schedule</button>
    </header>

    <div class="controls-panel mb-lg">
      <h3>Add Non-School Day</h3>
      <div class="form-row">
        <input type="date" v-model="newDate" />
        <input type="text" v-model="newLabel" placeholder="Reason (e.g. Fever, Thanksgiving)" />
        <button class="btn-ghost" @click="addSickDay">Add Sick Day 🤒</button>
        <button class="btn-ghost" @click="addHoliday">Add Holiday 🌴</button>
      </div>
    </div>

    <div class="grid-section">
      <h3>Current Week Schedule (Mon-Thu)</h3>
      <WeeklyGrid :tasks="tasksStore.allTasks" :start-date="currentMonday" />
    </div>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.controls-panel {
  background: var(--bg-card);
  padding: var(--space-md);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
}
.form-row {
  display: flex;
  gap: var(--space-sm);
  margin-top: var(--space-sm);
}
@media (max-width: 768px) {
  .form-row { flex-direction: column; }
}
</style>
