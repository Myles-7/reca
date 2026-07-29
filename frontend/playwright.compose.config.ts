import { defineConfig, devices } from "@playwright/test"

export default defineConfig({
  testDir: "./tests",
  testMatch: "system-status-compose.spec.ts",
  reporter: "list",
  use: {
    baseURL: process.env.FRONTEND_BASE_URL ?? "http://127.0.0.1:5173",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    ...devices["Desktop Chrome"],
  },
})
