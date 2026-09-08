import assert from 'node:assert/strict'
import test from 'node:test'

import { ActionLedger } from '../../dsh/orchestrator/action-ledger.mjs'

const action = { actionId: 'T42-military-001' }
const identity = { gameId: 'rome_123456', turn: 42 }
const result = {
  version: 1,
  gameId: identity.gameId,
  turn: identity.turn,
  actionId: action.actionId,
  status: 'executed',
  toolResult: 'OK',
  verified: true,
  observedEffects: ['Unit fortified'],
  replanRequired: false,
}

test('ledger claims once and records one schema-valid result', () => {
  const ledger = new ActionLedger(identity)
  ledger.claim(action, identity)
  ledger.record(result)
  assert.equal(ledger.has(action.actionId), true)
  assert.equal(ledger.result(action.actionId).verified, true)
  assert.equal(ledger.toJSON().results.length, 1)
})

test('duplicate claims and duplicate results fail closed', () => {
  const ledger = new ActionLedger(identity)
  ledger.claim(action, identity)
  assert.throws(() => ledger.claim(action, identity), (error) => error.code === 'duplicate_action_id')
  ledger.record(result)
  assert.throws(() => ledger.record(result), (error) => error.code === 'duplicate_execution_result')
})

test('stale identity and unclaimed results are rejected', () => {
  const ledger = new ActionLedger(identity)
  assert.throws(
    () => ledger.claim(action, { ...identity, turn: 43 }),
    (error) => error.code === 'stale_turn',
  )
  assert.throws(() => ledger.record(result), (error) => error.code === 'unclaimed_action')
})
