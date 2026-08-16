import { ref, watch, onUnmounted } from 'vue'

/**
 * Whether a loading placeholder should actually be on screen.
 *
 * Not simply `loading`, because showing a skeleton the instant a request
 * starts makes fast responses *worse*: the placeholder appears and vanishes
 * within a couple of frames, which reads as a flicker or a glitch rather than
 * as loading. Two rules fix that:
 *
 *   delay   -- nothing is shown for the first 200ms. A request that finishes
 *              inside that window shows no skeleton at all, which is correct;
 *              the user simply saw the content appear.
 *
 *   minimum -- once shown, it stays for at least 400ms. Without this, a
 *              request finishing at 210ms produces exactly the flicker the
 *              delay was meant to prevent, just shifted later.
 *
 * The result is that a skeleton only ever appears when there is a genuine wait,
 * and when it appears it is legible rather than a flash.
 */
export function useDelayedLoading(source, { delay = 200, minimum = 400 } = {}) {
  const visible = ref(false)

  let showTimer = null
  let hideTimer = null
  let shownAt = 0

  function clearTimers() {
    clearTimeout(showTimer)
    clearTimeout(hideTimer)
    showTimer = null
    hideTimer = null
  }

  watch(
    source,
    (loading) => {
      if (loading) {
        clearTimeout(hideTimer)
        hideTimer = null

        // Already on screen (a second load starting) -- leave it alone.
        if (visible.value || showTimer !== null) return

        showTimer = setTimeout(() => {
          visible.value = true
          shownAt = Date.now()
          showTimer = null
        }, delay)
        return
      }

      // Finished before the placeholder was ever shown: show nothing.
      if (showTimer !== null) {
        clearTimeout(showTimer)
        showTimer = null
        return
      }

      if (!visible.value) return

      const elapsed = Date.now() - shownAt
      const remaining = Math.max(minimum - elapsed, 0)

      if (remaining === 0) {
        visible.value = false
        return
      }

      hideTimer = setTimeout(() => {
        visible.value = false
        hideTimer = null
      }, remaining)
    },
    { immediate: true },
  )

  onUnmounted(clearTimers)

  return visible
}
