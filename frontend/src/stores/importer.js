import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api/client'

/**
 * The curriculum importer — the bulk half of ingest (the task form is the
 * single-item half). CSV text goes up inside a JSON body; the file never
 * leaves the browser as an upload, because the backend deliberately has no
 * upload endpoint (H-06) and the importer must not be the thing that quietly
 * reopens that decision.
 *
 * No trailing slash on these paths: they are actions on a fixed resource,
 * not collection routes, and the backend defines them slash-less — so unlike
 * /tasks/ there is no 307 redirect to provoke.
 */
export const useImporterStore = defineStore('importer', () => {
  const validating = ref(false)
  const committing = ref(false)

  async function validate(csvText) {
    validating.value = true
    try {
      return await api.post('/curriculum/validate', { csv_text: csvText })
    } finally {
      validating.value = false
    }
  }

  async function commit(csvText) {
    committing.value = true
    try {
      return await api.post('/curriculum/commit', { csv_text: csvText })
    } finally {
      committing.value = false
    }
  }

  async function rollback(importId, force = false) {
    return await api.post('/curriculum/rollback', { import_id: importId, force })
  }

  return { validating, committing, validate, commit, rollback }
})
