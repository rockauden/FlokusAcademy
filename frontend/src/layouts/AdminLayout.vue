<script setup>
import { useAuthStore } from '../stores/auth'
import SafetyAlertBanner from '../components/admin/SafetyAlertBanner.vue'
import StuckFlagStrip from '../components/admin/StuckFlagStrip.vue'

const authStore = useAuthStore()

function logout() {
  authStore.logout()
}
</script>

<template>
  <div class="admin-layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <h2>Flokus Admin</h2>
      </div>
      
      <nav class="sidebar-nav">
        <div class="nav-section">
          <div class="section-title">📝 Manage</div>
          <router-link to="/admin/week" class="nav-link" active-class="active">🗓️ Plan the Week</router-link>
          <router-link to="/admin/programs" class="nav-link" active-class="active">📚 Classes</router-link>
          <router-link to="/admin/tasks" class="nav-link" active-class="active">📋 Task Manager</router-link>
          <router-link to="/admin/calendar" class="nav-link" active-class="active">📆 Calendar</router-link>
          <router-link to="/admin/projects" class="nav-link" active-class="active">🛠️ Creator Projects</router-link>
        </div>

        <div class="nav-section">
          <div class="section-title">📊 Monitor</div>
          <router-link to="/admin/portfolio" class="nav-link" active-class="active">📂 Portfolio</router-link>
          <router-link to="/admin/analytics" class="nav-link" active-class="active">📈 Analytics</router-link>
        </div>

        <div class="nav-section">
          <div class="section-title">💼 Operations</div>
          <router-link to="/admin/finances" class="nav-link" active-class="active">💰 UFA Finances</router-link>
          <router-link to="/admin/settings" class="nav-link" active-class="active">⚙️ Settings</router-link>
        </div>
      </nav>
    </aside>

    <div class="main-wrapper">
      <header class="topbar">
        <div class="topbar-title">⚙️ ADMIN MODE — Full Curriculum Control Center</div>
        <button class="btn-ghost" @click="logout">Logout</button>
      </header>
      <main class="main-content">
        <SafetyAlertBanner />
        <StuckFlagStrip />
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 240px;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-default);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: var(--space-md);
  border-bottom: 1px solid var(--border-subtle);
  color: var(--accent-blue);
}

.sidebar-nav {
  padding: var(--space-md);
  flex: 1;
  overflow-y: auto;
}

.nav-section {
  margin-bottom: var(--space-lg);
}
.section-title {
  font-size: 0.75rem;
  text-transform: uppercase;
  color: var(--text-muted);
  font-weight: 700;
  margin-bottom: var(--space-sm);
  letter-spacing: 0.05em;
}

.main-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.topbar {
  height: 60px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-default);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-lg);
}
.topbar-title {
  font-weight: 600;
  color: var(--text-secondary);
}

.main-content {
  flex: 1;
  padding: var(--space-lg);
  overflow-y: auto;
}
</style>
