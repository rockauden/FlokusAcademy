<script setup>
import { onUnmounted, ref } from 'vue'

/**
 * A short particle burst for a finished task.
 *
 * Canvas rather than DOM nodes or hand-written SVG: a few dozen particles as
 * elements would mean a few dozen layout and paint operations per frame on a
 * tablet, and the shapes here are generated, not drawn.
 *
 * It is entirely decorative, so it is inert under prefers-reduced-motion --
 * not a faster version, none at all. It also never intercepts input; a child
 * tapping the next task mid-burst must not be blocked by confetti.
 */
const canvas = ref(null)
const active = ref(false)

let frame = null
let particles = []
let startedAt = 0

const DURATION = 1100
const GRAVITY = 0.00045

// Warm palette; the boss variant adds gold and is simply denser and faster.
const COLORS = ['#facc15', '#fb923c', '#4ade80', '#60a5fa', '#c084fc']

function prefersReducedMotion() {
  return typeof window !== 'undefined'
    && typeof window.matchMedia === 'function'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

function stop() {
  if (frame !== null) {
    cancelAnimationFrame(frame)
    frame = null
  }
  active.value = false
  particles = []
}

function spawn(count, speed) {
  const element = canvas.value
  const width = element.clientWidth
  const originX = width / 2
  const originY = element.clientHeight * 0.45

  particles = Array.from({ length: count }, () => {
    // Biased upward: things thrown in celebration go up before they fall.
    const angle = (-Math.PI / 2) + (Math.random() - 0.5) * Math.PI * 1.1
    const velocity = speed * (0.55 + Math.random() * 0.65)
    return {
      x: originX,
      y: originY,
      vx: Math.cos(angle) * velocity,
      vy: Math.sin(angle) * velocity,
      size: 3 + Math.random() * 4,
      spin: (Math.random() - 0.5) * 0.25,
      angle: Math.random() * Math.PI,
      color: COLORS[Math.floor(Math.random() * COLORS.length)],
    }
  })
}

function draw(now) {
  const element = canvas.value
  if (!element) return stop()

  const elapsed = now - startedAt
  const progress = elapsed / DURATION
  if (progress >= 1) return stop()

  const context = element.getContext('2d')
  const ratio = window.devicePixelRatio || 1

  // Size the backing store to the device pixels so the shapes are not blurry.
  const width = element.clientWidth
  const height = element.clientHeight
  if (element.width !== width * ratio || element.height !== height * ratio) {
    element.width = width * ratio
    element.height = height * ratio
  }

  context.setTransform(ratio, 0, 0, ratio, 0, 0)
  context.clearRect(0, 0, width, height)
  context.globalAlpha = 1 - progress * progress

  for (const particle of particles) {
    particle.x += particle.vx
    particle.y += particle.vy
    particle.vy += GRAVITY * elapsed
    particle.angle += particle.spin

    context.save()
    context.translate(particle.x, particle.y)
    context.rotate(particle.angle)
    context.fillStyle = particle.color
    context.fillRect(-particle.size / 2, -particle.size / 2, particle.size, particle.size * 0.6)
    context.restore()
  }

  frame = requestAnimationFrame(draw)
}

/** Called by the parent when a task is finished. */
function fire({ boss = false } = {}) {
  if (prefersReducedMotion() || !canvas.value) return

  stop()
  active.value = true

  // Let the element get its layout size before measuring it.
  requestAnimationFrame(() => {
    if (!canvas.value) return
    spawn(boss ? 70 : 32, boss ? 4.2 : 3)
    startedAt = performance.now()
    frame = requestAnimationFrame(draw)
  })
}

onUnmounted(stop)
defineExpose({ fire })
</script>

<template>
  <canvas
    ref="canvas"
    class="burst"
    :class="{ 'is-active': active }"
    aria-hidden="true"
  ></canvas>
</template>

<style scoped>
.burst {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  /* Never swallow a tap. */
  pointer-events: none;
  z-index: 900;
  opacity: 0;
}
.burst.is-active {
  opacity: 1;
}
</style>
