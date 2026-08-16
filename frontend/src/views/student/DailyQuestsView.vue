<script setup>
import { onMounted, onUnmounted, computed } from 'vue'
import { useTasksStore } from '../../stores/tasks'
import { api } from '../../api/client'
import TaskCard from '../../components/student/TaskCard.vue'
import ProgressBar from '../../components/common/ProgressBar.vue'
// WeekStrip.vue is kept, not deleted — it is wired back in during Phase 3
// (L-03) once a per-day completion endpoint exists to feed it.
import KpiCard from '../../components/common/KpiCard.vue'
import NotificationBar from '../../components/common/NotificationBar.vue'
import { taskXp } from '../../utils/xp'

const tasksStore = useTasksStore()
let pollInterval = null

onMounted(async () => {
  await tasksStore.fetchTodayTasks()
  pollInterval = setInterval(() => {
    tasksStore.fetchTodayTasks()
  }, 30000)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})

const totalTasks = computed(() => tasksStore.todayTasks.length)
const completedCount = computed(() => tasksStore.completedTasks.length)
const completionPercent = computed(() => totalTasks.value ? (completedCount.value / totalTasks.value) * 100 : 0)

const estimatedTime = computed(() => {
  return tasksStore.pendingTasks.reduce((sum, t) => sum + (t.estimated_minutes || 0), 0)
})

const xpAvailable = computed(() => {
  return tasksStore.pendingTasks.reduce((sum, t) => sum + taskXp(t), 0)
})

const xpEarned = computed(() => {
  return tasksStore.completedTasks.reduce((sum, t) => sum + taskXp(t), 0)
})

async function handleComplete({ id, notes, minutes }) {
  await tasksStore.completeTask(id, notes, minutes)
}
</script>

<template>
  <div class="quests-view">
    <NotificationBar />
    
    <header class="hero">
      <h1>Good morning, Sonny! 🚀</h1>
      <p class="subtitle">You have {{ tasksStore.pendingTasks.length }} tasks left today. Estimated time: {{ estimatedTime }}m. XP Available: {{ xpAvailable }}</p>
    </header>

    <div class="kpi-row">
      <KpiCard icon="🎯" :value="`${completedCount}/${totalTasks}`" label="Tasks Done" color="blue" />
      <KpiCard icon="⭐" :value="xpEarned" label="XP Earned Today" color="gold" />
      <!--
        TODO (Phase 3, L-03): restore the daily streak alongside the week strip
        below, once both are backed by real data.

        Removed rather than left in place because both were invented: the
        streak was the literal value 5, and the week strip was pinned to four
        dates in October 2023 with made-up completion counts. A motivational
        system that credits work a child did not do stops being believed the
        first time he notices, and it takes the honest parts down with it.

        Wiring these needs a per-day completion count for the student across a
        date range, which no endpoint returns yet.
      -->
    </div>

    <div class="progress-section mt-md mb-md">
      <ProgressBar :percent="completionPercent" label="Daily Completion" />
    </div>

    <div class="task-lists">
      <div v-for="(tasks, subject) in tasksStore.tasksBySubject" :key="subject" class="subject-group">
        <h3 class="subject-header">{{ subject }}</h3>
        <transition-group name="list" tag="div">
          <TaskCard 
            v-for="task in tasks.filter(t => !t.is_completed)" 
            :key="task.id" 
            :task="task" 
            @complete="handleComplete" 
          />
        </transition-group>
      </div>

      <div v-if="tasksStore.completedTasks.length > 0" class="completed-section mt-lg">
        <h3>Completed Quests ✅</h3>
        <transition-group name="list" tag="div">
          <TaskCard 
            v-for="task in tasksStore.completedTasks" 
            :key="task.id" 
            :task="task" 
          />
        </transition-group>
      </div>
    </div>
  </div>
</template>

<style scoped>
.hero {
  margin-bottom: var(--space-lg);
}
.hero h1 { margin-bottom: var(--space-xs); }
.subtitle { color: var(--text-secondary); }

.kpi-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-md);
}

.subject-header {
  margin: var(--space-lg) 0 var(--space-md);
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-subtle);
  padding-bottom: var(--space-xs);
}

.list-enter-active, .list-leave-active {
  transition: all 0.5s ease;
}
.list-enter-from, .list-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}
</style>
