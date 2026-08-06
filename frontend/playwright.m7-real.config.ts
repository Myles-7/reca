import { defineConfig, devices } from "@playwright/test"

export default defineConfig({
  testDir: "./tests",
  testMatch: "projects-m7-real-api.spec.ts",
  timeout: 120_000,
  reporter: "line",
  use: {
    ...devices["Desktop Chrome"],
    trace: "retain-on-failure",
  },
})
