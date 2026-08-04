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
const port = Number(process.env.RECA_PLAYWRIGHT_PORT ?? "5173")
const baseURL = `http://127.0.0.1:${port}`

if (process.platform === "win32") {
  process.env.PATH = `${path.dirname(bunExecutable)};${process.env.PATH ?? ""}`
}

export default defineConfig({
  testDir: "./tests",
  testMatch: ["system-shell.spec.ts", "projects-*.spec.ts", "m3-*.spec.ts"],
  fullyParallel: true,
  reporter: "list",
  use: {
    baseURL,
    ...devices["Desktop Chrome"],
  },
  webServer: {
    command: `"${bunExecutable}" run dev -- --host 127.0.0.1 --port ${port} --strictPort`,
    url: baseURL,
    reuseExistingServer: !process.env.CI,
  },
})
