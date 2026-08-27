<script setup>
import { ref } from 'vue'
import { api } from '../../api/client'

const aiPersona = ref('Socratic Tutor')

const chatNotice = ref('')
const chatArmed = ref(false)

async function clearChat() {
  chatArmed.value = false
  try {
    await api.delete('/ai/history/sonny_chat_1')
    chatNotice.value = 'Chat history cleared.'
  } catch (e) {
    chatNotice.value = e.message
  }
}

/**
 * The reset. Irreversible, so it is deliberately awkward: the phrase has to be
 * typed in full, and the server checks it again rather than trusting this
 * screen. A checkbox would be one stray click away from destroying a year of
 * records.
 */
const CONFIRM_PHRASE = 'DELETE ALL WORK'
const resetPhrase = ref('')
const resetResult = ref(null)
const resetError = ref('')
const resetting = ref(false)

async function resetCurriculum() {
  resetting.value = true
  resetError.value = ''
  try {
    resetResult.value = await api.post('/maintenance/reset-curriculum', { confirm: resetPhrase.value })
    resetPhrase.value = ''
  } catch (e) {
    resetError.value = e.message
  } finally {
    resetting.value = false
  }
}
</script>

<template>
  <div class="settings-view">
    <header class="page-header mb-lg">
      <h1>Settings</h1>
    </header>

    <div class="settings-grid">
      <div class="settings-panel">
        <h3>Ask Floki</h3>
        <div class="form-group mt-md">
          <label>Default Persona</label>
          <select v-model="aiPersona">
            <option>Socratic Tutor</option>
            <option>Norse Boatbuilder</option>
            <option>Space Robot</option>
          </select>
          <p class="text-muted mt-sm hint">Changes how Floki responds to questions.</p>
        </div>
        <button v-if="!chatArmed" class="btn-ghost mt-md" @click="chatArmed = true">
          Clear chat history
        </button>
        <button v-else class="btn-danger mt-md" @click="clearChat">
          Really clear Sonny's chat history
        </button>
        <p v-if="chatNotice" class="text-muted mt-sm hint">{{ chatNotice }}</p>
      </div>

      <div class="settings-panel">
        <h3>System</h3>
        <p class="text-muted">Flokus Academy — one teacher, one student.</p>
        <p class="text-muted hint">
          Work is planned by hand each week on the Plan the Week screen. Nothing in the app
          moves a day you have chosen.
        </p>
      </div>
    </div>

    <div class="settings-panel danger mt-lg" data-testid="reset-panel">
      <h3>Start over</h3>
      <p class="text-muted">
        Deletes <strong>every lesson, assignment, unit, XP entry and reward purchase</strong> —
        including anything already finished. Your classes, both accounts, the school calendar,
        UFA expenses and reward definitions are kept.
      </p>
      <p class="text-muted hint">This cannot be undone.</p>

      <div class="reset-row">
        <input
          v-model="resetPhrase"
          class="reset-input"
          data-testid="reset-phrase"
          :placeholder="`Type ${CONFIRM_PHRASE} to confirm`"
          aria-label="Confirmation phrase"
        />
        <button
          class="btn-danger"
          data-testid="reset-submit"
          :disabled="resetPhrase !== CONFIRM_PHRASE || resetting"
          @click="resetCurriculum"
        >
          {{ resetting ? 'Deleting…' : 'Delete all work' }}
        </button>
      </div>

      <p v-if="resetError" class="form-error">{{ resetError }}</p>
      <p v-if="resetResult" class="text-muted mt-sm" data-testid="reset-result">
        Deleted {{ resetResult.lessons }} lessons, {{ resetResult.assignments }} assignments,
        {{ resetResult.units }} units, {{ resetResult.xp_entries }} XP entries and
        {{ resetResult.purchases }} purchases.
      </p>
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
.settings-panel h3 { margin-top: 0; }
.settings-panel.danger {
  border-color: rgba(224, 82, 82, 0.5);
  background: rgba(224, 82, 82, 0.06);
}
.settings-panel.danger p { max-width: 70ch; }
.hint { font-size: 0.8125rem; }
.reset-row {
  display: flex;
  gap: var(--space-sm);
  align-items: center;
  flex-wrap: wrap;
  margin-top: var(--space-md);
}
.reset-input { min-width: 280px; }
.form-error { color: var(--color-danger, #e05252); margin-top: var(--space-sm); }
.btn-danger {
  background: var(--color-danger, #e05252);
  color: white;
  border: none;
  border-radius: 6px;
  padding: 8px 14px;
  cursor: pointer;
}
.btn-danger:disabled { opacity: 0.45; cursor: not-allowed; }
</style>
