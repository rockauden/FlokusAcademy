<script setup>
import { ref, computed, onUnmounted } from 'vue'

const props = defineProps({
  taskId: [String, Number],
  defaultMinutes: { type: Number, default: 15 }
})

const emit = defineEmits(['complete'])

const targetMinutes = ref(props.defaultMinutes)
const timeLeftSeconds = ref(props.defaultMinutes * 60)
const isRunning = ref(false)
const isDone = ref(false)
let timer = null

const displayTime = computed(() => {
  const m = Math.floor(timeLeftSeconds.value / 60)
  const s = timeLeftSeconds.value % 60
  return `${m}:${s.toString().padStart(2, '0')}`
})

const colorClass = computed(() => {
  if (timeLeftSeconds.value > 300) return 'blue'
  if (timeLeftSeconds.value > 60) return 'orange'
  return 'red'
})

function startTimer() {
  if (!isRunning.value) {
    if (timeLeftSeconds.value <= 0) {
      timeLeftSeconds.value = targetMinutes.value * 60
    }
    isRunning.value = true
    isDone.value = false
    timer = setInterval(() => {
      if (timeLeftSeconds.value > 0) {
        timeLeftSeconds.value--
      } else {
        stopTimer()
        isDone.value = true
      }
    }, 1000)
  }
}

function stopTimer() {
  isRunning.value = false
  if (timer) clearInterval(timer)
}

function resetTimer() {
  stopTimer()
  timeLeftSeconds.value = targetMinutes.value * 60
  isDone.value = false
}

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <div class="focus-timer">
    <div class="timer-setup" v-if="!isRunning && timeLeftSeconds === targetMinutes * 60 && !isDone">
      <label>Focus Time (min):</label>
      <input type="number" v-model="targetMinutes" min="1" max="60" @change="resetTimer" style="width: 80px;" />
      <button class="btn-primary" @click="startTimer">Start Sprint</button>
    </div>
    
    <div v-else class="timer-display">
      <div class="countdown" :class="colorClass">{{ displayTime }}</div>
      <div class="controls">
        <button v-if="isRunning" class="btn-ghost" @click="stopTimer">Pause</button>
        <button v-else-if="!isDone" class="btn-primary" @click="startTimer">Resume</button>
        <button class="btn-ghost" @click="resetTimer">Reset</button>
      </div>
    </div>
    
    <div v-if="isDone" class="done-message">
      Sprint Complete! Awesome focus.
    </div>
  </div>
</template>

<style scoped>
.focus-timer {
  background: var(--bg-input);
  padding: var(--space-md);
  border-radius: var(--radius-sm);
  text-align: center;
}
.timer-setup {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
}
.countdown {
  font-size: 3rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  line-height: 1;
  margin-bottom: var(--space-sm);
}
.countdown.blue { color: var(--accent-blue); }
.countdown.orange { color: var(--accent-orange); }
.countdown.red { color: var(--accent-red); animation: pulse 1s infinite; }
.controls {
  display: flex;
  gap: var(--space-sm);
  justify-content: center;
}
.done-message {
  color: var(--accent-green);
  font-weight: bold;
  margin-top: var(--space-sm);
}
</style>
