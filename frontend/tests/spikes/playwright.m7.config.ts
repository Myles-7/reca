import { defineConfig, devices } from "@playwright/test"

export default defineConfig({
  testDir: ".",
  testMatch: "m7-react-flow-spike.spec.ts",
  reporter: "line",
  use: {
    baseURL: process.env.RECA_M7_SPIKE_BASE_URL ?? "http://127.0.0.1:5178",
    ...devices["Desktop Chrome"],
  },
})
