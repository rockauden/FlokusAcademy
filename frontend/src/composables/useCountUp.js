import { ref, watch, onUnmounted } from 'vue'

/**
 * Ease a displayed number toward a target instead of snapping to it.
 *
 * XP jumping from 20 to 30 the instant a request returns reads as a data
 * refresh. The same change counted up over half a second reads as something
 * having been earned, which is the entire point of the number being on screen.
 *
 * Respects prefers-reduced-motion: the value is set directly, with no
 * animation frames scheduled at all. It is also checked live rather than once
 * at setup, so changing the OS setting takes effect without a reload.
 */
export function useCountUp(source, { duration = 650 } = {}) {
  const toNumber = (value) => {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : 0
  }

  const displayed = ref(toNumber(source.value))
  let frame = null

  function prefersReducedMotion() {
    return typeof window !== 'undefined'
      && typeof window.matchMedia === 'function'
      && window.matchMedia('(prefers-reduced-motion: reduce)').matches
  }

  function cancel() {
    if (frame !== null) {
      cancelAnimationFrame(frame)
      frame = null
    }
  }

  function animateTo(target) {
    cancel()

    const from = displayed.value
    const distance = target - from

    // Nothing to show, or the user asked for no motion.
    if (distance === 0 || duration <= 0 || prefersReducedMotion()) {
      displayed.value = target
      return
    }

    const started = performance.now()

    const step = (now) => {
      const elapsed = now - started
      const progress = Math.min(elapsed / duration, 1)
      // easeOutCubic: quick off the mark, settling gently rather than stopping
      // dead, which is what makes it feel like an arrival.
      const eased = 1 - Math.pow(1 - progress, 3)

      displayed.value = Math.round(from + distance * eased)

      if (progress < 1) {
        frame = requestAnimationFrame(step)
      } else {
        displayed.value = target
        frame = null
      }
    }

    frame = requestAnimationFrame(step)
  }

  watch(source, (next) => animateTo(toNumber(next)))
  onUnmounted(cancel)

  return displayed
}
