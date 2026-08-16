<script setup>
import { onErrorCaptured, ref } from 'vue'
import ErrorToasts from './components/common/ErrorToasts.vue'
import { useErrorsStore } from './stores/errors'

const errors = useErrorsStore()
const crashed = ref(false)

/**
 * A failed API call is not a broken page.
 *
 * onErrorCaptured sees both genuine render failures and rejections thrown out
 * of a child's onMounted -- and most of the latter are a fetch that failed.
 * Blanking the screen for those would turn a brief network blip into "the app
 * is broken", which is the overreaction version of the silent failures this
 * whole sprint exists to fix. Network and API errors get a toast and leave the
 * page alone; anything else is treated as a real render failure.
 */
function isApiFailure(error) {
  if (!error) return false
  if (error.requestId || typeof error.status === 'number') return true
  return error instanceof TypeError && /fetch|network/i.test(error.message || '')
}

onErrorCaptured((error) => {
  const apiFailure = isApiFailure(error)
  console.error(apiFailure ? 'API error reached the boundary:' : 'Render error captured:', error)

  errors.report(
    error?.message || 'Something went wrong while drawing this page.',
    { requestId: error?.requestId, fatal: !apiFailure },
  )

  if (!apiFailure) {
    crashed.value = true
  }

  // Stop propagation either way: without this Vue keeps unwinding and can
  // tear down the tree that is still perfectly usable.
  return false
})

function reload() {
  window.location.reload()
}
</script>

<template>
  <div v-if="crashed" class="crash">
    <h1>Something broke on this screen</h1>
    <p>The rest of the app is still running. Reloading usually fixes it.</p>
    <button class="btn-primary" @click="reload">Reload</button>
  </div>
  <router-view v-else />

  <ErrorToasts />
</template>

<style scoped>
.crash {
  max-width: 32rem;
  margin: 4rem auto;
  padding: 2rem;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  align-items: center;
}
</style>
