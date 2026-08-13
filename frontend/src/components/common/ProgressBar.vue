<script setup>
import { computed } from 'vue'

const props = defineProps({
  percent: { type: Number, default: 0 },
  label: String,
  color: { type: String, default: 'blue' }
})

const isComplete = computed(() => props.percent >= 100)
</script>

<template>
  <div class="progress-bar-wrapper">
    <div v-if="label" class="progress-label">
      <span>{{ label }}</span>
      <span>{{ Math.round(percent) }}%</span>
    </div>
    <div class="progress-bar-container">
      <div 
        class="progress-bar-fill" 
        :class="[isComplete ? 'success' : 'glow']"
        :style="{ width: `${Math.min(percent, 100)}%` }"
      ></div>
    </div>
  </div>
</template>

<style scoped>
.progress-bar-wrapper {
  width: 100%;
}
.progress-label {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--space-xs);
  font-size: 0.875rem;
  color: var(--text-secondary);
}
</style>
