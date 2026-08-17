<script setup>
import { ref, onMounted, computed } from 'vue'
import { useCoursesStore } from '../../stores/courses'
import UnitManagerView from './UnitManagerView.vue'

/**
 * Programs — the top tier of the curriculum model, and until now creatable
 * only by editing `services/curriculum_seeder.py` and redeploying. The API has
 * had full CRUD the whole time; nothing called it.
 *
 * "Program" is the teacher's word and `course` is the API's. The mismatch is
 * deliberate and documented at routers/modules.py:14 — renaming the paths is a
 * separate migration.
 */
const coursesStore = useCoursesStore()

// Deactivated programs are listed too, greyed out. DELETE only flips
// is_active, so hiding them here would make deactivation a one-way door.
const showInactive = ref(true)
const error = ref('')
const editingId = ref(null)
// Which program's units are open below the list. Null means none.
const unitsFor = ref(null)

function blankProgram() {
  return {
    title: '',
    subject_area: '',
    platform: '',
    platform_url: '',
    emoji: '📚',
    color_hex: '#63b3ed',
    sort_order: 0,
    ufa_eligible: true,
    is_active: true
  }
}

const form = ref(blankProgram())

const sorted = computed(() =>
  [...coursesStore.courses].sort((a, b) => a.sort_order - b.sort_order || a.title.localeCompare(b.title))
)

async function load() {
  await coursesStore.fetchCourses({ includeInactive: showInactive.value })
}

onMounted(load)

function startEdit(program) {
  editingId.value = program.id
  form.value = { ...program }
  error.value = ''
}

function cancelEdit() {
  editingId.value = null
  form.value = blankProgram()
  error.value = ''
}

async function save() {
  // Both are NOT NULL on the model and required by CourseBase, so catching
  // them here turns a 422 into a plain sentence.
  if (!form.value.title.trim()) {
    error.value = 'Give the program a title.'
    return
  }
  if (!form.value.subject_area.trim()) {
    error.value = 'Give the program a subject area — it is what groups the portfolio.'
    return
  }

  // CourseUpdate takes the whole object, so send the form as it stands rather
  // than a diff.
  const payload = { ...form.value }
  delete payload.id
  delete payload.created_at

  error.value = ''
  try {
    if (editingId.value) {
      await coursesStore.updateCourse(editingId.value, payload)
    } else {
      await coursesStore.createCourse(payload)
    }
    cancelEdit()
    await load()
  } catch (e) {
    error.value = e.message
  }
}

async function toggleActive(program) {
  try {
    if (program.is_active) {
      // DELETE deactivates. Its lessons, and the XP earned against them, stay.
      await coursesStore.deactivateCourse(program.id)
    } else {
      const { id, created_at, ...rest } = program
      await coursesStore.updateCourse(program.id, { ...rest, is_active: true })
    }
    if (unitsFor.value?.id === program.id) unitsFor.value = null
    await load()
  } catch (e) {
    error.value = e.message
  }
}

function toggleUnits(program) {
  unitsFor.value = unitsFor.value?.id === program.id ? null : program
}
</script>

<template>
  <div class="program-manager">
    <header class="page-header mb-lg">
      <h1>Programs</h1>
      <label class="inline-toggle text-muted">
        <input type="checkbox" v-model="showInactive" @change="load" />
        Show deactivated
      </label>
    </header>

    <div class="grid">
      <div class="panel program-form">
        <h3>{{ editingId ? 'Edit Program' : 'New Program' }}</h3>

        <div class="form-group mt-md">
          <label>Title *</label>
          <input type="text" v-model="form.title" placeholder="e.g. Social Studies — Tuttle Twins" />
        </div>

        <div class="form-group">
          <label>Subject Area *</label>
          <input type="text" v-model="form.subject_area" placeholder="e.g. Social Studies" />
        </div>

        <div class="form-group">
          <label>Platform</label>
          <input type="text" v-model="form.platform" placeholder="e.g. Tuttle Twins" />
        </div>

        <div class="form-group">
          <label>Platform URL</label>
          <input type="url" v-model="form.platform_url" placeholder="https://…" />
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>Emoji</label>
            <input type="text" v-model="form.emoji" maxlength="4" />
          </div>
          <div class="form-group">
            <label>Colour</label>
            <input type="color" v-model="form.color_hex" />
          </div>
          <div class="form-group">
            <label>Sort Order</label>
            <input type="number" v-model.number="form.sort_order" />
          </div>
        </div>

        <div class="form-group checkbox">
          <label>
            <input type="checkbox" v-model="form.ufa_eligible" />
            Counts toward the UFA record
          </label>
        </div>

        <p v-if="error" class="form-error">{{ error }}</p>

        <div class="actions mt-md">
          <button class="btn-primary" @click="save">{{ editingId ? 'Save Program' : 'Create Program' }}</button>
          <button v-if="editingId" class="btn-ghost" @click="cancelEdit">Cancel</button>
        </div>
      </div>

      <div class="panel program-list">
        <h3>All Programs</h3>
        <p v-if="!coursesStore.loading && sorted.length === 0" class="text-muted mt-md">
          No programs yet. Create the first one on the left.
        </p>
        <div class="list-container mt-md">
          <div
            v-for="p in sorted"
            :key="p.id"
            class="program-item"
            :class="{ inactive: !p.is_active }"
          >
            <div class="item-header">
              <strong :style="{ borderLeftColor: p.color_hex }" class="swatch">
                {{ p.emoji }} {{ p.title }}
              </strong>
              <span v-if="!p.is_active" class="badge badge-orange">Deactivated</span>
            </div>
            <div class="item-meta text-muted">
              {{ p.subject_area }}<span v-if="p.platform"> · {{ p.platform }}</span> · sort {{ p.sort_order }}
            </div>
            <div class="item-actions mt-sm">
              <button class="btn-ghost" @click="startEdit(p)">Edit</button>
              <button class="btn-ghost" @click="toggleUnits(p)">
                {{ unitsFor?.id === p.id ? 'Hide Units' : 'Units' }}
              </button>
              <button class="btn-ghost" @click="toggleActive(p)">
                {{ p.is_active ? 'Deactivate' : 'Reactivate' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <UnitManagerView v-if="unitsFor" :program="unitsFor" class="mt-lg" />
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.inline-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.875rem;
}
.grid {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: var(--space-lg);
}
@media (max-width: 900px) {
  .grid { grid-template-columns: 1fr; }
}
.panel {
  background: var(--bg-card);
  padding: var(--space-lg);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-default);
}
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: var(--space-sm);
}
.checkbox label {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  color: var(--text-primary);
  cursor: pointer;
}
.form-error {
  color: var(--color-danger, #e05252);
  margin-top: var(--space-md);
}
.actions {
  display: flex;
  gap: var(--space-sm);
}
.program-item {
  border-bottom: 1px solid var(--border-subtle);
  padding: var(--space-sm) 0;
}
.program-item:last-child { border-bottom: none; }
.program-item.inactive { opacity: 0.55; }
.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-sm);
}
.swatch {
  border-left: 4px solid var(--border-default);
  padding-left: var(--space-sm);
}
.item-meta { font-size: 0.875rem; }
.item-actions {
  display: flex;
  gap: var(--space-sm);
}
</style>
