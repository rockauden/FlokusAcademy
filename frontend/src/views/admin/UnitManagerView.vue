<script setup>
import { ref, watch, computed } from 'vue'
import { useUnitsStore } from '../../stores/units'

/**
 * Units inside one program, shown as a panel under the program list.
 *
 * `status` is the field that matters most here. The rolling scheduler paces
 * only `active` units, so flipping a unit to `active` is how work is released:
 * the year can be imported with everything `planned` and the student's day
 * stays empty until a unit is turned on. It is also what makes a mid-year
 * Beast Academy Level 2 → 3 jump a click rather than a migration — Level 3
 * units sit as `planned` until they are wanted.
 */
const props = defineProps({
  program: { type: Object, required: true }
})

const unitsStore = useUnitsStore()

const STATUSES = [
  { value: 'planned', label: 'Planned — imported, not released' },
  { value: 'active', label: 'Active — the scheduler paces this' },
  { value: 'completed', label: 'Completed' },
  { value: 'abandoned', label: 'Abandoned' }
]

const showInactive = ref(true)
const editingId = ref(null)
const error = ref('')

function blankUnit() {
  return {
    title: '',
    description: '',
    week_start: 1,
    week_end: 1,
    sort_order: 0,
    // New units default to planned, not active. Authoring a unit and releasing
    // it are separate decisions, and defaulting to active would date its
    // lessons on the next recalculation — which a sick day triggers on its own.
    status: 'planned',
    is_active: true
  }
}

const form = ref(blankUnit())

const sorted = computed(() =>
  [...unitsStore.units].sort((a, b) => a.sort_order - b.sort_order || a.title.localeCompare(b.title))
)

const activeCount = computed(() => unitsStore.units.filter(u => u.status === 'active').length)

async function load() {
  await unitsStore.fetchUnits(props.program.id, { includeInactive: showInactive.value })
}

// Reloads when the teacher opens a different program's units, and on mount —
// `immediate` is what covers the first render.
watch(() => props.program.id, load, { immediate: true })

function startEdit(unit) {
  editingId.value = unit.id
  form.value = { ...unit }
  error.value = ''
}

function cancelEdit() {
  editingId.value = null
  form.value = blankUnit()
  error.value = ''
}

async function save() {
  if (!form.value.title.trim()) {
    error.value = 'Give the unit a title.'
    return
  }

  const payload = { ...form.value }
  delete payload.id
  delete payload.created_at
  delete payload.course_id

  error.value = ''
  try {
    if (editingId.value) {
      await unitsStore.updateUnit(editingId.value, payload)
    } else {
      // ModuleCreate takes course_id; ModuleUpdate does not, so a unit cannot
      // be moved between programs after the fact.
      await unitsStore.createUnit({ ...payload, course_id: props.program.id })
    }
    cancelEdit()
    await load()
  } catch (e) {
    error.value = e.message
  }
}

/** Change status in place, without opening the edit form. */
async function setStatus(unit, status) {
  const { id, created_at, course_id, ...rest } = unit
  try {
    await unitsStore.updateUnit(unit.id, { ...rest, status })
    await load()
  } catch (e) {
    error.value = e.message
  }
}

async function toggleActive(unit) {
  // DELETE /api/modules/{id} really deletes, and Lesson.unit_id is ON DELETE
  // SET NULL — so a deleted unit silently returns its lessons to the unit-less
  // pool the scheduler mishandles. Deactivating keeps the link intact.
  const { id, created_at, course_id, ...rest } = unit
  try {
    await unitsStore.updateUnit(unit.id, { ...rest, is_active: !unit.is_active })
    await load()
  } catch (e) {
    error.value = e.message
  }
}
</script>

