import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

import {
  ContractError,
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
