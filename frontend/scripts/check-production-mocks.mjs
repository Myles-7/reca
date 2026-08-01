import fs from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)))
const sourceRoot = path.join(root, "src")
const forbidden = ["M1_CONTRACT_MOCK", "/fixtures/", "\\fixtures\\"]
const violations = []

function visit(directory) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const target = path.join(directory, entry.name)
    if (entry.isDirectory()) visit(target)
    else if (/\.(ts|tsx|js|jsx)$/.test(entry.name)) {
      const content = fs.readFileSync(target, "utf8")
      if (forbidden.some((marker) => content.includes(marker))) {
        violations.push(path.relative(root, target))
      }
    }
  }
}

visit(sourceRoot)
if (violations.length > 0) {
  throw new Error(
    `Production source imports contract mocks: ${violations.join(", ")}`,
  )
}
console.log("Production mock guard: clean")
