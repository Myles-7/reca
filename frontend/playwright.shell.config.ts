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

if (process.platform === "win32") {
  process.env.PATH = `${path.dirname(bunExecutable)};${process.env.PATH ?? ""}`
}

export default defineConfig({
  testDir: "./tests",
  testMatch: "system-shell.spec.ts",
  fullyParallel: true,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:5173",
    ...devices["Desktop Chrome"],
  },
  webServer: {
    command: `"${bunExecutable}" run dev -- --host 127.0.0.1`,
    url: "http://127.0.0.1:5173",
    reuseExistingServer: !process.env.CI,
  },
})
