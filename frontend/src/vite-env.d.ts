/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_APP_ENV?: "local" | "test" | "demo" | "production"
  readonly VITE_DEMO_MODE?: "true" | "false"
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
