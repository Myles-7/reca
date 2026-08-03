import fs from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)))
const sourceRoot = path.join(root, "src")
const sourceExtensions = new Set([".js", ".jsx", ".ts", ".tsx"])
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

function isInside(target, directory) {
  const relative = path.relative(directory, target)
  return (
    relative === "" ||
    (!relative.startsWith("..") && !path.isAbsolute(relative))
  )
}

function isDesignOnlyImport(specifier) {
  return specifier
    .split(/[\\/]/)
    .some((segment) => segment === "fixtures" || segment === "design-preview")
}

function isFixtureDataLayerImport(specifier) {
  const segments = specifier
    .split(/[\\/]/)
    .filter((segment) => segment && segment !== "..")
    .map((segment) => segment.replace(/\.[^.]+$/, ""))
  return segments.some((segment) =>
    [
      "api",
      "adapter",
      "generated",
      "cache",
      "containers",
      "controller",
      "mutations",
      "queries",
    ].includes(segment),
  )
}

function isFeatureFixtureFile(target, directory) {
  const segments = path.relative(directory, target).split(path.sep)
  return segments[0] === "features" && segments.includes("fixtures")
}

export function scanProductionMockViolations(
  directory = sourceRoot,
  relativeTo = root,
) {
  const violations = []
  const previewRoot = path.join(directory, "design-preview")

  function visit(current) {
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      const target = path.join(current, entry.name)
      if (entry.isDirectory()) {
        visit(target)
        continue
      }
      if (!sourceExtensions.has(path.extname(entry.name))) continue
      if (isInside(target, previewRoot)) {
        continue
      }
      const source = fs.readFileSync(target, "utf8")
      if (isFeatureFixtureFile(target, directory)) {
        const imports = importedModules(source).filter(isFixtureDataLayerImport)
        if (imports.length > 0) {
          violations.push({
            file: path.relative(relativeTo, target),
            imports: [...new Set(imports)],
          })
        }
        continue
      }
      const imports = importedModules(source).filter(isDesignOnlyImport)
      if (source.includes("M1_CONTRACT_MOCK")) imports.push("M1_CONTRACT_MOCK")
      if (imports.length > 0) {
        violations.push({
          file: path.relative(relativeTo, target),
          imports: [...new Set(imports)],
        })
      }
    }
  }

  if (fs.existsSync(directory)) visit(directory)
  return violations
}

const isCli = process.argv[1]
  ? path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
  : false

if (isCli) {
  const violations = scanProductionMockViolations()
  if (violations.length > 0) {
    const details = violations
      .map(({ file, imports }) => `${file}: ${imports.join(", ")}`)
      .join("\n")
    throw new Error(`Production source references design fixtures:\n${details}`)
  }
  console.log("Production mock guard: clean")
}
