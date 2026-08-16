import { defineConfig, devices } from '@playwright/test'
import path from 'path'
import { fileURLToPath } from 'url'

// Deliberately not 8000: that is the dev backend's port, and a test run must
// never point at a database someone is actually using.
const API_PORT = 8123
const WEB_PORT = 5174

// package.json sets "type": "module", so __dirname does not exist here.
const HERE = path.dirname(fileURLToPath(import.meta.url))
const BACKEND_DIR = path.resolve(HERE, '../backend')
const PYTHON = process.platform === 'win32'
  ? path.join(BACKEND_DIR, '.venv', 'Scripts', 'python.exe')
  : path.join(BACKEND_DIR, '.venv', 'bin', 'python')

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  expect: { timeout: 10_000 },

  // One API and one database are shared by the whole run, and several specs
  // create tasks, so parallel workers would see each other's rows.
  fullyParallel: false,
  workers: 1,

  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['github'], ['list']] : [['list']],

  use: {
    baseURL: `http://localhost:${WEB_PORT}`,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],

  webServer: [
    {
      // Builds a throwaway SQLite database by running the real migration
      // chain, seeds both accounts, then serves. Waiting on /health/ready
      // rather than /health means tests only start once the database is
      // genuinely reachable, not merely once the process is up.
      command: `"${PYTHON}" -m scripts.run_test_api --port ${API_PORT}`,
      cwd: BACKEND_DIR,
      url: `http://localhost:${API_PORT}/health/ready`,
      reuseExistingServer: false,
      stdout: 'pipe',
      stderr: 'pipe',
      timeout: 120_000,
    },
    {
      command: `npm run dev -- --port ${WEB_PORT} --strictPort`,
      url: `http://localhost:${WEB_PORT}`,
      reuseExistingServer: false,
      timeout: 60_000,
      env: {
        // Empty so the app uses relative /api and goes through the proxy
        // below, regardless of what the developer's .env happens to contain.
        VITE_API_URL: '',
        VITE_PROXY_TARGET: `http://localhost:${API_PORT}`,
      },
    },
  ],
})
