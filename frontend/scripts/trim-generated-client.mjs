import { readdir, readFile, writeFile } from "node:fs/promises"
import path from "node:path"

const clientDirectory = path.resolve("src/client")
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
