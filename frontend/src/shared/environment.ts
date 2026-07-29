export type PublicAppEnvironment = "local" | "test" | "demo" | "production"

const publicEnvironments: ReadonlySet<string> = new Set([
  "local",
  "test",
  "demo",
  "production",
])

function readAppEnvironment(value: string | undefined): PublicAppEnvironment {
  return publicEnvironments.has(value ?? "")
    ? (value as PublicAppEnvironment)
    : "local"
}

/**
 * Explicitly expose only browser-safe Vite variables to application code.
 * Server credentials must never use the VITE_ prefix or appear in this module.
 */
export const publicEnvironment = Object.freeze({
  apiUrl: import.meta.env.VITE_API_URL,
  appEnv: readAppEnvironment(import.meta.env.VITE_APP_ENV),
  demoMode: import.meta.env.VITE_DEMO_MODE === "true",
})
