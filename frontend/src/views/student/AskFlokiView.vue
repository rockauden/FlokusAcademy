<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api/client'
import { useFlokiStore } from '../../stores/floki'

const sessionId = 'sonny_chat_1'
const messages = ref([])
const input = ref('')
const loading = ref(false)
const persona = ref('Socratic Tutor')

// The tutor can be switched off server-side. Ask first, and render nothing
// either way until the answer arrives — see stores/floki.js for why the
// unknown state is not the same as "off".
const floki = useFlokiStore()

onMounted(async () => {
  const available = await floki.fetchStatus()
  if (!available) return

  try {
    const history = await api.get(`/ai/history/${sessionId}`)
    // The API returns rows shaped { sender, message }; the template renders
    // { role, content }. Without this mapping every bubble renders empty.
    // The API stores role-based senders ('student' / 'assistant'). Older rows
    // used the child's first name, so treat anything that isn't the assistant
    // as the student.
    messages.value = Array.isArray(history)
      ? history.map(h => ({
          role: h.sender === 'assistant' || h.sender === 'Floki' ? 'assistant' : 'user',
          content: h.message
        }))
      : []
  } catch (e) {
    console.error(e)
  }
})

async function sendMessage(text) {
  const msg = text || input.value
  if (!msg.trim() || loading.value) return

  messages.value.push({ role: 'user', content: msg })
  input.value = ''
  loading.value = true

  try {
    const res = await api.post('/ai/chat', {
      session_id: sessionId,
      message: msg,
      persona: persona.value
    })
    messages.value.push({ role: 'assistant', content: res.message })
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function quickAsk(topic) {
  sendMessage(`Can you help me with ${topic}?`)
}
</script>

<template>
  <div class="chat-view">
    <!-- Nothing at all until the server has answered. A flash of "resting"
         that turns into a chat box reads as a glitch. -->
    <div v-if="floki.enabled === false" class="resting">
      <div class="resting-icon" aria-hidden="true">💤</div>
      <h2>Floki is having a rest</h2>
      <p>Your dad will wake him up when he's ready.</p>
      <p class="resting-sub">Everything else still works — go and finish your quests!</p>
      <router-link to="/student/quests" class="btn-primary">Back to my quests</router-link>
    </div>

    <template v-else-if="floki.enabled === true">
    <header class="chat-header">
      <h2>Floki AI Tutor 💬</h2>
      <span class="persona-badge">Persona: {{ persona }}</span>
    </header>

    <div class="quick-topics">
      <button class="btn-ghost" @click="quickAsk('Math')">🧮 Math Helper</button>
      <button class="btn-ghost" @click="quickAsk('Science')">🧪 Science Guide</button>
      <button class="btn-ghost" @click="quickAsk('a Boss Fight')">👑 Boss Fight Tips</button>
      <button class="btn-ghost" @click="quickAsk('a Riddle')">🧩 Riddle Time</button>
    </div>

    <div class="chat-window">
      <div v-for="(msg, idx) in messages" :key="idx" class="message-wrapper" :class="msg.role">
        <div class="bubble">{{ msg.content }}</div>
      </div>
      <div v-if="loading" class="message-wrapper assistant">
        <div class="bubble typing">Floki is thinking...</div>
      </div>
    </div>

    <div class="chat-input-area">
      <input 
        type="text" 
        v-model="input" 
        @keyup.enter="sendMessage()" 
        placeholder="Ask Floki anything..." 
      />
      <button class="btn-primary" @click="sendMessage()" :disabled="loading">Send</button>
    </div>
    </template>
  </div>
</template>

<style scoped>
/* The resting state. Centred, roomy and quiet — it is a normal state of the
   app, not a failure, so it must not borrow any of the error styling. */
.resting {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: var(--space-sm);
  flex: 1;
  padding: var(--space-lg);
}
.resting-icon {
  font-size: 3.5rem;
  line-height: 1;
  margin-bottom: var(--space-sm);
}
.resting h2 {
  margin: 0;
}
.resting p {
  margin: 0;
  color: var(--text-muted);
  max-width: 34ch;
}
.resting-sub {
  margin-bottom: var(--space-md) !important;
}

.chat-view {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 100px);
  max-width: 800px;
  margin: 0 auto;
}
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-md);
}
.persona-badge {
  font-size: 0.875rem;
  color: var(--accent-blue);
  background: rgba(99,179,237,0.1);
  padding: 4px 8px;
  border-radius: var(--radius-pill);
}

.quick-topics {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
  overflow-x: auto;
  padding-bottom: 4px;
}
.quick-topics button { white-space: nowrap; }

.chat-window {
  flex: 1;
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  margin-bottom: var(--space-md);
}

.message-wrapper {
  display: flex;
  width: 100%;
}
.message-wrapper.user { justify-content: flex-end; }
.message-wrapper.assistant { justify-content: flex-start; }

.bubble {
  max-width: 80%;
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
  line-height: 1.5;
}
.user .bubble {
  background: var(--accent-blue);
  color: #fff;
  border-bottom-right-radius: 4px;
}
.assistant .bubble {
  background: var(--bg-input);
  color: var(--text-primary);
  border-bottom-left-radius: 4px;
}

.typing { font-style: italic; opacity: 0.7; }

.chat-input-area {
  display: flex;
  gap: var(--space-sm);
}
.chat-input-area input {
  flex: 1;
}
</style>
