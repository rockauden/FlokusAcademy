<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api/client'

const projects = ref([])
const form = ref({ title: '', platform: '', xp_bounty: 100 })

async function fetchProjects() {
  projects.value = await api.get('/projects') || []
}

onMounted(fetchProjects)

async function createProject() {
  await api.post('/projects', form.value)
  form.value = { title: '', platform: '', xp_bounty: 100 }
  await fetchProjects()
}
</script>

<template>
  <div class="project-manager">
    <header class="page-header mb-lg">
      <h1>Creator Projects</h1>
    </header>

    <div class="grid">
      <div class="deploy-form panel">
        <h3>Deploy New Project</h3>
        <div class="form-group mt-md">
          <label>Title</label>
          <input type="text" v-model="form.title" placeholder="e.g. Build a Python Snake Game" />
        </div>
        <div class="form-group">
          <label>Platform/Medium</label>
          <input type="text" v-model="form.platform" placeholder="e.g. Replit, Scratch, LEGO" />
        </div>
        <div class="form-group">
          <label>XP Bounty</label>
          <input type="number" v-model="form.xp_bounty" />
        </div>
        <button class="btn-primary mt-md" @click="createProject">Deploy Project</button>
      </div>

      <div class="projects-list panel">
        <h3>All Projects</h3>
        <div class="list-container mt-md">
          <div v-for="p in projects" :key="p.id" class="project-item">
            <div class="item-header">
              <strong>{{ p.title }}</strong>
              <span class="badge" :class="p.is_completed ? 'badge-green' : 'badge-orange'">
                {{ p.is_completed ? 'Done' : 'Active' }}
              </span>
            </div>
            <div class="item-meta text-muted">Platform: {{ p.platform }} | Bounty: {{ p.xp_bounty }} XP</div>
            <div v-if="p.is_completed" class="summary mt-sm">
              <em>"{{ p.project_summary }}"</em>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: var(--space-lg);
}
@media (max-width: 768px) {
  .grid { grid-template-columns: 1fr; }
}
.panel {
  background: var(--bg-card);
  padding: var(--space-lg);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-default);
}
.project-item {
  border-bottom: 1px solid var(--border-subtle);
  padding: var(--space-sm) 0;
}
.project-item:last-child { border-bottom: none; }
.item-header {
  display: flex;
  justify-content: space-between;
}
.summary {
  background: var(--bg-input);
  padding: var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
}
</style>
