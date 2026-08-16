<script setup>
import { computed, toRef } from 'vue'
import { useCountUp } from '../../composables/useCountUp'

const props = defineProps({
  icon: String,
  value: [String, Number],
  label: String,
  subtitle: String,
  color: { type: String, default: 'blue' },
  // Off for cards whose value is not a plain quantity -- "3/7" counts nothing.
  countUp: { type: Boolean, default: false }
})

const counted = useCountUp(toRef(props, 'value'))

// Only take the animated value when it is actually meaningful; otherwise the
// raw prop passes straight through untouched.
const shown = computed(() => (props.countUp ? counted.value : props.value))
</script>

<template>
  <div class="kpi-card">
    <div class="kpi-header">
      <span class="icon">{{ icon }}</span>
    </div>
    <div class="kpi-content">
      <div class="value" :style="{ color: `var(--accent-${color})` }">{{ shown }}</div>
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
  /* Digits change width as they count; tabular figures stop the label and card
     jittering sideways while that happens. */
  font-variant-numeric: tabular-nums;
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
