<script setup>
import { useErrorsStore } from '../../stores/errors'

const errors = useErrorsStore()
</script>

<template>
  <div v-if="errors.items.length" class="error-toasts" role="alert" aria-live="assertive">
    <div v-for="item in errors.items" :key="item.id" class="toast">
      <div class="text">
        <span>{{ item.message }}</span>
        <span v-if="item.count > 1" class="count">x{{ item.count }}</span>
        <!-- Shown so a failure can be quoted back and found in the logs. -->
        <code v-if="item.requestId" class="rid">{{ item.requestId }}</code>
      </div>
      <button class="close" aria-label="Dismiss" @click="errors.dismiss(item.id)">x</button>
    </div>
  </div>
</template>

<style scoped>
.error-toasts {
  position: fixed;
  right: 1rem;
  bottom: 1rem;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-width: min(26rem, calc(100vw - 2rem));
}

.toast {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  background: var(--bg-card, #1e2230);
  color: var(--text-primary, #e8eaf0);
  border: 1px solid var(--accent-red, #e05252);
  border-left: 4px solid var(--accent-red, #e05252);
  border-radius: var(--radius-sm, 6px);
  padding: 0.75rem 0.9rem;
  box-shadow: 0 6px 20px rgb(0 0 0 / 35%);
}

.text { display: flex; flex-direction: column; gap: 0.2rem; font-size: 0.9rem; }
.count { color: var(--text-secondary, #98a0b3); font-size: 0.8rem; }
.rid { color: var(--text-secondary, #98a0b3); font-size: 0.72rem; }

.close {
  background: none;
  border: none;
  color: var(--text-secondary, #98a0b3);
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  padding: 0 0.15rem;
}
.close:hover { color: var(--text-primary, #e8eaf0); }

@media (prefers-reduced-motion: no-preference) {
  .toast { animation: slide-in 160ms ease-out; }
  @keyframes slide-in {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: none; }
  }
}
</style>
