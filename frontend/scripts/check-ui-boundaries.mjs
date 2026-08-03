import fs from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)))
const featuresRoot = path.join(root, "src", "features")
const sourceExtensions = new Set([".js", ".jsx", ".ts", ".tsx"])
const forbiddenPrefixes = [
  "@/api/adapter",
  "@/api/generated",
  "@tanstack/react-query",
]
const forbiddenModules = new Set(["controller", "mutations", "queries"])

function importedModules(source) {
  const imports = []
  const patterns = [
    /\b(?:import|export)\s+(?:type\s+)?(?:[\s\S]*?\s+from\s+)?["']([^"']+)["']/g,
    /\bimport\s*\(\s*["']([^"']+)["']\s*\)/g,
    /\brequire\s*\(\s*["']([^"']+)["']\s*\)/g,
  ]
  for (const pattern of patterns) {
    for (const match of source.matchAll(pattern)) imports.push(match[1])
  }
  return imports
}

function moduleSegments(specifier) {
  return specifier
    .split(/[\\/]/)
    .filter((segment) => segment && segment !== "..")
}

export function forbiddenUiImports(source) {
  return importedModules(source).filter((specifier) => {
    if (
      forbiddenPrefixes.some(
        (prefix) => specifier === prefix || specifier.startsWith(`${prefix}/`),
      )
    ) {
      return true
    }
    return moduleSegments(specifier).some((segment) =>
      forbiddenModules.has(segment.replace(/\.[^.]+$/, "")),
    )
  })
}

function visit(directory, violations) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const target = path.join(directory, entry.name)
    if (entry.isDirectory()) {
      visit(target, violations)
      continue
    }
    if (!sourceExtensions.has(path.extname(entry.name))) continue
    const imports = forbiddenUiImports(fs.readFileSync(target, "utf8"))
    if (imports.length > 0) {
      violations.push({ file: path.relative(root, target), imports })
    }
  }
}

function findUiDirectories(directory, uiDirectories) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue
    const target = path.join(directory, entry.name)
    if (entry.name === "ui") {
      uiDirectories.push(target)
      continue
    }
    findUiDirectories(target, uiDirectories)
  }
}

export function scanUiBoundaries(
  featuresDirectory = featuresRoot,
  relativeTo = root,
) {
  const violations = []
  if (!fs.existsSync(featuresDirectory)) return violations
  const uiDirectories = []
  findUiDirectories(featuresDirectory, uiDirectories)
  for (const uiDirectory of uiDirectories) {
    const scopedViolations = []
    visit(uiDirectory, scopedViolations)
    violations.push(
      ...scopedViolations.map(({ file, imports }) => ({
        file: path.relative(relativeTo, path.resolve(root, file)),
        imports,
      })),
    )
  }
  return violations
}

const isCli = process.argv[1]
  ? path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
  : false

if (isCli) {
  const violations = scanUiBoundaries()
  if (violations.length > 0) {
    const details = violations
      .map(({ file, imports }) => `${file}: ${imports.join(", ")}`)
      .join("\n")
    throw new Error(`UI ownership boundary violations:\n${details}`)
  }
  console.log("UI ownership boundary guard: clean")
}
