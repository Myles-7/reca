import { mkdir, readdir, readFile, writeFile } from "node:fs/promises"
import path from "node:path"
import { fileURLToPath } from "node:url"

const frontendRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
)
const clientDirectory = path.join(frontendRoot, "src", "client")
await mkdir(clientDirectory, { recursive: true })
const files = await readdir(clientDirectory)

await Promise.all(
  files
    .filter((file) => file.endsWith(".gen.ts"))
    .map(async (file) => {
      const filePath = path.join(clientDirectory, file)
      const source = await readFile(filePath, "utf8")
      const normalized = source.replace(/[\t ]+$/gm, "")
      if (normalized !== source) {
        await writeFile(filePath, normalized, "utf8")
      }
    }),
)
