<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const sidebarOpen = ref(false)
const showPinModal = ref(false)
const adminPin = ref('')
const pinError = ref('')

function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
}

async function switchToAdmin() {
  pinError.value = ''
  try {
    await authStore.login('dad', adminPin.value)
    adminPin.value = ''
    showPinModal.value = false
    router.push('/admin')
  } catch (e) {
    // login() now rejects rather than returning false, so this has to be
    // caught or it surfaces as an unhandled rejection with no feedback.
    pinError.value = e?.message || 'Login failed. Please try again.'
  }
}
</script>

<template>
  <div class="student-layout">
    <aside class="sidebar" :class="{ open: sidebarOpen }">
      <div class="sidebar-header">
        <h1>🎓</h1>
        <h2 v-if="sidebarOpen" class="brand">Flokus</h2>
      </div>
      
      <nav class="sidebar-nav">
        <router-link to="/student/quests" class="nav-link" active-class="active">
          <span class="icon">📋</span>
          <span class="label" v-if="sidebarOpen">Daily Quests</span>
        </router-link>
        <router-link to="/student/calendar" class="nav-link" active-class="active">
          <span class="icon">📅</span>
          <span class="label" v-if="sidebarOpen">Calendar</span>
        </router-link>
        <router-link to="/student/creator" class="nav-link" active-class="active">
          <span class="icon">🛠️</span>
          <span class="label" v-if="sidebarOpen">Creator Block</span>
        </router-link>
        <router-link to="/student/floki" class="nav-link" active-class="active">
          <span class="icon">💬</span>
          <span class="label" v-if="sidebarOpen">Ask Floki</span>
        </router-link>
      </nav>
      
      <div class="sidebar-footer">
        <button class="btn-ghost" @click="showPinModal = true">
          ⚙️
        </button>
      </div>
    </aside>

    <main class="main-content">
      <header class="mobile-header">
        <button @click="toggleSidebar" class="btn-ghost">☰</button>
        <h2>🎓 Flokus Academy</h2>
      </header>
      <router-view />
    </main>

    <div v-if="showPinModal" class="modal-overlay" @click.self="showPinModal = false">
      <div class="modal-content">
        <h3>Admin Access</h3>
        <div class="form-group mt-md">
          <label>Enter Teacher PIN</label>
          <input type="password" v-model="adminPin" placeholder="****" @keyup.enter="switchToAdmin" />
          <p v-if="pinError" class="error mt-sm">{{ pinError }}</p>
        </div>
        <div class="flex-row" style="display:flex;gap:8px;margin-top:16px;">
          <button class="btn-primary" @click="switchToAdmin">Switch to Admin</button>
          <button class="btn-ghost" @click="showPinModal = false">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.student-layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 70px;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-default);
  display: flex;
  flex-direction: column;
  transition: width var(--transition-default);
}
.sidebar.open {
  width: 220px;
}

.sidebar-header {
  padding: var(--space-md);
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  border-bottom: 1px solid var(--border-subtle);
}
.sidebar-header h1 { font-size: 1.5rem; }
.brand { font-size: 1.2rem; color: var(--text-primary); }

.sidebar-nav {
  flex: 1;
  padding: var(--space-md) var(--space-sm);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.icon { font-size: 1.2rem; }
.label { font-weight: 600; }

.sidebar-footer {
  padding: var(--space-md);
  border-top: 1px solid var(--border-subtle);
  display: flex;
  justify-content: center;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: var(--space-lg);
  background: var(--bg-primary);
}

.mobile-header {
  display: none;
  align-items: center;
  gap: var(--space-md);
  padding-bottom: var(--space-md);
}

@media (max-width: 768px) {
  .sidebar { display: none; }
  .mobile-header { display: flex; }
}
</style>
