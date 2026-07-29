import path from "node:path"
import { fileURLToPath } from "node:url"
import { defineConfig } from "@hey-api/openapi-ts"

const frontendRoot = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  input: path.join(frontendRoot, "openapi.json"),
  output: {
    path: path.join(frontendRoot, "src", "api", "generated"),
    clean: true,
  },
  plugins: ["@hey-api/typescript", "@hey-api/client-fetch", "@hey-api/sdk"],
})
