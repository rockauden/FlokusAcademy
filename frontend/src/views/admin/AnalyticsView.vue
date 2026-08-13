<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api/client'
import KpiCard from '../../components/common/KpiCard.vue'

const summary = ref(null)

onMounted(async () => {
  summary.value = await api.get('/analytics/summary')
})
</script>

<template>
  <div class="analytics-view">
    <header class="page-header mb-lg">
      <h1>Learning Analytics</h1>
    </header>

    <div v-if="summary" class="kpi-grid mb-lg">
      <KpiCard icon="⭐" :value="summary.xp_balance" label="Total XP" color="gold" />
      <KpiCard icon="🔥" :value="summary.daily_streak" label="Daily Streak" color="orange" />
      <KpiCard icon="✅" :value="summary.total_completed_tasks" label="Completed Tasks" color="green" />
      <KpiCard icon="⏱️" :value="summary.total_focus_minutes" label="Focus Minutes" color="blue" />
    </div>

    <div v-if="summary" class="charts-grid">
      <div class="chart-panel">
        <h3>Completion by Subject</h3>
        <div class="bar-chart mt-md">
          <div v-for="(val, key) in summary.completion_by_subject" :key="key" class="bar-row">
            <div class="bar-label">{{ key }}</div>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: `${Math.min(val * 2, 100)}%` }"></div>
            </div>
            <div class="bar-value">{{ val }}</div>
          </div>
        </div>
      </div>
      
      <div class="chart-panel">
        <h3>Recent 7-Day Activity</h3>
        <div class="heatmap mt-md">
          <div v-for="day in summary.recent_7_day_activity" :key="day.date" class="heat-day">
            <div class="heat-box" :style="{ opacity: day.completed > 0 ? 0.2 + (day.completed/10) : 0.05 }"></div>
            <span>{{ new Date(day.date).toLocaleDateString(undefined, {weekday:'short'}) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-md);
}
.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-lg);
}
@media (max-width: 768px) {
  .charts-grid { grid-template-columns: 1fr; }
}
.chart-panel {
  background: var(--bg-card);
  padding: var(--space-lg);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-default);
}
.bar-row {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}
.bar-label { width: 100px; font-size: 0.875rem; text-align: right; }
.bar-track { flex: 1; height: 12px; background: var(--bg-input); border-radius: var(--radius-pill); }
.bar-fill { height: 100%; background: var(--accent-blue); border-radius: var(--radius-pill); }
.bar-value { width: 30px; font-size: 0.875rem; }

.heatmap {
  display: flex;
  gap: var(--space-sm);
  justify-content: center;
}
.heat-day {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  font-size: 0.75rem;
  color: var(--text-muted);
}
.heat-box {
  width: 30px;
  height: 30px;
  background: var(--accent-green);
  border-radius: 4px;
}
</style>
