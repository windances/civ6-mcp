import { readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'

const root = new URL('..', import.meta.url).pathname.replace(/\/$/, '')
const failures = []

function check(condition, message) {
  if (!condition) failures.push(message)
}

function read(relativePath) {
  return readFileSync(join(root, relativePath), 'utf8')
}

function parseJson(relativePath) {
  try {
    return JSON.parse(read(relativePath))
  } catch (error) {
    failures.push(`${relativePath}: invalid JSON: ${error.message}`)
    return undefined
  }
}

const schemas = [
  'contracts/turn-snapshot.schema.json',
  'contracts/worker-proposal.schema.json',
  'contracts/execution-result.schema.json',
]

const orchestratorRuntime = [
  'dsh/orchestrator/contracts.mjs',
  'dsh/orchestrator/conflict-resolver.mjs',
  'dsh/orchestrator/action-ledger.mjs',
  'dsh/orchestrator/sole-writer-executor.mjs',
  'dsh/orchestrator/types.d.ts',
]

const contractFixtures = [
  'fixtures/dsh/valid-snapshot.json',
  'fixtures/dsh/valid-military-proposal.json',
  'fixtures/dsh/invalid-unknown-tool.json',
  'fixtures/dsh/invalid-stale-turn.json',
  'fixtures/dsh/invalid-missing-unit.json',
]

for (const path of schemas) {
  const schema = parseJson(path)
  if (schema) {
    check(schema.type === 'object', `${path}: root type must be object`)
    check(schema.additionalProperties === false, `${path}: must fail closed on unknown fields`)
    check(Array.isArray(schema.required) && schema.required.length > 0, `${path}: required fields missing`)
  }
}

for (const path of orchestratorRuntime) {
  try {
    check(statSync(join(root, path)).size > 100, `${path}: runtime artifact is unexpectedly short`)
  } catch (error) {
    failures.push(`${path}: missing: ${error.message}`)
  }
}

for (const path of contractFixtures) parseJson(path)

const workerSchema = parseJson('contracts/worker-proposal.schema.json')
const expectedWorkers = ['strategy', 'military-map', 'economy-cities', 'diplomacy-victory']
check(
  JSON.stringify(workerSchema?.properties?.worker?.enum) === JSON.stringify(expectedWorkers),
  'worker proposal schema must enumerate all four worker roles',
)

for (const worker of expectedWorkers) {
  const path = `prompts/workers/${worker}.md`
  try {
    check(statSync(join(root, path)).size > 100, `${path}: prompt is unexpectedly short`)
    const prompt = read(path)
    check(prompt.includes('immutable'), `${path}: must state immutable-snapshot policy`)
    check(prompt.includes('Do not request tools'), `${path}: must forbid tool use`)
  } catch (error) {
    failures.push(`${path}: missing: ${error.message}`)
  }
}

const overlay = read('dsh/civ6.cordis.yml')
check(overlay.includes("CIV_MCP_DISABLE_LUA: '1'"), 'overlay must disable arbitrary Lua')
check(overlay.includes("CIV_MCP_DISABLE_WEB_API: '1'"), 'overlay must disable the embedded dashboard')
check(overlay.includes("CIV_MCP_DATA_DIR: !!js process.cwd() + '/.civ6-mcp-data'"), 'overlay must keep Civ telemetry in the workspace')
check(overlay.includes("UV_CACHE_DIR: !!js process.cwd() + '/.uv-cache'"), 'overlay must keep the uv cache in the workspace')
check(overlay.includes('toolCallTimeoutMs: 720000'), 'overlay must allow long end-turn calls')
check(overlay.includes('toolName: civ_advisor'), 'overlay must define the safe advisor route')
check(/toolFilter:\s*\n\s*allow: \[\]/m.test(overlay), 'advisor workers must have an empty tool allowlist')
for (const id of ['tool-subagent', 'tool-subagent-fork', 'tool-workflow', 'tool-ralph']) {
  check(
    new RegExp(`- id: ${id}\\n\\s+disabled: true`).test(overlay),
    `${id} must be disabled`,
  )
}

const server = read('src/civ_mcp/server.py')
const toolCount = (server.match(/^@mcp\.tool/gm) ?? []).length
const manifest = parseJson('baseline/manifest.json')
check(
  toolCount === manifest?.civ6Mcp?.expectedMcpTools,
  `MCP tool count ${toolCount} differs from baseline ${manifest?.civ6Mcp?.expectedMcpTools}`,
)

const packageJson = parseJson('package.json')
check(
  packageJson?.dependencies?.['@deepseek-ai/dsh'] === manifest?.deepseekHarness?.version,
  'DSH package and baseline versions must match',
)
check(packageJson?.dependencies?.ajv === '8.20.0', 'Ajv contract validator must remain exactly pinned')
check(
  packageJson?.scripts?.['test:orchestrator'] === 'node --test test/dsh/*.test.mjs',
  'orchestrator runtime test command must be registered',
)
check(
  packageJson?.scripts?.['qualify:mcp'] === 'bash scripts/qualify-mcp.sh',
  'MCP qualification command must be registered',
)

if (failures.length > 0) {
  console.error(`Static qualification failed (${failures.length}):`)
  for (const failure of failures) console.error(`- ${failure}`)
  process.exit(1)
}

console.log('Static qualification passed:')
console.log(`- ${schemas.length} fail-closed JSON schemas parsed`)
console.log(`- ${expectedWorkers.length} no-tool worker prompts checked`)
console.log(`- ${orchestratorRuntime.length} deterministic runtime artifacts checked`)
console.log(`- ${contractFixtures.length} contract fixtures parsed`)
console.log(`- DSH safety overlay checked`)
console.log(`- civ6-mcp tool inventory: ${toolCount}`)
console.log(`- DSH version pin: ${manifest.deepseekHarness.version}`)
