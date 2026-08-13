<script setup>
import { onMounted, onUnmounted, computed } from 'vue'
import { useTasksStore } from '../../stores/tasks'
import { api } from '../../api/client'
import TaskCard from '../../components/student/TaskCard.vue'
import ProgressBar from '../../components/common/ProgressBar.vue'
import WeekStrip from '../../components/student/WeekStrip.vue'
import KpiCard from '../../components/common/KpiCard.vue'
import NotificationBar from '../../components/common/NotificationBar.vue'

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
  return tasksStore.pendingTasks.reduce((sum, t) => sum + (t.xp_reward || 0), 0)
})

const xpEarned = computed(() => {
  return tasksStore.completedTasks.reduce((sum, t) => sum + (t.xp_reward || 0), 0)
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
      <KpiCard icon="🔥" value="5" label="Daily Streak" color="orange" subtitle="Keep it up!" />
    </div>

    <div class="progress-section mt-md mb-md">
      <ProgressBar :percent="completionPercent" label="Daily Completion" />
    </div>

    <!-- Placeholder week dates and counts, ideally fetched from an API -->
    <WeekStrip 
      :week-dates="['2023-10-23', '2023-10-24', '2023-10-25', '2023-10-26']"
      :task-counts="{ '2023-10-23': {total: 5, completed: 5}, '2023-10-24': {total: 4, completed: 2} }"
    />

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
