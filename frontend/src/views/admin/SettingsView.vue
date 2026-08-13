<script setup>
import { ref } from 'vue'
import { api } from '../../api/client'

const aiPersona = ref('Socratic Tutor')

async function clearChat() {
  if(confirm('Clear all chat history for Sonny?')) {
    await api.delete('/ai/history/sonny_chat_1')
    alert('Chat history cleared')
  }
}
</script>

<template>
  <div class="settings-view">
    <header class="page-header mb-lg">
      <h1>System Settings</h1>
    </header>

    <div class="settings-grid">
      <div class="settings-panel">
        <h3>AI Tutor Configuration</h3>
        <div class="form-group mt-md">
          <label>Default Persona</label>
          <select v-model="aiPersona">
            <option>Socratic Tutor</option>
            <option>Norse Boatbuilder</option>
            <option>Space Robot</option>
          </select>
          <p class="text-muted mt-sm" style="font-size:0.875rem;">Changes how Floki responds to questions.</p>
        </div>
        <button class="btn-danger mt-md" @click="clearChat">Clear Chat History</button>
      </div>

      <div class="settings-panel">
        <h3>System Info</h3>
        <p class="text-muted">API Endpoint: {{ 'http://localhost:8000' }}</p>
        <p class="text-muted">Version: 1.0.0</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-lg);
}
@media (max-width: 768px) {
  .settings-grid { grid-template-columns: 1fr; }
}
.settings-panel {
  background: var(--bg-card);
  padding: var(--space-lg);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-default);
}
</style>
