<script setup>
import { ref, computed } from 'vue'
import { useImporterStore } from '../../stores/importer'

/**
 * The import screen: choose a CSV → server-validated preview → commit → undo.
 *
 * The flow is a checkpoint, not a spreadsheet editor. Good rows preview in a
 * grid; rows with errors expose their raw CSV line for an in-place fix, and
 * every edit goes back through the server's validator — the client never
 * decides for itself that a row is now fine. Anything bigger than a typo
 * belongs back in the workbook, which stays the place curriculum is
 * maintained.
 *
 * Commit stays disabled while any error remains: there is no partial import,
 * so there is nothing honest the button could do with a half-valid file.
 */
const store = useImporterStore()

const fileName = ref('')
// The file as physical lines, so an error's row number indexes straight into
// it (spreadsheet row N = line N; the header is row 1, line 0). A quoted cell
// containing a newline would break that mapping — none of the curriculum
// fields are multiline, and the validator would surface the mangled row.
const lines = ref([])
const report = ref(null)
const committed = ref(null)
const error = ref('')
// Undo is a two-step control, then a third when completed work blocks it —
// never a browser confirm() dialog.
const undoArmed = ref(false)
const undoBlocked = ref('')
const undone = ref(null)

const csvText = computed(() => lines.value.join('\n'))
const canCommit = computed(() =>
  report.value && report.value.errors.length === 0 && report.value.total_rows > 0 && !store.committing
)

function reset() {
  report.value = null
  committed.value = null
  error.value = ''
  undoArmed.value = false
  undoBlocked.value = ''
  undone.value = null
}

async function onFileChange(event) {
  const file = event.target.files && event.target.files[0]
  if (!file) return
  reset()
  fileName.value = file.name
  const text = await file.text()
  lines.value = text.split(/\r\n|\n|\r/)
  await revalidate()
}

async function revalidate() {
  error.value = ''
  try {
    report.value = await store.validate(csvText.value)
  } catch (e) {
    report.value = null
    error.value = e.message
  }
}

async function commitImport() {
  error.value = ''
  try {
    committed.value = await store.commit(csvText.value)
    report.value = committed.value
  } catch (e) {
    error.value = e.message
  }
}

async function undoImport(force = false) {
  error.value = ''
  undoBlocked.value = ''
  try {
    undone.value = await store.rollback(committed.value.import_id, force)
    undoArmed.value = false
  } catch (e) {
    // A 409 here means completed work sits under the import. Surface it and
    // offer the forced path, which reverses the XP through the ledger first.
    if (String(e.message).includes('Completed work')) {
      undoBlocked.value = e.message
    } else {
      error.value = e.message
    }
  }
}

function lineFor(row) {
  return lines.value[row - 1] ?? ''
}
function setLine(row, value) {
  lines.value[row - 1] = value
}
</script>

