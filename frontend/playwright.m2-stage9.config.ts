import path from "node:path"
import { defineConfig, devices } from "@playwright/test"

const bunExecutable =
  process.platform === "win32"
    ? path.join(
        process.env.APPDATA ?? "",
        "npm",
        "node_modules",
        "bun",
        "bin",
        "bun.exe",
      )
    : "bun"
const port = Number(process.env.RECA_PLAYWRIGHT_PORT ?? "5182")
const baseURL = `http://127.0.0.1:${port}`
const apiURL = process.env.M2_STAGE9_API_URL ?? "http://127.0.0.1:8001"

if (process.platform === "win32") {
  process.env.PATH = `${path.dirname(bunExecutable)};${process.env.PATH ?? ""}`
}

export default defineConfig({
  testDir: "./tests",
  testMatch: "m2-stage9-vertical.spec.ts",
  workers: 1,
  reporter: "list",
  use: {
    baseURL,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    ...devices["Desktop Chrome"],
  },
  webServer: {
    command: `"${bunExecutable}" run dev -- --host 127.0.0.1 --port ${port} --strictPort`,
    env: { VITE_API_URL: apiURL },
    url: baseURL,
    reuseExistingServer: false,
  },
})