<template>
  <div class="unit-manager panel">
    <header class="unit-header">
      <h3>Units in {{ program.emoji }} {{ program.title }}</h3>
      <div class="header-side">
        <span class="badge" :class="activeCount ? 'badge-green' : 'badge-orange'">
          {{ activeCount }} active
        </span>
        <label class="inline-toggle text-muted">
          <input type="checkbox" v-model="showInactive" @change="load" />
          Show deactivated
        </label>
      </div>
    </header>

    <div class="unit-grid mt-md">
      <div class="unit-form">
        <h4>{{ editingId ? 'Edit Unit' : 'New Unit' }}</h4>

        <div class="form-group mt-sm">
          <label>Title *</label>
          <input type="text" v-model="form.title" placeholder="e.g. Vol 1 — The Miraculous Pencil" />
        </div>

        <div class="form-group">
          <label>Description</label>
          <input type="text" v-model="form.description" />
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>Week Start</label>
            <input type="number" v-model.number="form.week_start" />
          </div>
          <div class="form-group">
            <label>Week End</label>
            <input type="number" v-model.number="form.week_end" />
          </div>
          <div class="form-group">
            <label>Sort Order</label>
            <input type="number" v-model.number="form.sort_order" />
          </div>
        </div>

        <div class="form-group">
          <label>Status</label>
          <select v-model="form.status" class="unit-status-field">
            <option v-for="s in STATUSES" :key="s.value" :value="s.value">{{ s.label }}</option>
          </select>
          <p class="text-muted hint">Only <strong>active</strong> units are paced by the scheduler.</p>
        </div>

        <p v-if="error" class="form-error">{{ error }}</p>

        <div class="actions mt-md">
          <button class="btn-primary" @click="save">{{ editingId ? 'Save Unit' : 'Create Unit' }}</button>
          <button v-if="editingId" class="btn-ghost" @click="cancelEdit">Cancel</button>
        </div>
      </div>

      <div class="unit-list">
        <p v-if="!unitsStore.loading && sorted.length === 0" class="text-muted">
          No units in this program yet.
        </p>
        <div
          v-for="u in sorted"
          :key="u.id"
          class="unit-item"
          :class="{ inactive: !u.is_active }"
        >
          <div class="item-header">
            <strong>{{ u.title }}</strong>
            <span class="badge" :class="u.status === 'active' ? 'badge-green' : 'badge-orange'">
              {{ u.status }}
            </span>
          </div>
          <div class="item-meta text-muted">
            weeks {{ u.week_start }}–{{ u.week_end }} · sort {{ u.sort_order }}
            <span v-if="!u.is_active"> · deactivated</span>
          </div>
          <div class="item-actions mt-sm">
            <select
              :value="u.status"
              :aria-label="`Status for ${u.title}`"
              @change="setStatus(u, $event.target.value)"
            >
              <option v-for="s in STATUSES" :key="s.value" :value="s.value">{{ s.value }}</option>
            </select>
            <button class="btn-ghost" @click="startEdit(u)">Edit</button>
            <button class="btn-ghost" @click="toggleActive(u)">
              {{ u.is_active ? 'Deactivate' : 'Reactivate' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.panel {
  background: var(--bg-card);
  padding: var(--space-lg);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-default);
}
.unit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-md);
  flex-wrap: wrap;
}
.header-side {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}
.inline-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.875rem;
}
.unit-grid {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: var(--space-lg);
}
@media (max-width: 900px) {
  .unit-grid { grid-template-columns: 1fr; }
}
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: var(--space-sm);
}
.hint {
  font-size: 0.8125rem;
  margin-top: var(--space-sm);
}
.form-error {
  color: var(--color-danger, #e05252);
  margin-top: var(--space-md);
}
.actions {
  display: flex;
  gap: var(--space-sm);
}
.unit-item {
  border-bottom: 1px solid var(--border-subtle);
  padding: var(--space-sm) 0;
}
.unit-item:last-child { border-bottom: none; }
.unit-item.inactive { opacity: 0.55; }
.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-sm);
}
.item-meta { font-size: 0.875rem; }
.item-actions {
  display: flex;
  gap: var(--space-sm);
  align-items: center;
}
</style>
