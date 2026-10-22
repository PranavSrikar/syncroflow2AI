import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/browser',
  workers: 1,
  use: { baseURL: process.env.SYNCHROFLOW_TEST_URL || 'http://127.0.0.1:3017', channel: process.env.SYNCHROFLOW_BROWSER_CHANNEL || 'msedge', headless: true },
  webServer: process.env.SYNCHROFLOW_EXTERNAL_SERVERS === '1' ? undefined : [
    {
      command: '.venv\\Scripts\\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8017',
      cwd: './backend', env: { DEBUG: 'false' },
      url: 'http://127.0.0.1:8017/api/v1/health', reuseExistingServer: false,
    },
    {
      command: 'npm.cmd run dev -- --host 127.0.0.1 --port 3017',
      env: { VITE_BACKEND_API_URL: 'http://127.0.0.1:8017/api/v1', SYNCHROFLOW_VITE_CACHE_DIR: 'node_modules/.vite-e2e' },
      url: 'http://127.0.0.1:3017', reuseExistingServer: false,
    },
  ],
});