<template>
  <div class="import-view">
    <div class="page-header">
      <h1>Import Curriculum</h1>
      <p class="text-muted">
        One row per lesson; <code>program</code>, <code>unit</code> and <code>title</code> are required.
        Export a sheet of the curriculum workbook as CSV and choose it here. Importing never sets
        dates — everything arrives staged, invisible to the student until its unit is activated.
      </p>
    </div>

    <div class="card">
      <label class="file-pick">
        <input type="file" accept=".csv,text/csv" @change="onFileChange" />
      </label>
      <span v-if="fileName" class="file-name">{{ fileName }}</span>
      <span v-if="store.validating" class="text-muted">Checking…</span>
    </div>

    <p v-if="error" class="form-error">{{ error }}</p>

    <template v-if="report && !undone">
      <div class="card summary" data-testid="import-summary">
        <template v-if="!committed">
          Will create
          <strong>{{ report.new }}</strong> lesson{{ report.new === 1 ? '' : 's' }}
          <template v-if="report.updated"> · update <strong>{{ report.updated }}</strong></template>
          <template v-if="report.unchanged"> · leave <strong>{{ report.unchanged }}</strong> unchanged</template>
          <template v-if="report.programs_to_create.length">
            · new program{{ report.programs_to_create.length === 1 ? '' : 's' }}:
            {{ report.programs_to_create.join(', ') }}
          </template>
          <template v-if="report.units_to_create.length">
            · {{ report.units_to_create.length }} new unit{{ report.units_to_create.length === 1 ? '' : 's' }}
          </template>
          — <strong :class="report.errors.length ? 'err' : 'ok'">{{ report.errors.length }} error{{ report.errors.length === 1 ? '' : 's' }}</strong>
        </template>
        <template v-else>
          Imported: <strong>{{ committed.new }}</strong> new · {{ committed.updated }} updated ·
          {{ committed.unchanged }} unchanged. The student's day is unchanged — release units to
          schedule this work.
        </template>
      </div>

      <div v-if="report.errors.length" class="card errors" data-testid="import-errors">
        <h3>Fix these rows, then re-check</h3>
        <div v-for="issue in report.errors" :key="issue.row + issue.message" class="error-row">
          <p class="form-error">Row {{ issue.row }}: {{ issue.message }}</p>
          <input
            v-if="issue.row >= 1 && lineFor(issue.row) !== ''"
            class="line-edit"
            :value="lineFor(issue.row)"
            @input="setLine(issue.row, $event.target.value)"
          />
        </div>
        <button class="btn-primary" :disabled="store.validating" @click="revalidate">Re-check file</button>
      </div>

      <div v-if="report.rows.length" class="card">
        <div class="preview-scroll">
          <table class="preview">
            <thead>
              <tr><th>Row</th><th>Program</th><th>Unit</th><th>Lesson</th><th>Action</th></tr>
            </thead>
            <tbody>
              <tr v-for="r in report.rows" :key="r.row">
                <td class="num">{{ r.row }}</td>
                <td>{{ r.program }}</td>
                <td>{{ r.unit }}</td>
                <td>{{ r.title }}</td>
                <td><span class="chip" :class="r.action">{{ r.action }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="actions">
        <button
          v-if="!committed"
          class="btn-primary"
          data-testid="commit-import"
          :disabled="!canCommit"
          @click="commitImport"
        >
          {{ store.committing ? 'Importing…' : 'Import' }}
        </button>

        <template v-else>
          <span class="import-id">Import id: <code data-testid="import-id">{{ committed.import_id }}</code></span>
          <button v-if="!undoArmed" class="btn-ghost" @click="undoArmed = true">Undo this import</button>
          <button v-else class="btn-danger" data-testid="confirm-undo" @click="undoImport(false)">
            Really undo — delete {{ committed.new }} imported lesson{{ committed.new === 1 ? '' : 's' }}
          </button>
        </template>
      </div>

      <div v-if="undoBlocked" class="card errors">
        <p class="form-error">{{ undoBlocked }}</p>
        <button class="btn-danger" @click="undoImport(true)">
          Undo anyway — reverse the earned XP first
        </button>
      </div>
    </template>

    <div v-if="undone" class="card summary" data-testid="undo-summary">
      Undone: {{ undone.lessons_deleted }} lessons and {{ undone.assignments_deleted }} assignments
      removed<template v-if="undone.xp_reversed"> · {{ undone.xp_reversed }} XP reversed through the ledger</template>.
    </div>
  </div>
</template>

<style scoped>
.page-header p { max-width: 60ch; }
.card {
  background: var(--bg-secondary, rgba(255, 255, 255, 0.04));
  border: 1px solid var(--border-color, rgba(255, 255, 255, 0.08));
  border-radius: 8px;
  padding: var(--space-md);
  margin-top: var(--space-md);
}
.file-pick input { color: var(--text-primary); }
.file-name { margin-left: var(--space-sm); color: var(--text-secondary); }
.summary { line-height: 1.6; }
.summary .ok { color: var(--color-success, #48bb78); }
.summary .err { color: var(--color-danger, #e05252); }
.errors h3 { margin-top: 0; }
.error-row { margin-bottom: var(--space-md); }
.form-error { color: var(--color-danger, #e05252); margin: 0 0 var(--space-sm); }
.line-edit {
  width: 100%;
  font-family: monospace;
  font-size: 0.8125rem;
}
.preview-scroll { max-height: 420px; overflow: auto; }
table.preview { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
.preview th, .preview td {
  text-align: left;
  padding: 6px 10px;
  border-bottom: 1px solid var(--border-color, rgba(255, 255, 255, 0.08));
}
.preview .num { color: var(--text-secondary); }
.chip {
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: 999px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.chip.new { background: rgba(72, 187, 120, 0.15); color: var(--color-success, #48bb78); }
.chip.update { background: rgba(237, 176, 74, 0.15); color: #d99a2b; }
.chip.unchanged { background: rgba(255, 255, 255, 0.08); color: var(--text-secondary); }
.actions {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-top: var(--space-md);
}
.import-id { color: var(--text-secondary); font-size: 0.875rem; }
.btn-danger {
  background: var(--color-danger, #e05252);
  color: white;
  border: none;
  border-radius: 6px;
  padding: 8px 14px;
  cursor: pointer;
}
</style>
