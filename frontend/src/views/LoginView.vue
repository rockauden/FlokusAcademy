<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const mode = ref('select') // 'select' | 'student' | 'teacher'
const pin = ref('')
const errorMsg = ref('')
const submitting = ref(false)

const ROLES = {
  student: { username: 'sonny', heading: "Enter Sonny's PIN", destination: '/student' },
  teacher: { username: 'dad', heading: 'Enter Teacher PIN', destination: '/admin' }
}

function choose(role) {
  mode.value = role
  pin.value = ''
  errorMsg.value = ''
}

function back() {
  mode.value = 'select'
  pin.value = ''
  errorMsg.value = ''
}

async function submitPin() {
  const role = ROLES[mode.value]
  if (!role || submitting.value) return

  if (!pin.value) {
    errorMsg.value = 'Please enter your PIN.'
    return
  }

  submitting.value = true
  errorMsg.value = ''
  try {
    await authStore.login(role.username, pin.value)
    router.push(role.destination)
  } catch (e) {
    // The store rethrows the API's message, so a wrong PIN and a rate limit
    // read differently instead of both showing "Invalid PIN".
    errorMsg.value = e?.message || 'Login failed. Please try again.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="login-view">
    <div class="login-card">
      <h1 class="title">🎓 Flokus Academy</h1>
      
      <div v-if="mode === 'select'" class="cards-container">
        <button class="role-card" @click="choose('student')">
          <div class="emoji">📋</div>
          <h3>Sonny's Hub</h3>
          <p>Student Access</p>
        </button>

        <button class="role-card teacher" @click="choose('teacher')">
          <div class="emoji">⚙️</div>
          <h3>Dad's Dashboard</h3>
          <p>Teacher Access</p>
        </button>
      </div>

      <div v-else class="pin-container">
        <h3>{{ ROLES[mode].heading }}</h3>
        <input
          type="password"
          inputmode="numeric"
          autocomplete="off"
          v-model="pin"
          placeholder="****"
          class="pin-input"
          :disabled="submitting"
          @keyup.enter="submitPin"
        />
        <p v-if="errorMsg" class="error">{{ errorMsg }}</p>
        <div class="actions">
          <button class="btn-primary" @click="submitPin" :disabled="submitting">
            {{ submitting ? 'Checking…' : 'Login' }}
          </button>
          <button class="btn-ghost" @click="back" :disabled="submitting">Back</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-view {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle at 50% 50%, var(--bg-secondary) 0%, var(--bg-primary) 100%);
  animation: fadeIn 1s ease-out;
}

.login-card {
  background: var(--bg-card);
  padding: var(--space-2xl);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-hover);
  border: 1px solid var(--border-default);
  text-align: center;
  max-width: 600px;
  width: 90%;
}

.title {
  margin-bottom: var(--space-xl);
  color: var(--text-primary);
  font-size: 2.5rem;
}

.cards-container {
  display: flex;
  gap: var(--space-lg);
  justify-content: center;
}
@media (max-width: 600px) {
  .cards-container { flex-direction: column; }
}

.role-card {
  flex: 1;
  background: var(--bg-input);
  border: 1px solid var(--border-default);
  padding: var(--space-xl);
  border-radius: var(--radius-md);
  transition: all var(--transition-default);
}
.role-card:hover {
  transform: translateY(-5px);
  border-color: var(--accent-blue);
  box-shadow: var(--shadow-glow-blue);
}
.role-card.teacher:hover {
  border-color: var(--accent-orange);
  box-shadow: 0 0 15px rgba(246,173,85,0.3);
}

.emoji {
  font-size: 3rem;
  margin-bottom: var(--space-sm);
}
.role-card h3 { color: var(--text-primary); margin-bottom: var(--space-xs); }
.role-card p { color: var(--text-muted); font-size: 0.875rem; }

.pin-container {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  align-items: center;
}
.pin-input {
  text-align: center;
  font-size: 2rem;
  letter-spacing: 0.5em;
  width: 200px;
}
.actions { display: flex; gap: var(--space-md); }
.error { color: var(--accent-red); }
</style>
