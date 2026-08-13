<script setup>
defineProps({
  icon: String,
  value: [String, Number],
  label: String,
  subtitle: String,
  color: { type: String, default: 'blue' }
})
</script>

<template>
  <div class="kpi-card">
    <div class="kpi-header">
      <span class="icon">{{ icon }}</span>
    </div>
    <div class="kpi-content">
      <div class="value" :style="{ color: `var(--accent-${color})` }">{{ value }}</div>
      <div class="label">{{ label }}</div>
      <div v-if="subtitle" class="subtitle">{{ subtitle }}</div>
    </div>
  </div>
</template>

<style scoped>
.kpi-header {
  margin-bottom: var(--space-sm);
}
.icon {
  font-size: 1.5rem;
}
.value {
  font-size: 2rem;
  font-weight: 700;
  line-height: 1.2;
}
.label {
  color: var(--text-secondary);
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.subtitle {
  color: var(--text-muted);
  font-size: 0.75rem;
  margin-top: var(--space-xs);
}
</style>
