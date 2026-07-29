import fs from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)))
const output = path.join(root, "src", "api", "generated")
const required = ["client.gen.ts", "sdk.gen.ts", "types.gen.ts"]
for (const name of required) {
  if (!fs.existsSync(path.join(output, name))) {
    throw new Error(`OpenAPI generation missing ${name}`)
  }
}
const generatedFiles = fs
  .readdirSync(output)
  .filter((name) => name.endsWith(".ts"))
if (generatedFiles.length < required.length) {
  throw new Error("OpenAPI generation produced an incomplete client")
}
console.log(`OpenAPI generated files: ${generatedFiles.length}`)
