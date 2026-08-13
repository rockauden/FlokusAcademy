<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api/client'

const projects = ref([])
const completedProjects = ref([])
const loading = ref(false)
const selectedProject = ref(null)
const completionForm = ref({ summary: '' })

async function fetchProjects() {
  loading.value = true
  const active = await api.get('/projects/active')
  projects.value = active || []
  // Ideally fetch completed as well, mocking for now
  completedProjects.value = []
  loading.value = false
}

onMounted(fetchProjects)

function selectProject(p) {
  selectedProject.value = p
  completionForm.value.summary = ''
}

async function submitProject() {
  if (completionForm.value.summary.length < 30) {
    alert('Please write at least 30 characters summarizing your work.')
    return
  }
  await api.post(`/projects/${selectedProject.value.id}/complete`, {
    project_summary: completionForm.value.summary
  })
  selectedProject.value = null
  await fetchProjects()
}
</script>

<template>
  <div class="creator-view">
    <header class="hero mb-lg">
      <h1>Creator Block 🛠️</h1>
      <p class="subtitle">Build, code, and create! Earn huge XP bounties.</p>
    </header>

    <div v-if="loading" class="text-muted">Loading projects...</div>

    <div class="grid" v-else>
      <div class="active-projects">
        <h3>Active Bounties</h3>
        <div v-for="p in projects" :key="p.id" class="project-card" @click="selectProject(p)">
          <div class="card-header">
            <h4>{{ p.title }}</h4>
            <span class="badge badge-gold">{{ p.xp_bounty }} XP</span>
          </div>
          <p class="platform text-muted">Platform: {{ p.platform }}</p>
        </div>
      </div>

      <div class="submit-panel" v-if="selectedProject">
        <h3>Submit: {{ selectedProject.title }}</h3>
        <div class="form-group mt-md">
          <label>What did you build? (min 30 chars)</label>
          <textarea v-model="completionForm.summary" rows="5" placeholder="I built a..."></textarea>
        </div>
        <div class="form-group">
          <label>Attach screenshot/link (optional)</label>
          <input type="text" placeholder="URL or file name" />
        </div>
        <div class="actions mt-md">
          <button class="btn-primary" @click="submitProject">Submit for Review</button>
          <button class="btn-ghost" @click="selectedProject = null">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-lg);
}
@media (max-width: 768px) {
  .grid { grid-template-columns: 1fr; }
}

.project-card {
  background: var(--bg-card);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
  border: 1px solid var(--border-default);
  cursor: pointer;
  transition: all var(--transition-fast);
}
.project-card:hover {
  border-color: var(--accent-blue);
  box-shadow: var(--shadow-glow-blue);
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-xs);
}
.card-header h4 { margin: 0; }
.badge-gold { background: rgba(251,191,36,0.2); color: var(--accent-gold); }

.submit-panel {
  background: var(--bg-card);
  padding: var(--space-lg);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-active);
  box-shadow: var(--shadow-glow-blue);
}
.actions { display: flex; gap: var(--space-sm); }
</style>
