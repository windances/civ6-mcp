import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

import { resolveProposals } from '../../dsh/orchestrator/conflict-resolver.mjs'
import { validateSnapshot } from '../../dsh/orchestrator/contracts.mjs'

const here = dirname(fileURLToPath(import.meta.url))
const fixtureRoot = join(here, '..', '..', 'fixtures', 'dsh')
const load = (name) => JSON.parse(readFileSync(join(fixtureRoot, name), 'utf8'))
const snapshot = () => validateSnapshot(load('valid-snapshot.json'))

function proposal({ actionId, priority, unitId = 7, assessment = 'Military action' }) {
  const value = load('valid-military-proposal.json')
  value.priority = priority
  value.assessment = assessment
  value.actions[0].actionId = actionId
  value.actions[0].arguments.unit_id = unitId
  return value
}

test('survival deterministically wins a conflict over optional combat', () => {
  const result = resolveProposals(snapshot(), [
    proposal({ actionId: 'T42-military-attack', priority: 95 }),
    proposal({ actionId: 'T42-military-retreat', priority: 60, assessment: 'Retreat required for unit survival' }),
  ])
  assert.deepEqual(result.ordered.map((action) => action.actionId), ['T42-military-retreat'])
  assert.deepEqual(result.rejected, [{
    actionId: 'T42-military-attack',
    reason: 'target_conflict',
    target: 'unit:7',
    winnerActionId: 'T42-military-retreat',
  }])
})

test('independent unit actions remain serially ordered', () => {
  const result = resolveProposals(snapshot(), [
    proposal({ actionId: 'T42-military-low', priority: 30, unitId: 8 }),
    proposal({ actionId: 'T42-military-high', priority: 90, unitId: 7 }),
  ])
  assert.deepEqual(
    result.ordered.map((action) => action.actionId),
    ['T42-military-high', 'T42-military-low'],
  )
  assert.equal(result.rejected.length, 0)
  assert.equal(result.proposalErrors.length, 0)
})

test('resolution is stable when input proposal order changes', () => {
  const first = proposal({ actionId: 'T42-military-a', priority: 50, unitId: 7 })
  const second = proposal({ actionId: 'T42-military-b', priority: 50, unitId: 8 })
  const forward = resolveProposals(snapshot(), [first, second])
  const reverse = resolveProposals(snapshot(), [second, first])
  assert.deepEqual(forward.ordered, reverse.ordered)
})

test('one invalid worker does not block valid workers', () => {
  const invalid = proposal({ actionId: 'T42-military-invalid', priority: 100, unitId: 7 })
  invalid.actions[0].tool = 'run_lua'
  const valid = proposal({ actionId: 'T42-military-valid', priority: 50, unitId: 8 })
  const result = resolveProposals(snapshot(), [invalid, valid])
  assert.deepEqual(result.ordered.map((action) => action.actionId), ['T42-military-valid'])
  assert.equal(result.proposalErrors[0].code, 'forbidden_tool')
})
