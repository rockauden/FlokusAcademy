<script setup>
/**
 * One grey bar standing in for a piece of content that has not arrived.
 *
 * Sized in the caller rather than by a set of named variants, because the
 * whole value of a skeleton is that it occupies the same space the real thing
 * will -- a generic box that is the wrong size causes the layout jump it was
 * supposed to prevent.
 */
defineProps({
  width: { type: String, default: '100%' },
  height: { type: String, default: '1rem' },
  radius: { type: String, default: 'var(--radius-sm, 6px)' },
})
</script>

<template>
  <span
    class="skeleton"
    :style="{ width, height, borderRadius: radius }"
    aria-hidden="true"
  ></span>
</template>

<style scoped>
.skeleton {
  display: block;
  background: var(--bg-input, #232838);
  /* Never let a bar collapse to nothing when a flex parent squeezes it. */
  flex: none;
}

@media (prefers-reduced-motion: no-preference) {
  .skeleton {
    background: linear-gradient(
      90deg,
      var(--bg-input, #232838) 0%,
      var(--bg-card-hover, #2b3145) 50%,
      var(--bg-input, #232838) 100%
    );
    background-size: 200% 100%;
    animation: shimmer 1.4s ease-in-out infinite;
  }

  @keyframes shimmer {
    from { background-position: 200% 0; }
    to   { background-position: -200% 0; }
  }
}
</style>
