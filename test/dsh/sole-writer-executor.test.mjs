import assert from 'node:assert/strict'
import test from 'node:test'

import { SoleWriterExecutor } from '../../dsh/orchestrator/sole-writer-executor.mjs'

const identity = { gameId: 'rome_123456', turn: 42 }
const action = (actionId, unitId) => ({
  actionId,
  tool: 'unit_action',
  arguments: { unit_id: unitId, action: 'FORTIFY' },
  preconditions: [],
  expectedEffects: ['Unit fortified'],
  risk: 'low',
})
const plan = (...ordered) => ({ ...identity, ordered })

test('mutations execute serially and each effect is verified', async () => {
  const calls = []
  let active = 0
  let maxActive = 0
  const executor = new SoleWriterExecutor({
    readState: async () => identity,
    invokeTool: async (tool, args) => {
      active += 1
      maxActive = Math.max(maxActive, active)
      await new Promise((resolve) => setTimeout(resolve, 5))
      calls.push([tool, args.unit_id])
      active -= 1
      return 'OK'
    },
    verifyEffect: async () => ({ ok: true, observedEffects: ['Unit fortified'] }),
  })
  const result = await executor.execute(plan(
    action('T42-military-001', 7),
    action('T42-military-002', 8),
  ))
  assert.equal(maxActive, 1)
  assert.deepEqual(calls, [['unit_action', 7], ['unit_action', 8]])
  assert.equal(result.completed, true)
})

test('duplicate action IDs fail before any mutation', async () => {
  let calls = 0
  const executor = new SoleWriterExecutor({
    readState: async () => identity,
    invokeTool: async () => { calls += 1 },
    verifyEffect: async () => true,
  })
  const duplicate = action('T42-military-001', 7)
  await assert.rejects(
    executor.execute(plan(duplicate, { ...duplicate, arguments: { unit_id: 8 } })),
    (error) => error.code === 'duplicate_action_id',
  )
  assert.equal(calls, 0)
})

test('an ambiguous tool failure is verified without retrying', async () => {
  let invocations = 0
  let fortified = false
  const executor = new SoleWriterExecutor({
    readState: async () => ({ ...identity, fortified }),
    invokeTool: async () => {
      invocations += 1
      fortified = true
      throw new Error('tool response timed out')
    },
    verifyEffect: async (_action, { after }) => ({
      ok: after.fortified,
      observedEffects: after.fortified ? ['Unit fortified'] : [],
    }),
  })
  const result = await executor.execute(plan(action('T42-military-001', 7)))
  assert.equal(invocations, 1)
  assert.equal(result.results[0].status, 'executed')
  assert.equal(result.results[0].verified, true)
})

test('failed verification stops later actions', async () => {
  const calls = []
  const executor = new SoleWriterExecutor({
    readState: async () => identity,
    invokeTool: async (_tool, args) => { calls.push(args.unit_id); return 'OK' },
    verifyEffect: async () => false,
  })
  const result = await executor.execute(plan(
    action('T42-military-001', 7),
    action('T42-military-002', 8),
  ))
  assert.deepEqual(calls, [7])
  assert.equal(result.completed, false)
  assert.equal(result.results[0].status, 'failed')
})

test('stale state and failed preconditions prevent mutation', async () => {
  let calls = 0
  const stale = new SoleWriterExecutor({
    readState: async () => ({ ...identity, turn: 43 }),
    invokeTool: async () => { calls += 1 },
    verifyEffect: async () => true,
  })
  await assert.rejects(
    stale.execute(plan(action('T42-military-001', 7))),
    (error) => error.code === 'stale_turn',
  )

  const blocked = new SoleWriterExecutor({
    readState: async () => identity,
    checkPreconditions: async () => ({ ok: false, reason: 'Unit already moved' }),
    invokeTool: async () => { calls += 1 },
    verifyEffect: async () => true,
  })
  const result = await blocked.execute(plan(action('T42-military-002', 8)))
  assert.equal(calls, 0)
  assert.equal(result.results[0].status, 'rejected')
})
