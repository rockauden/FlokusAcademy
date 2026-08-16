<script setup>
import SkeletonBlock from '../common/SkeletonBlock.vue'

/**
 * Placeholder for a TaskCard.
 *
 * Reuses the real `.task-card` class rather than re-describing its box, so the
 * padding, radius, left border and margin cannot drift apart from the real
 * card and start causing a jump when the content swaps in.
 */
</script>

<template>
  <div class="task-card skeleton-card">
    <div class="task-header">
      <div class="title-section">
        <SkeletonBlock width="1.25rem" height="1.25rem" radius="50%" />
        <SkeletonBlock width="11rem" height="1.05rem" />
      </div>
      <div class="meta-section">
        <!-- 1.7rem, not 1.4rem: the real badges are the tallest thing in the
             header, so they set the card's height. Measured at 1.4rem the
             placeholder came out 54px against the real card's 59px, and five
             pixels per card is a visible shift once three of them swap out. -->
        <SkeletonBlock width="2.75rem" height="1.7rem" radius="999px" />
        <SkeletonBlock width="2rem" height="1.7rem" radius="999px" />
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Matches TaskCard's own header layout so the bars land where the real text,
   emoji and badges will be. */
.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.title-section {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}
.meta-section {
  display: flex;
  align-items: center;
  gap: var(--space-xs, 0.35rem);
}
/* The real card lifts on hover; a placeholder should not invite the pointer. */
.skeleton-card {
  cursor: default;
}
.skeleton-card:hover {
  transform: none;
  box-shadow: var(--shadow-card);
}
</style>
