import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api/client'

/**
 * Whether the AI tutor is switched on.
 *
 * The server owns this answer (`FLOKI_ENABLED` in the backend's config), and
 * the client has to ask before it offers a chat box — otherwise the only way
 * to find out the tutor is off is to type a question and get an error, which
 * on the student side is a crash screen for a completely ordinary state.
 *
 * `enabled` starts as null, meaning "not known yet", rather than false. That
 * distinction matters: rendering "Floki is resting" while the answer is still
 * in flight would assert something that might not be true, and the student
 * side is not allowed to do that. Callers render nothing until it is a boolean.
 */
export const useFlokiStore = defineStore('floki', () => {
  const enabled = ref(null)

  async function fetchStatus() {
    // Already answered once this session; the flag cannot change without a
    // redeploy, so there is nothing to gain from asking again on every mount.
    if (enabled.value !== null) return enabled.value

    try {
      const data = await api.get('/ai/status')
      enabled.value = !!(data && data.enabled)
    } catch {
      // A failed check must not put a broken tutor in front of the child, and
      // must not take the rest of his screen down either. Assume off.
      enabled.value = false
    }
    return enabled.value
  }

  return { enabled, fetchStatus }
})
