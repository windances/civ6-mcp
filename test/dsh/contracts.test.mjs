import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

import {
  ContractError,
  EXECUTOR_TOOL_ALLOWLIST,
  FORBIDDEN_TOOLS,
  WORKER_PROPOSAL_TOOL_ALLOWLIST,
  WORKER_TOOL_ALLOWLISTS,
  validateProposal,
  validateSnapshot,
} from '../../dsh/orchestrator/contracts.mjs'

const here = dirname(fileURLToPath(import.meta.url))
const fixtureRoot = join(here, '..', '..', 'fixtures', 'dsh')
const fixture = (name) => JSON.parse(readFileSync(join(fixtureRoot, name), 'utf8'))
const validSnapshot = () => validateSnapshot(fixture('valid-snapshot.json'))

test('valid fixtures are accepted and deeply immutable', () => {
  const snapshot = validSnapshot()
  const proposal = validateProposal(fixture('valid-military-proposal.json'), { snapshot })
  assert.equal(proposal.actions[0].tool, 'unit_action')
  assert.equal(Object.isFrozen(proposal.actions[0].arguments), true)
  assert.throws(() => { proposal.actions[0].arguments.unit_id = 8 }, TypeError)
})

for (const [name, code] of [
  ['invalid-unknown-tool.json', 'forbidden_tool'],
  ['invalid-stale-turn.json', 'stale_turn'],
  ['invalid-missing-unit.json', 'missing_unit'],
]) {
  test(`${name} fails closed`, () => {
    assert.throws(
      () => validateProposal(fixture(name), { snapshot: validSnapshot() }),
      (error) => error instanceof ContractError && error.code === code,
    )
  })
}

test('action IDs are unique across worker boundaries', () => {
  const snapshot = validSnapshot()
  const proposal = fixture('valid-military-proposal.json')
  const seenActionIds = new Set()
  validateProposal(proposal, { snapshot, seenActionIds })
  assert.throws(
    () => validateProposal(proposal, { snapshot, seenActionIds }),
    (error) => error.code === 'duplicate_action_id',
  )
})

test('out-of-bounds coordinates are rejected', () => {
  const proposal = fixture('valid-military-proposal.json')
  proposal.actions[0].arguments.x = 100
  proposal.actions[0].arguments.y = 8
  assert.throws(
    () => validateProposal(proposal, { snapshot: validSnapshot() }),
    (error) => error.code === 'invalid_coordinate',
  )
})

test('one hundred malformed proposals are rejected before mutation', () => {
  let mutationCalls = 0
  const snapshot = validSnapshot()
  for (let index = 0; index < 100; index += 1) {
    const proposal = fixture('valid-military-proposal.json')
    proposal.actions[0].actionId = `T42-military-${String(index).padStart(3, '0')}`
    switch (index % 10) {
      case 0: delete proposal.assessment; break
      case 1: proposal.unexpected = true; break
      case 2: proposal.turn = 43; break
      case 3: proposal.actions[0].tool = 'run_lua'; break
      case 4: proposal.actions[0].arguments.unit_id = 999; break
      case 5: proposal.actions[0].arguments.x = -1; break
      case 6: proposal.worker = 'economy-cities'; break
      case 7: proposal.actions[0].actionId = `T41-military-${index}`; break
      case 8: proposal.actions.push(structuredClone(proposal.actions[0])); break
      case 9: proposal.confidence = 2; break
    }
    assert.throws(() => validateProposal(proposal, { snapshot }))
  }
  assert.equal(mutationCalls, 0)
})

// The strategy bans peace outright - both presets say "never call propose_peace" - and until
// 2026-10-02 that ban lived only in prose: the tool sat in the diplomacy-victory allowlist, so the
// sole writer could end a war the strategy says has no exit. A ruling with no machinery is a
// suggestion, so this pins the machinery.
test('propose_peace is refused, because the strategy forbids peace', () => {
  const proposal = fixture('valid-military-proposal.json')
  proposal.worker = 'diplomacy-victory'
  proposal.actions[0].tool = 'propose_peace'
  assert.throws(
    () => validateProposal(proposal, { snapshot: validSnapshot() }),
    (error) => {
      assert.equal(error instanceof ContractError, true)
      assert.equal(error.code, 'forbidden_tool')
      assert.match(error.message, /strategy directive forbids peace/)
      return true
    },
  )
})

test('the banned tool is in no allowlist, and the lists stay derived from each other', () => {
  for (const tools of Object.values(WORKER_TOOL_ALLOWLISTS)) {
    assert.equal(tools.includes('propose_peace'), false)
  }
  assert.equal(WORKER_PROPOSAL_TOOL_ALLOWLIST.includes('propose_peace'), false)
  assert.equal(EXECUTOR_TOOL_ALLOWLIST.includes('propose_peace'), false)
  assert.deepEqual([...FORBIDDEN_TOOLS], ['propose_peace'])
})
