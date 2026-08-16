import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import './style.css'
import './assets/styles/variables.css'
import './assets/styles/main.css'
import './assets/styles/components.css'
import App from './App.vue'
import { useErrorsStore } from './stores/errors'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// The store has to be resolved after pinia is installed, but before the
// handlers below can use it.
const errors = useErrorsStore(pinia)

/**
 * Vue swallows errors thrown inside component handlers unless this is set: it
 * logs to the console and carries on, which on a tablet means the button
 * simply does nothing and nobody finds out. Everything surfaces now.
 */
app.config.errorHandler = (error, instance, info) => {
  console.error(`Vue error (${info}):`, error)
  errors.report(error?.message || 'Something went wrong.', { requestId: error?.requestId })
}

// A rejected promise nobody awaited -- the most common shape of a silent
// failure here, since most API calls are fire-and-forget from a handler.
window.addEventListener('unhandledrejection', (event) => {
  const reason = event.reason
  console.error('Unhandled rejection:', reason)
  // An expired session already redirects to /login and explains itself; a
  // toast on top of that is noise. Matched on the flag the client sets rather
  // than on the message text, which would break the moment the wording changed.
  if (reason?.sessionExpired) return
  errors.report(reason?.message || 'Something went wrong.', { requestId: reason?.requestId })
})

app.mount('#app')
